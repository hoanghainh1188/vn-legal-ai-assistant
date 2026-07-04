-- Lịch sử tra cứu — cô lập theo user bằng Row Level Security (Constitution V).

create table if not exists public.search_history (
    id         bigint generated always as identity primary key,
    user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
    query      text not null check (char_length(query) <= 500),
    sources    jsonb not null default '[]'::jsonb,   -- [{document_id, article_number, article_title}]
    created_at timestamptz not null default now()
);

create index if not exists search_history_user_created_idx
    on public.search_history (user_id, created_at desc);

alter table public.search_history enable row level security;

-- Cấp quyền cho role 'authenticated' (guest/anon KHÔNG có quyền — không dùng lịch sử).
-- RLS phía trên mới là lớp cô lập theo user; grant chỉ mở cổng cho user đã đăng nhập.
grant select, insert, delete on public.search_history to authenticated;

-- Mỗi user chỉ thao tác trên hàng của chính mình (auth.uid()).
create policy "history_select_own" on public.search_history
    for select using (user_id = auth.uid());
create policy "history_insert_own" on public.search_history
    for insert with check (user_id = auth.uid());
create policy "history_delete_own" on public.search_history
    for delete using (user_id = auth.uid());
