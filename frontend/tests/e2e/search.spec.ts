import { expect, test } from "@playwright/test";

/**
 * E2E luồng tra cứu — deterministic bằng cách mock SSE tại tầng mạng
 * (page.route), không cần backend/Ollama.
 */

const SOURCE = {
  document_id: "27/2023/QH15",
  article_number: 58,
  article_title: "Thời hạn sử dụng nhà chung cư",
  content: "Nội dung Điều 58.",
  relevance_score: 0.92,
  document_name: "Luật Nhà ở 2023",
  eff_status: "Hết hiệu lực một phần",
  eff_date: "2024-08-01",
  domain: "Nhà ở",
};

function sse(events: unknown[]): string {
  return events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
}

test.beforeEach(async ({ page }) => {
  // Bộ lọc lĩnh vực luôn có 2 lĩnh vực (mock /api/domains).
  await page.route("**/api/domains", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ domains: ["Đất đai", "Nhà ở"] }),
    }),
  );
});

test("hỏi → hiện Cơ sở pháp lý + câu trả lời stream", async ({ page }) => {
  await page.route("**/api/query", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sse([
        { type: "sources", data: [SOURCE] },
        { type: "token", data: "Theo Điều 58, " },
        {
          type: "token",
          data: "nhà chung cư có thời hạn sử dụng theo hồ sơ thiết kế.",
        },
        { type: "done", data: "" },
      ]),
    }),
  );

  await page.goto("/");
  await page.getByRole("textbox").fill("Chung cư có thời hạn sở hữu bao lâu?");
  await page.getByRole("button", { name: "Tìm kiếm" }).click();

  await expect(page.getByText("Cơ sở pháp lý")).toBeVisible();
  await expect(
    page.getByText(/nhà chung cư có thời hạn sử dụng/),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Điều 58/ })).toBeVisible();
});

test("câu ngoài phạm vi → hiện câu từ chối", async ({ page }) => {
  const refusal =
    "Dựa trên dữ liệu pháp luật hiện có, tôi chưa tìm thấy quy định cụ thể cho câu hỏi này.";
  await page.route("**/api/query", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sse([
        { type: "sources", data: [] },
        { type: "token", data: refusal },
        { type: "done", data: "" },
      ]),
    }),
  );

  await page.goto("/");
  await page.getByRole("textbox").fill("Lái xe quá tốc độ bị phạt bao nhiêu?");
  await page.getByRole("button", { name: "Tìm kiếm" }).click();

  await expect(page.getByText(/chưa tìm thấy quy định cụ thể/)).toBeVisible();
});

test("bộ lọc lĩnh vực hiển thị các lĩnh vực (động)", async ({ page }) => {
  await page.goto("/");
  // Scope trong group bộ lọc để tránh trùng tên với nút câu hỏi mẫu.
  const filter = page.getByRole("group", { name: "Lọc theo lĩnh vực" });
  await expect(
    filter.getByRole("button", { name: "Tất cả", exact: true }),
  ).toBeVisible();
  await expect(
    filter.getByRole("button", { name: "Đất đai", exact: true }),
  ).toBeVisible();
  await expect(
    filter.getByRole("button", { name: "Nhà ở", exact: true }),
  ).toBeVisible();
});
