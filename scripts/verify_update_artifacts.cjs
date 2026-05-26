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

async function main() {
  const pkgPath = path.join(PROJECT_ROOT, 'package.json');
  const latestPath = path.join(RELEASE_DIR, 'latest.yml');
  const manifestPath = path.join(RELEASE_DIR, 'janus-update-manifest.json');

  ensure(fs.existsSync(pkgPath), `Missing package.json: ${pkgPath}`);
  ensure(fs.existsSync(latestPath), `Missing latest.yml: ${latestPath}`);
  ensure(fs.existsSync(manifestPath), `Missing manifest: ${manifestPath}`);

  const pkg = readJson(pkgPath, 'package.json');
  const latest = readYaml(latestPath, 'latest.yml');
  const manifest = readJson(manifestPath, 'janus-update-manifest.json');

  ensure(typeof pkg.version === 'string' && pkg.version.length > 0, 'package.json.version missing');
  ensure(typeof latest.version === 'string' && latest.version.length > 0, 'latest.yml version missing');
  ensure(typeof latest.path === 'string' && latest.path.length > 0, 'latest.yml path missing');
  ensure(typeof latest.sha512 === 'string' && latest.sha512.length > 0, 'latest.yml sha512 missing');
  ensure(typeof manifest.version === 'string' && manifest.version.length > 0, 'manifest version missing');
  ensure(typeof manifest.assetName === 'string' && manifest.assetName.length > 0, 'manifest assetName missing');
  ensure(typeof manifest.sha512 === 'string' && manifest.sha512.length > 0, 'manifest sha512 missing');
  ensure(typeof manifest.critical === 'boolean', 'manifest critical must be boolean');
  ensure(!Number.isNaN(Date.parse(manifest.createdAt)), 'manifest createdAt must be ISO timestamp');

  ensure(pkg.version === latest.version, `Version mismatch: package=${pkg.version}, latest=${latest.version}`);
  ensure(pkg.version === manifest.version, `Version mismatch: package=${pkg.version}, manifest=${manifest.version}`);
  ensure(latest.path === manifest.assetName, `Asset mismatch: latest.path=${latest.path}, manifest.assetName=${manifest.assetName}`);

  const installerPath = path.join(RELEASE_DIR, latest.path);
  ensure(fs.existsSync(installerPath), `Installer missing: ${installerPath}`);

  const sha512Base64 = await calculateHash(installerPath, 'sha512', 'base64');
  const sha256Hex = await calculateHash(installerPath, 'sha256', 'hex');

  ensure(sha512Base64 === latest.sha512, 'SHA512 mismatch: installer vs latest.yml');
  ensure(sha512Base64 === manifest.sha512, 'SHA512 mismatch: installer vs manifest');

  // Optional backwards-compat check if sha256 exists in manifest.
  if (typeof manifest.sha256 === 'string' && manifest.sha256.length > 0) {
    ensure(/^[a-f0-9]{64}$/i.test(manifest.sha256), 'manifest sha256 must be 64 hex chars');
    ensure(sha256Hex.toLowerCase() === manifest.sha256.toLowerCase(), 'SHA256 mismatch: installer vs manifest');
  }

  // Optional latest.yml files list consistency check.
  if (Array.isArray(latest.files) && latest.files.length > 0) {
    const entry = latest.files.find((f) => f && f.url === latest.path);
    ensure(!!entry, 'latest.yml files[] does not contain path entry');
    if (entry.sha512) {
      ensure(entry.sha512 === latest.sha512, 'latest.yml files[].sha512 differs from root sha512');
    }
  }

  console.log('verify:update-artifacts PASS');
  console.log(`version=${pkg.version}`);
  console.log(`asset=${latest.path}`);
  console.log(`sha512=${sha512Base64}`);
  console.log(`sha256=${sha256Hex}`);
}

main().catch((err) => {
  console.error(`verify:update-artifacts FAIL: ${err.message}`);
  process.exit(1);
});
