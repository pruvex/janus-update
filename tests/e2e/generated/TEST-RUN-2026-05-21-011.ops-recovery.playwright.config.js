import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: ['tests/e2e/generated/TEST-RUN-2026-05-21-011.ops-recovery.spec.js'],
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
      name: 'ops-recovery',
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
        JANUS_DISABLE_CLOUD_PROVIDERS: '1',
        JANUS_DISABLE_EXTERNAL_TOOLS: '1',
        JANUS_DISABLE_WRITE_TOOLS: '1',
        JANUS_DISABLE_MEMORY_RAG: '1',
        JANUS_LOCK_LOCAL_BETA_USER: '1',
        JANUS_TELEMETRY_MODE: 'minimal',
        ANONYMIZED_TELEMETRY: 'False',
        CHROMA_TELEMETRY_ENABLED: 'False',
        DO_NOT_TRACK: '1',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
