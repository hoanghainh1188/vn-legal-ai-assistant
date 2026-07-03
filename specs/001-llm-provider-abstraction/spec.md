# Feature Specification: Lớp abstraction nhà cung cấp LLM/embedding

**Feature Branch**: `001-llm-provider-abstraction`

**Created**: 2026-07-03

**Status**: Draft

**Input**: Issue #1 — chuẩn bị nền tảng hybrid AI (embedding self-host + chat Claude API) cho giai đoạn productization.

## Clarifications

### Session 2026-07-03

- Q: Model Claude mặc định cho chat provider? → A: `claude-sonnet-4-6` (cân bằng chất lượng/chi phí/độ trễ), cấu hình được qua biến môi trường.
- Q: Xử lý khi provider lỗi giữa chừng stream? → A: Phát sự kiện SSE `error` rồi dừng; client hiển thị lỗi rõ, không trình bày phần câu trả lời cắt dở như đã hoàn tất.

## User Scenarios & Testing *(mandatory)*

> Ghi chú: "người dùng" của tính năng này là **đội phát triển/vận hành** sản phẩm; giá trị
> là khả năng đổi nhà cung cấp AI mà không phá hành vi hiện có. Người dùng cuối (người dân
> tra cứu) KHÔNG được cảm nhận bất kỳ thay đổi nào khi vẫn dùng cấu hình mặc định.

### User Story 1 - Giữ nguyên hành vi với cấu hình mặc định (Priority: P1)

Đội vận hành chạy hệ thống với cấu hình mặc định (Ollama) sau khi tái cấu trúc, và mọi
thứ hoạt động **giống hệt trước**: câu trả lời, trích dẫn, luồng streaming, và cả 3 hành vi
kiểm thử gốc (thời hạn chung cư, việt kiều mua nhà, câu hỏi ngoài phạm vi) không đổi.

**Why this priority**: Đây là ràng buộc bất khả xâm phạm — tái cấu trúc không được làm hồi
quy sản phẩm đang chạy. Không đạt điều này thì feature vô giá trị/nguy hiểm.

**Independent Test**: Chạy toàn bộ test suite hiện có + 3 acceptance case với cấu hình mặc
định; tất cả phải xanh, output không đổi so với trước.

**Acceptance Scenarios**:

1. **Given** cấu hình mặc định (chat & embedding = ollama), **When** người dùng hỏi một câu
   trong phạm vi, **Then** hệ thống trả lời kèm "Cơ sở pháp lý" đúng như hành vi hiện tại.
2. **Given** cấu hình mặc định, **When** người dùng hỏi câu ngoài phạm vi, **Then** hệ thống
   từ chối an toàn bằng câu cố định (không đổi so với hiện tại).
3. **Given** codebase sau tái cấu trúc, **When** kiểm tra phụ thuộc của orchestration RAG,
   **Then** nó chỉ phụ thuộc interface, không tham chiếu trực tiếp tới nhà cung cấp cụ thể.

---

### User Story 2 - Đổi nhà cung cấp chat qua cấu hình (Priority: P2)

Đội vận hành đổi nhà cung cấp chat sang Claude bằng cách thay đổi **cấu hình** (không sửa
code business logic) và cung cấp khóa qua biến môi trường; hệ thống chuyển sang dùng Claude
để sinh câu trả lời streaming, giữ nguyên luồng và định dạng.

**Why this priority**: Đây là mục tiêu kiến trúc hybrid (chat chất lượng cao qua API). P2 vì
phụ thuộc P1 (nền abstraction) đã đúng.

**Independent Test**: Đặt cấu hình chat = claude + khóa hợp lệ, gửi một câu hỏi, xác nhận
câu trả lời được sinh qua Claude ở dạng streaming; đặt lại mặc định thì quay về Ollama.

**Acceptance Scenarios**:

1. **Given** cấu hình chat = claude và khóa hợp lệ, **When** người dùng hỏi, **Then** câu trả
   lời được sinh streaming qua Claude theo cùng luồng sự kiện như hiện tại.
2. **Given** cấu hình chat = claude nhưng **thiếu khóa**, **When** khởi động/gọi, **Then** hệ
   thống báo lỗi cấu hình rõ ràng (không chạy im lặng, không lộ giá trị nhạy cảm).

---

### User Story 3 - Mở rộng nhà cung cấp về sau dễ dàng (Priority: P3)

Lập trình viên thêm một nhà cung cấp mới (ví dụ embedding qua API ở feature sau) bằng cách
hiện thực interface và đăng ký với factory, **không phải sửa** orchestration RAG.

**Why this priority**: Lợi ích dài hạn (bảo trì/mở rộng), không chặn giá trị trước mắt.

**Independent Test**: Thêm một hiện thực provider giả (fake) qua factory trong test và xác
nhận orchestration dùng được nó mà không thay đổi mã orchestration.

**Acceptance Scenarios**:

1. **Given** một hiện thực provider mới tuân theo interface, **When** cấu hình trỏ tới nó,
   **Then** factory trả về đúng provider đó cho orchestration.

### Edge Cases

- Cấu hình provider không hợp lệ (giá trị lạ) → báo lỗi rõ ràng khi khởi tạo, liệt kê giá trị hợp lệ.
- Chọn chat = claude nhưng thiếu/không hợp lệ khóa API → lỗi cấu hình tường minh, KHÔNG in khóa.
- Nhà cung cấp bên ngoài (Claude) lỗi mạng/timeout khi streaming → phát sự kiện SSE `error`
  và dừng luồng (FR-011); KHÔNG fallback tự động sang Ollama (quyết định A3).
- Embedding luôn dùng self-host (bge-m3) ở feature này — không có nhánh embedding qua API (A1).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI định nghĩa interface `ChatProvider` với thao tác sinh câu trả lời
  **streaming** dưới dạng luồng token text (`AsyncIterator[str]`), nhận system prompt + message.
- **FR-002**: Hệ thống PHẢI định nghĩa interface `EmbeddingProvider` với thao tác sinh vector
  embedding cho một đoạn text.
- **FR-003**: Hệ thống PHẢI cung cấp hiện thực Ollama cho cả hai interface, giữ **đúng hành vi
  hiện tại** (chat qwen3.5 với thinking tắt; embedding bge-m3 với cắt độ dài an toàn).
- **FR-004**: Hệ thống PHẢI cung cấp `ClaudeChatProvider` sinh câu trả lời streaming qua Claude
  API, chuẩn hóa đầu ra về cùng dạng `AsyncIterator[str]` (chỉ text, bỏ metadata/thinking — A2).
  Model mặc định `claude-sonnet-4-6`, cấu hình được qua biến môi trường.
- **FR-005**: Hệ thống PHẢI chọn nhà cung cấp qua **cấu hình** (biến môi trường) `chat_provider`
  và `embedding_provider`, mặc định `ollama`; việc chọn là **tĩnh** theo cấu hình (A3).
- **FR-006**: Orchestration RAG PHẢI phụ thuộc **chỉ vào interface** (thông qua một factory),
  KHÔNG import/tham chiếu trực tiếp nhà cung cấp cụ thể.
- **FR-007**: Khóa/bí mật của nhà cung cấp ngoài PHẢI lấy từ biến môi trường; KHÔNG hardcode;
  KHÔNG ghi log giá trị bí mật.
- **FR-008**: Khi cấu hình không hợp lệ hoặc thiếu bí mật cần thiết, hệ thống PHẢI báo lỗi rõ
  ràng, tường minh (fail fast) thay vì chạy sai âm thầm.
- **FR-009**: Biến môi trường mới PHẢI được tài liệu hóa trong `.env.example`.
- **FR-010**: Phạm vi RAG (retrieval, prompt chống hallucination, luồng SSE) PHẢI **không đổi**;
  feature này chỉ tái cấu trúc cách gọi provider.
- **FR-011**: Khi provider lỗi **giữa chừng** stream (đã gửi một phần token rồi mất mạng/timeout),
  hệ thống PHẢI phát một sự kiện SSE `error` và dừng luồng, để client báo lỗi rõ ràng và KHÔNG
  trình bày phần câu trả lời cắt dở như đã hoàn tất.

### Key Entities

- **ChatProvider**: hợp đồng cho việc sinh câu trả lời streaming; ẩn chi tiết nhà cung cấp.
- **EmbeddingProvider**: hợp đồng cho việc sinh vector embedding.
- **Provider factory/registry**: ánh xạ cấu hình → hiện thực provider tương ứng.
- **Provider config**: giá trị chọn provider + tham số/bí mật liên quan, đọc theo môi trường.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Với cấu hình mặc định, **100%** test hiện có (27) + 3 acceptance case xanh, đầu ra
  không đổi so với trước tái cấu trúc.
- **SC-002**: Đổi nhà cung cấp chat giữa Ollama và Claude **chỉ bằng thay đổi cấu hình** (0 dòng
  sửa ở business logic RAG).
- **SC-003**: Thêm một nhà cung cấp mới yêu cầu **0 thay đổi** ở mã orchestration RAG (chỉ thêm
  hiện thực + đăng ký factory).
- **SC-004**: **0** bí mật bị hardcode trong mã (xác minh bằng rà soát); mọi biến môi trường mới
  có mặt trong `.env.example`.
- **SC-005**: Độ phủ test ≥ **80%**, gồm test cho factory (chọn đúng provider) và trường hợp lỗi
  cấu hình/thiếu khóa.

## Assumptions

- Embedding vẫn **self-host** (bge-m3) trong feature này; provider embedding qua API để feature
  sau (quyết định A1).
- Chọn provider là **tĩnh** theo cấu hình lúc khởi tạo; KHÔNG có fallback tự động ở feature này (A3).
- Không cần khóa Claude để chạy/kiểm thử cấu hình mặc định (Ollama).
- Ollama local (qwen3.5 + bge-m3) sẵn sàng cho môi trường phát triển như hiện tại.
- Không thay đổi hợp đồng API `/api/query` hay giao diện frontend.
