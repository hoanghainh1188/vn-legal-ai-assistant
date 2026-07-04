import { redirect } from "next/navigation";
import { Clock } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import type { SourceRef } from "@/lib/history";

interface HistoryRow {
  id: number;
  query: string;
  sources: SourceRef[];
  created_at: string;
}

const dateFmt = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default async function HistoryPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  // RLS tự lọc theo auth.uid() — chỉ trả lịch sử của chính user này.
  const { data } = await supabase
    .from("search_history")
    .select("id, query, sources, created_at")
    .order("created_at", { ascending: false });
  const rows = (data ?? []) as HistoryRow[];

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">Lịch sử tra cứu</h1>

      {rows.length === 0 ? (
        <p className="mt-6 text-slate-500">
          Chưa có lượt tra cứu nào được lưu.
        </p>
      ) : (
        <ul className="mt-6 flex flex-col gap-3">
          {rows.map((row) => (
            <li
              key={row.id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <p className="font-medium text-slate-900">{row.query}</p>
              <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                <Clock size={12} />
                <time dateTime={row.created_at}>
                  {dateFmt.format(new Date(row.created_at))}
                </time>
              </div>
              {row.sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {row.sources.map((s, i) => (
                    <span
                      key={`${row.id}-${i}`}
                      className="rounded-md bg-primary/10 px-2 py-0.5 text-xs text-primary"
                    >
                      Điều {s.article_number}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
