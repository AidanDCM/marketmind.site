import { describe, it, expect, beforeEach } from "vitest";
import {
  ACTIVE_ATTENTION_ONLY_KEY,
  readActiveAttentionOnlyPreference,
  writeActiveAttentionOnlyPreference,
  readActiveStatusFilterPreference,
  writeActiveStatusFilterPreference,
} from "./activeExperimentsPreferences";

describe("activeExperimentsPreferences", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults attention filter to false", () => {
    expect(readActiveAttentionOnlyPreference()).toBe(false);
  });

  it("persists attention filter preference", () => {
    writeActiveAttentionOnlyPreference(true);
    expect(localStorage.getItem(ACTIVE_ATTENTION_ONLY_KEY)).toBe("true");
    expect(readActiveAttentionOnlyPreference()).toBe(true);
  });

  it("defaults status filter to active", () => {
    expect(readActiveStatusFilterPreference()).toBe("active");
  });

  it("persists status filter preference", () => {
    writeActiveStatusFilterPreference("ended");
    expect(readActiveStatusFilterPreference()).toBe("ended");
  });
});
