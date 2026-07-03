<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Bump rationale: Lần đầu phê chuẩn constitution — thiết lập toàn bộ nguyên tắc.

Principles (mới định nghĩa):
  I.   Chính xác pháp lý & Chống bịa (NON-NEGOTIABLE)
  II.  Trung thực với nguồn gốc (Verbatim)
  III. Test-First & Cổng chất lượng (NON-NEGOTIABLE)
  IV.  Minh bạch & An toàn người dùng
  V.   Riêng tư & Tối thiểu dữ liệu ra ngoài
  VI.  Đơn giản & Bảo trì được

Added sections:
  - Ràng buộc kỹ thuật & Bảo mật
  - Quy trình phát triển & Cổng chất lượng
  - Governance

Templates checked:
  ✅ .specify/templates/plan-template.md   — "Constitution Check" tương thích, không cần sửa
  ✅ .specify/templates/spec-template.md    — không thêm/bớt mục bắt buộc, tương thích
  ✅ .specify/templates/tasks-template.md   — loại task (test, security, observability) đã bao phủ
  ✅ CLAUDE.md / docs/architecture.md         — quy ước hiện tại nhất quán với principles

Deferred TODOs: (không có)
-->

# Hiến chương (Constitution) — Trợ lý tra cứu Luật Nhà ở Việt Nam

Tài liệu này là **nguồn nguyên tắc tối cao** của dự án. Mọi spec, plan, task, code và quy
ước khác phải tuân theo. Khi có mâu thuẫn, Hiến chương thắng.

## Core Principles

### I. Chính xác pháp lý & Chống bịa (NON-NEGOTIABLE)

Mọi câu trả lời của hệ thống PHẢI chỉ dựa trên văn bản luật truy xuất được trong context
của lượt hỏi đó. Hệ thống PHẢI:

- Trích dẫn điều/khoản **có thật** trong context, đúng số hiệu.
- **Từ chối an toàn** bằng câu cố định khi câu hỏi nằm ngoài phạm vi dữ liệu.
- TUYỆT ĐỐI KHÔNG bịa số năm/số tiền/thời hạn, KHÔNG nêu điều luật hay văn bản không có
  trong context (kể cả để nói "không có").

**Lý do:** đây là công cụ pháp lý cho người dân — một câu trả lời sai/bịa có thể gây hậu
quả thực tế. Thà từ chối còn hơn trả lời sai. Mọi thay đổi ở prompt, retrieval hay dữ liệu
PHẢI được kiểm chứng lại rằng câu hỏi ngoài phạm vi vẫn bị từ chối.

### II. Trung thực với nguồn gốc (Verbatim)

Nội dung điều luật PHẢI lấy **nguyên văn** từ nguồn chính thống (API Bộ Tư pháp
`apipacs.moj.gov.vn`). Cấm sửa tay nội dung điều luật trong kho dữ liệu. Mỗi trích dẫn PHẢI
kèm số hiệu văn bản; khi có, kèm trạng thái hiệu lực.

**Lý do:** giá trị của sản phẩm nằm ở việc người dùng tin được câu trả lời khớp văn bản
gốc. Paraphrase hay chỉnh sửa văn bản luật phá vỡ niềm tin đó và tạo rủi ro pháp lý.

### III. Test-First & Cổng chất lượng (NON-NEGOTIABLE)

Áp dụng TDD (Red → Green → Refactor): viết test trước, chạy thấy fail, rồi mới implement.
Ba acceptance case gốc (thời hạn chung cư · việt kiều mua nhà · câu hỏi ngoài phạm vi) là
**test hồi quy bắt buộc** — không được để chúng đỏ. `lint` + `test` + `build` PHẢI xanh
trước khi merge. Coverage tối thiểu **80%**.

**Lý do:** hệ thống RAG dễ hồi quy âm thầm (đổi model/prompt/retrieval làm hỏng case cũ).
Test là lưới an toàn duy nhất phát hiện sớm.

### IV. Minh bạch & An toàn người dùng

Mỗi câu trả lời PHẢI đi kèm mục **"Cơ sở pháp lý"** (các điều luật được trích dẫn, xem
được nguyên văn) và **disclaimer** rằng đây là công cụ tham khảo dựa trên AI, không thay
thế tư vấn pháp lý chuyên nghiệp.

**Lý do:** người dùng cần kiểm chứng được nguồn và hiểu đúng giới hạn của công cụ để không
ra quyết định pháp lý sai lầm chỉ dựa vào AI.

### V. Riêng tư & Tối thiểu dữ liệu ra ngoài

Dữ liệu người dùng (tài khoản, lịch sử tra cứu) PHẢI được bảo mật và chỉ dùng cho mục đích
phục vụ chính người dùng đó. Khi gọi LLM bên ngoài (Claude API), chỉ gửi phần dữ liệu thật
sự cần cho câu trả lời. Tuân thủ nguyên tắc thu thập tối thiểu; không lưu dữ liệu nhạy cảm
ngoài mức cần thiết.

**Lý do:** câu hỏi pháp lý có thể lộ hoàn cảnh cá nhân nhạy cảm; tôn trọng quyền riêng tư
là điều kiện để người dân tin dùng.

### VI. Đơn giản & Bảo trì được

Ưu tiên kiến trúc rõ ràng, nhiều file nhỏ (200–400 dòng, tối đa 800). Nhà cung cấp LLM và
embedding PHẢI nằm sau một lớp abstraction để đổi provider không phải sửa business logic
(RAG orchestration). Tài liệu kiến trúc (`docs/architecture.md`) PHẢI được cập nhật cùng
lúc với thay đổi kiến trúc; quyết định kỹ thuật ghi vào `docs/04-decisions/`.

**Lý do:** dự án sẽ đổi provider, mở rộng phạm vi luật và có nhiều người cùng làm — sự đơn
giản và tài liệu đồng bộ là điều kiện để tiến hóa mà không vỡ.

## Ràng buộc kỹ thuật & Bảo mật

- **Kiến trúc AI (hybrid):** embedding self-host (`bge-m3`); chat qua Claude API — qua lớp
  provider abstraction.
- **Lưu trữ:** Postgres + pgvector là kho thống nhất cho vector, tài khoản và lịch sử (thay
  ChromaDB ở production).
- **Hạ tầng:** Frontend trên Vercel; backend + DB trên dịch vụ managed.
- **Bảo mật:** cấm hardcode secret (dùng biến môi trường/secret manager); cấu hình CSP +
  security headers ở production; rate-limit các endpoint công khai để chống lạm dụng; validate
  mọi input ở biên hệ thống.
- **Pháp lý:** disclaimer bắt buộc; không tự đưa ra tư vấn pháp lý cá nhân hóa vượt ngoài
  việc trích dẫn văn bản.

## Quy trình phát triển & Cổng chất lượng

- **Spec-driven:** dùng Spec Kit — specify → clarify → plan → tasks → analyze → implement.
  Mỗi feature gắn với **1 GitHub issue** (Feature ID); branch `NNN-<slug>`.
- **Sync trước khi làm:** sync `main` trước khi bắt feature; khi constitution/glossary vừa
  đổi, rebase và chạy lại `speckit-analyze` để bắt drift.
- **Code review:** dùng subagent `code-reviewer` đối chiếu code với constitution + spec +
  plan + tasks sau implement; xử lý mọi mục Blocking trước test gate.
- **Test gate → Deploy:** test/build xanh mới deploy; deploy là hành động ra ngoài, luôn xin
  xác nhận rõ ràng.
- **File gác cổng:** `docs/00-glossary.md` và `.specify/memory/constitution.md` chỉ đổi qua
  **PR riêng** được steward (code-owner) duyệt — không nhét chung PR feature.

## Governance

Hiến chương này thắng mọi tài liệu và quy ước khác trong workflow. Mọi PR/review PHẢI kiểm
tra sự tuân thủ với các nguyên tắc ở đây; độ phức tạp thêm vào PHẢI được biện minh.

Sửa đổi Hiến chương PHẢI qua một PR riêng, có mô tả lý do và được steward duyệt. Phiên bản
tuân theo semantic versioning: **MAJOR** khi gỡ/định nghĩa lại nguyên tắc theo hướng không
tương thích; **MINOR** khi thêm nguyên tắc/mục hoặc mở rộng đáng kể; **PATCH** khi làm rõ
câu chữ. Khi sửa, cập nhật đồng bộ các template phụ thuộc trong `.specify/templates/`.

Hướng dẫn vận hành hằng ngày cho AI agent: xem [`CLAUDE.md`](../../CLAUDE.md).

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
