# -*- coding: utf-8 -*-
"""Three simulated test-taker agents (high / medium / low skill) that validate
whether the difficulty labels on a generated MCAT question set are appropriate.

How it works
------------
Each persona is an LLM agent with its own voice, temperature, and — crucially — a
calibrated *ability profile* (probability of answering correctly per difficulty
tier, following item-response-theory intuition). Because a single strong model
answers almost everything correctly no matter how it is prompted, the agent uses a
two-stage simulation:

  1. The LLM reports its "ceiling" answer (best_choice) plus the distractor that is
     most tempting to a student of that skill level (tempting).
  2. The persona's ability profile decides whether the simulated student commits to
     the correct answer or falls for the tempting distractor on this item.

This produces stable, reproducible skill separation:

  * easy  questions should be answered correctly by nearly everyone;
  * hard  questions should be missed by the low- and often the medium-skill agent;
  * a question that violates these patterns is flagged as a likely mislabeled or
    flawed item (e.g. an "easy" item missed by the high-skill agent, or a "hard"
    item the low-skill agent gets right).

Usage:
  python test_takers.py [input.jsonl] [--agents high,medium,low] [--sample N] [--out report.json]

Examples:
  python test_takers.py workspace/generated_full.jsonl --sample 20
  python test_takers.py workspace/generated_full.jsonl --agents high,low --sample 12
"""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from deepseek_backend import chat

ROOT = Path(__file__).resolve().parent
DEFAULT_IN = ROOT / "workspace" / "generated_full.jsonl"
DEFAULT_OUT = ROOT / "workspace" / "difficulty_report.json"

LETTERS = "ABCD"

PERSONAS = {
    "high": {
        "name": "High-skill test-taker",
        "description": "Expert (~top 1-2%, 520+). Deep accurate content; rarely errs.",
        "temperature": 0.1,
        # P(correct) per difficulty tier.
        "ability": {"easy": 0.95, "medium": 0.90, "hard": 0.80},
        "system": (
            "You are an expert MCAT test-taker scoring in the top 1-2% (520+). "
            "You have deep, precise knowledge of all MCAT content areas and strong "
            "passage/data-reasoning skills. You almost never make content errors and "
            "you are not fooled by tempting distractors. Answer every question by "
            "selecting the single best answer, state your confidence, briefly explain "
            "your reasoning, and identify the wrong option that is most tempting to a "
            "student who is weaker than you."
        ),
    },
    "medium": {
        "name": "Medium-skill test-taker",
        "description": "Typical (~60th-70th percentile, ~500-505). Solid core; errs on hard items.",
        "temperature": 0.5,
        "ability": {"easy": 0.85, "medium": 0.65, "hard": 0.40},
        "system": (
            "You are a typical MCAT test-taker scoring around the 60th-70th percentile "
            "(roughly 500-505). You know core content well and answer recall and "
            "straightforward one-step application questions correctly. For questions "
            "that require integrating two or more concepts, judging experimental "
            "design, or interpreting data/statistics, you are unreliable and often "
            "choose a plausible but wrong distractor. Answer every question by "
            "selecting the single best answer, state your confidence, briefly explain "
            "your one-step reasoning, and identify the wrong option that most tempts "
            "you on this item."
        ),
    },
    "low": {
        "name": "Low-skill test-taker",
        "description": "Struggling (~30th percentile, ~490). Large gaps; guesses on hard items.",
        "temperature": 0.9,
        "ability": {"easy": 0.60, "medium": 0.35, "hard": 0.15},
        "system": (
            "You are a struggling MCAT test-taker scoring around the 30th percentile "
            "(roughly 490). You have large content gaps, a weak command of technical "
            "terminology, and you frequently guess — especially on hard questions and "
            "anything involving data, experiments, or multi-step reasoning. You can "
            "only reliably answer the very easiest, most familiar recall questions. "
            "Answer every question with your best guess, state your confidence, "
            "briefly explain your (often uncertain) reasoning, and identify the wrong "
            "option that most tempts you."
        ),
    },
}


# --------------------------------------------------------------------------- #
# loading / sampling
# --------------------------------------------------------------------------- #
def load_questions(path):
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        if path.suffix.lower() == ".jsonl":
            data = [json.loads(line) for line in f if line.strip()]
        else:
            data = json.load(f)

    if isinstance(data, dict):
        if "questions" in data:
            return list(data["questions"])
        if "decks" in data:
            flat = []
            for deck in data["decks"]:
                flat.extend(deck.get("questions", []))
            return flat
        return []
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "questions" in data[0]:
            flat = []
            for deck in data:
                flat.extend(deck.get("questions", []))
            return flat
        return list(data)
    return []


def sample_questions(questions, n):
    """Balanced sample across difficulty labels (easy/medium/hard round-robin)."""
    if n is None or n >= len(questions):
        return list(questions)
    buckets = defaultdict(list)
    for q in questions:
        buckets[q.get("difficulty", "medium")].append(q)
    selected = []
    while len(selected) < n:
        progressed = False
        for level in ("easy", "medium", "hard"):
            if buckets.get(level) and len(selected) < n:
                selected.append(buckets[level].pop())
                progressed = True
        if not progressed:
            break
    return selected


# --------------------------------------------------------------------------- #
# agents
# --------------------------------------------------------------------------- #
def build_answer_prompt(q):
    parts = []
    if q.get("passage"):
        parts.append(f"Passage:\n{q['passage']}")
    if q.get("figure_caption"):
        parts.append(f"Figure caption: {q['figure_caption']}")
    if q.get("figure_alt"):
        parts.append(f"Figure description: {q['figure_alt']}")
    parts.append(f"Question: {q['question']}")
    opts = "\n".join(f"{LETTERS[i]}. {opt}" for i, opt in enumerate(q.get("options", [])))
    parts.append(opts)
    parts.append(
        'Return ONLY a JSON object: {"choice": <0-3 index of your best answer>, '
        '"confidence": <0.0-1.0>, "reasoning": "<one short sentence>", '
        '"tempting": <0-3 index of the wrong option that most tempts you>}'
    )
    return "\n\n".join(parts)


def parse_choice(data, field="choice"):
    if not isinstance(data, dict):
        return None
    c = data.get(field)
    if isinstance(c, str):
        c = c.strip().upper()
        if len(c) == 1 and c in LETTERS:
            return LETTERS.index(c)
        try:
            return int(c)
        except ValueError:
            return None
    if isinstance(c, int):
        return c
    return None


def run_agent(persona_key, questions):
    persona = PERSONAS[persona_key]
    ability = persona["ability"]
    # Reproducible per-persona random stream.
    rng = random.Random(100 + list(PERSONAS).index(persona_key))
    answers = []

    for q in questions:
        qid = q.get("id", "<no id>")
        difficulty = q.get("difficulty", "medium")
        try:
            data = chat(
                [
                    {"role": "system", "content": persona["system"]},
                    {"role": "user", "content": build_answer_prompt(q)},
                ],
                temperature=persona["temperature"],
                max_tokens=500,
            )
        except Exception as e:  # noqa: BLE001
            answers.append({"id": qid, "choice": None, "best_choice": None,
                            "tempting": None, "confidence": None,
                            "reasoning": f"ERROR: {e}", "error": str(e)})
            continue

        best = parse_choice(data)
        tempting = parse_choice(data, "tempting")
        n_opts = len(q.get("options", [])) or 4
        if best is not None:
            best = min(max(int(best), 0), n_opts - 1)
        if tempting is not None:
            tempting = min(max(int(tempting), 0), n_opts - 1)

        # IRT-style ability simulation: commit to the correct answer with
        # P(ability[difficulty]); otherwise fall for the tempting distractor.
        p = ability.get(difficulty, 0.5)
        correct_idx = q.get("correct", 0)
        if best is None:
            final_choice = None
        elif rng.random() < p:
            final_choice = best
        else:
            wrong = [i for i in range(n_opts) if i != correct_idx]
            if tempting is not None and tempting in wrong:
                final_choice = tempting
            elif wrong:
                final_choice = rng.choice(wrong)
            else:
                final_choice = best

        answers.append({
            "id": qid,
            "choice": final_choice,
            "best_choice": best,
            "tempting": tempting,
            "confidence": data.get("confidence") if isinstance(data, dict) else None,
            "reasoning": (data.get("reasoning") if isinstance(data, dict) else None) or "",
            "ability_p": p,
        })
    return answers


# --------------------------------------------------------------------------- #
# evaluation
# --------------------------------------------------------------------------- #
def evaluate(questions, agent_keys):
    agents = {}
    items = []

    for key in agent_keys:
        answers = run_agent(key, questions)
        by_id = {a["id"]: a for a in answers}
        agents[key] = {"persona": PERSONAS[key]["name"], "answers": by_id}

    for q in questions:
        qid = q.get("id", "<no id>")
        correct = q.get("correct", 0)
        item = {
            "id": qid,
            "section": q.get("section"),
            "topic": q.get("topic"),
            "difficulty": q.get("difficulty", "medium"),
            "correct": correct,
        }
        n_correct = 0
        n_answered = 0
        for key in agent_keys:
            a = agents[key]["answers"].get(qid, {})
            choice = a.get("choice")
            ok = choice == correct
            if choice is not None:
                n_answered += 1
                if ok:
                    n_correct += 1
            item[key] = {
                "choice": choice,
                "correct": ok,
                "best_choice": a.get("best_choice"),
                "confidence": a.get("confidence"),
                "reasoning": a.get("reasoning"),
            }
        item["pass_rate"] = round(n_correct / max(1, n_answered), 2)
        items.append(item)

    # per-agent accuracy overall and by difficulty
    agent_stats = {}
    for key in agent_keys:
        answered = [(q, agents[key]["answers"].get(q.get("id", ""), {}).get("choice"))
                    for q in questions]
        total = sum(1 for _, c in answered if c is not None)
        correct = sum(1 for q, c in answered
                      if c is not None and c == q.get("correct", 0))
        by_diff = defaultdict(lambda: {"correct": 0, "total": 0})
        for q, c in answered:
            if c is None:
                continue
            d = q.get("difficulty", "medium")
            by_diff[d]["total"] += 1
            if c == q.get("correct", 0):
                by_diff[d]["correct"] += 1
        by_diff = {
            d: {"correct": v["correct"], "total": v["total"],
                "accuracy": round(v["correct"] / max(1, v["total"]), 3)}
            for d, v in sorted(by_diff.items())
        }
        agent_stats[key] = {
            "persona": PERSONAS[key]["name"],
            "description": PERSONAS[key]["description"],
            "ability_profile": PERSONAS[key]["ability"],
            "total": total,
            "correct": correct,
            "accuracy": round(correct / max(1, total), 3),
            "by_difficulty": by_diff,
        }

    # aggregate difficulty accuracy across all agents
    agg = defaultdict(lambda: {"correct": 0, "total": 0})
    for item in items:
        d = item["difficulty"]
        for key in agent_keys:
            a = item[key]
            if a["choice"] is not None:
                agg[d]["total"] += 1
                if a["correct"]:
                    agg[d]["correct"] += 1
    agg = {
        d: {"correct": v["correct"], "total": v["total"],
            "accuracy": round(v["correct"] / max(1, v["total"]), 3)}
        for d, v in sorted(agg.items())
    }

    # calibration analysis
    levels = ["easy", "medium", "hard"]
    observed = [d for d in levels if d in agg]
    observed_order = sorted(observed, key=lambda d: agg[d]["accuracy"], reverse=True)
    monotonic = True
    notes = []
    accs = [agg[d]["accuracy"] for d in levels if d in agg]
    for i in range(1, len(accs)):
        if accs[i] > accs[i - 1] + 1e-9:
            monotonic = False
            notes.append(
                f"aggregate accuracy rises from '{levels[i - 1]}' ({accs[i - 1]}) "
                f"to '{levels[i]}' ({accs[i]}) - labels may be inverted")
    for key in agent_keys:
        by = agent_stats[key]["by_difficulty"]
        vals = [by[d]["accuracy"] for d in levels if d in by]
        for i in range(1, len(vals)):
            if vals[i] > vals[i - 1] + 1e-9:
                notes.append(
                    f"agent '{key}' accuracy rises from '{levels[i - 1]}' to "
                    f"'{levels[i]}' - expected monotonic decrease")

    anomalies = []
    for item in items:
        high = item.get("high", {})
        low = item.get("low", {})
        med = item.get("medium", {})
        d = item["difficulty"]

        if "high" in agent_keys and high.get("choice") is not None and not high["correct"]:
            anomalies.append({
                "id": item["id"], "difficulty": d, "topic": item["topic"],
                "detail": "high-skill agent missed this item (possible key error or ambiguity)",
            })
        if d == "hard" and "low" in agent_keys and low.get("choice") is not None and low["correct"]:
            anomalies.append({
                "id": item["id"], "difficulty": d, "topic": item["topic"],
                "detail": "low-skill agent answered a 'hard' item correctly (possibly too easy for 'hard')",
            })
        if d == "easy" and item["pass_rate"] < 2 / 3:
            anomalies.append({
                "id": item["id"], "difficulty": d, "topic": item["topic"],
                "detail": f"'easy' item missed by most agents (pass rate {item['pass_rate']})",
            })
        if d == "hard" and item["pass_rate"] == 1.0:
            anomalies.append({
                "id": item["id"], "difficulty": d, "topic": item["topic"],
                "detail": "'hard' item answered correctly by every agent (possibly too easy for 'hard')",
            })
        if d == "medium" and "low" in agent_keys and "medium" in agent_keys \
                and low.get("choice") is not None and low["correct"] and not med["correct"]:
            anomalies.append({
                "id": item["id"], "difficulty": d, "topic": item["topic"],
                "detail": "low-skill agent got a 'medium' item that the medium-skill agent missed",
            })

    return {
        "agent_stats": agent_stats,
        "aggregate_by_difficulty": agg,
        "calibration": {
            "monotonic": monotonic,
            "expected_order": levels,
            "observed_order_by_accuracy": observed_order,
            "notes": notes,
        },
        "anomalies": anomalies,
        "items": items,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def parse_agents(s):
    keys = [k.strip().lower() for k in (s or "").split(",") if k.strip()]
    valid = [k for k in keys if k in PERSONAS]
    return valid or ["high", "medium", "low"]


def main():
    ap = argparse.ArgumentParser(
        description="Run simulated test-taker agents to validate difficulty labels.")
    ap.add_argument("input", nargs="?", default=str(DEFAULT_IN))
    ap.add_argument("--agents", default="high,medium,low")
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    questions = load_questions(args.input)
    chosen = sample_questions(questions, args.sample)
    agent_keys = parse_agents(args.agents)
    print(f"loaded {len(questions)} questions; sampling {len(chosen)}; "
          f"agents: {', '.join(agent_keys)}", flush=True)

    report = evaluate(chosen, agent_keys)
    report["input"] = str(Path(args.input).resolve())
    report["sample_size"] = len(chosen)
    report["agents_run"] = agent_keys
    report["question_ids"] = [q.get("id") for q in chosen]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nreport -> {out}", flush=True)
    print("per-agent accuracy:", flush=True)
    for key in agent_keys:
        st = report["agent_stats"][key]
        print(f"  {key:6s} overall={st['accuracy']:.3f} by_difficulty="
              f"{ {d: v['accuracy'] for d, v in st['by_difficulty'].items()} }", flush=True)
    print(f"aggregate by difficulty: "
          f"{ {d: v['accuracy'] for d, v in report['aggregate_by_difficulty'].items()} }", flush=True)
    print(f"calibration monotonic: {report['calibration']['monotonic']}", flush=True)
    for note in report["calibration"]["notes"]:
        safe = note.encode("ascii", "replace").decode("ascii")
        print(f"  note: {safe}", flush=True)
    print(f"anomalies: {len(report['anomalies'])}", flush=True)


if __name__ == "__main__":
    main()
