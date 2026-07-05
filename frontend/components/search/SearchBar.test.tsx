import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SearchBar } from "./SearchBar";

describe("SearchBar", () => {
  it("gõ + submit → onSearch với chuỗi đã trim", async () => {
    const onSearch = vi.fn();
    const user = userEvent.setup();
    render(<SearchBar onSearch={onSearch} isLoading={false} />);
    await user.type(screen.getByRole("textbox"), "  câu hỏi  ");
    await user.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    expect(onSearch).toHaveBeenCalledWith("câu hỏi");
  });

  it("rỗng → nút Tìm kiếm disabled", () => {
    render(<SearchBar onSearch={vi.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: "Tìm kiếm" })).toBeDisabled();
  });

  it("đang tải → input bị vô hiệu hoá", () => {
    render(<SearchBar onSearch={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});
