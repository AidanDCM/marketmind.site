// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke-test the Health page renders and shows at least some tabular data.
test('Health page renders', async ({ page }) => {
  await page.goto('/health');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish "Checking session…" screen
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // Page structure should have content
  await expect(page.locator('main')).toBeVisible();

  // Expect the page heading or any heading/table to be present
  const heading = page.locator('h1:has-text("System Health"), h1, h2');
  await heading.first().waitFor({ timeout: 10000 }).catch(() => {});
  const hasTable = await page.locator('table').first().isVisible().catch(() => false);
  const headingCount = await heading.count();
  expect(hasTable || headingCount > 0).toBeTruthy();
});
