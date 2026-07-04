"use client";

import { useState } from "react";
import { ArrowLeft, Scale } from "lucide-react";
import { SearchBar } from "@/components/search/SearchBar";
import { SuggestedQuestions } from "@/components/search/SuggestedQuestions";
import { DomainFilter } from "@/components/search/DomainFilter";
import { AnswerStream } from "@/components/result/AnswerStream";
import { LegalReference } from "@/components/result/LegalReference";
import { SafetyDisclaimer } from "@/components/result/SafetyDisclaimer";
import { useStreamQuery } from "@/hooks/useStreamQuery";

export default function Home() {
  const { status, answer, sources, error, search, reset } = useStreamQuery();
  const [domain, setDomain] = useState<string | null>(null);

  const isIdle = status === "idle";
  const isActive = !isIdle;

  function handleSearch(query: string) {
    search(query, domain);
  }

  return (
    <main className="flex-1 flex flex-col">
      {isIdle ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4 pb-24">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
              <Scale className="text-primary" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
              Tra cứu pháp luật Việt Nam
            </h1>
            <p className="mt-2 text-slate-500 max-w-md mx-auto">
              Hỏi bằng ngôn ngữ tự nhiên. Chọn lĩnh vực để thu hẹp phạm vi tra
              cứu.
            </p>
          </div>
          <SearchBar onSearch={handleSearch} isLoading={false} size="large" />
          <DomainFilter value={domain} onChange={setDomain} />
          <SuggestedQuestions onSelect={handleSearch} />
        </div>
      ) : (
        <div className="flex-1 px-4 py-6 max-w-3xl mx-auto w-full">
          <div className="mb-6 flex items-center gap-3">
            <button
              onClick={reset}
              className="p-2 rounded-full hover:bg-slate-100 transition-colors cursor-pointer"
              aria-label="Quay lại"
            >
              <ArrowLeft size={20} className="text-slate-500" />
            </button>
            <SearchBar
              onSearch={handleSearch}
              isLoading={status === "loading" || status === "streaming"}
              size="compact"
            />
          </div>

          {status === "loading" && (
            <div className="flex items-center gap-3 text-slate-500 animate-fade-in">
              <div className="flex gap-1">
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-dot"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-dot"
                  style={{ animationDelay: "200ms" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-dot"
                  style={{ animationDelay: "400ms" }}
                />
              </div>
              <span className="text-sm">
                Đang tìm kiếm trong văn bản luật...
              </span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm animate-fade-in">
              {error}
            </div>
          )}

          <AnswerStream answer={answer} isStreaming={status === "streaming"} />

          {isActive && <LegalReference sources={sources} />}

          {(status === "done" || status === "error") && <SafetyDisclaimer />}
        </div>
      )}
    </main>
  );
}
