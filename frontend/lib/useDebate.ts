"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL, type Persona } from "./config";
import { readSse } from "./sse";
import type { AiSections, Citation, Fallacy, JudgeResult, Turn, TurnEvent } from "./types";

export type Phase = "setup" | "starting" | "streaming" | "ready" | "judging";
export type Side = "for" | "against";

type Provider = { name: string; fallback: boolean };

export function useDebate() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [debateId, setDebateId] = useState<string | null>(null);
  const [topic, setTopic] = useState("");
  const [side, setSide] = useState<Side>("for");
  const [persona, setPersona] = useState<Persona>("Socratic");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [live, setLive] = useState<AiSections>({});
  const [judge, setJudge] = useState<JudgeResult | null>(null);
  const [provider, setProvider] = useState<Provider>({ name: "…", fallback: false });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((h) => setProvider({ name: h.provider, fallback: Boolean(h.fallback) }))
      .catch(() => setProvider({ name: "offline", fallback: true }));
  }, []);

  const sendTurn = useCallback(
    async (id: string, argument: string) => {
      setPhase("streaming");
      setError(null);
      setLive({});
      let sections: AiSections = {};
      let fallacies: Fallacy[] = [];
      let citations: Citation[] = [];
      try {
        const res = await fetch(`${API_URL}/api/debates/${id}/turn`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ argument }),
        });
        if (!res.ok || !res.body) throw new Error(`The debate server returned ${res.status}.`);

        for await (const event of readSse<TurnEvent>(res.body)) {
          switch (event.type) {
            case "section":
              sections = { ...sections, [event.section]: (sections[event.section] ?? "") + event.text };
              setLive(sections);
              break;
            case "done":
              sections = event.sections;
              setProvider({ name: event.provider, fallback: event.fallback });
              break;
            case "user":
              fallacies = event.fallacies;
              break;
            case "citations":
              citations = event.citations;
              break;
            case "error":
              throw new Error(event.message);
          }
        }
        setTurns((prev) => [...prev, { argument, fallacies, ai: sections, citations }]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Connection lost.");
      } finally {
        setLive({});
        setPhase("ready");
      }
    },
    [],
  );

  const start = useCallback(
    async (motion: string) => {
      setPhase("starting");
      setError(null);
      try {
        const res = await fetch(`${API_URL}/api/debates`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: motion, side, persona }),
        });
        if (!res.ok) throw new Error("Could not start a debate. Is the backend running?");
        const { id } = (await res.json()) as { id: string };
        setDebateId(id);
        setTopic(motion);
        setTurns([]);
        setJudge(null);
        await sendTurn(id, "Give your opening argument.");
      } catch (e) {
        setError(e instanceof Error ? e.message : "API unavailable.");
        setPhase("setup");
      }
    },
    [side, persona, sendTurn],
  );

  const send = useCallback(
    async (argument: string) => {
      if (!debateId || !argument.trim() || phase === "streaming") return;
      await sendTurn(debateId, argument.trim());
    },
    [debateId, phase, sendTurn],
  );

  const finish = useCallback(async () => {
    if (!debateId) return;
    setPhase("judging");
    try {
      const res = await fetch(`${API_URL}/api/debates/${debateId}/judge`, { method: "POST" });
      if (!res.ok) throw new Error("The judge is unavailable right now.");
      setJudge((await res.json()) as JudgeResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Judge unavailable.");
    } finally {
      setPhase("ready");
    }
  }, [debateId]);

  const exit = useCallback(() => {
    setDebateId(null);
    setTurns([]);
    setJudge(null);
    setError(null);
    setPhase("setup");
  }, []);

  return {
    phase,
    topic,
    side,
    setSide,
    persona,
    setPersona,
    turns,
    live,
    judge,
    provider,
    error,
    start,
    send,
    finish,
    exit,
  };
}

export type DebateState = ReturnType<typeof useDebate>;
