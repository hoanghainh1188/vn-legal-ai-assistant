"use client";

import { MessageCircleQuestion } from "lucide-react";

const SUGGESTIONS = [
  "Chung cư có thời hạn sở hữu tối đa bao nhiêu năm?",
  "Việt kiều mua nhà ở Việt Nam có được không?",
  "Điều kiện người nước ngoài sở hữu nhà tại Việt Nam?",
];

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      <p className="text-sm text-slate-500 mb-3 flex items-center gap-1.5">
        <MessageCircleQuestion size={14} />
        Câu hỏi mẫu
      </p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200
                       rounded-full hover:border-slate-300 hover:bg-slate-50
                       transition-colors duration-150 text-left cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
