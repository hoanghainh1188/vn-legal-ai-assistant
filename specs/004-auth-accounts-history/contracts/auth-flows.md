# Contract: Luồng Auth (Supabase) + ghi lịch sử client-side

**Feature**: `004-auth-accounts-history` | **Date**: 2026-07-04

## Client Supabase (frontend)

```ts
// lib/supabase/client.ts — browser (anon key)
import { createBrowserClient } from "@supabase/ssr";
export const createClient = () =>
  createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );

// lib/supabase/server.ts — server component/route (đọc cookies)
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
// ... createServerClient(URL, ANON, { cookies: { getAll, setAll } })
```

`middleware.ts` gọi `supabase.auth.getUser()` mỗi request để refresh phiên (ghi cookie httpOnly).

## Auth flows (GoTrue)

| Hành động | Gọi | Kết quả |
|-----------|-----|---------|
| Đăng ký | `supabase.auth.signUp({ email, password })` | tạo `auth.users`, phiên (cookie httpOnly) |
| Đăng nhập | `supabase.auth.signInWithPassword({ email, password })` | phiên; sai → lỗi chung |
| Đăng xuất | `supabase.auth.signOut()` | vô hiệu phiên, xoá cookie |
| User hiện tại | `supabase.auth.getUser()` | `{ id, email }` hoặc null (guest) |

- Mật khẩu do GoTrue hash; app **không** chạm plaintext, không lưu.
- Lỗi đăng nhập hiển thị thông báo chung (không tiết lộ email tồn tại).

## Ghi lịch sử (sau khi tra cứu xong)

```ts
// lib/history.ts
export async function saveHistory(query: string, sources: SourceRef[]) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;                       // guest → bỏ qua (FR-006)
  await supabase.from("search_history").insert({ query, sources });
  // user_id tự = auth.uid() (default) — RLS with check đảm bảo đúng chủ
}
```

Gọi trong `useStreamQuery` sau sự kiện SSE `done` (đã có `answer` + `sources`). `SourceRef` =
`{ document_id, article_number, article_title }` trích từ `sources` của lượt tra cứu.

## Đọc lịch sử (trang /history)

```ts
const supabase = createClient();
const { data } = await supabase
  .from("search_history")
  .select("id, query, sources, created_at")
  .order("created_at", { ascending: false });
// RLS chỉ trả hàng của auth.uid() — không cần lọc user_id thủ công
```

## Bất biến bảo mật
- Frontend chỉ dùng **anon key**; `service_role` KHÔNG bao giờ vào bundle frontend.
- Không có endpoint FastAPI nào cho auth/history — cô lập hoàn toàn bằng RLS.
- `/api/query` (RAG) không đổi; không nhận/không cần token.
