const fs = require('fs');
const { transitionUpdateState, readUpdateState } = require('./update-state.cjs');
const { validateDownloadedAsset } = require('./update-security.cjs');

function initJanusUpdateManager({ app, autoUpdater, mainWindow, log }) {
  log.info('[JanusUpdateManager] Initializing...');

  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = false;
  // Reliability first: avoid brittle differential update path handling on Windows.
  autoUpdater.disableDifferentialDownload = true;

  const broadcast = (state) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('update-state-changed', state);
    }
  };

  autoUpdater.on('checking-for-update', () => {
    log.info('[JanusUpdateManager] Checking for update...');
    try {
      const state = transitionUpdateState(app, {
        status: 'checking',
        errorCode: null,
        errorMessage: null,
      });
      broadcast(state);
    } catch (err) {
      log.error('[JanusUpdateManager] Failed to transition to checking:', err);
    }
  });

  autoUpdater.on('update-available', (info) => {
    log.info(`[JanusUpdateManager] Update available: ${info.version}`);
    try {
      const state = transitionUpdateState(app, {
        status: 'update_available',
        targetVersion: info.version,
        releaseNotes: info.releaseNotes || null,
        isCritical: info.critical === true,
      });
      broadcast(state);
    } catch (err) {
      log.error('[JanusUpdateManager] Failed to transition to update_available:', err);
    }
  });

  autoUpdater.on('download-progress', (progressObj) => {
    try {
      const state = transitionUpdateState(app, {
        status: 'downloading',
      });
      broadcast(state);
    } catch (err) {
      log.error('[JanusUpdateManager] Failed to transition to downloading:', err);
    }
  });

  autoUpdater.on('update-downloaded', async (info) => {
    log.info('[JanusUpdateManager] Update downloaded, validating...');
    try {
      const state = transitionUpdateState(app, {
        status: 'validating',
      });
      broadcast(state);

      const expectedHash = info.sha512 || info.files?.[0]?.sha512 || info.sha256 || '';
      const result = await validateDownloadedAsset({
        assetPath: info.downloadedFile,
        expectedHash,
      });

      if (result.valid) {
        log.info('[JanusUpdateManager] Validation successful');
        const readyState = transitionUpdateState(app, {
          status: 'ready_to_install',
          assetPath: info.downloadedFile,
          downloadedHash: result.actualSha256,
        });
        broadcast(readyState);
      } else {
        log.error(`[JanusUpdateManager] Validation failed: ${result.errorCode}`);
        await fs.promises.unlink(info.downloadedFile).catch(() => {});
        const failedState = transitionUpdateState(app, {
          status: 'validation_failed',
          errorCode: result.errorCode,
          errorMessage: `SHA256 validation failed: ${result.errorCode}`,
        });
        broadcast(failedState);
      }
    } catch (err) {
      log.error('[JanusUpdateManager] Error during validation:', err);
    }
  });

  autoUpdater.on('error', (err) => {
    log.error('[JanusUpdateManager] Error:', err);
    try {
      const currentState = readUpdateState(app);
      let newState;

      if (currentState.status === 'downloading') {
        const newRetryCount = (currentState.retryCount || 0) + 1;
        if (newRetryCount < 3) {
          newState = transitionUpdateState(app, {
            retryCount: newRetryCount,
          });
          log.info(`[JanusUpdateManager] Retrying download (${newRetryCount}/3)`);
          autoUpdater.downloadUpdate();
          broadcast(newState);
          return;
        } else {
          newState = transitionUpdateState(app, {
            status: 'download_failed',
            errorMessage: err.message,
          });
        }
      } else if (currentState.status === 'installing' || currentState.status === 'ready_to_install') {
        newState = transitionUpdateState(app, {
          status: 'install_failed',
          errorMessage: err.message,
        });
      } else {
        newState = transitionUpdateState(app, {
          status: 'idle',
          errorCode: 'CHECK_ERROR',
          errorMessage: err.message,
        });
      }

      broadcast(newState);
    } catch (err) {
      log.error('[JanusUpdateManager] Failed to handle error:', err);
    }
  });

  log.info('[JanusUpdateManager] Starting update check...');
  autoUpdater.checkForUpdates().catch((err) => {
    log.error('[JanusUpdateManager] Check failed:', err);
  });
}

module.exports = {
  initJanusUpdateManager,
};
