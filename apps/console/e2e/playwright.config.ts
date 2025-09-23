// @ts-nocheck
import { defineConfig } from '@playwright/test';

// Base URL for Console. Override via CONSOLE_BASE_URL env when running in CI or staging.
const baseURL = process.env.CONSOLE_BASE_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: 'tests',
  timeout: 30_000,
  use: {
    baseURL,
    headless: true,
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  reporter: [['list']],
  webServer: {
    command: 'npm run dev',
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120_000,
    cwd: '../',
    env: {
      NEXT_PUBLIC_AUTH_DISABLED: 'true',
      NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8001',
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'
    }
  }
});
