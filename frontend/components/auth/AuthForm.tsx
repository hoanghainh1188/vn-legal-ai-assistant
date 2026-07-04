"use client";

import { useActionState, useState } from "react";
import { signIn, signUp, type AuthState } from "@/app/login/actions";

const INITIAL: AuthState = { error: null };

type Mode = "login" | "register";

export function AuthForm() {
  const [mode, setMode] = useState<Mode>("login");
  const [state, formAction, pending] = useActionState(
    mode === "login" ? signIn : signUp,
    INITIAL,
  );
  // Ẩn lỗi cũ khi đổi mode; hiện lại ngay khi submit lượt mới (tránh dính lỗi
  // của mode trước mà KHÔNG remount input — remount sẽ xoá dữ liệu đang gõ).
  const [hideError, setHideError] = useState(false);

  const isLogin = mode === "login";
  const error = hideError ? null : state.error;

  function toggleMode() {
    setHideError(true);
    setMode(isLogin ? "register" : "login");
  }

  return (
    <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-bold text-slate-900">
        {isLogin ? "Đăng nhập" : "Tạo tài khoản"}
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        {isLogin
          ? "Đăng nhập để lưu lịch sử tra cứu."
          : "Đăng ký để lưu lịch sử tra cứu."}
      </p>

      <form
        action={formAction}
        onSubmit={() => setHideError(false)}
        className="mt-5 flex flex-col gap-3"
      >
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-slate-600">Email</span>
          <input
            type="email"
            name="email"
            required
            autoComplete="email"
            className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-primary"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-slate-600">Mật khẩu</span>
          <input
            type="password"
            name="password"
            required
            minLength={6}
            autoComplete={isLogin ? "current-password" : "new-password"}
            className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-primary"
          />
        </label>

        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={pending}
          className="mt-1 rounded-lg bg-primary px-4 py-2 font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-60"
        >
          {pending ? "Đang xử lý..." : isLogin ? "Đăng nhập" : "Đăng ký"}
        </button>
      </form>

      <button
        type="button"
        onClick={toggleMode}
        className="mt-4 w-full text-sm text-slate-500 hover:text-slate-700"
      >
        {isLogin ? "Chưa có tài khoản? Đăng ký" : "Đã có tài khoản? Đăng nhập"}
      </button>
    </div>
  );
}
