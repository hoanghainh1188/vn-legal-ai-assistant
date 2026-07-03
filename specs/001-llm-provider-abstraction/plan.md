# Implementation Plan: Lớp abstraction nhà cung cấp LLM/embedding

**Branch**: `001-llm-provider-abstraction` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-llm-provider-abstraction/spec.md`

## Summary

Tách nhà cung cấp LLM/embedding ra sau hai interface (`ChatProvider`, `EmbeddingProvider`)
với một factory chọn theo cấu hình, để đổi chat từ Ollama sang Claude API mà không sửa
business logic RAG. Non-breaking: Ollama là mặc định, hành vi giữ nguyên (27 test + 3
acceptance case xanh). Thêm `ClaudeChatProvider` (model mặc định `claude-sonnet-4-6`) và
xử lý lỗi mid-stream bằng sự kiện SSE `error`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, httpx (Ollama), anthropic (Python SDK — thêm mới), pydantic-settings

**Storage**: N/A (feature này không đụng ChromaDB/dữ liệu)

**Testing**: pytest (+ pytest-asyncio, respx cho mock HTTP)

**Target Platform**: Linux server (backend managed) / dev local

**Project Type**: Web service (backend của web app frontend+backend)

**Performance Goals**: Không thay đổi so với hiện tại ở cấu hình Ollama; với Claude, đặt
timeout hợp lý (mặc định 300s cho streaming) để tránh treo.

**Constraints**: Hành vi mặc định (Ollama) phải giống hệt hiện tại; không hardcode secret;
không đổi hợp đồng `/api/query` và luồng SSE (ngoài việc thêm sự kiện `error`).

**Scale/Scope**: Refactor phạm vi hẹp — 1 package mới `providers/`, sửa `config.py` +
`rag.py`; ~6 file nguồn + test. Không đổi frontend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Không đổi prompt/retrieval/SSE ngữ nghĩa; verify bằng 3 acceptance case | ✅ PASS (gate: 3 case phải xanh) |
| II. Verbatim | Không đụng dữ liệu/ingest | ✅ PASS (N/A) |
| III. Test-First & ≥80% | TDD: viết test provider/factory trước; giữ 27 test + thêm test mới | ✅ PASS (gate) |
| IV. Minh bạch | UI/luồng "Cơ sở pháp lý" không đổi | ✅ PASS (N/A) |
| V. Riêng tư/secret | Claude key qua env, không log; chỉ gửi phần cần tới Claude | ✅ PASS (gate: rà soát không log secret) |
| VI. Đơn giản/abstraction | Feature này CHÍNH LÀ abstraction; nhiều file nhỏ | ✅ PASS |

**Kết luận:** Không có vi phạm cần biện minh → Complexity Tracking để trống.

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-provider-abstraction/
├── plan.md              # File này
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (interface contracts)
│   └── providers.md
└── tasks.md             # Phase 2 (/speckit-tasks — chưa tạo ở đây)
```

### Source Code (repository root)

```text
backend/app/
├── config.py                 # (sửa) thêm chat_provider, embedding_provider, claude_api_key, claude_model
├── providers/                # (mới) package abstraction
│   ├── __init__.py
│   ├── base.py               # Protocol ChatProvider + EmbeddingProvider
│   ├── ollama.py             # OllamaChatProvider, OllamaEmbeddingProvider (port từ services/llm.py)
│   ├── claude.py             # ClaudeChatProvider (Anthropic SDK, model claude-sonnet-4-6)
│   └── factory.py            # get_chat_provider(), get_embedding_provider() theo config
├── services/
│   └── rag.py                # (sửa) dùng factory thay vì import llm trực tiếp
# services/llm.py             # (XÓA — logic Ollama chuyển sang providers/ollama.py, theo research R5)
└── ...

backend/tests/
├── test_providers.py         # (mới) factory chọn provider, lỗi cấu hình/thiếu key
├── test_claude_provider.py   # (mới) ClaudeChatProvider streaming (mock anthropic)
└── (giữ) test_rag.py, test_query.py, test_chunking.py, test_html_parser.py

backend/.env.example          # (sửa) thêm biến provider mới
```

**Structure Decision**: Web service backend hiện có. Thêm package `backend/app/providers/`
đóng gói toàn bộ chi tiết nhà cung cấp; `services/rag.py` chỉ phụ thuộc `providers` qua
factory. Frontend không đổi.

## Complexity Tracking

> Không có vi phạm Constitution → không cần biện minh độ phức tạp.
