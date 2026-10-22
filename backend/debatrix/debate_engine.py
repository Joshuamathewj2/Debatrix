import logging
import re

from .llm.providers import MockProvider
from .parser import SectionParser

logger = logging.getLogger(__name__)


CONCESSION = re.compile(
    r"\b(i (?:now )?(?:agree|concede)|you(?:'re| are) (?:right|correct)|"
    r"i(?:'ve| have) changed my mind|i support your)\b"
)
# Explicit first-person statements of the side the AI must NOT take.
FLIP_TO_FOR = re.compile(
    r"\b(?:i|we) (?:now )?(?:am|argue|stand|support|favou?r)\s+(?:in favou?r of|for)\b"
)
FLIP_TO_AGAINST = re.compile(
    r"\b(?:i|we) (?:now )?(?:am|argue|stand)\s+against\b|\bi (?:now )?oppose\b"
)


def stance_drift(text: str, ai_side: str) -> bool:
    """True if the POSITION section is missing, concedes, or explicitly takes the other side.

    Only explicit phrases count: words like "for" appear in ordinary sentences
    ("therefore", "bad for workers") and must not trigger a regeneration.
    """
    position = re.search(r"@@POSITION@@(.*?)(?:@@|$)", text, re.S | re.I)
    if not position:
        return True
    p = position.group(1).lower()
    flip = FLIP_TO_FOR if ai_side.upper() == "AGAINST" else FLIP_TO_AGAINST
    return bool(CONCESSION.search(p) or flip.search(p))


def _parse(
    provider,
    topic: str,
    user_side: str,
    persona: str,
    last_point: str,
    evidence: list[dict[str, object]],
    ai_side: str,
):
    parser = SectionParser()
    pending = []
    checked = False
    whole = ""
    for chunk in provider.stream(topic, user_side, persona, last_point, evidence):
        whole += chunk
        events = parser.feed(chunk)
        pending.extend(events)
        if not checked and any(e["section"] == "arguments" for e in events):
            position = "@@POSITION@@" + "".join(
                e["text"] for e in pending if e["section"] == "position"
            )
            if stance_drift(position, ai_side):
                return None
            checked = True
            for event in pending:
                yield event
            pending = []
        elif checked:
            for event in events:
                yield event
    if not checked and stance_drift(whole, ai_side):
        return None
    tail = parser.finish()
    if checked:
        # Parser finish includes accumulated text; chunks have already been sent, so only return state.
        return tail
    for event in pending:
        yield event
    return tail


def stream_turn(
    provider,
    topic: str,
    user_side: str,
    persona: str,
    last_point: str,
    evidence: list[dict[str, object]],
):
    ai_side = "AGAINST" if user_side.lower() in ("for", "pro", "support") else "FOR"
    result = yield from _parse(provider, topic, user_side, persona, last_point, evidence, ai_side)
    if result is None:
        # Nothing has been shown yet (drift is checked before streaming), so retry the same model.
        logger.warning(
            "stance drift detected for %s; regenerating once with %s", topic, provider.name
        )
        result = yield from _parse(
            provider, topic, user_side, persona, last_point, evidence, ai_side
        )
    if result is None:
        logger.warning("stance drift again; using the offline template provider for this turn")
        provider = MockProvider()
        parser = SectionParser()
        for chunk in provider.stream(topic, user_side, persona, last_point, evidence):
            for event in parser.feed(chunk):
                yield event
        sections = parser.finish()
    else:
        # A generator's return value carries the finished section map.
        sections = result
    yield {
        "type": "done",
        "sections": sections,
        "provider": provider.name,
        "ai_side": ai_side,
    }
