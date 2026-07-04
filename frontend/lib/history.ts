import { createClient } from "@/lib/supabase/client";
import type { SourceDocument } from "@/lib/types";

/** Tham chiếu điều luật lưu trong lịch sử (tối thiểu — không lưu toàn văn câu trả lời). */
export interface SourceRef {
  document_id: string;
  article_number: number;
  article_title: string;
}

/**
 * Lưu một lượt tra cứu vào search_history. Chỉ khi đã đăng nhập — guest bỏ qua
 * (FR-006). RLS đảm bảo user_id = auth.uid(); không lộ dữ liệu người khác.
 */
export async function saveHistory(
  query: string,
  sources: SourceDocument[],
): Promise<void> {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return;

  const refs: SourceRef[] = sources.map((s) => ({
    document_id: s.document_id,
    article_number: s.article_number,
    article_title: s.article_title,
  }));

  const { error } = await supabase
    .from("search_history")
    .insert({ query, sources: refs });
  if (error) {
    // Không chặn UX, nhưng KHÔNG nuốt lỗi im lặng — để có tín hiệu debug.
    console.warn("[history] lưu lịch sử thất bại:", error.message);
  }
}
