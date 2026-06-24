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

  it("opens approval queue from pending approval lesson", () => {
    const onOpenApprovals = vi.fn();
    render(
      <DailyReportLessonsCard
        lessons={["2 approval(s) pending — unblocking these may unlock next steps."]}
        onOpenApprovals={onOpenApprovals}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));
    expect(onOpenApprovals).toHaveBeenCalledOnce();
  });

  it("opens live data from no-orders lesson", () => {
    const onOpenLiveData = vi.fn();
    render(
      <DailyReportLessonsCard
        lessons={["No orders: verify that the payment link / checkout is live and working."]}
        onOpenLiveData={onOpenLiveData}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Check Live Data" }));
    expect(onOpenLiveData).toHaveBeenCalledOnce();
  });

  it("opens lessons library from past lesson line", () => {
    const onOpenLessons = vi.fn();
    render(
      <DailyReportLessonsCard
        lessons={["Past lesson: Pause ads when CAC spikes."]}
        onOpenLessons={onOpenLessons}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View library" }));
    expect(onOpenLessons).toHaveBeenCalledOnce();
  });
});
