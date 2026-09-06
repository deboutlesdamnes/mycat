# -*- coding: utf-8 -*-
"""Evaluator agent: audit a generated MCAT question set for corpus accuracy and coverage.

Two complementary audits run in one pass:

1. Coverage audit (deterministic, no LLM): compares the question set against the
   full-length content spec in gen_config.py. Reports missing/under-covered topics,
   extra topics, skill mix vs. AAMC targets, difficulty mix, passage/discrete mix,
   and duplicate questions.

2. Accuracy audit (LLM): for a (configurable, section-stratified) sample of
   questions, retrieves the most relevant corpus excerpts with retrieve.retrieve()
   and asks the DeepSeek backend to fact-check the stem, key, distractors, and
   explanation for scientific correctness and consistency with the corpus.

Usage:
  python audit_questions.py [input.jsonl] [--sample N|all] [--out report.json]

Examples:
  python audit_questions.py workspace/generated_full.jsonl --sample 30
  python audit_questions.py workspace/generated_full.jsonl --sample all
"""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from deepseek_backend import chat
from gen_config import build_tasks, total_questions
from retrieve import retrieve

ROOT = Path(__file__).resolve().parent
DEFAULT_IN = ROOT / "workspace" / "generated_full.jsonl"
DEFAULT_OUT = ROOT / "workspace" / "audit_report.json"

# AAMC science-section reasoning skill targets (percent of science questions).
SCIENCE_SKILL_TARGETS = {"skill1": 35, "skill2": 45, "skill3": 20, "skill4": 5}
# AAMC CARS skill targets (percent of CARS questions).
CARS_SKILL_TARGETS = {"cars-foc": 30, "cars-rwt": 30, "cars-rbt": 40}
# Expected passage/discrete split per science section (50/50 plan).
EXPECTED_PASSAGE_DISCRETE = {"passage": 30, "discrete": 29}

AUDITOR_SYSTEM = """\
You are a rigorous MCAT content auditor. You are given a practice question (as JSON,
including its designated correct answer index and explanation) plus reference excerpts
retrieved from the project study corpus.

Your job is to verify:
1. The question STEM is clear, unambiguous, answerable, and factually sound.
2. The designated CORRECT answer is actually correct and is the single best answer.
3. Each DISTRACTOR is actually incorrect (or clearly inferior), never arguably correct.
4. The EXPLANATION is factually accurate and teaches correct MCAT-level science.
5. Corpus consistency: where the excerpts cover the topic, the question's content should
   agree with them. Flag any contradiction with the excerpts. If the excerpts do not
   cover the topic, judge against standard, uncontroversial MCAT science instead.

Return ONLY a JSON object (no markdown fences, no commentary) with this exact shape:
{
  "verdict": "accurate" | "minor_issue" | "inaccurate",
  "confidence": 0.0,
  "issues": [{"severity": "blocking" | "minor", "detail": "..."}],
  "evidence": "short quote or reasoning supporting your verdict"
}

Use "accurate" only if the key, distractors, and explanation are all correct.
Use "minor_issue" for wording/scope concerns that do not make the designated answer wrong.
Use "inaccurate" if the key is wrong, a distractor is also correct, or the explanation is
factually wrong. Set "confidence" between 0.0 (guessing) and 1.0 (certain).
"""


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def load_questions(path):
    """Load questions from a .jsonl file, a .json list, or a site deck JSON."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        if path.suffix.lower() == ".jsonl":
            data = [json.loads(line) for line in f if line.strip()]
        else:
            data = json.load(f)

    if isinstance(data, dict):
        # e.g. {"questions": [...]} or {"decks": [{"questions": [...]}]}
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


def norm(s):
    return (s or "").strip().lower()


def stratified_sample(questions, n, key):
    """Round-robin across distinct key values so the sample spans sections/difficulties."""
    if n is None or n >= len(questions):
        return list(questions)
    random.seed(42)
    buckets = defaultdict(list)
    for q in questions:
        buckets[key(q)].append(q)
    for bucket in buckets.values():
        random.shuffle(bucket)
    selected = []
    while len(selected) < n:
        progressed = False
        for k in sorted(buckets):
            if buckets[k] and len(selected) < n:
                selected.append(buckets[k].pop())
                progressed = True
        if not progressed:
            break
    return selected


# --------------------------------------------------------------------------- #
# deterministic coverage audit
# --------------------------------------------------------------------------- #
def _pct(counter):
    total = sum(counter.values())
    if total == 0:
        return {}
    return {k: round(100.0 * v / total, 1) for k, v in sorted(counter.items())}


def coverage_audit(questions):
    tasks = build_tasks()
    expected_total = total_questions()

    topic_index = defaultdict(int)          # (norm section, norm topic) -> count
    section_counts = Counter()
    for q in questions:
        topic_index[(norm(q.get("section")), norm(q.get("topic")))] += 1
        section_counts[q.get("section") or "<none>"] += 1

    spec_index = defaultdict(int)
    task_by_key = {}
    for t in tasks:
        key = (norm(t["section"]), norm(t["topic"]))
        spec_index[key] += t["n"]
        task_by_key.setdefault(key, t)

    missing, under, covered = [], [], []
    for key, need in spec_index.items():
        got = topic_index.get(key, 0)
        entry = {
            "section": task_by_key[key]["section"],
            "subject": task_by_key[key]["subject"],
            "topic": task_by_key[key]["topic"],
            "expected": need,
            "actual": got,
        }
        if got == 0:
            missing.append(entry)
        elif got < need:
            under.append(entry)
        else:
            covered.append(entry)

    extra = [
        {"section": key[0], "topic": key[1], "actual": got}
        for key, got in topic_index.items()
        if key not in spec_index
    ]

    # skill mix
    science_skills = Counter()
    cars_skills = Counter()
    for q in questions:
        sk = q.get("skill") or "unknown"
        if norm(q.get("section")) == norm("Critical Analysis and Reasoning Skills"):
            cars_skills[sk] += 1
        else:
            science_skills[sk] += 1

    science_actual_pct = _pct(science_skills)
    science_delta = {
        k: round(science_actual_pct.get(k, 0.0) - v, 1)
        for k, v in SCIENCE_SKILL_TARGETS.items()
    }
    cars_actual_pct = _pct(cars_skills)
    cars_delta = {
        k: round(cars_actual_pct.get(k, 0.0) - v, 1)
        for k, v in CARS_SKILL_TARGETS.items()
    }

    # difficulty mix
    difficulty = Counter(q.get("difficulty", "medium") for q in questions)

    # passage/discrete mix per section
    type_by_section = defaultdict(Counter)
    for q in questions:
        type_by_section[q.get("section") or "<none>"][q.get("type", "discrete")] += 1
    type_by_section = {sec: dict(c) for sec, c in sorted(type_by_section.items())}

    # duplicates
    seen_ids = set()
    duplicate_ids = []
    stem_index = {}
    duplicate_stems = []
    for q in questions:
        qid = q.get("id", "<no id>")
        if qid in seen_ids:
            duplicate_ids.append(qid)
        seen_ids.add(qid)

        stem = norm(q.get("question"))
        if stem in stem_index:
            duplicate_stems.append({"id": qid, "duplicate_of": stem_index[stem]})
        else:
            stem_index[stem] = qid

    return {
        "expected_total": expected_total,
        "actual_total": len(questions),
        "section_counts": dict(section_counts),
        "missing_topics": missing,
        "under_covered_topics": under,
        "covered_topics": len(covered),
        "extra_topics": extra,
        "coverage_rate": round(100.0 * len(covered) / max(1, len(spec_index)), 1),
        "science_skill_mix": {
            "targets": SCIENCE_SKILL_TARGETS,
            "actual_pct": science_actual_pct,
            "delta_pct": science_delta,
            "raw_counts": dict(science_skills),
        },
        "cars_skill_mix": {
            "targets": CARS_SKILL_TARGETS,
            "actual_pct": cars_actual_pct,
            "delta_pct": cars_delta,
            "raw_counts": dict(cars_skills),
        },
        "difficulty_mix": dict(difficulty),
        "type_by_section": type_by_section,
        "expected_passage_discrete_per_science_section": EXPECTED_PASSAGE_DISCRETE,
        "duplicate_ids": duplicate_ids,
        "duplicate_stems": duplicate_stems,
    }


# --------------------------------------------------------------------------- #
# LLM accuracy audit
# --------------------------------------------------------------------------- #
def build_accuracy_prompt(q):
    topic = q.get("topic") or q.get("knowledge_point") or ""
    excerpts = retrieve(topic, k=3, max_chars=1500)
    ref = ""
    for i, ex in enumerate(excerpts, 1):
        ref += (
            f"\n--- corpus excerpt {i} (file: {ex['file']}, score {ex['score']}) ---\n"
            f"{ex['text']}\n"
        )
    if not ref:
        ref = ("(no corpus excerpt matched this topic; judge against standard, "
               "uncontroversial MCAT science)")

    payload = {
        "id": q.get("id"),
        "section": q.get("section"),
        "subject": q.get("subject"),
        "topic": q.get("topic"),
        "question": q.get("question"),
        "options": q.get("options"),
        "correct_index": q.get("correct"),
        "correct_text": (q.get("options") or [""])[q.get("correct", 0)] if q.get("options") else None,
        "explanation": q.get("explanation"),
    }
    if q.get("passage"):
        payload["passage"] = q["passage"]

    return (
        f"Reference material from the project corpus:\n{ref}\n\n"
        f"Question under review (JSON):\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
    )


def accuracy_audit(questions, sample):
    chosen = questions if sample is None else stratified_sample(
        questions, sample, key=lambda q: q.get("section")
    )
    results = []
    for q in chosen:
        qid = q.get("id", "<no id>")
        try:
            data = chat(
                [
                    {"role": "system", "content": AUDITOR_SYSTEM},
                    {"role": "user", "content": build_accuracy_prompt(q)},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
        except Exception as e:  # noqa: BLE001
            results.append({
                "id": qid,
                "section": q.get("section"),
                "topic": q.get("topic"),
                "verdict": "error",
                "issues": [{"severity": "blocking", "detail": str(e)}],
            })
            continue

        if not isinstance(data, dict):
            results.append({
                "id": qid, "section": q.get("section"), "topic": q.get("topic"),
                "verdict": "malformed", "issues": [{"severity": "blocking",
                                                    "detail": "non-object LLM response"}],
            })
            continue

        verdict = data.get("verdict")
        if verdict not in ("accurate", "minor_issue", "inaccurate"):
            verdict = "needs_review"
        results.append({
            "id": qid,
            "section": q.get("section"),
            "topic": q.get("topic"),
            "difficulty": q.get("difficulty"),
            "verdict": verdict,
            "confidence": data.get("confidence"),
            "issues": data.get("issues", []),
            "evidence": data.get("evidence"),
        })

    verdict_counts = Counter(r["verdict"] for r in results)
    flagged = [r for r in results if r["verdict"] in ("inaccurate", "minor_issue",
                                                      "needs_review", "error", "malformed")]
    return {
        "sampled": len(results),
        "verdict_counts": dict(verdict_counts),
        "flag_rate": round(100.0 * len(flagged) / max(1, len(results)), 1),
        "flagged": flagged,
        "results": results,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def parse_sample(s):
    if s is None:
        return None
    s = str(s).strip().lower()
    if s in ("all", "-1", "none"):
        return None
    return int(s)


def main():
    ap = argparse.ArgumentParser(description="Audit a generated MCAT question set.")
    ap.add_argument("input", nargs="?", default=str(DEFAULT_IN))
    ap.add_argument("--sample", default="30",
                    help="number of questions to fact-check with the LLM, or 'all'")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    questions = load_questions(args.input)
    print(f"loaded {len(questions)} questions from {args.input}", flush=True)

    print("running deterministic coverage audit ...", flush=True)
    coverage = coverage_audit(questions)

    sample = parse_sample(args.sample)
    print(f"running LLM accuracy audit on {('all ' + str(len(questions))) if sample is None else sample} question(s) ...",
          flush=True)
    accuracy = accuracy_audit(questions, sample)

    report = {
        "input": str(Path(args.input).resolve()),
        "coverage": coverage,
        "accuracy": accuracy,
        "summary": {
            "actual_total": coverage["actual_total"],
            "expected_total": coverage["expected_total"],
            "coverage_rate_pct": coverage["coverage_rate"],
            "missing_topic_count": len(coverage["missing_topics"]),
            "under_covered_topic_count": len(coverage["under_covered_topics"]),
            "extra_topic_count": len(coverage["extra_topics"]),
            "duplicate_id_count": len(coverage["duplicate_ids"]),
            "duplicate_stem_count": len(coverage["duplicate_stems"]),
            "accuracy_audit": accuracy["verdict_counts"],
            "accuracy_flag_rate_pct": accuracy["flag_rate"],
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nreport -> {out}", flush=True)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
