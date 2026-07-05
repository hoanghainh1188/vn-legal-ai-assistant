import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnswerStream } from "./AnswerStream";

describe("AnswerStream", () => {
  it("rỗng & không streaming → không render gì", () => {
    const { container } = render(
      <AnswerStream answer="" isStreaming={false} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("render markdown của câu trả lời", () => {
    render(<AnswerStream answer="**Điều 58** quy định" isStreaming={false} />);
    expect(screen.getByText("Điều 58")).toBeInTheDocument();
  });

  it("đang streaming (answer rỗng) → vẫn render chỉ báo", () => {
    const { container } = render(<AnswerStream answer="" isStreaming={true} />);
    expect(container).not.toBeEmptyDOMElement();
  });

  it("render đầy đủ phần tử markdown (heading, list, link, code, quote)", () => {
    const md = [
      "# Tiêu đề",
      "## Mục",
      "### Mục nhỏ",
      "",
      "- mục một",
      "- mục hai",
      "",
      "1. thứ nhất",
      "",
      "> trích dẫn",
      "",
      "Có `mã` và [liên kết](https://example.com).",
    ].join("\n");
    const { container } = render(
      <AnswerStream answer={md} isStreaming={false} />,
    );
    expect(container.querySelector("h1")?.textContent).toBe("Tiêu đề");
    expect(container.querySelector("ul li")).toBeInTheDocument();
    expect(container.querySelector("ol li")).toBeInTheDocument();
    expect(container.querySelector("blockquote")).toBeInTheDocument();
    expect(container.querySelector("code")?.textContent).toBe("mã");
    expect(container.querySelector("a")?.getAttribute("href")).toBe(
      "https://example.com",
    );
  });
});
