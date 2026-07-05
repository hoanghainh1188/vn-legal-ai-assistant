"use client";

import { Search, Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  size?: "large" | "compact";
}

export function SearchBar({
  onSearch,
  isLoading,
  size = "large",
}: SearchBarProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !isLoading) {
      onSearch(trimmed);
    }
  }

  const isLarge = size === "large";

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div
        className={`
        relative flex items-center rounded-full border border-slate-200
        bg-white shadow-sm transition-shadow duration-150
        focus-within:shadow-md focus-within:border-slate-300
        ${isLarge ? "px-6 py-4" : "px-4 py-2.5"}
      `}
      >
        {isLoading ? (
          <Loader2
            className="shrink-0 text-slate-400 animate-spin"
            size={isLarge ? 22 : 18}
          />
        ) : (
          <Search
            className="shrink-0 text-slate-400"
            size={isLarge ? 22 : 18}
          />
        )}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Hỏi về pháp luật Việt Nam..."
          disabled={isLoading}
          className={`
            flex-1 bg-transparent outline-none placeholder:text-slate-400
            disabled:opacity-50
            ${isLarge ? "ml-4 text-lg" : "ml-3 text-base"}
          `}
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className={`
            shrink-0 rounded-full bg-primary text-white font-medium
            transition-opacity duration-150
            disabled:opacity-40 hover:opacity-90 cursor-pointer
            ${isLarge ? "px-6 py-2.5 text-base" : "px-4 py-1.5 text-sm"}
          `}
        >
          Tìm kiếm
        </button>
      </div>
    </form>
  );
}
