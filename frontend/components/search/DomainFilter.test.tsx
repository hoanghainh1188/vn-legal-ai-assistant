import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DomainFilter } from "./DomainFilter";

function mockDomains(domains: string[]) {
  global.fetch = vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ domains }),
  }) as typeof fetch;
}

afterEach(() => vi.restoreAllMocks());

describe("DomainFilter", () => {
  it("trong lúc tải → giữ chỗ skeleton (aria-hidden), chưa có chip (chống CLS)", () => {
    // fetch treo (chưa resolve) → domains=null → trạng thái loading.
    global.fetch = vi
      .fn()
      .mockReturnValue(new Promise(() => {})) as typeof fetch;
    const { container } = render(
      <DomainFilter value={null} onChange={vi.fn()} />,
    );
    expect(container.querySelector('[aria-hidden="true"]')).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("sau khi tải → hiện 'Tất cả' + các lĩnh vực", async () => {
    mockDomains(["Đất đai", "Nhà ở"]);
    render(<DomainFilter value={null} onChange={vi.fn()} />);
    expect(
      await screen.findByRole("button", { name: "Tất cả" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đất đai" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Nhà ở" })).toBeInTheDocument();
  });

  it("không có lĩnh vực → không render gì", async () => {
    mockDomains([]);
    const { container } = render(
      <DomainFilter value={null} onChange={vi.fn()} />,
    );
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("click chip lĩnh vực → onChange đúng giá trị", async () => {
    mockDomains(["Đất đai", "Nhà ở"]);
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DomainFilter value={null} onChange={onChange} />);
    await user.click(await screen.findByRole("button", { name: "Đất đai" }));
    expect(onChange).toHaveBeenCalledWith("Đất đai");
  });

  it("click 'Tất cả' → onChange(null)", async () => {
    mockDomains(["Nhà ở"]);
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DomainFilter value="Nhà ở" onChange={onChange} />);
    await user.click(await screen.findByRole("button", { name: "Tất cả" }));
    expect(onChange).toHaveBeenCalledWith(null);
  });
});
