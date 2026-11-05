import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.js',
  timeout: 30000,
  reporter: 'list',
  outputDir: '../../test-results/playwright',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 820 },
    screenshot: 'only-on-failure'
  }
});
