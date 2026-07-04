"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export interface AuthState {
  error: string | null;
}

function validate(email: string, password: string): string | null {
  if (!email.includes("@") || email.length < 3) return "Email không hợp lệ.";
  if (password.length < 6) return "Mật khẩu phải có ít nhất 6 ký tự.";
  return null;
}

export async function signIn(
  _prev: AuthState,
  formData: FormData,
): Promise<AuthState> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");

  const invalid = validate(email, password);
  if (invalid) return { error: invalid };

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  // Thông báo chung — KHÔNG tiết lộ email có tồn tại hay không (FR-010).
  if (error) return { error: "Email hoặc mật khẩu không đúng." };

  redirect("/");
}

export async function signUp(
  _prev: AuthState,
  formData: FormData,
): Promise<AuthState> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");

  const invalid = validate(email, password);
  if (invalid) return { error: invalid };

  const supabase = await createClient();
  const { error } = await supabase.auth.signUp({ email, password });
  if (error) {
    const already = /registered|already/i.test(error.message);
    return {
      error: already
        ? "Email đã được đăng ký."
        : "Không thể tạo tài khoản. Vui lòng thử lại.",
    };
  }

  redirect("/");
}

export async function signOut(): Promise<void> {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();
  if (error) console.warn("[auth] signOut lỗi:", error.message);
  redirect("/");
}
