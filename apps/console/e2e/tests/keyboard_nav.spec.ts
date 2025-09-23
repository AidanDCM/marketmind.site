// @ts-nocheck
import { test, expect } from '@playwright/test';

// Keyboard-only navigation smoke across a few core pages.
// Ensures at least one focusable element receives focus via Tab.
for (const path of ['/health', '/integrations', '/pricing']) {
  test(`Keyboard nav focusable on ${path}`, async ({ page }) => {
    await page.goto(path);
    await page.waitForLoadState('domcontentloaded');
    // Wait for AuthGate
    await page.locator('text=Checking session').first().waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

    // Start from body and tab through a handful of elements
    await page.locator('body').click();
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab');
    }

    // Expect some focusable element to be focused
    const active = page.locator(':focus');
    await expect(active).toBeVisible();
  });
}
