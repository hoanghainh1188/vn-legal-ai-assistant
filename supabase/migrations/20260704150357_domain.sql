-- Lĩnh vực pháp luật của văn bản (Feature #8, F1). Taxonomy tự chọn trong sources.py.
alter table public.legal_chunks add column if not exists domain text;
create index if not exists legal_chunks_domain_idx on public.legal_chunks (domain);
