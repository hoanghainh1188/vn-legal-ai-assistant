import { beforeEach, describe, expect, it, vi } from "vitest";
import { createClient } from "@/lib/supabase/client";
import type { SourceDocument } from "@/lib/types";
import { saveHistory } from "./history";

vi.mock("@/lib/supabase/client", () => ({ createClient: vi.fn() }));

function makeSupabase(user: unknown) {
  const insert = vi.fn().mockResolvedValue({ error: null });
  const from = vi.fn().mockReturnValue({ insert });
  const getUser = vi.fn().mockResolvedValue({ data: { user } });
  return { client: { auth: { getUser }, from }, from, insert };
}

const sources: SourceDocument[] = [
  {
    document_id: "27/2023/QH15",
    article_number: 58,
    article_title: "Thời hạn sử dụng nhà chung cư",
    content: "Nội dung điều 58.",
    relevance_score: 0.9,
    domain: "Nhà ở",
  },
];

beforeEach(() => vi.clearAllMocks());

describe("saveHistory", () => {
  it("guest (chưa đăng nhập) → không insert", async () => {
    const { client, from } = makeSupabase(null);
    vi.mocked(createClient).mockReturnValue(client as never);
    await saveHistory("q", sources);
    expect(from).not.toHaveBeenCalled();
  });

  it("đã đăng nhập → insert refs tối thiểu map từ sources", async () => {
    const { client, from, insert } = makeSupabase({ id: "u1" });
    vi.mocked(createClient).mockReturnValue(client as never);
    await saveHistory("câu hỏi", sources);
    expect(from).toHaveBeenCalledWith("search_history");
    // Chỉ lưu tham chiếu tối thiểu (không toàn văn/relevance/domain).
    expect(insert).toHaveBeenCalledWith({
      query: "câu hỏi",
      sources: [
        {
          document_id: "27/2023/QH15",
          article_number: 58,
          article_title: "Thời hạn sử dụng nhà chung cư",
        },
      ],
    });
  });
});
