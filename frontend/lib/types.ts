export interface SourceDocument {
  article_number: number;
  article_title: string;
  document_id: string;
  content: string;
  relevance_score: number;
}

export type RAGEvent =
  | { type: "sources"; data: SourceDocument[] }
  | { type: "token"; data: string }
  | { type: "done"; data: string };

export interface SearchState {
  status: "idle" | "loading" | "streaming" | "done" | "error";
  answer: string;
  sources: SourceDocument[];
  error: string | null;
}
