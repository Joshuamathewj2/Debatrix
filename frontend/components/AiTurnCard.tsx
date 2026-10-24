import { PERSONA_ACCENT, type Persona } from "../lib/config";
import type { AiSections } from "../lib/types";

const SECTIONS = [
  { key: "position", label: "01 · POSITION", accent: "text-mint" },
  { key: "arguments", label: "02 · ARGUMENTS", accent: "" },
  { key: "counter", label: "03 · COUNTER", accent: "" },
  { key: "question", label: "04 · YOUR TURN", accent: "text-violet" },
] as const;

type Props = { sections: AiSections; persona: Persona; streaming?: boolean };

export function AiTurnCard({ sections, persona, streaming = false }: Props) {
  const accent = PERSONA_ACCENT[persona] ?? PERSONA_ACCENT.Socratic;
  return (
    <article className={`glass rounded-2xl border p-5 md:p-6 ${accent.border}`} aria-busy={streaming}>
      <header className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`grid h-7 w-7 place-items-center rounded-lg text-xs ${accent.tint}`} aria-hidden="true">
            D
          </span>
          <span className="text-sm font-semibold">Critical Debater</span>
        </div>
        <span className="label">
          {persona.toUpperCase()} · {streaming ? "RESPONDING" : "AI POSITION"}
        </span>
      </header>
      {SECTIONS.map(({ key, label, accent: labelAccent }) =>
        sections[key] ? (
          <section key={key} className="mb-4 last:mb-0">
            <h3 className={`label ${labelAccent}`}>{label}</h3>
            <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-300">{sections[key]}</p>
          </section>
        ) : null,
      )}
    </article>
  );
}
