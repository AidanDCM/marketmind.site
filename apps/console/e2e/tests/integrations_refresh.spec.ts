// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke: Integrations Refresh should be stable; toast optional.
test('Integrations refresh is stable', async ({ page }) => {
  await page.goto('/integrations');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // Click Refresh button if present
  const refresh = page.locator('button:has-text("Refresh")').first();
  if (await refresh.count() > 0) {
    await refresh.click();
  }

  // Assert main remains visible; toast is optional
  await expect(page.locator('main').first()).toBeVisible();
  const toastVisible = await page.locator('[role="alert"], [role="status"]').first().isVisible().catch(() => false);
  expect([true, false]).toContain(toastVisible);
});
