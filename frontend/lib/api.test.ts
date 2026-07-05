import { afterEach, describe, expect, it, vi } from "vitest";
import type { RAGEvent } from "./types";
import { searchStream } from "./api";

/** Dựng ReadableStream từ danh sách chunk chuỗi (mô phỏng SSE cắt tuỳ ý). */
function streamFrom(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) controller.enqueue(enc.encode(chunks[i++]));
      else controller.close();
    },
  });
}

function mockFetch(chunks: string[], ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    body: ok ? streamFrom(chunks) : null,
  });
}

async function collect(gen: AsyncGenerator<RAGEvent>): Promise<RAGEvent[]> {
  const out: RAGEvent[] = [];
  for await (const e of gen) out.push(e);
  return out;
}

afterEach(() => vi.restoreAllMocks());

describe("searchStream", () => {
  it("yield sources/token/done đúng thứ tự", async () => {
    global.fetch = mockFetch([
      'data: {"type":"sources","data":[]}\n',
      'data: {"type":"token","data":"Xin"}\n',
      'data: {"type":"token","data":" chào"}\n',
      'data: {"type":"done","data":""}\n',
    ]) as typeof fetch;
    const events = await collect(searchStream("hỏi"));
    expect(events.map((e) => e.type)).toEqual([
      "sources",
      "token",
      "token",
      "done",
    ]);
  });

  it("ghép lại một dòng data bị cắt giữa hai chunk", async () => {
    global.fetch = mockFetch([
      'data: {"type":"to',
      'ken","data":"A"}\n',
    ]) as typeof fetch;
    const events = await collect(searchStream("q"));
    expect(events).toEqual([{ type: "token", data: "A" }]);
  });

  it("bỏ qua dòng JSON hỏng, không vỡ stream", async () => {
    global.fetch = mockFetch([
      "data: not-json\n",
      'data: {"type":"done","data":""}\n',
    ]) as typeof fetch;
    const events = await collect(searchStream("q"));
    expect(events).toEqual([{ type: "done", data: "" }]);
  });

  it("ném lỗi khi HTTP không ok", async () => {
    global.fetch = mockFetch([], false, 500) as typeof fetch;
    await expect(collect(searchStream("q"))).rejects.toThrow(
      "Search failed: 500",
    );
  });

  it("ném lỗi khi response không có body", async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, status: 200, body: null }) as typeof fetch;
    await expect(collect(searchStream("q"))).rejects.toThrow(
      "No response body",
    );
  });

  it("gửi domain đã chọn trong body", async () => {
    const fetchMock = mockFetch(['data: {"type":"done","data":""}\n']);
    global.fetch = fetchMock as typeof fetch;
    await collect(searchStream("q", "Đất đai"));
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body).toEqual({ query: "q", domain: "Đất đai" });
  });

  it("domain rỗng → null trong body (Tất cả)", async () => {
    const fetchMock = mockFetch(['data: {"type":"done","data":""}\n']);
    global.fetch = fetchMock as typeof fetch;
    await collect(searchStream("q"));
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body).toEqual({ query: "q", domain: null });
  });
});
