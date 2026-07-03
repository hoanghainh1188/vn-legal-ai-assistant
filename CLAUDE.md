# Quy ước dự án cho AI agent

## Tổng quan
<Điền: dự án làm gì, khách hàng là ai, ngôn ngữ tài liệu thiết kế gốc>

## Tech stack
<Điền khi bắt đầu code — mặc dù `impl-planner` của Spec Kit sẽ tự phát hiện, khai báo sẵn ở đây
giúp mọi agent nhất quán ngay từ lượt gọi đầu tiên>

## Cấu trúc và ý nghĩa từng phần

- **`docs/01-basic-design/`, `docs/02-detail-design/`, `docs/03-ui/`** — nguồn sự thật GỐC từ khách hàng.
  Đây là source of truth duy nhất. Agent KHÔNG BAO GIỜ sửa nội dung ở đây. Khi có bản mới, thêm file mới +
  CHANGELOG.md, không ghi đè.

- **`docs/00-glossary.md`** — thuật ngữ Nhật-Việt-Anh. Mọi agent PHẢI tra file này trước khi đặt tên biến/field
  liên quan nghiệp vụ. Nếu gặp thuật ngữ mới, thêm vào đây trước, không tự dịch.

- **`docs/04-decisions/`** — nơi lưu câu trả lời cho mọi ambiguity mà `/speckit.clarify` từng giải quyết.
  Trước khi hỏi lại 1 câu đã có trong đây, agent phải tra cứu trước.

- **`docs/intake/`** — output của subagent `design-intake`. Đây là cầu nối giữa tài liệu Nhật/Figma và Spec Kit.

- **`specs/<feature>/`** — do Spec Kit sinh (spec.md, plan.md, tasks.md). CÓ THỂ tái sinh, không chỉnh tay.
  Nếu sai, sửa docs/ gốc hoặc bổ sung docs/04-decisions/ rồi chạy lại pipeline.

- **`.specify/memory/constitution.md`** — nguyên tắc bất di bất dịch của dự án. Thắng mọi thứ khác trong workflow Spec Kit.

- **`src/`** — code thật. Agent bám theo pattern đã có, không tự đổi kiến trúc.

## Cách chạy pipeline sinh code từ design
Gõ `/design-to-code` trong Claude Code, cung cấp đường dẫn tài liệu và link Figma khi được hỏi.

**Mô hình chạy:** `/design-to-code` là một *runbook điều phối*, KHÔNG tự gọi được các slash command
`/speckit.*` (Claude Code không cho command gọi command). Vì vậy:
- Bước dùng **subagent** (`design-intake`, `code-reviewer`) → command tự gọi qua Task tool.
- Bước dùng **Spec Kit** (`/speckit.specify|clarify|plan|tasks|analyze|implement`) → command in ra
  lệnh chính xác để **bạn tự dán và chạy**, rồi dừng chờ bạn báo xong.

Trình tự: design-intake → [handoff] specify → clarify → plan → tasks → analyze → implement
→ code-reviewer → **test gate** → **deploy**. Dừng xin xác nhận ở mọi checkpoint.

## Deploy
<Điền phương thức deploy cụ thể của dự án — `/design-to-code` bước 12 sẽ đọc mục này.
Ví dụ: `vercel --prod`, hoặc push lên branch trigger CI/CD, hoặc build container + đẩy registry.
Nếu để trống, pipeline sẽ dừng và hỏi bạn trước khi deploy.>

## Quy tắc bắt buộc
1. Mọi mâu thuẫn giữa basic design / detail design / Figma phải được nêu vào `/speckit.clarify`,
   không được tự chọn 1 bên và im lặng.
2. Mọi câu trả lời cho clarify phải được ghi vào `docs/04-decisions/`, không chỉ trả lời miệng trong chat.
3. `docs/intake/` và `specs/` được commit vào Git — bằng chứng agent đã hiểu đúng design tại thời điểm code được viết.
4. **Feature ID = số issue GitHub.** Branch đặt tên `NNN-<slug>` với `NNN` = số issue zero-pad tối thiểu
   3 chữ số (VD issue #42 → `042-user-reservation`). Không tự chọn số → tránh trùng khi nhiều người làm.
5. **Gác cổng file dùng chung:** `docs/00-glossary.md` và `.specify/memory/constitution.md` chỉ được đổi
   qua **PR riêng** được steward (code-owner) duyệt — không nhét chung vào PR feature.
6. **Chống lệch ngữ cảnh:** sync `main` trước khi bắt đầu feature; khi constitution/glossary vừa đổi trên
   `main`, rebase và **chạy lại `/speckit.analyze`** để bắt drift.

> Làm việc nhóm (nhiều người/1 dự án): xem đầy đủ ở [`docs/TEAM-WORKFLOW.md`](docs/TEAM-WORKFLOW.md).
