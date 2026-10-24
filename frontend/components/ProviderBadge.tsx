type Props = { name: string; fallback: boolean };

export function ProviderBadge({ name, fallback }: Props) {
  return (
    <div
      className="flex items-center gap-3 rounded-full border border-white/10 bg-white/[.035] px-4 py-2 text-xs"
      role="status"
      aria-label={`Model provider: ${name}${fallback ? ", offline fallback active" : ""}`}
    >
      <span className="dot" aria-hidden="true" />
      <span className="text-slate-300">{name.toUpperCase()}</span>
      {fallback && (
        <span
          className="rounded-full bg-amber-400/10 px-2 py-1 text-amber-300"
          title="The selected model is unreachable, so answers come from the offline template provider."
        >
          FALLBACK
        </span>
      )}
    </div>
  );
}
