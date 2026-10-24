import re

RULES = [
    (
        "Ad hominem",
        r"\b(idiot|stupid|ignorant|corrupt|moron)\b",
        "Attacks a person instead of addressing their reasoning.",
    ),
    (
        "Straw man",
        r"\b(so you.re saying|you just want|you believe everyone)\b",
        "Recasts the opposing view in an easier-to-attack form.",
    ),
    (
        "Slippery slope",
        r"\b(s inevitably leads to|will lead to|next thing you know)\b",
        "Assumes a chain of consequences without showing the links.",
    ),
    (
        "False dilemma",
        r"\b(either .{1,55} or|only two options|you.re either with us)\b",
        "Presents limited choices as if they are the only possibilities.",
    ),
    (
        "Appeal to authority",
        r"\b(expert says|because .{0,25} said so|celebrity says)\b",
        "Treats authority as sufficient proof without supporting evidence.",
    ),
    (
        "Hasty generalization",
        r"\b(all .{1,30} are|everyone .{1,20} is|always happens)\b",
        "Draws a broad conclusion from too little evidence.",
    ),
    (
        "Whataboutism",
        r"\b(what about|but what about)\b",
        "Deflects criticism by changing the subject to another issue.",
    ),
    (
        "Appeal to emotion",
        r"\b(if you care about|think of the children|heartless)\b",
        "Uses emotional pressure in place of relevant support.",
    ),
    (
        "Bandwagon",
        r"\b(everyone knows|everybody believes|most people agree)\b",
        "Uses popularity as evidence that a claim is true.",
    ),
    (
        "Circular reasoning",
        r"\b(it is true because|because it.s true|that proves itself)\b",
        "Uses the conclusion as its own supporting reason.",
    ),
]


def detect(text: str) -> list[dict[str, object]]:
    found = []
    for name, pattern, explanation in RULES:
        for m in re.finditer(pattern, text, re.I):
            found.append(
                {
                    "type": name,
                    "start": m.start(),
                    "end": m.end(),
                    "text": m.group(),
                    "explanation": explanation,
                }
            )
    return sorted(found, key=lambda x: x["start"])


def detect_hybrid(text: str, provider: object) -> list[dict[str, object]]:
    found = detect(text)
    if getattr(provider, "name", "mock") == "mock" or not hasattr(provider, "classify_fallacies"):
        return found
    try:
        classifications = provider.classify_fallacies(text)
    except Exception:
        return found
    valid = {name: explanation for name, _, explanation in RULES}
    for item in classifications if isinstance(classifications, list) else []:
        label = item.get("type")
        phrase = item.get("text", "")
        if label not in valid or not phrase or not isinstance(phrase, str):
            continue
        start = text.lower().find(phrase.lower())
        if start < 0 or any(f["start"] == start and f["end"] == start + len(phrase) for f in found):
            continue
        found.append(
            {
                "type": label,
                "start": start,
                "end": start + len(phrase),
                "text": text[start : start + len(phrase)],
                "explanation": str(item.get("explanation") or valid[label]),
            }
        )
    return sorted(found, key=lambda f: f["start"])
