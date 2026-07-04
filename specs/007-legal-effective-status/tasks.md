# Tasks: Nhãn hiệu lực + cảnh báo cấp văn bản

**Feature**: `007-legal-effective-status` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: test-first (Constitution III).

---

## Phase 1: Dữ liệu & schema
- [ ] T001 Xác minh `eff_status`/`eff_date` của **NĐ 95/2024** qua API MOJ (169709); điền bảng metadata
- [ ] T002 `supabase/migrations/*_effective_status.sql`: `alter table legal_chunks add column document_name text,
  eff_status text, eff_date date` (nullable); áp vào DB đang chạy
- [ ] T003 `backend/scripts/sources.py`: thêm `eff_status`, `eff_date` vào `LegalSource` (5 văn bản, xác minh)

## Phase 2: Backend carry metadata (US1)

### Tests (viết trước)
- [ ] T004 [P] [US1] `tests/test_vector_store.py`: `hybrid_rank` dựng `SourceDocument` kèm `document_name`
  + `eff_status` (từ RetrievedRow)
- [ ] T005 [P] [US1] `tests/test_repository.py` (integration): upsert + đọc lại có `document_name/eff_status/eff_date`

### Implementation
- [ ] T006 [US1] `app/models/schemas.py`: `SourceDocument` +`document_name: str|None`, `eff_status: str|None`,
  `eff_date: str|None`
- [ ] T007 [US1] `app/db/repository.py`: `ChunkRow`/`RetrievedRow` +3 field; `upsert_chunks` (INSERT + ON
  CONFLICT DO UPDATE cả 3); `dense_candidates`/`all_rows` SELECT thêm; `_to_row` map
- [ ] T008 [US1] `app/services/vector_store.py`: `hybrid_rank` truyền `document_name/eff_status/eff_date` vào SourceDocument
- [ ] T009 [US1] `app/scripts/ingest.py`: build `ChunkRow` kèm metadata từ `source`
- [ ] T010 [US1] Re-ingest 440 chunk → verify cột đã điền; 3 acceptance case + Điều 58 không hồi quy

## Phase 3: Frontend nhãn + cảnh báo (US1 + US2)

### Implementation
- [ ] T011 [US1] `frontend/lib/types.ts`: `SourceDocument` +`document_name`, `eff_status`, `eff_date`
- [ ] T012 [US1] `LegalReference.tsx`: dùng `document_name` (bỏ hardcode nhãn sai); thêm **badge** trạng thái hiệu lực
- [ ] T013 [US2] `LegalReference.tsx`: gộp **1 cảnh báo** khi có ≥1 nguồn "hết hiệu lực…"; trung tính (không cấp điều)
- [ ] T014 [US1/US2] `npm run build` + kiểm thủ công (curl/port khác): nhãn đúng + badge + cảnh báo

## Phase 4: Verify & chốt
- [ ] T015 3 acceptance case + guarantee Điều 58 (không hồi quy); rà **không** khẳng định cấp điều (prompt/UI/metadata)
- [ ] T016 `uv run pytest --cov=app` ≥80% + `ruff` sạch
- [ ] T017 [P] `docs/architecture.md`: ghi nhãn hiệu lực (cấp văn bản)

---

## Dependencies
```
T001–T003 (data/schema) → T004–T010 (backend) → T011–T014 (frontend) → T015–T017 (chốt)
```

## MVP
US1 (nhãn đúng + trạng thái) + US2 (cảnh báo) = giá trị cốt lõi độ tin cậy.
