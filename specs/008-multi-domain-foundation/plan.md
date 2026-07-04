# Implementation Plan: Nền tảng đa lĩnh vực (F1)

**Branch**: `008-multi-domain-foundation` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

## Summary

Thêm metadata **lĩnh vực** (cột `domain`, giống eff_status) cho văn bản; **tổng quát hoá prompt** (giữ
chống bịa); endpoint **`/api/domains`** (động) + **bộ lọc lĩnh vực** ở UI; **retrieval lọc theo lĩnh vực**
(tùy chọn, "Tất cả" = không lọc = hành vi cũ). Corpus hiện tại = 1 lĩnh vực "Nhà ở". Không đổi retrieval lõi.

## Technical Context

**Language/Version**: Python 3.12 · TypeScript/Next 16.
**Storage**: cột `domain` trên `legal_chunks` (migration + re-ingest 440).
**Testing**: pytest (domain filter, /api/domains, prompt tổng quát + từ chối, carry domain) + frontend build.
**Constraints**: chống bịa KHÔNG suy yếu (3 acceptance case + từ chối); "Tất cả" giữ nguyên hành vi.
**Scale/Scope**: backend (migration, sources, repository, schemas, rag, vector_store, router, prompts) +
frontend (types, api/proxy, DomainFilter, page/branding).

## Constitution Check

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Prompt tổng quát GIỮ rules chống bịa; test từ chối + 3 case | ✅ PASS (gate) |
| II. Verbatim | Không đụng nội dung điều luật | ✅ PASS |
| III. Test-First & ≥80% | Test domain filter/prompt/domains viết trước | ✅ PASS (gate) |
| IV. Minh bạch | Hiển thị lĩnh vực; bộ lọc rõ ràng | ✅ PASS |
| V. Riêng tư | Không đụng dữ liệu người dùng | ✅ PASS (N/A) |
| VI. Đơn giản | Thêm 1 cột + 1 điều kiện lọc + 1 endpoint; không service mới | ✅ PASS |

## Project Structure

```text
supabase/migrations/*_domain.sql       # +cột domain
backend/
├── scripts/sources.py                 # +domain mỗi văn bản ("Nhà ở")
├── scripts/ingest.py                  # ChunkRow kèm domain
├── app/db/repository.py               # ChunkRow/RetrievedRow +domain; upsert/SELECT/_to_row;
│                                       #   dense_candidates/all_rows +filter domain; list_domains()
├── app/models/schemas.py              # SourceDocument +domain; SearchRequest +domain (optional)
├── app/services/vector_store.py       # hybrid_rank dựng SourceDocument kèm domain
├── app/services/rag.py                # search_stream(query, domain=None) → repo filter
├── app/routers/query.py               # truyền payload.domain; +GET /api/domains
└── app/prompts/system.py              # tổng quát SYSTEM_PROMPT + REFUSAL (giữ rules chống bịa)
frontend/
├── lib/types.ts                       # SourceDocument +domain; body query +domain
├── lib/api.ts + app/api/query/route.ts# gửi domain; +app/api/domains/route.ts (proxy)
├── components/search/DomainFilter.tsx # (mới) chọn lĩnh vực (fetch /api/domains) + "Tất cả"
├── app/page.tsx                       # gắn DomainFilter + truyền domain vào search; branding
└── app/layout.tsx                     # metadata branding tổng quát
```

**Structure Decision**: Domain đi cùng chunk (manifest → DB → RetrievedRow → SourceDocument). Retrieval
thêm điều kiện `WHERE domain = %s` (chỉ khi chọn). Prompt tổng quát tách khỏi housing. `/api/domains` động
để UI tự mở rộng.

## Ghi chú
- **Test scope-guard cũ** (`test_system_prompt_declares_full_corpus_scope`, Pha 7) khẳng định prompt liệt kê
  5 văn bản → **thay** bằng test: prompt KHÔNG khoá cứng "Luật Nhà ở", nhưng GIỮ câu từ chối + rule trích dẫn.
- Re-ingest re-embed 440 (chấp nhận) để backfill `domain`.
- `/api/domains` không bị rate-limit (chỉ /api/query có).

## Complexity Tracking
> Không vi phạm — mở rộng tuyến tính; 0 abstraction mới.
