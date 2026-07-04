import { expect, test } from "@playwright/test";

async function register(
  page: import("@playwright/test").Page,
  email: string,
  password: string,
) {
  await page.goto("/login");
  await page.getByRole("button", { name: /Chưa có tài khoản/ }).click();
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: "Đăng ký", exact: true }).click();
  await expect(page.getByRole("button", { name: /Đăng xuất/ })).toBeVisible();
}

/**
 * US2 + US3 + cô lập (SC-004): A tra cứu → lịch sử lưu + xem lại được; B đăng nhập
 * → KHÔNG thấy lịch sử của A. Cần backend RAG (8000) + Supabase local.
 */
test("lưu, xem lại, và cô lập lịch sử giữa hai tài khoản", async ({
  page,
  browser,
}) => {
  test.setTimeout(150_000);
  const password = "password123";
  const emailA = `a_${Date.now()}@test.local`;
  const emailB = `b_${Date.now()}@test.local`;
  const query = "Việt kiều mua nhà ở Việt Nam được không?";

  // A đăng ký + tra cứu thật
  await register(page, emailA, password);
  await page.goto("/");
  await page.getByPlaceholder("Hỏi về Luật Nhà ở...").fill(query);
  await page.getByRole("button", { name: "Tìm kiếm" }).click();
  await expect(page.getByText(/không thay thế tư vấn pháp lý/)).toBeVisible({
    timeout: 120_000,
  });

  // A xem lại — poll (reload) tới khi bản ghi xuất hiện (không dùng sleep cứng)
  await expect(async () => {
    await page.goto("/history");
    await expect(page.getByText(query)).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 15_000 });

  // B ở context riêng (cookie độc lập) → KHÔNG thấy lịch sử của A (RLS cô lập)
  const contextB = await browser.newContext();
  const pageB = await contextB.newPage();
  try {
    await register(pageB, emailB, password);
    await pageB.goto("/history");
    await expect(pageB.getByText(/Chưa có lượt tra cứu nào/)).toBeVisible();
    await expect(pageB.getByText(query)).toHaveCount(0);
  } finally {
    await contextB.close();
  }
});

test("guest không xem được trang lịch sử (chuyển tới đăng nhập)", async ({
  page,
}) => {
  await page.goto("/history");
  await expect(page).toHaveURL(/\/login/);
});
