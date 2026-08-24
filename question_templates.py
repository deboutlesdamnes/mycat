# -*- coding: utf-8 -*-
"""Deterministic templates that render knowledge-base fact entries into
structured MCAT-style questions.

Each template returns a dict conforming to question_schema.json. The correct
answer's position is rotated deterministically (via CRC32 of the question id)
so correct answers are not always option A.
"""
import zlib

from question_kb import SECTION_MAP


def _pos(qid):
    """Deterministic position 0..3 for the correct answer."""
    return zlib.crc32(qid.encode("utf-8")) % 4


def _meta(fact, qid, qtype, skill, subtype):
    return {
        "id": qid,
        "section": SECTION_MAP.get(fact["subject"], fact["subject"]),
        "subject": fact["subject"],
        "topic": fact["topic"],
        "knowledge_point": fact.get("kp", fact["topic"]),
        "type": qtype,
        "skill": skill,
        "subtype": subtype,
    }


def _assemble(qid, base, options, correct_index):
    """Rotate options so the correct answer lands at a deterministic position."""
    shift = _pos(qid) % len(options)
    options = options[shift:] + options[:shift]
    base["options"] = options
    base["correct"] = (correct_index - shift) % len(options)
    return base


def t_recall(fact):
    qid = f"gen-{fact['id']}-recall"
    base = _meta(fact, qid, "discrete", "skill1", "recall")
    base["question"] = f"Which of the following best describes the {fact['term']}?"
    base["explanation"] = fact["explanation"]
    options = [fact["definition"]] + list(fact["false"][:3])
    return _assemble(qid, base, options, 0)


def t_except(fact):
    qid = f"gen-{fact['id']}-except"
    base = _meta(fact, qid, "discrete", "skill1", "except")
    base["question"] = f"All of the following are true of the {fact['term']} EXCEPT:"
    base["explanation"] = f"The exception (the false statement) is the correct answer. {fact['explanation']}"
    options = [fact["false"][0]] + list(fact["true"][:3])
    return _assemble(qid, base, options, 0)


def t_roman(fact):
    qid = f"gen-{fact['id']}-roman"
    base = _meta(fact, qid, "discrete", "skill1", "roman")
    t0, t1 = fact["true"][0], fact["true"][1]
    f0, f1 = fact["false"][0], fact["false"][1]
    base["question"] = (
        f"Which of the following statements regarding the {fact['term']} is/are correct?\n"
        f"I. {t0}\n"
        f"II. {f0}\n"
        f"III. {t1}\n"
        f"IV. {f1}"
    )
    base["explanation"] = fact["explanation"]
    options = [
        "I and III only",
        "I and II only",
        "II and IV only",
        "I, II, III, and IV",
    ]
    return _assemble(qid, base, options, 0)


def t_sequence(fact):
    qid = f"gen-{fact['id']}-sequence"
    base = _meta(fact, qid, "discrete", "skill1", "sequence")
    seq = fact["sequence"]
    base["question"] = f"Which of the following is the correct order of {fact['process']}?"
    base["explanation"] = fact["explanation"]
    correct_text = " -> ".join(seq)
    swapped = list(seq)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    options = [
        correct_text,
        " -> ".join(reversed(seq)),
        " -> ".join(swapped),
        " -> ".join(seq[1:] + seq[:1]),
    ]
    return _assemble(qid, base, options, 0)


TEMPLATE_FUNCS = {
    "recall": t_recall,
    "except": t_except,
    "roman": t_roman,
    "sequence": t_sequence,
}
