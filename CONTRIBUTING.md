# Đóng góp cho dự án

Cảm ơn bạn quan tâm! Tài liệu này mô tả quy ước đóng góp cho **Trợ lý tra cứu Luật Nhà
ở Việt Nam (RAG PoC)**.

## Cách đóng góp

1. **Báo lỗi hoặc đề xuất**: mở Issue trên GitHub, mô tả rõ tình huống, câu hỏi mẫu và
   kết quả thực tế vs. mong đợi.
2. **Sửa lỗi hoặc thêm tính năng**: tạo branch `feat/<mo-ta-ngan>` hoặc
   `fix/<mo-ta-ngan>`, mở Pull Request. Xem thêm quy ước branch/commit tại
   [`CLAUDE.md`](CLAUDE.md).

## Trước khi mở PR

Chạy kiểm thử tương đương CI:

```bash
# Backend
cd backend
uv run pytest                 # 27 tests: chunking, parser, hybrid, RAG, API
uv run ruff check .           # lint

# Frontend
cd frontend
npm run build                 # build + type-check
```

Đảm bảo:
- Test pass (đặc biệt 3 test case gốc: chung cư, việt kiều, câu hỏi ngoài phạm vi)
- Không hardcode secret; không commit `.env*`, `chroma_data/`, `node_modules/`

## Nguyên tắc thay đổi

- **Anti-hallucination là ưu tiên số 1**: mọi thay đổi ở `prompts/system.py`,
  retrieval, hay dữ liệu phải kiểm tra lại câu hỏi ngoài phạm vi vẫn bị từ chối an toàn.
- **Dữ liệu pháp lý phải nguyên văn**: chỉ nạp qua `scripts/ingest.py` (fetch từ API
  Bộ Tư pháp). Không sửa tay nội dung điều luật trong `data/`.
- **Đổi model / retrieval**: ghi lại quyết định vào `docs/04-decisions/` và cập nhật
  `docs/architecture.md` nếu ảnh hưởng kiến trúc.

## Cấu trúc & kiến trúc

- Tổng quan code + luồng RAG: [`docs/architecture.md`](docs/architecture.md)
- Quyết định kỹ thuật (D1–D8): [`docs/04-decisions/`](docs/04-decisions/)
- Quy ước dự án cho AI agent: [`CLAUDE.md`](CLAUDE.md)
