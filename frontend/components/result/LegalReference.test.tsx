import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { SourceDocument } from "@/lib/types";
import { LegalReference } from "./LegalReference";

function source(over: Partial<SourceDocument> = {}): SourceDocument {
  return {
    document_id: "27/2023/QH15",
    article_number: 58,
    article_title: "Thời hạn sử dụng nhà chung cư",
    content: "Nội dung điều 58.",
    relevance_score: 0.9,
    document_name: "Luật Nhà ở 2023",
    eff_status: "Hết hiệu lực một phần",
    eff_date: "2024-08-01",
    domain: "Nhà ở",
    ...over,
  };
}

describe("LegalReference", () => {
  it("rỗng → không render gì", () => {
    const { container } = render(<LegalReference sources={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("dùng document_name làm nhãn (không suy từ số hiệu)", () => {
    render(<LegalReference sources={[source()]} />);
    expect(screen.getByText(/Luật Nhà ở 2023/)).toBeInTheDocument();
  });

  it.each([
    ["05/2024/TT-BXD", "Thông tư 05/2024/TT-BXD"],
    ["27/2023/QH15", "Luật 27/2023/QH15"],
    ["95/2024/NĐ-CP", "Nghị định 95/2024/NĐ-CP"],
  ])("fallback nhãn theo loại khi thiếu document_name: %s", (id, label) => {
    render(
      <LegalReference
        sources={[source({ document_id: id, document_name: null })]}
      />,
    );
    expect(
      screen.getByText(new RegExp(label.replace(/\//g, "\\/"))),
    ).toBeInTheDocument();
  });

  it("có văn bản hết hiệu lực → hiện cảnh báo gộp (role=status) + badge", () => {
    render(<LegalReference sources={[source()]} />);
    const warning = screen.getByRole("status");
    expect(warning.textContent).toMatch(/hết hiệu lực/i);
    expect(screen.getByText("Hết hiệu lực một phần")).toBeInTheDocument();
  });

  it("còn hiệu lực → KHÔNG cảnh báo", () => {
    render(
      <LegalReference sources={[source({ eff_status: "Còn hiệu lực" })]} />,
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("bung điều → hiện lĩnh vực + ngày hiệu lực dạng VN", async () => {
    const user = userEvent.setup();
    render(<LegalReference sources={[source()]} />);
    await user.click(screen.getByRole("button", { name: /Điều 58/ }));
    expect(screen.getByText(/Lĩnh vực: Nhà ở/)).toBeInTheDocument();
    expect(screen.getByText(/Hiệu lực từ 01\/08\/2024/)).toBeInTheDocument();
  });
});
