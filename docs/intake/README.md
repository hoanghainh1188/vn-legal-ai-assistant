# Intake — output của subagent design-intake

Đây là "cầu nối" giữa tài liệu Nhật/Figma và Spec Kit.
Mỗi feature 1 file: docs/intake/<feature-slug>.md gồm:
- Input sources (đường dẫn docs + Figma)
- Prompt for /speckit.specify (copy-paste vào Claude Code)
- Ambiguities to raise in /speckit.clarify
- Suggested constitution amendments

File này commit vào Git — bằng chứng agent đã hiểu đúng tài liệu Nhật tại thời điểm sinh spec.
