from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator

import httpx


class ProviderUnavailable(RuntimeError):
    pass


class MockProvider:
    name = "mock"
    available = True

    def stream(
        self,
        topic: str,
        user_side: str,
        persona: str,
        last_point: str,
        evidence: list[dict[str, object]],
    ) -> Iterator[str]:
        """Deterministic, template-based opponent so the app works with no model at all.

        Output varies with the user's latest point and draws on the retrieved evidence,
        so the offline demo still behaves like a debate rather than a repeated script.
        """
        seed = int(hashlib.sha256(f"{topic}|{last_point}".encode()).hexdigest()[:8], 16)
        ai_side = "against" if user_side.lower() in ("for", "pro", "support") else "for"
        motion = topic.strip().rstrip("?.")
        opening = last_point.strip().lower().startswith("give your opening argument")

        position = _pick(MOCK_POSITIONS, seed).format(side=ai_side, motion=motion)
        claim = _pick(MOCK_CLAIMS, seed // 7)
        if evidence:
            fact = str(evidence[seed % len(evidence)]["text"]).split(". ")[0].rstrip(".")
            claim += f" Consider the record: {fact} [{seed % len(evidence) + 1}]."
        if opening:
            counter = "You have not made a case yet, so here is the bar it must clear: show the benefit, the cost, and who pays it."
        else:
            counter = _pick(MOCK_COUNTERS, seed // 13).format(point=_quote(last_point))
        body = (
            f"@@POSITION@@\n{position}\n\n@@ARGUMENTS@@\n{claim}\n\n"
            f"@@COUNTER@@\n{counter}\n\n@@QUESTION@@\n{_pick(MOCK_QUESTIONS, seed // 17)}"
        )
        for i in range(0, len(body), 13):
            yield body[i : i + 13]


MOCK_POSITIONS = [
    "I argue {side} the motion “{motion}”. The case turns on measurable outcomes, incentives, and who bears the risk.",
    "My position is {side} “{motion}”: good intentions are not evidence, and the trade-offs here are real.",
    "I stand {side} the motion “{motion}”, because the strongest version of the other side still leaves key costs unanswered.",
]
MOCK_CLAIMS = [
    "A durable argument must distinguish a compelling example from a population-wide result.",
    "The key question is whether the change improves outcomes compared with realistic alternatives, not with doing nothing.",
    "Even a well-intended policy can create costs that fall hardest on people with the least room to absorb them.",
    "Second-order effects matter: incentives shift once a rule exists, and people adapt in ways planners rarely predict.",
]
MOCK_COUNTERS = [
    "You said {point}. That names a real concern, but it does not show the benefits outweigh the trade-offs.",
    "Take your claim that {point}. Strong as it sounds, it assumes the outcome you need to prove.",
    "On {point}: what would we observe if you were wrong? Without that, the claim cannot be tested.",
]
MOCK_QUESTIONS = [
    "What evidence would change your mind, and how would you measure unintended effects?",
    "Who bears the cost of your proposal, and why is that distribution fair?",
    "What is the strongest objection to your view, and how do you answer it?",
    "Can you point to a real-world case where this worked at scale?",
]


def _pick(options: list[str], seed: int) -> str:
    return options[seed % len(options)]


def _quote(text: str, limit: int = 90) -> str:
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return f"“{text}”"


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")

    def stream(
        self,
        topic: str,
        user_side: str,
        persona: str,
        last_point: str,
        evidence: list[dict[str, object]],
    ) -> Iterator[str]:
        import json

        prompt = _prompt(topic, user_side, persona, last_point, evidence)
        try:
            with httpx.stream(
                "POST",
                f"{self.url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True},
                timeout=90,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("response"):
                            yield data["response"]
        except Exception as e:
            raise ProviderUnavailable(str(e)) from e

    def classify_fallacies(self, text: str) -> list[dict[str, str]]:
        import json

        prompt = (
            'Identify only fallacies in this argument from these labels: Ad hominem, Straw man, Slippery slope, False dilemma, Appeal to authority, Hasty generalization, Whataboutism, Appeal to emotion, Bandwagon, Circular reasoning. Return JSON array of objects {"type":"label","text":"exact quoted span","explanation":"brief reason"}. Return [] when none. Argument: '
            + text
        )
        try:
            r = httpx.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=30,
            )
            r.raise_for_status()
            return json.loads(r.json().get("response", "[]"))
        except Exception:
            return []


FALLACY_LABELS = [
    "Ad hominem",
    "Straw man",
    "Slippery slope",
    "False dilemma",
    "Appeal to authority",
    "Hasty generalization",
    "Whataboutism",
    "Appeal to emotion",
    "Bandwagon",
    "Circular reasoning",
]

FALLACY_SCHEMA = {
    "type": "object",
    "properties": {
        "fallacies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": FALLACY_LABELS},
                    "text": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["type", "text", "explanation"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["fallacies"],
    "additionalProperties": False,
}


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")

    def stream(
        self,
        topic: str,
        user_side: str,
        persona: str,
        last_point: str,
        evidence: list[dict[str, object]],
    ) -> Iterator[str]:
        try:
            import anthropic

            client = anthropic.Anthropic()
            # Thinking tokens count toward max_tokens, so leave generous room.
            with client.beta.messages.stream(
                model=self.model,
                max_tokens=16000,
                output_config={"effort": "medium"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=(
                    f"You are a rigorous debate opponent. {persona_style(persona)} Keep stance firm. "
                    "Output exactly sections @@POSITION@@, @@ARGUMENTS@@, @@COUNTER@@, @@QUESTION@@. "
                    "Cite supplied evidence as [1]."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": _prompt(topic, user_side, persona, last_point, evidence),
                    }
                ],
            ) as s:
                yield from s.text_stream
                if s.get_final_message().stop_reason == "refusal":
                    raise ProviderUnavailable("model declined this turn")
        except ProviderUnavailable:
            raise
        except Exception as e:
            raise ProviderUnavailable(str(e)) from e

    def classify_fallacies(self, text: str) -> list[dict[str, str]]:
        import json

        try:
            import anthropic

            result = anthropic.Anthropic().messages.create(
                model=self.model,
                max_tokens=16000,
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": FALLACY_SCHEMA},
                },
                system=(
                    "Identify only clear instances of these classic logical fallacies in the user's "
                    f"argument: {', '.join(FALLACY_LABELS)}. Quote the exact span in `text`. "
                    "Return an empty list when the reasoning is sound."
                ),
                messages=[{"role": "user", "content": text}],
            )
            # With thinking on, the first block can be a thinking block: find the text block.
            body = next((b.text for b in result.content if b.type == "text"), "")
            return json.loads(body).get("fallacies", []) if body else []
        except Exception:
            return []


def persona_style(persona: str) -> str:
    return {
        "Socratic": "Ask probing questions and expose assumptions through careful inquiry.",
        "Aggressive Litigator": "Be forceful and concise; challenge weak premises directly while staying civil.",
        "Academic": "Use measured language, qualify claims, and foreground evidence quality and uncertainty.",
        "Devil's Advocate": "Stress-test popular assumptions and explore the strongest overlooked countercase.",
    }.get(persona, "Be rigorous, fair, and evidence-led.")


def _prompt(
    topic: str, side: str, persona: str, point: str, evidence: list[dict[str, object]]
) -> str:
    refs = "\n".join(f"[{i + 1}] {x['title']}: {x['text']}" for i, x in enumerate(evidence))
    return f"You are debating in the {persona} persona: {persona_style(persona)}\nOutput exactly @@POSITION@@, @@ARGUMENTS@@, @@COUNTER@@, @@QUESTION@@ sections. Maintain the side opposite the user.\nTopic: {topic}\nUser argues: {side}\nRespond to: {point}\nEvidence:\n{refs}"


def get_provider(name: str | None = None) -> MockProvider | OllamaProvider | AnthropicProvider:
    selected = (name or os.getenv("DEBATRIX_PROVIDER", "ollama")).lower()
    if selected == "mock":
        return MockProvider()
    if selected == "anthropic":
        return AnthropicProvider()
    return OllamaProvider()
