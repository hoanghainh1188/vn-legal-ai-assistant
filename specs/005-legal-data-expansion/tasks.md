# Tasks: Mở rộng dữ liệu — văn bản hướng dẫn Luật Nhà ở

**Feature**: `005-legal-data-expansion` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: test chunker cho văn bản mới viết trước (Constitution III).

---

## Phase 1: Test (viết trước)
- [ ] T001 [US1] Thêm test trong `backend/tests/test_chunking.py`: chunk một mẫu văn bản kiểu Nghị định
  (nhiều Điều, có Chương) → số điều đúng, không trùng, metadata (document_id/chapter) đúng

## Phase 2: Dữ liệu
- [ ] T002 [US1] Thêm 3 `LegalSource` vào `backend/scripts/sources.py`: NĐ 98 (169711), NĐ 100 (169712),
  TT 05 (169122) — kèm `document_id`, `name`, tên file html/txt
- [ ] T003 [US1] Re-ingest: `uv run python scripts/ingest.py` → **440 chunk**; HTML cache vào `data/raw_html/`,
  text vào `data/raw/` (commit làm bằng chứng nguồn)

## Phase 3: Verify (không hồi quy — Constitution I)
- [ ] T004 [US2] 3 acceptance case gốc + guarantee **Điều 58 (Luật Nhà ở)** vẫn đúng trên corpus 440
- [ ] T005 [US1] Truy hồi câu thuộc **NĐ 100** (nhà ở xã hội) → trích đúng `100/2024/NĐ-CP`; câu thuộc
  **NĐ 98** → `98/2024/NĐ-CP`
- [ ] T006 [US1] Ingest idempotent: chạy lại → vẫn 440 (không nhân bản)

## Phase 4: Docs & chốt
- [ ] T007 [P] `docs/architecture.md` + `README.md`: cập nhật phạm vi (4 văn bản, 440 chunk)
- [ ] T008 [P] `docs/04-decisions/2026-07-04-feature-005-data-expansion.md`: hiệu lực một phần + phụ lục
  TT 05 ngoài phạm vi + danh sách ItemID đã verify
- [ ] T009 `uv run pytest` xanh + `ruff check` sạch (coverage ≥80%)

---

## Dependencies
```
T001 (test) → T002 (sources) → T003 (ingest) → T004/T005/T006 (verify) → T007–T009 (docs+chốt)
```

## MVP
Thêm dữ liệu + không hồi quy (T001–T006) = giá trị cốt lõi; docs là hoàn thiện.
