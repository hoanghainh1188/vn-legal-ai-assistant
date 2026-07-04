# Tasks: Lớp abstraction nhà cung cấp LLM/embedding

**Feature**: `001-llm-provider-abstraction` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: BẮT BUỘC (Constitution — Principle III: test-first). Test viết trước implementation.

**Format**: `- [ ] [TaskID] [P?] [Story?] Mô tả + đường dẫn file`

---

## Phase 1: Setup

- [X] T001 Thêm dependency `anthropic>=0.40` (ghim version tối thiểu) vào `[project.dependencies]` trong `backend/pyproject.toml`
- [X] T002 Chạy `uv sync` trong `backend/` để cài `anthropic`
- [X] T003 [P] Thêm các trường config provider vào `backend/app/config.py`: `chat_provider` (default "ollama"), `embedding_provider` (default "ollama"), `claude_api_key` (str|None), `claude_model` (default "claude-sonnet-4-6"), `claude_timeout` (default 300.0)

## Phase 2: Foundational (chặn tất cả user story)

- [X] T004 Tạo `backend/app/providers/__init__.py`
- [X] T005 Định nghĩa `ChatProvider` và `EmbeddingProvider` (Protocol) trong `backend/app/providers/base.py` theo `contracts/providers.md`

---

## Phase 3: User Story 1 — Hành vi mặc định không đổi (Ollama qua abstraction) (P1) 🎯 MVP

**Goal**: Refactor sang abstraction mà giữ nguyên hành vi mặc định (Ollama). **Independent test**: `uv run pytest` + 3 acceptance case xanh, output không đổi.

### Tests (viết trước)
- [X] T006 [P] [US1] Test factory chọn Ollama theo mặc định (`get_chat_provider`, `get_embedding_provider`) trong `backend/tests/test_providers.py`
- [X] T007 [P] [US1] Test `OllamaEmbeddingProvider.embed_text` cắt theo `max_embed_chars` (giữ hành vi) trong `backend/tests/test_providers.py`

### Implementation
- [X] T008 [US1] Hiện thực `OllamaChatProvider` + `OllamaEmbeddingProvider` trong `backend/app/providers/ollama.py` (port logic từ `services/llm.py`: qwen3.5 `think=false`, bge-m3, cắt độ dài)
- [X] T009 [US1] Hiện thực `get_chat_provider()` + `get_embedding_provider()` trong `backend/app/providers/factory.py` (chọn theo config; giá trị lạ → `ValueError`)
- [X] T010 [US1] Sửa `backend/app/services/rag.py` dùng factory thay vì import `services/llm` trực tiếp
- [X] T011 [US1] Sửa `backend/scripts/ingest.py` dùng `get_embedding_provider()` thay `llm.embed_texts`
- [X] T012 [US1] Xóa `backend/app/services/llm.py` (logic đã chuyển sang `providers/ollama.py`)
- [X] T013 [US1] Cập nhật `backend/tests/test_rag.py` patch theo provider/factory thay vì `app.services.llm`
- [X] T014 [US1] Chạy `uv run pytest` + 3 acceptance case → tất cả xanh, xác nhận output không đổi

**Checkpoint**: MVP hoàn tất — hệ thống chạy trên abstraction, hành vi giống hệt trước.

---

## Phase 4: User Story 2 — Đổi chat sang Claude + xử lý lỗi mid-stream (P2)

**Goal**: Chọn Claude qua config; lỗi giữa chừng phát SSE `error`. **Independent test**: đặt `chat_provider=claude` + key → trả lời qua Claude; thiếu key → lỗi rõ ràng; mock lỗi mid-stream → sự kiện `error`.

### Tests (viết trước)
- [X] T015 [P] [US2] Test `ClaudeChatProvider.stream` yield text (mock `anthropic` messages.stream) trong `backend/tests/test_claude_provider.py`
- [X] T016 [P] [US2] Test factory raise lỗi cấu hình rõ ràng khi `chat_provider=claude` mà thiếu `claude_api_key`, **và xác nhận `claude_api_key` KHÔNG xuất hiện trong thông điệp lỗi/log** (FR-007), trong `backend/tests/test_providers.py`
- [X] T017 [US2] Test `rag.search_stream` phát sự kiện SSE `error` (không phát `done`) khi provider lỗi sau vài token — đặt trong `backend/tests/test_rag.py` (`TestSearchStreamMidStreamError`)

### Implementation
- [X] T018 [US2] Hiện thực `ClaudeChatProvider` trong `backend/app/providers/claude.py` (Anthropic async SDK, `messages.stream` → `text_stream`, model `claude_model`, timeout `claude_timeout`)
- [X] T019 [US2] Mở rộng `factory.py`: hỗ trợ `chat_provider=claude`, kiểm tra key trước khi khởi tạo
- [X] T020 [US2] Sửa `backend/app/services/rag.py`: bọc vòng streaming try/except → phát `data: {"type":"error",...}` khi lỗi mid-stream (FR-011); thêm `SearchErrorEvent` vào `backend/app/models/schemas.py`
- [X] T021 [US2] Frontend xử lý sự kiện `error`: thêm vào `frontend/lib/types.ts` (RAGEvent), `frontend/hooks/useStreamQuery.ts` (set trạng thái lỗi), `frontend/app/page.tsx` (hiển thị lỗi, không coi phần dở là hoàn chỉnh)
- [X] T022 [US2] Thêm log INFO tên provider + model khi factory khởi tạo (KHÔNG log key) trong `backend/app/providers/factory.py`

**Checkpoint**: Đổi được Ollama ↔ Claude bằng config; lỗi mid-stream báo rõ ràng.

---

## Phase 5: User Story 3 — Dễ mở rộng provider mới (P3)

**Goal**: Thêm provider mới không phải sửa orchestration. **Independent test**: fake provider qua factory được `rag` dùng mà không đổi mã orchestration.

- [X] T023 [P] [US3] Test: đăng ký một fake `ChatProvider` qua factory (monkeypatch) và xác nhận `rag` dùng được nó, không thay đổi mã `rag.py`, trong `backend/tests/test_providers.py`

---

## Phase 6: Polish & Cross-Cutting

- [X] T024 [P] Cập nhật `backend/.env.example` (CHAT_PROVIDER, EMBEDDING_PROVIDER, CLAUDE_API_KEY, CLAUDE_MODEL, CLAUDE_TIMEOUT, CLAUDE_MAX_TOKENS; sửa EMBED_MODEL→bge-m3)
- [X] T025 [P] Cập nhật `docs/architecture.md`: lớp provider abstraction + sự kiện SSE `error`
- [X] T026 Chạy `uv run ruff check .` và kiểm tra coverage ≥ 80% (`uv run pytest --cov`)
- [X] T027 Chạy `npm run build` ở `frontend/` (type-check xử lý sự kiện error)

---

## Dependencies & thứ tự

```
Setup (T001–T003) → Foundational (T004–T005) → US1 (T006–T014) → US2 (T015–T022) → US3 (T023) → Polish (T024–T027)
```

- US1 là **MVP** — độc lập, hoàn tất là có sản phẩm chạy trên abstraction (hành vi cũ).
- US2 phụ thuộc US1 (cần base + factory + ollama đã ổn).
- US3 phụ thuộc factory (US1).

## Cơ hội chạy song song [P]

- T003 song song với T004/T005 (khác file).
- Trong US1: T006, T007 (test) song song.
- Trong US2: T015, T016 (test) song song.
- Polish: T024, T025 song song.

## MVP scope

**Chỉ US1 (T001–T014)** = MVP: hệ thống chạy trên lớp abstraction, hành vi giống hệt PoC.
US2 (Claude) và US3 (mở rộng) là increment tiếp theo.
