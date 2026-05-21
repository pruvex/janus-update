import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: ['tests/e2e/generated/TEST-RUN-2026-05-21-006.multi-account-isolation.spec.js'],
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
      name: 'packaged-local-profile-isolation',
      use: {},
    },
  ],
  webServer: [
    {
      name: 'backend-api',
      command: 'npm run start-backend-only-without-reload',
      url: 'http://127.0.0.1:8001/api/health',
      reuseExistingServer: true,
      timeout: 300000,
      cwd: process.cwd(),
      env: {
        PYTHONIOENCODING: 'UTF-8',
        JANUS_E2E_FAST_MODE: '1',
        JANUS_ENABLE_DEBUG_ENDPOINTS: '0',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
