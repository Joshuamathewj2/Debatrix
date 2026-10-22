import type { Persona } from "../lib/config";
import type { Citation } from "../lib/types";
import type { Side } from "../lib/useDebate";

type Props = { side: Side; persona: Persona; turnCount: number; citations: Citation[] };

function Row({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="mt-3 flex justify-between text-sm text-slate-300 first:mt-4">
      <span>{label}</span>
      <span className={accent ? "text-mint" : "text-slate-500"}>{value}</span>
    </div>
  );
}

export function DebateSidebar({ side, persona, turnCount, citations }: Props) {
  return (
    <aside className="space-y-4">
      <div className="glass rounded-2xl p-5">
        <h2 className="label">DEBATE BRIEF</h2>
        <Row label="AI stance" value={side === "for" ? "AGAINST" : "FOR"} accent />
        <Row label="Persona" value={persona} />
        <Row label="Arguments" value={turnCount} />
      </div>

      <div className="glass rounded-2xl p-5">
        <h2 className="label">EVIDENCE DESK</h2>
        {citations.length === 0 ? (
          <p className="mt-3 text-xs leading-5 text-slate-500">
            Evidence retrieved for the latest exchange will appear here.
          </p>
        ) : (
          citations.map((c, i) => (
            <a
              key={`${c.source}-${i}`}
              href={c.source}
              target="_blank"
              rel="noreferrer"
              className="mt-4 block border-l border-mint/30 pl-3 hover:border-mint"
            >
              <div className="text-xs font-semibold text-slate-200">
                [{i + 1}] {c.title}
              </div>
              <p className="mt-1 line-clamp-3 text-[11px] leading-5 text-slate-500">{c.text}</p>
              <div className="mt-1 text-[10px] text-mint">SOURCE ↗</div>
            </a>
          ))
        )}
      </div>

      <div className="rounded-2xl border border-white/[.07] p-5">
        <h2 className="label">HOW TO WIN</h2>
        <p className="mt-3 text-xs leading-6 text-slate-500">
          Make precise claims. Support them with evidence. Address the strongest opposing point.
        </p>
      </div>
    </aside>
  );
}
