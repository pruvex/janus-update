// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// import dotenv from 'dotenv';
// import path from 'path';
// dotenv.config({ path: path.resolve(__dirname, '.env') });

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: '.',
  testMatch: [
    'tests/e2e/**/*.spec.js',
    'tests/functional/**/*.spec.js',
    'frontend/tests/e2e/**/*.spec.ts',
  ],
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. HTML must never open/serve, otherwise automation waits at localhost:9323. */
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],

  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5173', // Dein Vite-Frontend-Server

    /* Collect trace when test fails */
    trace: 'retain-on-failure',

    /* Take a screenshot only when a test fails */
    screenshot: 'only-on-failure',

    /* Record a video only when a test fails */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'janus-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Self-contained environment: Runner owns full lifecycle */
  webServer: [
    {
      name: 'backend-api',
      command: 'npm run start-backend-only-without-reload',
      url: 'http://localhost:8001/api/health',
      reuseExistingServer: true,
      timeout: 300000,
      cwd: process.cwd(),
      env: { PYTHONIOENCODING: 'UTF-8', NODE_ENV: 'development', JANUS_E2E_FAST_MODE: '1' },
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      name: 'frontend-vite',
      command: 'npm run start-vite',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 300000,
      cwd: process.cwd(),
      env: { NODE_ENV: 'development' },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
