import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DailyReportLessonsCard } from "./DailyReportLessonsCard";

describe("DailyReportLessonsCard", () => {
  it("renders nothing when there are no lessons", () => {
    const { container } = render(<DailyReportLessonsCard lessons={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("opens the lessons library from the card action", () => {
    const onOpenLessons = vi.fn();
    render(
      <DailyReportLessonsCard
        lessons={["Pause ads when CAC exceeds break-even for 3 days"]}
        onOpenLessons={onOpenLessons}
      />,
    );
    expect(screen.getByText(/Pause ads when CAC/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "View library" }));
    expect(onOpenLessons).toHaveBeenCalledOnce();
  });
});
