import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: ['tests/e2e/generated/TEST-RUN-2026-05-21-012.beta-privacy-notice.spec.js'],
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
  projects: [{ name: 'beta-privacy-notice', use: {} }],
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
        JANUS_TELEMETRY_MODE: 'off',
        ANONYMIZED_TELEMETRY: 'False',
        CHROMA_TELEMETRY_ENABLED: 'False',
        DO_NOT_TRACK: '1',
        JANUS_E2E_FAST_MODE: '1',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
