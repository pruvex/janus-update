import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './waechter/tests/e2e',
  use: {
    baseURL: 'http://localhost:5173', // Annahme: Vite Dev Server läuft auf diesem Port
  },
});