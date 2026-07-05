import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SuggestedQuestions } from "./SuggestedQuestions";

describe("SuggestedQuestions", () => {
  it("hiện câu hỏi mẫu; click → onSelect đúng câu", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<SuggestedQuestions onSelect={onSelect} />);
    const btn = screen.getByRole("button", { name: /Chung cư có thời hạn/ });
    await user.click(btn);
    expect(onSelect).toHaveBeenCalledWith(
      "Chung cư có thời hạn sở hữu tối đa bao nhiêu năm?",
    );
  });
});
