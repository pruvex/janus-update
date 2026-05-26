const fs = require('fs');
const path = require('path');

const VALID_UPDATE_STATES = [
  'idle',
  'checking',
  'update_available',
  'downloading',
  'download_paused',
  'download_failed',
  'validating',
  'validation_failed',
  'ready_to_install',
  'installing',
  'install_failed',
  'installed',
];

const DEFAULT_UPDATE_STATE = {
  status: 'idle',
  targetVersion: null,
  currentVersion: null,
  assetPath: null,
  manifestHash: null,
  downloadedHash: null,
  downloadProgress: null,
  errorCode: null,
  errorMessage: null,
  updatedAt: null,
  retryCount: 0,
  isCritical: false,
  releaseNotes: null,
};

function getUpdateStatePath(app) {
  return path.join(app.getPath('userData'), 'janus-update-state.json');
}

function readUpdateState(app) {
  const filePath = getUpdateStatePath(app);
  try {
    const data = fs.readFileSync(filePath, 'utf-8');
    const parsed = JSON.parse(data);
    return { ...DEFAULT_UPDATE_STATE, ...parsed };
  } catch {
    return { ...DEFAULT_UPDATE_STATE };
  }
}

function writeUpdateState(app, state) {
  const filePath = getUpdateStatePath(app);
  state.updatedAt = new Date().toISOString();
  fs.writeFileSync(filePath, JSON.stringify(state, null, 2), 'utf-8');
}

function transitionUpdateState(app, patch) {
  const currentState = readUpdateState(app);
  const newState = Object.assign({}, currentState, patch);
  if (!VALID_UPDATE_STATES.includes(newState.status)) {
    throw new Error('Invalid update state');
  }
  writeUpdateState(app, newState);
  return newState;
}

function resetUpdateState(app) {
  writeUpdateState(app, { ...DEFAULT_UPDATE_STATE });
}

module.exports = {
  VALID_UPDATE_STATES,
  DEFAULT_UPDATE_STATE,
  getUpdateStatePath,
  readUpdateState,
  writeUpdateState,
  transitionUpdateState,
  resetUpdateState,
};
