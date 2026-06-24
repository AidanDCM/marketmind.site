import { describe, it, expect, beforeEach } from "vitest";
import {
  ACTIVE_ATTENTION_ONLY_KEY,
  readActiveAttentionOnlyPreference,
  writeActiveAttentionOnlyPreference,
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
});
