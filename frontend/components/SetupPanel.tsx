"use client";

import { useState } from "react";
import { PERSONAS, STARTER_TOPICS, type Persona } from "../lib/config";
import type { Side } from "../lib/useDebate";

type Props = {
  side: Side;
  persona: Persona;
  busy: boolean;
  error: string | null;
  onSideChange: (side: Side) => void;
  onPersonaChange: (persona: Persona) => void;
  onStart: (motion: string) => void;
};

export function SetupPanel({ side, persona, busy, error, onSideChange, onPersonaChange, onStart }: Props) {
  const [selected, setSelected] = useState<string>(STARTER_TOPICS[0].title);
  const [custom, setCustom] = useState("");
  const motion = custom.trim() || selected;

  return (
    <div className="glass glow rounded-3xl p-6 md:p-8">
      <div className="flex items-center justify-between">
        <div>
          <div className="label">01 · TOPIC</div>
          <h2 className="mt-2 text-xl font-semibold">Choose your position</h2>
        </div>
        <span className="text-xs text-slate-500">{STARTER_TOPICS.length} STARTERS</span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-2" role="radiogroup" aria-label="Starter topics">
        {STARTER_TOPICS.map((t) => {
          const active = !custom.trim() && selected === t.title;
          return (
            <button
              key={t.title}
              type="button"
              role="radio"
              aria-checked={active}
              title={t.title}
              onClick={() => {
                setSelected(t.title);
                setCustom("");
              }}
              className={`rounded-xl border p-3 text-left transition ${
                active ? "border-mint/40 bg-mint/[.08]" : "border-white/[.07] bg-white/[.025] hover:border-white/20"
              }`}
            >
              <span className="label">{t.category}</span>
              <div className="mt-1 text-sm">{t.label}</div>
            </button>
          );
        })}
      </div>

      <label className="sr-only" htmlFor="custom-motion">
        Custom motion
      </label>
      <input
        id="custom-motion"
        value={custom}
        onChange={(e) => setCustom(e.target.value)}
        placeholder="Or write your own motion…"
        maxLength={300}
        className="mt-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-600 focus:border-mint/40"
      />

      <div className="mt-7 grid gap-5 sm:grid-cols-2">
        <div>
          <div className="label" id="side-label">
            YOU ARGUE
          </div>
          <div className="mt-2 flex rounded-xl bg-black/20 p-1" role="radiogroup" aria-labelledby="side-label">
            {(["for", "against"] as const).map((s) => (
              <button
                key={s}
                type="button"
                role="radio"
                aria-checked={side === s}
                onClick={() => onSideChange(s)}
                className={`flex-1 rounded-lg py-2 text-sm capitalize ${
                  side === s ? "bg-white/10 text-white" : "text-slate-500"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="label" htmlFor="persona">
            AI PERSONA
          </label>
          <select
            id="persona"
            value={persona}
            onChange={(e) => onPersonaChange(e.target.value as Persona)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-[#111923] px-3 py-[10px] text-sm"
          >
            {PERSONAS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={() => onStart(motion)}
        disabled={busy || motion.length < 3}
        className="mt-7 w-full rounded-xl bg-mint py-3.5 font-semibold text-[#07120f] transition hover:brightness-110 disabled:opacity-50"
      >
        {busy ? "Opening the arena…" : "Enter the arena →"}
      </button>
      {error && (
        <p className="mt-3 text-sm text-rose-300" role="alert">
          {error}
        </p>
      )}
      <p className="mt-4 text-center text-[11px] text-slate-600">
        Evidence-linked · Fallacy-aware · Scored on a transparent rubric
      </p>
    </div>
  );
}
