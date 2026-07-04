import { createBrowserClient } from "@supabase/ssr";

/**
 * Supabase client cho browser (Client Components). Chỉ dùng **anon key** —
 * KHÔNG bao giờ đưa service_role vào frontend (Constitution V, FR-009).
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
