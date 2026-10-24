"""Rubric scoring of the user's side of a debate.

Scores are computed from observable features of the user's arguments (citations,
fallacy flags, rebuttal markers, length), so every number can be explained and
the result is the same with or without an LLM.
"""

import re
from typing import Any

EVIDENCE_PATTERN = re.compile(
    r"\[\d+\]|https?://|according to|study found|data shows|\b\d{2,}\b", re.I
)
REBUTTAL_PATTERN = re.compile(r"\b(but|however|although|your point|you argued|that claim)\b", re.I)

TIPS = [
    "Attach a credible source or concrete example to factual claims.",
    "State the strongest opposing argument before rebutting it.",
    "Replace absolute language with a testable, bounded claim.",
]


def _clamp(value: float) -> int:
    return max(0, min(10, int(value)))


# The client sends this to let the AI open the debate; it is not the user's argument.
OPENING_PROMPT = "Give your opening argument."


def score_debate(turns: list[dict[str, Any]]) -> dict[str, Any]:
    turns = [turn for turn in turns if turn.get("argument", "").strip() != OPENING_PROMPT]
    arguments = [turn.get("argument", "") for turn in turns]
    words = " ".join(arguments).split()
    fallacy_count = sum(len(turn.get("fallacies", [])) for turn in turns)
    evidenced = sum(bool(EVIDENCE_PATTERN.search(arg)) for arg in arguments)
    rebuttals = sum(bool(REBUTTAL_PATTERN.search(arg)) for arg in arguments)
    avg_words = len(words) / max(1, len(arguments))

    evidence = min(10, 2 + evidenced * 3)
    rubric = {
        "Evidence use": (
            evidence,
            "Your arguments include cited sources, attribution, or checkable data."
            if evidence > 2
            else "Support factual claims with a source, example, or measurable detail.",
        ),
        "Logical validity": (
            max(1, min(10, 8 - fallacy_count)),
            f"{fallacy_count} fallacy flag(s) affected the score; make each premise explicit "
            "and connect it to the conclusion.",
        ),
        "Rebuttal quality": (
            min(10, 3 + rebuttals * 2),
            f"{rebuttals} argument(s) directly engaged a counterpoint; address the strongest "
            "opposing reason.",
        ),
        "Clarity": (
            min(10, max(3, 9 - abs(avg_words - 45) // 15)),
            f"Judged from {len(words)} words across {len(arguments)} turn(s); use concise claims "
            "with clear structure.",
        ),
        "Fallacy control": (
            max(0, 10 - fallacy_count * 2),
            f"{fallacy_count} detected fallacy flag(s); replace broad or personal claims with "
            "bounded evidence.",
        ),
    }
    scores = {
        name: {"score": _clamp(value), "justification": reason}
        for name, (value, reason) in rubric.items()
    }
    overall = round(sum(s["score"] for s in scores.values()) / len(scores), 1)
    if overall >= 8:
        verdict = "A persuasive case with strong support and disciplined rebuttals."
    elif overall >= 5:
        verdict = (
            "A promising case; tighter evidence and more direct rebuttals would make it stronger."
        )
    else:
        verdict = (
            "The case needs clearer claims, stronger evidence, and closer attention to reasoning."
        )
    return {"scores": scores, "overall": overall, "verdict": verdict, "tips": list(TIPS)}
