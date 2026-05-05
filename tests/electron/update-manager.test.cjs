const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');
const os = require('os');

const { initJanusUpdateManager } = require('../../electron/update-manager.cjs');

// Mock Electron app
function createMockApp(tempDir) {
  return { getPath: (name) => tempDir };
}

// Mock autoUpdater extending EventEmitter
class MockAutoUpdater extends EventEmitter {
  constructor() {
    super();
    this.autoDownload = false;
    this.autoInstallOnAppQuit = false;
  }
  checkForUpdates() { return Promise.resolve(); }
  downloadUpdate() { return Promise.resolve(); }
  quitAndInstall() {}
}

// Mock mainWindow with send collector
function createMockMainWindow() {
  const sentEvents = [];
  return {
    isDestroyed: () => false,
    webContents: {
      send: (channel, data) => {
        sentEvents.push({ channel, data });
      }
    },
    _sentEvents: sentEvents
  };
}

// Mock logger
const mockLog = {
  info: () => {},
  error: () => {},
  warn: () => {}
};

describe('Update Manager Integration Tests', () => {
  let tempDir;
  let mockApp;
  let mockAutoUpdater;
  let mockWindow;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'janus-update-test-'));
    mockApp = createMockApp(tempDir);
    mockAutoUpdater = new MockAutoUpdater();
    mockWindow = createMockMainWindow();
  });

  afterEach(() => {
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch {
      // ignore cleanup errors
    }
  });

  function readStateFile() {
    const statePath = path.join(tempDir, 'janus-update-state.json');
    try {
      return JSON.parse(fs.readFileSync(statePath, 'utf-8'));
    } catch {
      return null;
    }
  }

  function getLastSentState() {
    const stateEvents = mockWindow._sentEvents.filter(e => e.channel === 'update-state-changed');
    return stateEvents.length > 0 ? stateEvents[stateEvents.length - 1].data : null;
  }

  test('checking-for-update transitions to checking state', () => {
    initJanusUpdateManager({
      app: mockApp,
      autoUpdater: mockAutoUpdater,
      mainWindow: mockWindow,
      log: mockLog
    });

    mockAutoUpdater.emit('checking-for-update');

    const state = readStateFile();
    assert.strictEqual(state.status, 'checking');

    const sentState = getLastSentState();
    assert.ok(sentState);
    assert.strictEqual(sentState.status, 'checking');
  });

  test('update-available transitions to update_available with version', () => {
    initJanusUpdateManager({
      app: mockApp,
      autoUpdater: mockAutoUpdater,
      mainWindow: mockWindow,
      log: mockLog
    });

    mockAutoUpdater.emit('update-available', {
      version: '1.0.0',
      releaseNotes: 'Test notes'
    });

    const state = readStateFile();
    assert.strictEqual(state.status, 'update_available');
    assert.strictEqual(state.targetVersion, '1.0.0');
    assert.strictEqual(state.releaseNotes, 'Test notes');
  });

  test('update-downloaded with valid sha512 transitions to ready_to_install', async () => {
    // Create a fake downloaded file with known hash
    const fakeFile = path.join(tempDir, 'fake-installer.exe');
    fs.writeFileSync(fakeFile, 'fake-installer-content');

    const crypto = require('crypto');
    const realHash = crypto.createHash('sha512').update('fake-installer-content').digest('base64');

    initJanusUpdateManager({
      app: mockApp,
      autoUpdater: mockAutoUpdater,
      mainWindow: mockWindow,
      log: mockLog
    });

    mockAutoUpdater.emit('update-downloaded', {
      downloadedFile: fakeFile,
      sha512: realHash
    });

    // Wait for async validation
    await new Promise(r => setTimeout(r, 100));

    const state = readStateFile();
    assert.strictEqual(state.status, 'ready_to_install');
    assert.strictEqual(state.assetPath, fakeFile);
    assert.ok(state.downloadedHash);
  });

  test('update-downloaded with invalid hash transitions to validation_failed', async () => {
    const fakeFile = path.join(tempDir, 'fake-installer.exe');
    fs.writeFileSync(fakeFile, 'fake-installer-content');

    initJanusUpdateManager({
      app: mockApp,
      autoUpdater: mockAutoUpdater,
      mainWindow: mockWindow,
      log: mockLog
    });

    mockAutoUpdater.emit('update-downloaded', {
      downloadedFile: fakeFile,
      sha256: '0000000000000000000000000000000000000000000000000000000000000000'
    });

    // Wait for async validation
    await new Promise(r => setTimeout(r, 100));

    const state = readStateFile();
    assert.strictEqual(state.status, 'validation_failed');
    assert.strictEqual(state.errorCode, 'HASH_MISMATCH');
  });

  test('download error retries max 3 times then fails', async () => {
    const { writeUpdateState } = require('../../electron/update-state.cjs');

    // Set initial state to downloading
    writeUpdateState(mockApp, {
      status: 'downloading',
      retryCount: 0
    });

    initJanusUpdateManager({
      app: mockApp,
      autoUpdater: mockAutoUpdater,
      mainWindow: mockWindow,
      log: mockLog
    });

    // Emit error 3 times
    mockAutoUpdater.emit('error', new Error('Network timeout'));
    mockAutoUpdater.emit('error', new Error('Network timeout'));
    mockAutoUpdater.emit('error', new Error('Network timeout'));

    const state = readStateFile();
    assert.strictEqual(state.status, 'download_failed');
  });
});
