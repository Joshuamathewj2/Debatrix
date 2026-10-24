export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const STARTER_TOPICS = [
  { title: "Should AI development be regulated?", label: "AI regulation", category: "TECHNOLOGY" },
  { title: "Should governments provide universal basic income?", label: "Universal basic income", category: "ECONOMICS" },
  { title: "Should nuclear energy be expanded?", label: "Nuclear energy", category: "CLIMATE" },
  { title: "Should social media access be restricted for teens?", label: "Social media & teens", category: "SOCIETY" },
  { title: "Is remote work better than office work?", label: "Remote work", category: "WORK" },
  { title: "Should schools require uniforms?", label: "School uniforms", category: "EDUCATION" },
] as const;

/** Must match the keys of persona_style() in backend/debatrix/llm/providers.py. */
export const PERSONAS = ["Socratic", "Aggressive Litigator", "Academic", "Devil's Advocate"] as const;
export type Persona = (typeof PERSONAS)[number];

export const PERSONA_ACCENT: Record<Persona, { border: string; tint: string }> = {
  Socratic: { border: "border-mint/20", tint: "bg-mint/10 text-mint" },
  "Aggressive Litigator": { border: "border-rose-400/25", tint: "bg-rose-400/10 text-rose-300" },
  Academic: { border: "border-sky-300/25", tint: "bg-sky-300/10 text-sky-200" },
  "Devil's Advocate": { border: "border-violet/30", tint: "bg-violet/10 text-violet" },
};
