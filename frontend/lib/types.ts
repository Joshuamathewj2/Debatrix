export type Fallacy = {
  type: string;
  start: number;
  end: number;
  text: string;
  explanation: string;
};

export type Citation = { id?: number; title: string; source: string; text: string };

export type AiSections = Partial<Record<"position" | "arguments" | "counter" | "question", string>>;

export type Turn = {
  argument: string;
  fallacies: Fallacy[];
  ai: AiSections;
  citations: Citation[];
};

export type RubricScore = { score: number; justification: string };

export type JudgeResult = {
  overall: number;
  verdict: string;
  scores: Record<string, RubricScore>;
  tips: string[];
};

/** Events streamed by POST /api/debates/{id}/turn. */
export type TurnEvent =
  | { type: "section"; section: keyof AiSections; text: string; fallback?: boolean }
  | { type: "done"; sections: AiSections; provider: string; ai_side: string; fallback: boolean }
  | { type: "user"; argument: string; fallacies: Fallacy[]; fallback: boolean }
  | { type: "citations"; citations: Citation[]; fallback: boolean }
  | { type: "error"; message: string; fallback: boolean };
