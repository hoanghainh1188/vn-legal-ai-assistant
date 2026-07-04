# Feature Specification: Migrate kho vector sang Postgres + pgvector

**Feature Branch**: `003-postgres-pgvector`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #3 — thay kho vector ChromaDB local bằng Postgres + pgvector, làm xương sống lưu
trữ thống nhất cho giai đoạn productization (roadmap epic #2, Pha 1).

## Clarifications

### Session 2026-07-04

- Q: Cách truy cập Postgres từ backend? → A: **psycopg3 async + raw SQL** (+ pgvector register), không ORM — theo Constitution VI (đơn giản).
- Q: Lexical retrieval giữ nguyên (IDF/BM25-lite Python) hay chuyển sang Postgres FTS? → A: **Giữ IDF/BM25-lite Python** (lấy rows từ Postgres, score trong Python) — bảo toàn hành vi (title×3, guarantee Điều 58).
- Q: DB cho dev/test — pgvector qua Docker + seam repository? → A: **Repository seam** (`VectorRepository` protocol) cho unit test không cần DB thật; pgvector qua Docker cho e2e/ingest local (bắt buộc bởi FR-008 + Constitution III).
- Q: Công cụ migration schema? → A: **File SQL versioned + runner nhỏ** (chưa dùng Alembic; nâng ở Pha 6 nếu cần).
- Q: Kết nối Supabase cloud thật ở Pha 1 hay hoãn Pha 6? → A: **Hoãn tới Pha 6** — Pha 1 dùng pgvector cục bộ (Docker), tương thích Supabase.

## User Scenarios & Testing *(mandatory)*

> Ghi chú: "người dùng" của tính năng này là **đội phát triển/vận hành**; giá trị là chuyển kho
> vector sang nền tảng production (Postgres+pgvector) mà **không** làm người dân tra cứu cảm nhận
> bất kỳ thay đổi nào. Đây là điều kiện tiên quyết cho tài khoản + lịch sử (Pha 2) và deploy thật.

### User Story 1 - Giữ nguyên hành vi sau khi đổi kho vector (Priority: P1)

Đội vận hành thay ChromaDB bằng Postgres+pgvector; sau khi nạp lại dữ liệu, hệ thống trả lời
**giống hệt trước**: cùng câu trả lời, cùng "Cơ sở pháp lý" trích dẫn, cùng luồng streaming, và
cả 3 hành vi kiểm thử gốc không đổi. Đặc biệt hybrid retrieval vẫn **surface được Điều 58** dù
điểm dense thấp.

**Why this priority**: Ràng buộc bất khả xâm phạm (Constitution I — chống bịa/đúng nguồn). Migrate
hạ tầng không được làm hồi quy sản phẩm đang chạy; nếu chất lượng truy hồi giảm, feature vô giá trị.

**Independent Test**: Chạy toàn bộ test suite + 3 acceptance case sau migration; tất cả xanh, thứ
tự/nội dung nguồn trả về tương đương trước.

**Acceptance Scenarios**:

1. **Given** dữ liệu đã nạp vào Postgres+pgvector, **When** người dùng hỏi "Chung cư có thời hạn
   sở hữu tối đa bao nhiêu năm?", **Then** hệ thống trả lời kèm trích dẫn **Điều 58** như hiện tại.
2. **Given** dữ liệu đã nạp, **When** người dùng hỏi "Việt kiều mua nhà ở VN được không?", **Then**
   hệ thống trả lời có trích **Điều 8 & 9** như hiện tại.
3. **Given** dữ liệu đã nạp, **When** người dùng hỏi câu ngoài phạm vi (vượt tốc độ), **Then** hệ
   thống từ chối an toàn bằng câu cố định, không đổi so với hiện tại.
4. **Given** một truy vấn mà điều luật liên quan có điểm dense thấp nhưng khớp tiêu đề, **When**
   truy hồi hybrid chạy, **Then** điều đó vẫn được đưa lên (guarantee lexical giữ nguyên).

---

### User Story 2 - Kho lưu trữ quan hệ thống nhất, tái tạo được (Priority: P2)

Đội vận hành có một kho **Postgres** chứa các chunk pháp lý + vector embedding, sẵn sàng để về sau
đặt cùng tài khoản/lịch sử (Pha 2). Chạy lại pipeline ingest nạp lại toàn bộ dữ liệu một cách
**idempotent** (không nhân bản), tái tạo được từ đầu.

**Why this priority**: Đây là mục tiêu hạ tầng của Pha 1 — nền tảng cho các pha sau. P2 vì phụ
thuộc P1 (hành vi truy hồi phải đúng trước đã).

**Independent Test**: Chạy script ingest hai lần liên tiếp; số chunk trong DB ổn định (293), không
trùng lặp; truy vấn cho kết quả nhất quán.

**Acceptance Scenarios**:

1. **Given** DB rỗng, **When** chạy ingest, **Then** toàn bộ chunk (198 điều Luật + 95 điều Nghị
   định = 293) được nạp với đầy đủ metadata (article_number, article_title, document_id, chapter).
2. **Given** DB đã có dữ liệu, **When** chạy lại ingest, **Then** dữ liệu được làm mới không nhân
   bản (idempotent).

---

### User Story 3 - Kiểm thử truy hồi không cần DB thật (Priority: P3)

Lập trình viên chạy được toàn bộ test suite (gồm test logic hybrid/RRF/lexical) mà **không cần**
một Postgres đang chạy, nhờ tách logic truy hồi khỏi tầng truy cập dữ liệu qua một lớp trừu tượng.

**Why this priority**: Giữ vòng lặp TDD nhanh (Constitution III test-first) và CI nhẹ. Lợi ích bảo
trì dài hạn, không chặn giá trị trước mắt.

**Independent Test**: Chạy `pytest` trên máy không có Postgres; các test logic truy hồi vẫn chạy và
xanh nhờ repository giả (fake).

**Acceptance Scenarios**:

1. **Given** không có Postgres đang chạy, **When** chạy test suite, **Then** test logic hybrid dùng
   repository giả vẫn xanh (Điều 58 vẫn được surface).

### Edge Cases

- Cấu hình DB thiếu/không hợp lệ (thiếu `DATABASE_URL`, sai host/cổng) → báo lỗi rõ ràng, fail fast;
  KHÔNG in giá trị bí mật (mật khẩu trong connection string).
- Bảng chưa được nạp dữ liệu (rỗng) → truy vấn trả về rỗng một cách an toàn, không lỗi 500 khó hiểu.
- Số chiều embedding không khớp cột `vector(1024)` → báo lỗi tường minh khi ghi.
- Chạy ingest khi DB đang có dữ liệu → làm mới idempotent, không nhân bản chunk.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI lưu mỗi chunk pháp lý cùng vector embedding **1024 chiều** trong Postgres
  với pgvector, giữ nguyên metadata: `article_number, article_title, document_id, chapter, content`.
- **FR-002**: Hệ thống PHẢI truy hồi theo độ tương đồng **cosine** trên pgvector, trả về cùng cấu
  trúc `SourceDocument` như hiện tại (không đổi hợp đồng phía trên).
- **FR-003**: Hệ thống PHẢI **giữ nguyên** thuật toán hybrid: dense + lexical IDF/BM25-lite (tiêu đề
  ×3) + Reciprocal Rank Fusion (`rrf_k=60`) + guarantee-slot cho khớp tiêu đề; kết quả tương đương
  hành vi hiện tại (Điều 58 vẫn được surface khi dense rank thấp).
- **FR-004**: Orchestration RAG, prompt chống hallucination, hợp đồng `/api/query` và luồng SSE PHẢI
  **không đổi**; feature này chỉ thay tầng lưu trữ/truy hồi vector.
- **FR-005**: Pipeline ingest PHẢI nạp lại toàn bộ chunk một cách **idempotent** (làm mới không nhân
  bản), tái tạo được từ đầu; tổng 293 chunk từ 2 văn bản.
- **FR-006**: Thông tin kết nối DB PHẢI lấy từ cấu hình/biến môi trường (`VN_LEGAL_DATABASE_URL`);
  KHÔNG hardcode; KHÔNG ghi log chuỗi kết nối/bí mật.
- **FR-007**: Khi cấu hình DB thiếu/không hợp lệ, hệ thống PHẢI báo lỗi rõ ràng (fail fast) thay vì
  chạy sai âm thầm.
- **FR-008**: Logic truy hồi (dense/lexical/RRF) PHẢI kiểm thử được **không cần DB thật**, thông qua
  một lớp trừu tượng truy cập dữ liệu (repository) cho phép tiêm bản giả trong test.
- **FR-009**: Biến môi trường mới PHẢI được tài liệu hoá trong `.env.example`; PHẢI có cách chạy một
  Postgres+pgvector cục bộ cho phát triển.
- **FR-010**: Phụ thuộc và mã liên quan **ChromaDB** PHẢI được gỡ bỏ khỏi dự án sau migration.
- **FR-011**: Schema DB (extension `vector`, bảng, index vector) PHẢI được tạo lại một cách tái tạo
  được (reproducible) cho môi trường mới.

### Key Entities

- **LegalChunk (bản ghi DB)**: một điều luật đã chunk — `article_number, article_title, document_id,
  chapter, content` + vector embedding 1024 chiều.
- **VectorRepository**: hợp đồng lưu/truy hồi chunk (ẩn chi tiết Postgres), là seam để test không cần
  DB thật và để tách logic hybrid khỏi tầng dữ liệu.
- **Kho Postgres+pgvector**: kho quan hệ thống nhất, về sau chứa cả tài khoản/lịch sử (Pha 2).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sau migration, **100%** test hiện có + 3 acceptance case xanh; câu trả lời & trích dẫn
  tương đương trước migration.
- **SC-002**: Guarantee hybrid được bảo toàn: có test xác nhận điều khớp tiêu đề (Điều 58) được
  surface dù dense rank thấp.
- **SC-003**: Toàn bộ test suite chạy được **không cần** Postgres đang chạy (repository giả).
- **SC-004**: **0** bí mật hardcode; `VN_LEGAL_DATABASE_URL` có trong `.env.example`; `chromadb` đã
  được gỡ khỏi phụ thuộc và mã.
- **SC-005**: Độ phủ test ≥ **80%**.
- **SC-006**: Chạy ingest nạp **293** chunk vào Postgres một cách tái tạo được & idempotent.

## Assumptions

- Embedding vẫn **self-host** bge-m3 (1024 chiều); không đổi provider embedding ở feature này.
- Pha 1 dùng **pgvector cục bộ** (Docker) — tương thích Supabase (cùng pgvector); wiring Supabase
  cloud thật hoãn tới **Pha 6**.
- Không thay đổi hợp đồng API `/api/query` hay giao diện frontend.
- Auth/RLS/đa người dùng **ngoài phạm vi** (thuộc Pha 2).
- Ollama local (bge-m3) sẵn sàng cho môi trường phát triển như hiện tại.
