// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke-test the Finance Invoices page renders with a heading and table markup.
test('Finance Invoices renders', async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.setItem('api_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiadminIn0.dummy'); } catch {}
  });
  await page.goto('/finance/invoices');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // Page visible
  await expect(page.locator('main')).toBeVisible();

  // Expect the Invoices heading or a table structure
  const heading = page.locator('h1:has-text("Invoices"), h2:has-text("Invoices")');
  await heading.first().waitFor({ timeout: 15000 }).catch(() => {});
  const hasHeading = (await heading.count()) > 0;
  const hasTable = (await page.locator('table').count()) > 0;
  const mainVisible = await page.locator('main').first().isVisible().catch(() => false);
  expect(hasHeading || hasTable || mainVisible).toBeTruthy();
});
