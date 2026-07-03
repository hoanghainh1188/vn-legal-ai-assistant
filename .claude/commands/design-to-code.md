---
description: Pipeline hybrid — đọc tài liệu Nhật/Figma rồi dẫn dắt toàn bộ workflow Spec Kit đến test + deploy
---

Bạn là **điều phối viên (runbook)**. Bạn KHÔNG tự gọi được các slash command `/speckit.*`
— Claude Code không cho một command gọi command khác. Với mỗi bước Spec Kit, bạn phải **in ra
lệnh chính xác để người dùng tự dán và chạy**, rồi DỪNG chờ họ báo xong mới tiếp tục.
Chỉ có subagent (`design-intake`, `code-reviewer`) là bạn gọi trực tiếp qua Task tool.

Quy ước:
- **[TỰ CHẠY]** = bạn tự làm (git, gọi subagent).
- **[HANDOFF]** = in lệnh `/speckit.x …` cho người dùng chạy, rồi DỪNG chờ xác nhận.
- **[DỪNG]** = checkpoint bắt buộc chờ người dùng review trước khi đi tiếp.

Sau mỗi bước: báo cáo ngắn — vừa làm gì, artifact ở đâu, bước kế tiếp là gì.

---

1. **[TỰ CHẠY] Tạo git branch mới** cho feature: `git checkout -b <NNN>-<feature-slug>`.
   `<NNN>` = **số GitHub issue** của feature, zero-pad tối thiểu 3 chữ số (VD issue #42 →
   `042-user-reservation`). Nếu chưa có issue, DỪNG và yêu cầu người dùng tạo issue trước (dùng
   `Feature` issue template). Số issue là ID toàn cục → tránh trùng khi nhiều người cùng làm.
   Xem `docs/TEAM-WORKFLOW.md`. Spec Kit dùng tên branch để phát hiện feature đang active.

2. **[TỰ CHẠY] Gọi subagent `design-intake`** (qua Task tool) với đường dẫn tài liệu trong
   `docs/01-basic-design/`, `docs/02-detail-design/` và link/node Figma trong `docs/03-ui/`.
   Nó ghi ra `docs/intake/<feature>.md`.

3. **[DỪNG]** Hiển thị file intake, đặc biệt mục "Prompt for /speckit.specify" và "Ambiguities".
   Chờ người dùng xác nhận trước khi tiếp tục.

4. **[HANDOFF] specify** — In cho người dùng:
   > Dán và chạy lệnh sau, xong báo tôi:
   > `/speckit.specify <đoạn prompt lấy nguyên từ file intake>`
   Chờ người dùng báo `spec.md` đã sinh xong.

5. **[HANDOFF] clarify** (chỉ khi file intake có "Ambiguities") — In:
   > `/speckit.clarify <các câu hỏi/tiêu điểm lấy từ mục Ambiguities>`
   Lệnh này sẽ hỏi ngược người dùng. Sau khi họ trả lời xong, **[TỰ CHẠY]** ghi câu trả lời vào
   `docs/04-decisions/<YYYY-MM-DD>-<slug>.md` (được phép Write) rồi tiếp tục.

6. **[HANDOFF] plan** — In: `/speckit.plan` (thêm tech stack/constraint nếu cần). Chờ `plan.md`.

7. **[HANDOFF] tasks** — In: `/speckit.tasks`. Chờ `tasks.md`.

8. **[HANDOFF + DỪNG] analyze** — In: `/speckit.analyze`. Yêu cầu người dùng dán lại kết quả
   cross-artifact analysis. Nếu có vấn đề, quay lại sửa spec/plan/tasks (lặp bước 4–7) **trước khi**
   sang implement. Không đi tiếp khi analyze còn cảnh báo chưa xử lý.

9. **[HANDOFF] implement** — In: `/speckit.implement`. Chờ người dùng báo code đã sinh xong.

10. **[TỰ CHẠY] Gọi subagent `code-reviewer`** (qua Task tool) để đối chiếu code với 4 nguồn
    (constitution, spec, plan, tasks). Mọi mục **Blocking** phải xử lý (thường bằng cách chạy lại
    `/speckit.implement` với yêu cầu sửa cụ thể) trước khi sang test gate.

11. **[DỪNG] Test gate** — Chạy `npm run lint`, `npm run test`, `npm run build`
    (hoặc lệnh test/build tương đương của dự án). **Bắt buộc xanh** mới đi tiếp; nếu đỏ, báo lỗi
    và dừng — không deploy khi test/build còn fail.

12. **[DỪNG] Deploy** — Đọc mục **"## Deploy"** trong `CLAUDE.md` để lấy phương thức deploy cụ thể
    của dự án (VD: Vercel, CI/CD, container…). Xác nhận build production ok, rồi thực hiện deploy theo
    đúng phương thức đó. Đây là hành động ra bên ngoài — luôn xin xác nhận rõ ràng trước khi chạy.
    Nếu `CLAUDE.md` chưa khai báo phương thức deploy, DỪNG và hỏi người dùng.

Không tự ý bỏ qua bước [DỪNG]/[HANDOFF] dù người dùng có vẻ vội — luôn chờ xác nhận rõ ràng, và
không bao giờ giả vờ đã chạy `/speckit.*` thay người dùng.
