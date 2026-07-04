# Tasks: Nền tảng đa lĩnh vực (F1)

**Feature**: `008-multi-domain-foundation` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: test-first (Constitution III). Gate chống bịa (Constitution I): từ chối + 3 acceptance case.

---

## Phase 1: Dữ liệu & schema (US2)
- [ ] T001 `supabase/migrations/*_domain.sql`: `alter table legal_chunks add column domain text`; áp DB đang chạy
- [ ] T002 `scripts/sources.py`: thêm `domain="Nhà ở"` cho cả 5 văn bản

## Phase 2: Prompt tổng quát (US1) 🎯 gate chống bịa

### Tests (viết trước)
- [ ] T003 [P] [US1] `tests/test_rag.py`: **thay** test scope-guard cũ → prompt KHÔNG khoá cứng "Luật Nhà ở"
  (không chứa "phạm vi ... Luật Nhà ở"); vẫn có câu từ chối + rule "Theo Điều" + "chỉ ... Context"

### Implementation
- [ ] T004 [US1] `app/prompts/system.py`: tổng quát mở đầu SYSTEM_PROMPT ("trợ lý pháp luật VN, chỉ dùng
  Context"); `REFUSAL` trung tính; GIỮ NGUYÊN rules 1-6

## Phase 3: Backend carry + filter lĩnh vực (US2 + US3)

### Tests (viết trước)
- [ ] T005 [P] [US3] `tests/test_repository.py` (integration): upsert domain; `dense_candidates(domain="Nhà ở")`
  chỉ trả điều nhà ở; `list_domains()` chứa "Nhà ở"
- [ ] T006 [P] [US2] `tests/test_vector_store.py`: `hybrid_rank` mang `domain` sang SourceDocument
- [ ] T007 [P] [US3] `tests/test_query.py`: `POST /api/query` nhận `domain`; `GET /api/domains` trả danh sách

### Implementation
- [ ] T008 [US2] `app/models/schemas.py`: `SourceDocument` +`domain`; `SearchRequest` +`domain: str|None=None`
- [ ] T009 [US3] `app/db/repository.py`: ChunkRow/RetrievedRow +domain; upsert (INSERT+ON CONFLICT); `_to_row`;
  `dense_candidates`/`all_rows` nhận `domain` optional (`WHERE domain = %s`); thêm `list_domains()`
- [ ] T010 [US2] `app/services/vector_store.py`: `hybrid_rank` truyền `domain` vào SourceDocument
- [ ] T011 [US3] `app/services/rag.py`: `search_stream(query, domain=None)` → truyền domain xuống repo
- [ ] T012 [US3] `app/routers/query.py`: truyền `payload.domain`; thêm `GET /api/domains` (repo.list_domains)
- [ ] T013 [US2] `scripts/ingest.py`: ChunkRow kèm `domain=source.domain`; re-ingest 440 (backfill)

## Phase 4: Frontend (US3 + branding)

- [ ] T014 [US3] `frontend/lib/types.ts`: `SourceDocument` +`domain`; hàm search gửi `domain`
- [ ] T015 [US3] `frontend/lib/api.ts` + `app/api/query/route.ts`: truyền `domain` trong body;
  thêm `app/api/domains/route.ts` (proxy GET /api/domains)
- [ ] T016 [US3] `components/search/DomainFilter.tsx` (mới): fetch /api/domains, chọn lĩnh vực + "Tất cả"
- [ ] T017 [US3] `app/page.tsx`: gắn DomainFilter, truyền domain vào `search`; **branding** (tiêu đề không
  còn khoá cứng "Luật Nhà ở")
- [ ] T018 [US2] `LegalReference.tsx`: (tùy chọn) hiển thị lĩnh vực nhỏ; `app/layout.tsx` metadata tổng quát

## Phase 5: Verify & chốt
- [ ] T019 3 acceptance case gốc + guarantee Điều 58 với "Tất cả" (không hồi quy); câu ngoài phạm vi vẫn từ chối
- [ ] T020 Chọn "Nhà ở" → chỉ trả điều nhà ở; `/api/domains` = ["Nhà ở"]
- [ ] T021 `uv run pytest --cov=app` ≥80% + ruff sạch; `npm run build`
- [ ] T022 [P] `docs/architecture.md` + `README.md` + `CLAUDE.md`: cập nhật định vị đa lĩnh vực + lĩnh vực/lọc

---

## Dependencies
```
T001–T002 (data) → T003–T004 (prompt) → T005–T013 (backend) → T014–T018 (frontend) → T019–T022 (chốt)
```

## MVP
US1 (prompt tổng quát, không hồi quy) + US2 (metadata lĩnh vực) = nền; US3 (lọc) hoàn thiện.
