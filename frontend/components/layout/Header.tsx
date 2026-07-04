import Link from "next/link";
import { Scale } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { UserMenu } from "@/components/auth/UserMenu";

/**
 * Header server component — đọc phiên hiện tại (Supabase) và hiển thị trạng thái
 * đăng nhập. Guest thấy nút "Đăng nhập"; không chặn việc tra cứu.
 */
export async function Header() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 font-semibold text-slate-900"
        >
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Scale size={18} className="text-primary" />
          </span>
          <span className="hidden sm:inline">Luật Nhà ở</span>
        </Link>

        {user ? (
          <UserMenu email={user.email ?? ""} />
        ) : (
          <Link
            href="/login"
            className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white hover:bg-primary/90"
          >
            Đăng nhập
          </Link>
        )}
      </div>
    </header>
  );
}
