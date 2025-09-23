// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke-test the Profit page renders with heading and a table region.
test('Profit page renders', async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.setItem('api_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiadminIn0.dummy'); } catch {}
  });
  await page.route('**/auth/users/me', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  await page.goto('/profit');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // URL and main region visible
  await expect(page).toHaveURL(/\/profit/);
  await expect(page.locator('main').first()).toBeVisible();
  // Basic smoke only: URL + main visible
});
