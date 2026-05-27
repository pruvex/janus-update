const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const yaml = require('js-yaml');

const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');

function readJson(filePath, label) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (err) {
    throw new Error(`${label} read/parse failed: ${err.message}`);
  }
}

function readYaml(filePath, label) {
  try {
    return yaml.load(fs.readFileSync(filePath, 'utf-8'));
  } catch (err) {
    throw new Error(`${label} read/parse failed: ${err.message}`);
  }
}

function ensure(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function calculateHash(filePath, algorithm, encoding) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash(algorithm);
    const stream = fs.createReadStream(filePath);
    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('end', () => resolve(hash.digest(encoding)));
    stream.on('error', reject);
  });
}

function resolveChannelFile(version) {
  const isAlpha = /-alpha(\.|$)/i.test(version);
  const isBeta = /-beta(\.|$)/i.test(version);
  if (isAlpha && fs.existsSync(path.join(RELEASE_DIR, 'alpha.yml'))) {
    return 'alpha.yml';
  }
  if (isBeta && fs.existsSync(path.join(RELEASE_DIR, 'beta.yml'))) {
    return 'beta.yml';
  }
  return 'latest.yml';
}

async function main() {
  const pkgPath = path.join(PROJECT_ROOT, 'package.json');
  const manifestPath = path.join(RELEASE_DIR, 'janus-update-manifest.json');

  ensure(fs.existsSync(pkgPath), `Missing package.json: ${pkgPath}`);
  ensure(fs.existsSync(manifestPath), `Missing manifest: ${manifestPath}`);

  const pkg = readJson(pkgPath, 'package.json');
  const channelFile = resolveChannelFile(pkg.version);
  const channelPath = path.join(RELEASE_DIR, channelFile);
  ensure(fs.existsSync(channelPath), `Missing ${channelFile}: ${channelPath}`);

  const channelData = readYaml(channelPath, channelFile);
  const manifest = readJson(manifestPath, 'janus-update-manifest.json');

  ensure(typeof pkg.version === 'string' && pkg.version.length > 0, 'package.json.version missing');
  ensure(typeof channelData.version === 'string' && channelData.version.length > 0, `${channelFile} version missing`);
  ensure(typeof channelData.path === 'string' && channelData.path.length > 0, `${channelFile} path missing`);
  ensure(typeof channelData.sha512 === 'string' && channelData.sha512.length > 0, `${channelFile} sha512 missing`);
  ensure(typeof manifest.version === 'string' && manifest.version.length > 0, 'manifest version missing');
  ensure(typeof manifest.assetName === 'string' && manifest.assetName.length > 0, 'manifest assetName missing');
  ensure(typeof manifest.sha512 === 'string' && manifest.sha512.length > 0, 'manifest sha512 missing');
  ensure(typeof manifest.critical === 'boolean', 'manifest critical must be boolean');
  ensure(!Number.isNaN(Date.parse(manifest.createdAt)), 'manifest createdAt must be ISO timestamp');

  ensure(pkg.version === channelData.version, `Version mismatch: package=${pkg.version}, ${channelFile}=${channelData.version}`);
  ensure(pkg.version === manifest.version, `Version mismatch: package=${pkg.version}, manifest=${manifest.version}`);
  ensure(channelData.path === manifest.assetName, `Asset mismatch: ${channelFile}.path=${channelData.path}, manifest.assetName=${manifest.assetName}`);

  const installerPath = path.join(RELEASE_DIR, channelData.path);
  ensure(fs.existsSync(installerPath), `Installer missing: ${installerPath}`);

  const sha512Base64 = await calculateHash(installerPath, 'sha512', 'base64');
  const sha256Hex = await calculateHash(installerPath, 'sha256', 'hex');

  ensure(sha512Base64 === channelData.sha512, `SHA512 mismatch: installer vs ${channelFile}`);
  ensure(sha512Base64 === manifest.sha512, 'SHA512 mismatch: installer vs manifest');

  if (typeof manifest.sha256 === 'string' && manifest.sha256.length > 0) {
    ensure(/^[a-f0-9]{64}$/i.test(manifest.sha256), 'manifest sha256 must be 64 hex chars');
    ensure(sha256Hex.toLowerCase() === manifest.sha256.toLowerCase(), 'SHA256 mismatch: installer vs manifest');
  }

  if (Array.isArray(channelData.files) && channelData.files.length > 0) {
    const entry = channelData.files.find((f) => f && f.url === channelData.path);
    ensure(!!entry, `${channelFile} files[] does not contain path entry`);
    if (entry.sha512) {
      ensure(entry.sha512 === channelData.sha512, `${channelFile} files[].sha512 differs from root sha512`);
    }
  }

  console.log('verify:update-artifacts PASS');
  console.log(`version=${pkg.version}`);
  console.log(`channel_file=${channelFile}`);
  console.log(`asset=${channelData.path}`);
  console.log(`sha512=${sha512Base64}`);
  console.log(`sha256=${sha256Hex}`);
}

main().catch((err) => {
  console.error(`verify:update-artifacts FAIL: ${err.message}`);
  process.exit(1);
});
