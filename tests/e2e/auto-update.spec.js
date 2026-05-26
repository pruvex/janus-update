import { test, expect } from '@playwright/test';

test.describe('Auto Update UI E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window._updateStateCallbacks = [];
      window._ipcCalls = [];

      window.electron = {
        getUpdateState: async () => ({ status: 'idle' }),
        installUpdateNow: () => {
          window._ipcCalls.push('installUpdateNow');
        },
        retryUpdate: () => {
          window._ipcCalls.push('retryUpdate');
        },
        dismissNormalUpdate: () => {
          window._ipcCalls.push('dismissNormalUpdate');
        },
        onUpdateStateChanged: (callback) => {
          window._updateStateCallbacks.push(callback);
        },
      };

      window._emitUpdateStateChange = (state) => {
        window._updateStateCallbacks.forEach((callback) => callback(state));
      };
    });

    await page.goto('/');
    await page.waitForFunction(() => window._updateStateCallbacks.length > 0, { timeout: 10000 });
  });

  test('Normal update displays toast with Installieren and Später buttons', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'ready_to_install',
        isCritical: false,
        targetVersion: '1.0.0',
      });
    });

    await expect(page.locator('.update-toast')).toBeVisible();
    await expect(page.locator('#update-install-btn')).toBeVisible();
    await expect(page.locator('#update-install-btn')).toHaveText('Installieren');
    await expect(page.locator('#update-dismiss-btn')).toBeVisible();
    await expect(page.locator('#update-dismiss-btn')).toHaveText('Später');
  });

  test('Critical update displays blocking modal without Später button', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'ready_to_install',
        isCritical: true,
        targetVersion: '1.0.0',
      });
    });

    await expect(page.locator('.update-modal--critical')).toBeVisible();
    await expect(page.locator('#update-critical-install-btn')).toBeVisible();
    await expect(page.locator('#update-critical-install-btn')).toHaveText('Installieren');
    await expect(page.locator('#update-dismiss-btn')).not.toBeAttached();
  });

  test('Download failure displays error banner with Retry button', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'download_failed',
        errorCode: 'NETWORK_ERROR',
        errorMessage: 'Connection timeout',
      });
    });

    await expect(page.locator('.update-error-banner')).toBeVisible();
    await expect(page.locator('.update-error-message')).toContainText('Update fehlgeschlagen');
    await expect(page.locator('#update-retry-btn')).toBeVisible();
    await expect(page.locator('#update-retry-btn')).toHaveText('Retry');
  });

  test('Validation failure displays error banner with Retry button', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'validation_failed',
        errorCode: 'HASH_MISMATCH',
      });
    });

    await expect(page.locator('.update-error-banner')).toBeVisible();
    await expect(page.locator('.update-error-message')).toContainText('Update fehlgeschlagen');
    await expect(page.locator('#update-retry-btn')).toBeVisible();
  });

  test('Install failure displays error banner with Retry button', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'install_failed',
        errorCode: 'INSTALL_ERROR',
      });
    });

    await expect(page.locator('.update-error-banner')).toBeVisible();
    await expect(page.locator('.update-error-message')).toContainText('Update fehlgeschlagen');
    await expect(page.locator('#update-retry-btn')).toBeVisible();
  });

  test('Update UI buttons call allowed IPC bridge methods', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'ready_to_install',
        isCritical: false,
        targetVersion: '1.0.0',
      });
    });

    await page.click('#update-install-btn');
    await page.click('#update-dismiss-btn');

    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'download_failed',
        errorCode: 'NETWORK_ERROR',
      });
    });

    await page.click('#update-retry-btn');

    const ipcCalls = await page.evaluate(() => window._ipcCalls);
    expect(ipcCalls).toContain('installUpdateNow');
    expect(ipcCalls).toContain('dismissNormalUpdate');
    expect(ipcCalls).toContain('retryUpdate');
  });

  test('Idle state hides all update UI elements', async ({ page }) => {
    await page.evaluate(() => {
      window._emitUpdateStateChange({
        status: 'ready_to_install',
        isCritical: false,
        targetVersion: '1.0.0',
      });
    });

    await expect(page.locator('.update-toast')).toBeVisible();

    await page.evaluate(() => {
      window._emitUpdateStateChange({ status: 'idle' });
    });

    await expect(page.locator('.update-toast')).not.toBeVisible();
    await expect(page.locator('.update-modal')).not.toBeVisible();
    await expect(page.locator('.update-error-banner')).not.toBeVisible();
  });
});
