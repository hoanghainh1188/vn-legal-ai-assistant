import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { searchStream } from "@/lib/api";
import { saveHistory } from "@/lib/history";
import type { RAGEvent, SourceDocument } from "@/lib/types";
import { useStreamQuery } from "./useStreamQuery";

vi.mock("@/lib/api", () => ({ searchStream: vi.fn() }));
vi.mock("@/lib/history", () => ({
  saveHistory: vi.fn().mockResolvedValue(undefined),
}));

function feed(events: RAGEvent[]) {
  vi.mocked(searchStream).mockImplementation(async function* () {
    for (const e of events) yield e;
  });
}

const src: SourceDocument[] = [
  {
    document_id: "27/2023/QH15",
    article_number: 58,
    article_title: "Thời hạn",
    content: "c",
    relevance_score: 1,
  },
];

beforeEach(() => vi.clearAllMocks());

describe("useStreamQuery", () => {
  it("trạng thái ban đầu là idle", () => {
    const { result } = renderHook(() => useStreamQuery());
    expect(result.current.status).toBe("idle");
    expect(result.current.answer).toBe("");
    expect(result.current.sources).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("thành công: sources→token→done, cộng dồn answer, gọi saveHistory", async () => {
    feed([
      { type: "sources", data: src },
      { type: "token", data: "Xin" },
      { type: "token", data: " chào" },
      { type: "done", data: "" },
    ]);
    const { result } = renderHook(() => useStreamQuery());
    await act(async () => {
      await result.current.search("q");
    });
    expect(result.current.status).toBe("done");
    expect(result.current.answer).toBe("Xin chào");
    expect(result.current.sources).toEqual(src);
    expect(saveHistory).toHaveBeenCalledWith("q", src);
  });

  it("đi qua loading (trước khi nhận event đầu tiên)", async () => {
    let releaseFirst!: () => void;
    const gate = new Promise<void>((r) => {
      releaseFirst = r;
    });
    vi.mocked(searchStream).mockImplementation(async function* () {
      await gate; // treo trước khi yield → status còn loading
      yield { type: "done", data: "" };
    });
    const { result } = renderHook(() => useStreamQuery());
    let p!: Promise<void>;
    act(() => {
      p = result.current.search("q");
    });
    expect(result.current.status).toBe("loading");
    await act(async () => {
      releaseFirst();
      await p;
    });
    expect(result.current.status).toBe("done");
  });

  it("chuyển sang streaming khi nhận sources (trước done)", async () => {
    let releaseDone!: () => void;
    const gate = new Promise<void>((r) => {
      releaseDone = r;
    });
    vi.mocked(searchStream).mockImplementation(async function* () {
      yield { type: "sources", data: src };
      await gate; // treo ở streaming, chưa done
      yield { type: "done", data: "" };
    });
    const { result } = renderHook(() => useStreamQuery());
    let p!: Promise<void>;
    act(() => {
      p = result.current.search("q");
    });
    await waitFor(() => expect(result.current.status).toBe("streaming"));
    expect(result.current.sources).toEqual(src);
    await act(async () => {
      releaseDone();
      await p;
    });
    expect(result.current.status).toBe("done");
  });

  it("lỗi giữa chừng: status error, KHÔNG done, không lưu lịch sử", async () => {
    feed([
      { type: "token", data: "một phần" },
      { type: "error", data: "provider lỗi" },
    ]);
    const { result } = renderHook(() => useStreamQuery());
    await act(async () => {
      await result.current.search("q");
    });
    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("provider lỗi");
    expect(saveHistory).not.toHaveBeenCalled();
  });

  it("searchStream ném lỗi → status error", async () => {
    vi.mocked(searchStream).mockImplementation(async function* () {
      throw new Error("mạng lỗi");
    });
    const { result } = renderHook(() => useStreamQuery());
    await act(async () => {
      await result.current.search("q");
    });
    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("mạng lỗi");
  });

  it("reset → idle", async () => {
    feed([{ type: "done", data: "" }]);
    const { result } = renderHook(() => useStreamQuery());
    await act(async () => {
      await result.current.search("q");
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.status).toBe("idle");
    expect(result.current.answer).toBe("");
  });

  it("truyền domain đã chọn vào searchStream", async () => {
    feed([{ type: "done", data: "" }]);
    const { result } = renderHook(() => useStreamQuery());
    await act(async () => {
      await result.current.search("q", "Đất đai");
    });
    expect(searchStream).toHaveBeenCalledWith("q", "Đất đai");
  });
});
