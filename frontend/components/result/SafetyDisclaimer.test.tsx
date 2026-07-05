import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SafetyDisclaimer } from "./SafetyDisclaimer";

describe("SafetyDisclaimer", () => {
  it("hiện tuyên bố miễn trừ (không thay thế tư vấn pháp lý)", () => {
    render(<SafetyDisclaimer />);
    expect(
      screen.getByText(/không thay thế tư vấn pháp lý/),
    ).toBeInTheDocument();
  });
});
