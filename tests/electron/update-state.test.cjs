const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const os = require('os');

const {
  VALID_UPDATE_STATES,
  DEFAULT_UPDATE_STATE,
  getUpdateStatePath,
  readUpdateState,
  writeUpdateState,
  transitionUpdateState,
  resetUpdateState,
} = require('../../electron/update-state.cjs');

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'janus-update-state-test-'));

const mockApp = {
  getPath: () => tempDir,
};

const testFilePath = path.join(tempDir, 'janus-update-state.json');

// Cleanup helper
function cleanup() {
  try {
    fs.unlinkSync(testFilePath);
  } catch {
    // Ignore if file doesn't exist
  }
}

// Run cleanup before tests
cleanup();

test.after(() => {
  cleanup();
  fs.rmSync(tempDir, { recursive: true, force: true });
});

test('returns default state when no file exists', () => {
  cleanup();
  const state = readUpdateState(mockApp);
  assert.deepStrictEqual(state, DEFAULT_UPDATE_STATE);
});

test('writes and reads state identically', () => {
  cleanup();
  const testState = {
    ...DEFAULT_UPDATE_STATE,
    status: 'checking',
    targetVersion: '1.0.0',
    currentVersion: '0.9.0',
    retryCount: 1,
    isCritical: true,
    releaseNotes: 'Test release',
  };
  writeUpdateState(mockApp, testState);
  const readBack = readUpdateState(mockApp);
  assert.strictEqual(readBack.status, 'checking');
  assert.strictEqual(readBack.targetVersion, '1.0.0');
  assert.strictEqual(readBack.currentVersion, '0.9.0');
  assert.strictEqual(readBack.retryCount, 1);
  assert.strictEqual(readBack.isCritical, true);
  assert.strictEqual(readBack.releaseNotes, 'Test release');
  // updatedAt should be set by writeUpdateState
  assert.ok(readBack.updatedAt !== null);
});

test('transitionUpdateState throws on invalid status', () => {
  cleanup();
  assert.throws(
    () => transitionUpdateState(mockApp, { status: 'not_a_real_state' }),
    /Invalid update state/
  );
});

test('transitionUpdateState updates valid status', () => {
  cleanup();
  const newState = transitionUpdateState(mockApp, { status: 'update_available', targetVersion: '2.0.0' });
  assert.strictEqual(newState.status, 'update_available');
  assert.strictEqual(newState.targetVersion, '2.0.0');
  const readBack = readUpdateState(mockApp);
  assert.strictEqual(readBack.status, 'update_available');
});

test('resetUpdateState resets to default', () => {
  cleanup();
  transitionUpdateState(mockApp, { status: 'downloading', targetVersion: '3.0.0' });
  resetUpdateState(mockApp);
  const state = readUpdateState(mockApp);
  assert.strictEqual(state.status, 'idle');
  assert.strictEqual(state.targetVersion, null);
});

test('getUpdateStatePath returns correct path', () => {
  const filePath = getUpdateStatePath(mockApp);
  assert.ok(filePath.includes('janus-update-state.json'));
});

