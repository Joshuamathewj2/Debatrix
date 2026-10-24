"""FastAPI routes for Debatrix."""

import json
import os
from collections.abc import Iterator
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import storage
from .debate_engine import stream_turn
from .fallacies import detect_hybrid
from .judge import score_debate
from .llm.providers import MockProvider, ProviderUnavailable, get_provider
from .rag import retrieve

app = FastAPI(title="Debatrix API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TOPICS = [
    {
        "id": "ai-regulation",
        "title": "Should AI development be regulated?",
        "category": "Technology",
    },
    {
        "id": "ubi",
        "title": "Should governments provide universal basic income?",
        "category": "Economics",
    },
    {"id": "nuclear", "title": "Should nuclear energy be expanded?", "category": "Energy"},
    {
        "id": "social-media",
        "title": "Should social media access be restricted for teens?",
        "category": "Society",
    },
    {"id": "remote-work", "title": "Is remote work better than office work?", "category": "Work"},
    {"id": "uniforms", "title": "Should schools require uniforms?", "category": "Education"},
]


class NewDebate(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    side: str = Field(default="for", pattern="^(for|against)$")
    persona: str = "Socratic"
    provider: str | None = None


class TurnRequest(BaseModel):
    argument: str = Field(min_length=1, max_length=4000)


def _require_debate(ident: str) -> dict[str, Any]:
    debate = storage.get_debate(ident)
    if debate is None:
        raise HTTPException(404, "Debate not found")
    return debate


def _sse(event: dict[str, Any]) -> str:
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


@app.get("/api/health")
def health() -> dict[str, object]:
    provider = get_provider()
    available = True
    if provider.name == "ollama":
        try:
            available = httpx.get(provider.url, timeout=1).status_code < 500
        except httpx.HTTPError:
            available = False
    elif provider.name == "anthropic":
        available = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok",
        "provider": provider.name,
        "available": available,
        "fallback": not available,
    }


@app.get("/api/topics")
def topics() -> list[dict[str, str]]:
    return TOPICS


@app.post("/api/debates")
def create(req: NewDebate) -> dict[str, str]:
    provider = req.provider or os.getenv("DEBATRIX_PROVIDER", "ollama")
    ident = storage.create_debate(req.topic, req.side, req.persona, provider)
    return {"id": ident, "topic": req.topic, "side": req.side, "persona": req.persona}


@app.get("/api/debates/{ident}")
def get_debate(ident: str) -> dict[str, Any]:
    return _require_debate(ident)


@app.post("/api/debates/{ident}/turn")
def turn(ident: str, req: TurnRequest) -> StreamingResponse:
    debate = _require_debate(ident)
    selected = get_provider(debate["provider"])
    fallacies = detect_hybrid(req.argument, selected)
    evidence = retrieve(debate["topic"] + " " + req.argument, 3, motion=debate["topic"])
    args = (debate["topic"], debate["side"], debate["persona"], req.argument, evidence)

    def generate() -> Iterator[str]:
        sections: dict[str, str] = {}
        fallback = False
        delivered = False
        try:
            for event in stream_turn(selected, *args):
                if event["type"] == "done":
                    sections = event["sections"]
                    fallback = event["provider"] != selected.name
                else:
                    delivered = True
                yield _sse({**event, "fallback": fallback})
        except ProviderUnavailable:
            if delivered:
                # Half an answer was already shown; don't splice in a different provider.
                yield _sse(
                    {
                        "type": "error",
                        "message": "Provider disconnected during generation. Please retry.",
                        "fallback": False,
                    }
                )
                return
            fallback = True
            for event in stream_turn(MockProvider(), *args):
                if event["type"] == "done":
                    sections = event["sections"]
                yield _sse({**event, "fallback": True})

        storage.append_turn(
            ident,
            {
                "argument": req.argument,
                "fallacies": fallacies,
                "ai": sections,
                "citations": evidence,
            },
        )
        citations = [
            {"id": i + 1, "title": e["title"], "source": e["source"], "text": e["text"]}
            for i, e in enumerate(evidence)
        ]
        yield _sse(
            {"type": "user", "argument": req.argument, "fallacies": fallacies, "fallback": fallback}
        )
        yield _sse({"type": "citations", "citations": citations, "fallback": fallback})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/debates/{ident}/judge")
def judge(ident: str) -> dict[str, Any]:
    return score_debate(_require_debate(ident)["turns"])
