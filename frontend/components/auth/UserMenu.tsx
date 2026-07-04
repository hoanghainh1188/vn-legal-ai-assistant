"use client";

import Link from "next/link";
import { History, LogOut } from "lucide-react";
import { signOut } from "@/app/login/actions";

interface UserMenuProps {
  email: string;
}

export function UserMenu({ email }: UserMenuProps) {
  return (
    <div className="flex items-center gap-3">
      <Link
        href="/history"
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900"
      >
        <History size={16} />
        <span className="hidden sm:inline">Lịch sử</span>
      </Link>
      <span
        className="hidden max-w-[16ch] truncate text-sm text-slate-400 sm:inline"
        title={email}
      >
        {email}
      </span>
      <form action={signOut}>
        <button
          type="submit"
          className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Đăng xuất</span>
        </button>
      </form>
    </div>
  );
}
