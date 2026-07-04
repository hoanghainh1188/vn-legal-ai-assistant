"use client";

import { AlertTriangle, ChevronDown, Scale } from "lucide-react";
import { useState } from "react";
import type { SourceDocument } from "@/lib/types";

interface LegalReferenceProps {
  sources: SourceDocument[];
}

/** Văn bản "hết hiệu lực" (một phần hoặc toàn bộ) → cần cảnh báo. */
function isAmended(status?: string | null): boolean {
  return !!status && status.toLowerCase().includes("hết hiệu lực");
}

/** Nhãn văn bản: ưu tiên tên đầy đủ từ backend; fallback suy từ số hiệu. */
function docLabel(source: SourceDocument): string {
  if (source.document_name) return source.document_name;
  const id = source.document_id;
  if (id.includes("QH")) return `Luật ${id}`;
  if (id.includes("TT")) return `Thông tư ${id}`;
  if (id.includes("ND-CP") || id.includes("NĐ-CP")) return `Nghị định ${id}`;
  return id;
}

/** "2024-08-01" → "01/08/2024" (dễ đọc cho người Việt); giữ nguyên nếu không phải ISO. */
function formatDate(iso?: string | null): string | null {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : iso;
}

export function LegalReference({ sources }: LegalReferenceProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (sources.length === 0) return null;

  function toggle(index: number) {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }

  // Gộp 1 cảnh báo nếu có ≥1 trích dẫn thuộc văn bản đã bị sửa (cấp văn bản).
  const hasAmended = sources.some((s) => isAmended(s.eff_status));

  return (
    <div className="mt-6 animate-fade-in" style={{ animationDelay: "200ms" }}>
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
        <Scale size={14} />
        Cơ sở pháp lý
      </h3>

      {hasAmended && (
        <div
          role="status"
          className="mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
        >
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>
            Một số văn bản được trích dẫn đang ở trạng thái{" "}
            <strong>hết hiệu lực (một phần hoặc toàn bộ)</strong> — một số quy
            định có thể đã được sửa đổi. Vui lòng đối chiếu văn bản mới nhất.
          </span>
        </div>
      )}

      <div className="space-y-2">
        {sources.map((source, i) => {
          const isExpanded = expandedIndex === i;
          const amended = isAmended(source.eff_status);

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
                    — {docLabel(source)}
                  </span>
                  {source.eff_status && (
                    <span
                      className={`ml-2 inline-block rounded px-1.5 py-0.5 text-xs font-normal ${
                        amended
                          ? "bg-amber-100 text-amber-700"
                          : "bg-emerald-100 text-emerald-700"
                      }`}
                      title={
                        source.eff_date
                          ? `Hiệu lực từ ${formatDate(source.eff_date)}`
                          : undefined
                      }
                    >
                      {source.eff_status}
                    </span>
                  )}
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
                    {source.eff_date && (
                      <> · Hiệu lực từ {formatDate(source.eff_date)}</>
                    )}
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
