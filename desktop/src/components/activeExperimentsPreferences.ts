export const ACTIVE_ATTENTION_ONLY_KEY = "marketmind_active_attention_only";

export function readActiveAttentionOnlyPreference(): boolean {
  try {
    return localStorage.getItem(ACTIVE_ATTENTION_ONLY_KEY) === "true";
  } catch {
    return false;
  }
}

export function writeActiveAttentionOnlyPreference(value: boolean): void {
  try {
    localStorage.setItem(ACTIVE_ATTENTION_ONLY_KEY, value ? "true" : "false");
  } catch {
    // ignore storage errors in non-browser contexts
  }
}
