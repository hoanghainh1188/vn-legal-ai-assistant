import { expect, test } from "@playwright/test";

/**
 * US1: đăng ký → thấy đã đăng nhập → đăng xuất → đăng nhập lại.
 * Chỉ cần frontend + Supabase local (không cần backend RAG).
 */
test("đăng ký, đăng xuất, đăng nhập lại", async ({ page }) => {
  const email = `e2e_${Date.now()}@test.local`;
  const password = "password123";

  // Đăng ký (chuyển sang chế độ Đăng ký trước).
  await page.goto("/login");
  await page.getByRole("button", { name: /Chưa có tài khoản/ }).click();
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: "Đăng ký", exact: true }).click();

  // Về trang chủ, header hiện trạng thái đã đăng nhập (nút Đăng xuất).
  await expect(page.getByRole("button", { name: /Đăng xuất/ })).toBeVisible();

  // Đăng xuất → header hiện nút Đăng nhập.
  await page.getByRole("button", { name: /Đăng xuất/ }).click();
  await expect(page.getByRole("link", { name: /Đăng nhập/ })).toBeVisible();

  // Đăng nhập lại bằng đúng thông tin.
  await page.goto("/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByRole("button", { name: /Đăng xuất/ })).toBeVisible();
});

test("đăng nhập sai mật khẩu bị từ chối", async ({ page }) => {
  await page.goto("/login");
  await page
    .locator('input[name="email"]')
    .fill(`nobody_${Date.now()}@test.local`);
  await page.locator('input[name="password"]').fill("wrongpassword");
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByText(/Email hoặc mật khẩu không đúng/)).toBeVisible();
});
