import type { JudgeResult } from "../lib/types";

const SIZE = 220;
const CENTER = SIZE / 2;
const RADIUS = 78;

function point(i: number, n: number, r: number): [number, number] {
  const angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
  return [CENTER + r * Math.cos(angle), CENTER + r * Math.sin(angle)];
}

function polygon(values: number[], max: number): string {
  return values.map((v, i) => point(i, values.length, (v / max) * RADIUS).join(",")).join(" ");
}

function Radar({ labels, values }: { labels: string[]; values: number[] }) {
  const n = labels.length;
  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="h-56 w-56 shrink-0" role="img" aria-label="Rubric scores radar chart">
      {[0.25, 0.5, 0.75, 1].map((ring) => (
        <polygon key={ring} points={polygon(Array(n).fill(10 * ring), 10)} fill="none" stroke="rgba(255,255,255,.08)" />
      ))}
      {labels.map((_, i) => {
        const [x, y] = point(i, n, RADIUS);
        return <line key={i} x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="rgba(255,255,255,.08)" />;
      })}
      <polygon points={polygon(values, 10)} fill="rgba(105,240,192,.18)" stroke="#69f0c0" strokeWidth={2} />
      {labels.map((label, i) => {
        const [x, y] = point(i, n, RADIUS + 18);
        return (
          <text key={label} x={x} y={y} fill="#8192a4" fontSize={8} textAnchor="middle" dominantBaseline="middle">
            {label.split(" ")[0].toUpperCase()}
          </text>
        );
      })}
    </svg>
  );
}

export function JudgeScorecard({ result }: { result: JudgeResult }) {
  const entries = Object.entries(result.scores);
  return (
    <section className="glass mt-5 rounded-2xl p-6" aria-labelledby="scorecard-title">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="scorecard-title" className="label text-mint">
          JUDGE&apos;S SCORECARD
        </h2>
        <span className="text-3xl font-semibold">
          {result.overall}
          <span className="text-base text-slate-500">/10</span>
        </span>
      </div>
      <p className="mt-2 text-slate-200">{result.verdict}</p>

      <div className="mt-5 flex flex-col items-center gap-6 md:flex-row md:items-start">
        <Radar labels={entries.map(([k]) => k)} values={entries.map(([, v]) => v.score)} />
        <dl className="grid w-full gap-2">
          {entries.map(([name, { score, justification }]) => (
            <div key={name} className="rounded-xl bg-black/20 p-3">
              <dt className="flex justify-between text-xs">
                <span>{name}</span>
                <b className="text-mint">{score}/10</b>
              </dt>
              <dd className="mt-1 text-[11px] leading-5 text-slate-500">{justification}</dd>
            </div>
          ))}
        </dl>
      </div>

      <h3 className="label mt-5">HOW TO IMPROVE</h3>
      <ul className="mt-2 list-inside list-disc text-sm text-slate-300">
        {result.tips.map((tip) => (
          <li key={tip} className="mt-1">
            {tip}
          </li>
        ))}
      </ul>
    </section>
  );
}
