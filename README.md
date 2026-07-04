# Trợ lý tra cứu Luật Nhà ở Việt Nam (RAG PoC)

Ứng dụng web tra cứu pháp luật Việt Nam bằng AI, cho phép người dân hỏi bằng **ngôn ngữ
tự nhiên** và nhận câu trả lời dễ hiểu kèm **trích dẫn điều luật**. Toàn bộ AI chạy
**local** qua Ollama — không gọi API bên ngoài.

Phạm vi dữ liệu hiện tại: **Luật Nhà ở 2023 (Luật số 27/2023/QH15)** và **Nghị định
95/2024/NĐ-CP** (198 + 95 điều).

## Tính năng

- 🔍 **Tìm kiếm ngữ nghĩa** — hỏi tự nhiên tiếng Việt, không cần đúng từ khóa điều luật
- 💬 **Câu trả lời streaming** — hiển thị dần theo thời gian thực (SSE), render markdown
- 📖 **Cơ sở pháp lý** — accordion mở rộng xem nguyên văn các điều được trích dẫn
- 🛡️ **Chống bịa (anti-hallucination)** — chỉ trả lời trong phạm vi dữ liệu, từ chối an
  toàn khi câu hỏi ngoài phạm vi
- 🔒 **Chạy hoàn toàn local** — dữ liệu và AI đều trên máy, hoạt động cả khi offline

## Tech stack

| Tầng | Công nghệ |
|------|-----------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, react-markdown, Lucide Icons |
| Backend | Python 3.12, FastAPI, Postgres + pgvector (kho vector, local qua Docker) |
| AI | Ollama — `qwen3.5` (chat), `bge-m3` (embedding, 1024-dim) |
| Retrieval | Hybrid: dense (vector) + lexical BM25-lite, fusion RRF |
| Package managers | `uv` (Python), `npm` (Node) |

## Yêu cầu

- Python 3.12, [`uv`](https://github.com/astral-sh/uv)
- Node.js 18+, npm
- Docker (Postgres + pgvector cục bộ)
- [Ollama](https://ollama.com) đang chạy, đã pull 2 model:

```bash
ollama pull qwen3.5
ollama pull bge-m3
```

## Cài đặt & chạy

```bash
# 0. Khởi Postgres + pgvector (local) và đặt biến kết nối
docker compose up -d db
export VN_LEGAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vn_legal

# 1. Nạp dữ liệu vào Postgres (chạy 1 lần — tự áp schema + fetch toàn văn từ API Bộ Tư pháp)
cd backend
uv run python scripts/ingest.py

# 2. Chạy backend (port 8000)
uv run uvicorn app.main:app --reload --port 8000

# 3. Chạy frontend (port 3000) — ở terminal khác
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000 và bắt đầu tra cứu.

> **Lưu ý:** bước ingest (Pha 1) chỉ chạy khi cài đặt hoặc cập nhật dữ liệu. Khi search
> (Pha 2), ứng dụng **không** truy cập internet — chỉ đọc Postgres + pgvector + Ollama local.

## Cách hoạt động (RAG)

```
Câu hỏi → embed (bge-m3) → hybrid retrieval (Postgres+pgvector) → top-8 điều liên quan
       → prompt (chống bịa) → qwen3.5 streaming → câu trả lời + trích dẫn
```

Xem chi tiết kiến trúc, sơ đồ Mermaid và luồng dữ liệu tại
[`docs/architecture.md`](docs/architecture.md).

## Chuẩn bị / cập nhật dữ liệu

Dữ liệu được fetch tự động từ **API mở của Bộ Tư pháp** (`apipacs.moj.gov.vn`) — không
cần tải thủ công.

| Trường hợp | Lệnh |
|---|---|
| Thêm luật mới | Thêm `vbpl_id` vào `backend/scripts/sources.py` → `uv run python scripts/ingest.py` |
| Luật được sửa đổi | `uv run python scripts/fetch_sources.py` → `uv run python scripts/ingest.py` |

`vbpl_id` là ItemID trên vbpl.vn (số cuối URL trang chi tiết văn bản).

## Cấu trúc dự án

```
backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + lifespan (đóng pool)
│   ├── config.py            # Settings (model, DATABASE_URL, top_k...)
│   ├── db/                  # Kho vector Postgres+pgvector
│   │   ├── connection.py    # Pool psycopg3 async + đăng ký pgvector
│   │   ├── repository.py    # VectorRepository (seam) + PgVectorRepository
│   │   └── schema.sql       # legal_chunks + index HNSW cosine
│   ├── routers/query.py     # POST /api/query (SSE)
│   ├── providers/           # Abstraction LLM/embedding (Ollama/Claude)
│   ├── services/
│   │   ├── rag.py           # Điều phối RAG (repository → hybrid_rank → stream)
│   │   └── vector_store.py  # hybrid_rank — hàm thuần dense + lexical RRF
│   └── prompts/system.py    # System prompt chống hallucination
├── scripts/
│   ├── sources.py           # Manifest tài liệu (vbpl_id)
│   ├── fetch_sources.py     # Fetch toàn văn từ API MOJ
│   ├── html_to_legal_text.py# HTML → text sạch (bỏ mục lục)
│   ├── chunk_legal_text.py  # Tách theo "Điều"
│   ├── init_db.py           # Áp schema.sql (idempotent)
│   └── ingest.py            # 1 lệnh: schema → fetch → chunk → embed → upsert
├── data/raw_html/           # Cache HTML nguồn (fetch từ API)
├── data/raw/                # Text đã xử lý (đầu vào ingest)
└── tests/                   # unit (không cần DB) + integration (cần Postgres)

frontend/
├── app/                     # page.tsx, layout, api/query proxy
├── components/search|result/# SearchBar, AnswerStream, LegalReference...
├── hooks/useStreamQuery.ts  # Parse SSE stream
└── lib/                     # api.ts, types.ts
```

## Kiểm thử

```bash
cd backend && uv run pytest        # 27 tests: chunking, parser, hybrid, RAG, API
cd frontend && npm run build       # kiểm tra build + type-check
```

## Deploy

- **Frontend**: Vercel (`vercel --prod` từ thư mục `frontend/`)
- **Backend**: Docker Compose (`docker compose up -d` từ root)

## Ghi chú

Dự án được khởi tạo từ template [spec-driven-jp](https://github.com/hoanghainh1188/spec-driven-jp);
quy ước làm việc với AI agent xem tại [`CLAUDE.md`](CLAUDE.md), các quyết định kỹ thuật
tại [`docs/04-decisions/`](docs/04-decisions/).

> ⚠️ Đây là **công cụ tham khảo dựa trên AI**, không thay thế tư vấn pháp lý chuyên nghiệp.
