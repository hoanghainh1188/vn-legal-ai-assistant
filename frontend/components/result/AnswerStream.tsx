"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

interface AnswerStreamProps {
  answer: string;
  isStreaming: boolean;
}

const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-3 ml-5 list-disc space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 ml-5 list-decimal space-y-1">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => (
    <strong className="font-semibold text-slate-900">{children}</strong>
  ),
  h1: ({ children }) => (
    <h1 className="mb-3 mt-4 text-lg font-bold text-slate-900">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 mt-4 text-base font-bold text-slate-900">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-3 text-base font-semibold text-slate-900">
      {children}
    </h3>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-primary/40 pl-4 italic text-slate-600">
      {children}
    </blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-slate-100 px-1 py-0.5 text-sm text-slate-800">
      {children}
    </code>
  ),
  a: ({ children, href }) => (
    <a href={href} className="text-primary underline underline-offset-2">
      {children}
    </a>
  ),
};

export function AnswerStream({ answer, isStreaming }: AnswerStreamProps) {
  if (!answer && !isStreaming) return null;

  return (
    <div className="animate-fade-in text-slate-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {answer}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-flex gap-0.5 align-baseline">
          <span
            className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-dot"
            style={{ animationDelay: "0ms" }}
          />
          <span
            className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-dot"
            style={{ animationDelay: "200ms" }}
          />
          <span
            className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-dot"
            style={{ animationDelay: "400ms" }}
          />
        </span>
      )}
    </div>
  );
}
