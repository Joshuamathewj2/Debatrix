"use client";

import { useState } from "react";

type Props = { busy: boolean; onSend: (argument: string) => void };

export function Composer({ busy, onSend }: Props) {
  const [text, setText] = useState("");

  const submit = () => {
    if (busy || !text.trim()) return;
    onSend(text);
    setText("");
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className="glass mt-5 rounded-2xl p-3"
    >
      <label htmlFor="argument" className="sr-only">
        Your argument
      </label>
      <textarea
        id="argument"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="Make your case. Be specific…"
        rows={3}
        maxLength={4000}
        className="w-full resize-none bg-transparent p-2 text-sm leading-6 outline-none placeholder:text-slate-600"
      />
      <div className="flex items-center justify-between border-t border-white/[.07] pt-3">
        <span className="hidden text-[11px] text-slate-600 sm:inline">ENTER TO SEND · SHIFT + ENTER FOR NEW LINE</span>
        <button
          type="submit"
          disabled={busy || !text.trim()}
          className="ml-auto rounded-lg bg-mint px-4 py-2 text-xs font-bold text-[#07120f] disabled:opacity-40"
        >
          {busy ? "THINKING…" : "SEND ARGUMENT →"}
        </button>
      </div>
    </form>
  );
}
