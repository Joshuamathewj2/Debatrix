"use client";

import { useEffect, useRef } from "react";
import type { DebateState } from "../lib/useDebate";
import { AiTurnCard } from "./AiTurnCard";
import { Composer } from "./Composer";
import { DebateSidebar } from "./DebateSidebar";
import { JudgeScorecard } from "./JudgeScorecard";
import { UserArgument } from "./UserArgument";

const OPENING_PROMPT = "Give your opening argument.";

export function DebateArena({ debate }: { debate: DebateState }) {
  const { topic, side, persona, turns, live, judge, phase, error } = debate;
  const streaming = phase === "streaming";
  const hasLive = Object.keys(live).length > 0;
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, hasLive, judge]);

  return (
    <section className="mx-auto mt-10 grid max-w-7xl gap-5 lg:grid-cols-[1fr_300px]">
      <div className="min-w-0">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="label">ROUND {turns.length + (streaming ? 1 : 0)}</div>
            <h1 className="mt-1 text-2xl font-semibold">{topic}</h1>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full border border-mint/20 bg-mint/[.07] px-3 py-1.5 text-xs text-mint">
              YOU · {side.toUpperCase()}
            </span>
            <button
              type="button"
              onClick={debate.finish}
              disabled={streaming || phase === "judging" || turns.length < 2}
              title={turns.length < 2 ? "Make at least one argument first" : undefined}
              className="rounded-full border border-white/10 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
            >
              {phase === "judging" ? "Scoring…" : "End & score"}
            </button>
            <button
              type="button"
              onClick={debate.exit}
              className="rounded-full border border-white/10 px-3 py-1.5 text-xs hover:bg-white/5"
            >
              Exit
            </button>
          </div>
        </div>

        <div className="space-y-4" aria-live="polite">
          {turns.map((t, i) => (
            <div key={i} className="space-y-3">
              {t.argument !== OPENING_PROMPT && <UserArgument text={t.argument} fallacies={t.fallacies} />}
              <AiTurnCard sections={t.ai} persona={persona} />
            </div>
          ))}
          {hasLive && <AiTurnCard sections={live} persona={persona} streaming />}
          {streaming && !hasLive && (
            <div className="glass rounded-2xl p-5 text-sm text-slate-400">
              <span className="dot mr-2 animate-pulse" aria-hidden="true" />
              Building the counterargument…
            </div>
          )}
        </div>

        <Composer busy={streaming || phase === "judging"} onSend={debate.send} />
        {error && (
          <p className="mt-3 text-sm text-rose-300" role="alert">
            {error}
          </p>
        )}
        {judge && <JudgeScorecard result={judge} />}
        <div ref={endRef} />
      </div>

      <DebateSidebar
        side={side}
        persona={persona}
        turnCount={turns.filter((t) => t.argument !== OPENING_PROMPT).length}
        citations={turns.at(-1)?.citations ?? []}
      />
    </section>
  );
}
