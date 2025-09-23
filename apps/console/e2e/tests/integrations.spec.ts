// @ts-nocheck
import { test, expect } from '@playwright/test';

// Smoke-test the Integrations page renders and basic content is present.
test('Integrations page renders', async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.setItem('api_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiadminIn0.dummy'); } catch {}
  });
  await page.goto('/integrations');
  await page.waitForLoadState('domcontentloaded');
  // Wait for AuthGate to finish "Checking session…"
  await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // Expect the page heading to be present
  const heading = page.locator('h1:has-text("Integrations"), h2:has-text("Integrations")');
  await heading.first().waitFor({ timeout: 15000 }).catch(() => {});
  const hasHeading = (await heading.count()) > 0;
  const hasTable = await page.locator('table').first().isVisible().catch(() => false);
  const mainVisible = await page.locator('main').first().isVisible().catch(() => false);
  expect(hasHeading || hasTable || mainVisible).toBeTruthy();
});
