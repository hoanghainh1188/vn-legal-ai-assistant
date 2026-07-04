export interface SourceDocument {
  article_number: number;
  article_title: string;
  document_id: string;
  content: string;
  relevance_score: number;
  // Metadata hiệu lực cấp văn bản (Feature #7).
  document_name?: string | null;
  eff_status?: string | null;
  eff_date?: string | null;
  // Lĩnh vực pháp luật (Feature #8).
  domain?: string | null;
}

export type RAGEvent =
  | { type: "sources"; data: SourceDocument[] }
  | { type: "token"; data: string }
  | { type: "done"; data: string }
  | { type: "error"; data: string };

export interface SearchState {
  status: "idle" | "loading" | "streaming" | "done" | "error";
  answer: string;
  sources: SourceDocument[];
  error: string | null;
}
