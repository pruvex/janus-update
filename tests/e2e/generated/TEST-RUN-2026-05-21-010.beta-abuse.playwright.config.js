import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: ['tests/e2e/generated/TEST-RUN-2026-05-21-010.beta-abuse.spec.js'],
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:8001',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    {
      name: 'beta-abuse',
      use: {},
    },
  ],
  webServer: [
    {
      name: 'backend-api',
      command: 'npm run start-backend-only-without-reload',
      url: 'http://127.0.0.1:8001/api/health',
      reuseExistingServer: false,
      timeout: 300000,
      cwd: process.cwd(),
      env: {
        PYTHONIOENCODING: 'UTF-8',
        JANUS_DISABLE_SENTRY: '1',
        JANUS_E2E_FAST_MODE: '1',
        JANUS_ENABLE_DEBUG_ENDPOINTS: '0',
        JANUS_ENABLE_BETA_ABUSE_LIMITS: '1',
        JANUS_BETA_ABUSE_WINDOW_SECONDS: '60',
        JANUS_BETA_USER_BURST_LIMIT: '2',
        JANUS_BETA_GLOBAL_BURST_LIMIT: '2',
        JANUS_MAX_IMAGE_UPLOAD_BYTES: '8',
        JANUS_MAX_DOCUMENT_UPLOAD_BYTES: '8',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
