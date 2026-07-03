"use client";

import { ChevronDown, Scale } from "lucide-react";
import { useState } from "react";
import type { SourceDocument } from "@/lib/types";

interface LegalReferenceProps {
  sources: SourceDocument[];
}

export function LegalReference({ sources }: LegalReferenceProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (sources.length === 0) return null;

  function toggle(index: number) {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }

  return (
    <div className="mt-6 animate-fade-in" style={{ animationDelay: "200ms" }}>
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
        <Scale size={14} />
        Cơ sở pháp lý
      </h3>
      <div className="space-y-2">
        {sources.map((source, i) => {
          const isExpanded = expandedIndex === i;
          const docLabel =
            source.document_id === "27/2023/QH15"
              ? "Luật Nhà ở 2023"
              : `NĐ ${source.document_id}`;

          return (
            <div
              key={`${source.document_id}-${source.article_number}`}
              className="border border-slate-200 rounded-lg bg-white overflow-hidden"
            >
              <button
                onClick={() => toggle(i)}
                className="w-full flex items-center justify-between px-4 py-3 text-left
                           hover:bg-slate-50 transition-colors duration-150 cursor-pointer"
              >
                <span className="text-sm font-medium text-slate-700">
                  Điều {source.article_number}. {source.article_title}
                  <span className="ml-2 text-xs text-slate-400 font-normal">
                    — {docLabel}
                  </span>
                </span>
                <ChevronDown
                  size={16}
                  className={`shrink-0 text-slate-400 transition-transform duration-200
                    ${isExpanded ? "rotate-180" : ""}`}
                />
              </button>
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-slate-100">
                  <pre className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed mt-3 font-sans">
                    {source.content}
                  </pre>
                  <div className="mt-2 text-xs text-slate-400">
                    Độ liên quan: {Math.round(source.relevance_score * 100)}%
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
