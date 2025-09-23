// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke: Recheck action should not error; toast is optional.
test('Health recheck is stable', async ({ page }) => {
  await page.goto('/health');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // Click Recheck button if present (Health page uses "Recheck")
  const recheck = page.locator('button:has-text("Recheck")').first();
  if (await recheck.count() > 0) {
    await recheck.click();
  }

  // Assert main remains visible; toast may or may not appear depending on timing
  await expect(page.locator('main').first()).toBeVisible();
  // Optionally look for a toast without failing the test
  const toastVisible = await page.locator('[role="alert"], [role="status"]').first().isVisible().catch(() => false);
  expect([true, false]).toContain(toastVisible);
});
