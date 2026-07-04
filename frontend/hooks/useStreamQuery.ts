"use client";

import { useCallback, useRef, useState } from "react";
import { searchStream } from "@/lib/api";
import type { SearchState } from "@/lib/types";

const INITIAL_STATE: SearchState = {
  status: "idle",
  answer: "",
  sources: [],
  error: null,
};

export function useStreamQuery() {
  const [state, setState] = useState<SearchState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const search = useCallback(async (query: string) => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState({ status: "loading", answer: "", sources: [], error: null });

    try {
      for await (const event of searchStream(query)) {
        if (abortRef.current?.signal.aborted) break;

        switch (event.type) {
          case "sources":
            setState((prev) => ({
              ...prev,
              status: "streaming",
              sources: event.data,
            }));
            break;
          case "token":
            setState((prev) => ({
              ...prev,
              answer: prev.answer + event.data,
            }));
            break;
          case "done":
            setState((prev) => ({ ...prev, status: "done" }));
            break;
          case "error":
            // Lỗi giữa chừng stream: đánh dấu lỗi, KHÔNG coi phần đã nhận là
            // câu trả lời hoàn chỉnh.
            setState((prev) => ({
              ...prev,
              status: "error",
              error: event.data,
            }));
            break;
        }
      }
    } catch (err) {
      if (abortRef.current?.signal.aborted) return;
      const message =
        err instanceof Error ? err.message : "Đã xảy ra lỗi không xác định";
      setState((prev) => ({ ...prev, status: "error", error: message }));
    }
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL_STATE);
  }, []);

  return { ...state, search, reset };
}
