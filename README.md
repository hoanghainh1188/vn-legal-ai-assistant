# Trợ lý pháp luật Việt Nam (RAG)

Ứng dụng web tra cứu pháp luật Việt Nam bằng AI, cho phép người dân hỏi bằng **ngôn ngữ
tự nhiên** và nhận câu trả lời dễ hiểu kèm **trích dẫn điều luật**, **lọc theo lĩnh vực**.
Nền tảng **đa lĩnh vực, mở rộng dần** (thêm lĩnh vực = thêm văn bản + re-ingest).

Lĩnh vực hiện có (**700 điều / 2 lĩnh vực**):
- **Nhà ở** — Luật Nhà ở 2023 (27/2023/QH15) + NĐ 95/98/100/2024 + TT 05/2024/TT-BXD (440 điều).
- **Đất đai** — Luật Đất đai 2024 (31/2024/QH15) (260 điều).

Các lĩnh vực khác (lao động, doanh nghiệp…) thêm dần — chỉ thêm văn bản + `domain`, re-ingest.

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
| Frontend | Next.js 16 (App Router), Tailwind CSS, react-markdown, Lucide Icons |
| Backend | Python 3.12, FastAPI (chỉ lo RAG) |
| Kho + Auth | Supabase local (Postgres + pgvector + Auth), schema qua migrations |
| AI | Ollama — `qwen3.5` (chat), `bge-m3` (embedding, 1024-dim) |
| Retrieval | Hybrid: dense (vector) + lexical BM25-lite, fusion RRF |
| Package managers | `uv` (Python), `npm` (Node), `supabase` CLI |

## Yêu cầu

- Python 3.12, [`uv`](https://github.com/astral-sh/uv)
- Node.js 18+, npm
- Docker + [`supabase` CLI](https://supabase.com/docs/guides/cli) (chạy Postgres+pgvector+Auth local)
- [Ollama](https://ollama.com) đang chạy, đã pull 2 model:

```bash
ollama pull qwen3.5
ollama pull bge-m3
```

## Cài đặt & chạy

```bash
# 0. Khởi Supabase local (Postgres + pgvector + Auth) và áp migrations
supabase start
supabase db reset
export VN_LEGAL_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54422/postgres

# 1. Nạp dữ liệu (chạy 1 lần — tự fetch toàn văn từ API Bộ Tư pháp → Postgres của Supabase)
cd backend
uv run python scripts/ingest.py

# 2. Chạy backend (port 8000)
uv run uvicorn app.main:app --reload --port 8000

# 3. Chạy frontend (port 3000) — ở terminal khác
#    Tạo frontend/.env.local từ .env.local.example (URL + anon key từ `supabase start`)
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000 và bắt đầu tra cứu. Đăng ký/đăng nhập để lưu **lịch sử tra cứu**
(guest vẫn tra cứu bình thường).

> **Cổng:** project này dùng dải **544xx** cho Supabase local (đổi từ mặc định 543xx) để chạy
> song song với project Supabase khác. Lấy URL/anon key thực tế từ output `supabase start`.
>
> **Lưu ý:** ingest chỉ chạy khi cài đặt/cập nhật dữ liệu. Khi search, ứng dụng **không** truy
> cập internet — chỉ đọc Supabase + Ollama local.

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
supabase/
├── config.toml              # Supabase local (cổng 544xx)
└── migrations/              # NGUỒN schema — supabase db reset
    ├── *_legal_chunks.sql   # extension vector + legal_chunks + HNSW
    └── *_search_history.sql # search_history + RLS + grant authenticated

backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + lifespan (đóng pool)
│   ├── config.py            # Settings (model, DATABASE_URL, top_k...)
│   ├── db/                  # Kho vector (Postgres của Supabase)
│   │   ├── connection.py    # Pool psycopg3 async + đăng ký pgvector
│   │   └── repository.py    # VectorRepository (seam) + PgVectorRepository
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
│   └── ingest.py            # 1 lệnh: fetch → chunk → embed → upsert
├── data/raw_html/           # Cache HTML nguồn (fetch từ API)
├── data/raw/                # Text đã xử lý (đầu vào ingest)
└── tests/                   # unit (không cần DB) + integration (Postgres/RLS)

frontend/
├── app/                     # page.tsx, layout, login, history, api/query proxy
├── components/{search,result,auth,layout}/  # UI + AuthForm/UserMenu/Header
├── hooks/useStreamQuery.ts  # Parse SSE + ghi lịch sử sau 'done'
├── lib/                     # api.ts, types.ts, history.ts, supabase/{client,server}
├── proxy.ts                 # Refresh phiên Supabase (cookie httpOnly)
└── tests/e2e/               # Playwright: auth + history
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
