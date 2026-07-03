# Quickstart / Validation — Feature #1: Provider Abstraction

Hướng dẫn kiểm chứng feature hoạt động end-to-end. Không chứa mã hiện thực (xem `tasks.md`).

## Tiền đề
- Ollama chạy local với `qwen3.5` + `bge-m3` (như hiện tại).
- Dependency `anthropic` đã cài (`uv sync`).

## 1. Hành vi mặc định không đổi (US1 — quan trọng nhất)

```bash
cd backend
uv run pytest            # 27 test cũ + test mới đều xanh
```

Chạy 3 acceptance case (mặc định Ollama) và xác nhận:
- "Chung cư có thời hạn sở hữu tối đa bao nhiêu năm?" → có Điều 58 trong "Cơ sở pháp lý".
- "Việt kiều mua nhà ở Việt Nam được không?" → trả "Được" + trích Điều 8.
- "Lái xe quá tốc độ bị phạt bao nhiêu?" → từ chối an toàn.

**Kỳ vọng:** output giống hệt trước khi refactor.

## 2. Đổi chat provider sang Claude (US2)

```bash
export VN_LEGAL_CHAT_PROVIDER=claude
export VN_LEGAL_CLAUDE_API_KEY=sk-ant-...   # khóa thật, KHÔNG commit
uv run uvicorn app.main:app --port 8000
```

Gửi một câu hỏi trong phạm vi → câu trả lời được sinh streaming qua Claude
(`claude-sonnet-4-6`), luồng SSE `sources → token... → done` như cũ.

## 3. Lỗi cấu hình (US2, edge case)

```bash
export VN_LEGAL_CHAT_PROVIDER=claude
unset VN_LEGAL_CLAUDE_API_KEY
uv run uvicorn app.main:app --port 8000     # phải báo lỗi cấu hình rõ ràng, KHÔNG lộ key
```

## 4. Lỗi giữa chừng stream (FR-011)

Trong test: mock provider raise lỗi sau khi yield vài token → xác nhận stream phát sự kiện
`error` và KHÔNG phát `done`.

## Tiêu chí "xong" (đối chiếu Success Criteria)
- SC-001: 100% test + 3 acceptance xanh ở mặc định.
- SC-002: đổi provider chỉ bằng biến môi trường (0 sửa business logic).
- SC-004: không secret hardcode; `.env.example` có biến mới.
- SC-005: coverage ≥ 80%.
