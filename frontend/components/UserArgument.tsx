import type { ReactNode } from "react";
import type { Fallacy } from "../lib/types";

/** Renders the argument with each detected fallacy span highlighted and explained on hover. */
export function HighlightedText({ text, fallacies }: { text: string; fallacies: Fallacy[] }) {
  const nodes: ReactNode[] = [];
  let offset = 0;
  [...fallacies]
    .sort((a, b) => a.start - b.start)
    .forEach((f, i) => {
      if (f.start < offset) return; // skip overlapping spans
      if (f.start > offset) nodes.push(text.slice(offset, f.start));
      nodes.push(
        <mark
          key={`${f.start}-${i}`}
          title={`${f.type}: ${f.explanation}`}
          className="rounded bg-amber-300/20 px-0.5 text-amber-100 underline decoration-amber-300/70 decoration-dotted"
        >
          {text.slice(f.start, f.end)}
        </mark>,
      );
      offset = f.end;
    });
  if (offset < text.length) nodes.push(text.slice(offset));
  return <>{nodes}</>;
}

export function UserArgument({ text, fallacies }: { text: string; fallacies: Fallacy[] }) {
  return (
    <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm border border-violet/20 bg-violet/[.07] p-4">
      <div className="label text-violet">YOUR ARGUMENT</div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6">
        <HighlightedText text={text} fallacies={fallacies} />
      </p>
      {fallacies.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2" aria-label="Detected fallacies">
          {fallacies.map((f, i) => (
            <li
              key={i}
              title={f.explanation}
              className="rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-1 text-[11px] text-amber-200"
            >
              ⚠ {f.type}: “{f.text}”
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
