"use client";

import { DebateArena } from "../components/DebateArena";
import { ProviderBadge } from "../components/ProviderBadge";
import { SetupPanel } from "../components/SetupPanel";
import { useDebate } from "../lib/useDebate";

export default function Home() {
  const debate = useDebate();
  const inSetup = debate.phase === "setup" || debate.phase === "starting";

  return (
    <main className="min-h-screen px-5 py-6 md:px-10 md:py-9">
      <header className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo-mark.svg" alt="" className="h-10 w-10" />
          <div>
            <div className="text-lg font-bold tracking-tight">
              DEBATRIX<span className="text-mint">.</span>
            </div>
            <div className="label">THINK SHARPER</div>
          </div>
        </div>
        <ProviderBadge name={debate.provider.name} fallback={debate.provider.fallback} />
      </header>

      {inSetup ? (
        <section className="mx-auto mt-16 grid max-w-7xl gap-12 lg:grid-cols-[1.1fr_.9fr]">
          <div>
            <p className="label text-mint">THE ARGUMENT GYM</p>
            <h1 className="mt-5 max-w-2xl text-5xl font-semibold leading-[1.06] tracking-[-.045em] md:text-7xl">
              Ideas get <span className="text-mint">stronger</span> under pressure.
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-slate-400">
              A debate partner that takes the other side, cites evidence, flags weak reasoning, and scores your case.
            </p>
            <ol className="mt-10 flex flex-wrap gap-x-8 gap-y-2 text-xs text-slate-400">
              <li>01 / PICK A CLAIM</li>
              <li>02 / DEFEND IT</li>
              <li>03 / GET THE VERDICT</li>
            </ol>
          </div>
          <SetupPanel
            side={debate.side}
            persona={debate.persona}
            busy={debate.phase === "starting"}
            error={debate.error}
            onSideChange={debate.setSide}
            onPersonaChange={debate.setPersona}
            onStart={debate.start}
          />
        </section>
      ) : (
        <DebateArena debate={debate} />
      )}

      <footer className="mx-auto mt-16 flex max-w-7xl flex-wrap justify-between gap-2 border-t border-white/[.07] pt-5 text-[10px] tracking-widest text-slate-600">
        <span>DEBATRIX / REASON IN PUBLIC</span>
        <span>BUILT FOR BETTER ARGUMENTS</span>
      </footer>
    </main>
  );
}
