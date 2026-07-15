const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.join(__dirname, '..', '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8'));
const packageLock = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package-lock.json'), 'utf8'));

process.env.JANUS_CODEX_RUNTIME_HELPERS_ONLY = '1';
const {
  CODEX_RUNTIME_VENDOR_RELATIVE,
  CODEX_PACKAGED_RESOURCE_DIR,
  getJanusCodexHomePath,
  getDevelopmentCodexRuntimePath,
  getPackagedCodexRuntimePath,
  getCodexRuntimeExecutablePath,
  buildCodexBackendEnvironment,
} = require('../../main.electron.cjs');
delete process.env.JANUS_CODEX_RUNTIME_HELPERS_ONLY;

const { resolveCodexBackendEnvironment } = require('../../scripts/run-backend-dev.cjs');
const fakeResourcesPath = path.join(projectRoot, 'release', 'win-unpacked', 'resources');

test('development runtime path targets the pinned Windows x64 executable', () => {
  const runtimePath = getDevelopmentCodexRuntimePath(projectRoot);
  assert.strictEqual(
    runtimePath,
    path.join(
      projectRoot,
      'node_modules',
      '@openai',
      'codex-win32-x64',
      'vendor',
      'x86_64-pc-windows-msvc',
      'bin',
      'codex.exe'
    )
  );
  assert.ok(path.isAbsolute(runtimePath));
  assert.ok(fs.existsSync(runtimePath));
});

test('packaged runtime path uses only the explicit Electron resource location', () => {
  const runtimePath = getPackagedCodexRuntimePath(fakeResourcesPath);
  assert.strictEqual(
    runtimePath,
    path.join(fakeResourcesPath, CODEX_PACKAGED_RESOURCE_DIR, CODEX_RUNTIME_VENDOR_RELATIVE)
  );
  assert.notStrictEqual(runtimePath, 'codex');
});

test('development and packaged resolution never use a PATH lookup sentinel', () => {
  const devPath = getCodexRuntimeExecutablePath({ isDev: true, projectRoot });
  const prodPath = getCodexRuntimeExecutablePath({
    isDev: false,
    projectRoot,
    resourcesPath: fakeResourcesPath,
  });
  assert.notStrictEqual(devPath, 'codex');
  assert.notStrictEqual(prodPath, 'codex');
  assert.ok(path.isAbsolute(devPath));
  assert.ok(path.isAbsolute(prodPath));
});

test('backend environment forwards isolated userData home and keyring-only policy', () => {
  const userDataPath = path.join(projectRoot, 'tmp-test-userdata', 'Janus Projekt');
  const env = buildCodexBackendEnvironment({
    isDev: false,
    projectRoot,
    userDataPath,
    resourcesPath: fakeResourcesPath,
  });
  assert.deepStrictEqual(env, {
    JANUS_CODEX_RUNTIME_PATH: getPackagedCodexRuntimePath(fakeResourcesPath),
    JANUS_CODEX_HOME: path.join(userDataPath, 'codex-home'),
    JANUS_CODEX_CREDENTIALS_STORE: 'keyring',
  });
  assert.ok(!Object.keys(env).some((key) => key.includes('EVIDENCE')));
});

test('APPDATA and dev runner resolve the same Janus-only home namespace', () => {
  const appDataRoot = path.join(projectRoot, 'tmp-test-appdata');
  const expectedHome = getJanusCodexHomePath(appDataRoot);
  const electronEnv = buildCodexBackendEnvironment({
    isDev: true,
    projectRoot,
    appDataRoot,
  });
  const previousAppData = process.env.APPDATA;
  process.env.APPDATA = appDataRoot;
  try {
    const devEnv = resolveCodexBackendEnvironment(projectRoot);
    assert.strictEqual(devEnv.JANUS_CODEX_HOME, expectedHome);
    assert.strictEqual(devEnv.JANUS_CODEX_RUNTIME_PATH, getDevelopmentCodexRuntimePath(projectRoot));
    assert.strictEqual(devEnv.JANUS_CODEX_CREDENTIALS_STORE, 'keyring');
    assert.ok(!Object.keys(devEnv).some((key) => key.includes('EVIDENCE')));
  } finally {
    if (previousAppData === undefined) delete process.env.APPDATA;
    else process.env.APPDATA = previousAppData;
  }
  assert.strictEqual(electronEnv.JANUS_CODEX_HOME, expectedHome);
});

test('reload-mode runner preserves the Windows default event loop for Codex subprocesses', () => {
  const runnerPath = path.join(projectRoot, 'scripts', 'run-backend-dev.cjs');
  const runnerSource = fs.readFileSync(runnerPath, 'utf8');
  assert.match(
    runnerSource,
    /uvicornArgs\.push\("--loop", "none", "--reload", "--reload-dir", "backend"\)/
  );
});

test('package pins official Codex and ships runtime plus Apache license', () => {
  assert.strictEqual(packageJson.optionalDependencies['@openai/codex'], '0.144.4');
  const rootLock = packageLock.packages[''];
  assert.strictEqual(rootLock.optionalDependencies['@openai/codex'], '0.144.4');
  assert.strictEqual(packageLock.packages['node_modules/@openai/codex'].version, '0.144.4');
  assert.strictEqual(
    packageLock.packages['node_modules/@openai/codex-win32-x64'].version,
    '0.144.4-win32-x64'
  );

  const extraResources = packageJson.build.extraResources;
  const runtimeEntry = extraResources.find((entry) =>
    entry.to.endsWith('codex-runtime/vendor/x86_64-pc-windows-msvc/bin/codex.exe')
  );
  const licenseEntry = extraResources.find((entry) => entry.to === 'codex-runtime/LICENSE.txt');
  assert.ok(runtimeEntry);
  assert.ok(runtimeEntry.from.includes('@openai/codex-win32-x64'));
  assert.ok(licenseEntry);
  assert.strictEqual(licenseEntry.from, 'licenses/openai-codex/LICENSE.txt');
});

test('Python lifecycle uses only official App Server device-code auth and keyring persistence', () => {
  const lifecyclePath = path.join(projectRoot, 'backend', 'llm_providers', 'codex_app_server.py');
  const source = fs.readFileSync(lifecyclePath, 'utf8');

  assert.match(source, /MANAGED_LOGIN_TYPE = "chatgptDeviceCode"/);
  assert.match(source, /OFFICIAL_DEVICE_VERIFICATION_URL = "https:\/\/auth\.openai\.com\/codex\/device"/);
  assert.match(source, /cli_auth_credentials_store="keyring"/);
  assert.doesNotMatch(source, /chatgptAuthTokens/);
  assert.doesNotMatch(source, /\/oauth\/token/);
  assert.doesNotMatch(source, /\/deviceauth\//);
});

test('local redistribution license is the Apache License 2.0 text', () => {
  const licensePath = path.join(projectRoot, 'licenses', 'openai-codex', 'LICENSE.txt');
  const text = fs.readFileSync(licensePath, 'utf8');
  assert.ok(text.trimStart().startsWith('Apache License'));
  assert.ok(text.includes('Version 2.0, January 2004'));
  assert.ok(text.includes('END OF TERMS AND CONDITIONS'));
});
