import { describe, it, expect, beforeEach } from "vitest";
import {
  APPROVAL_FILTER_KEY,
  readApprovalFilterPreference,
  writeApprovalFilterPreference,
} from "./approvalQueuePreferences";

describe("approvalQueuePreferences", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults filter to pending", () => {
    expect(readApprovalFilterPreference()).toBe("pending");
  });

  it("persists selected filter", () => {
    writeApprovalFilterPreference("approved");
    expect(localStorage.getItem(APPROVAL_FILTER_KEY)).toBe("approved");
    expect(readApprovalFilterPreference()).toBe("approved");
  });

  it("ignores invalid stored filter", () => {
    localStorage.setItem(APPROVAL_FILTER_KEY, "not-a-filter");
    expect(readApprovalFilterPreference()).toBe("pending");
  });
});
