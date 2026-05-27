const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');

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
  const packageJsonPath = path.join(PROJECT_ROOT, 'package.json');

  let version;
  try {
    const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    version = packageData.version;
  } catch (err) {
    console.error('[Manifest] Failed to read package.json:', err.message);
    process.exit(1);
  }

  if (!version) {
    console.error('[Manifest] No version found in package.json');
    process.exit(1);
  }

  const channelFile = resolveChannelFile(version);
  const channelYmlPath = path.join(RELEASE_DIR, channelFile);
  if (!fs.existsSync(channelYmlPath)) {
    console.error(`[Manifest] CRITICAL: ${channelFile} not found at ${channelYmlPath}`);
    process.exit(1);
  }

  console.log(`[Manifest] Reading ${channelFile}...`);

  let channelYmlContent;
  try {
    channelYmlContent = fs.readFileSync(channelYmlPath, 'utf-8');
  } catch (err) {
    console.error(`[Manifest] Failed to read ${channelFile}:`, err.message);
    process.exit(1);
  }

  let channelData;
  try {
    channelData = yaml.load(channelYmlContent);
  } catch (err) {
    console.error(`[Manifest] Failed to parse ${channelFile}:`, err.message);
    process.exit(1);
  }

  if (!channelData || !channelData.sha512 || !channelData.path) {
    console.error(`[Manifest] CRITICAL: ${channelFile} missing required fields (sha512 or path)`);
    process.exit(1);
  }

  const sha512 = channelData.sha512;
  const assetName = channelData.path;

  console.log(`[Manifest] Extracted from ${channelFile}:`);
  console.log(`[Manifest]   Asset: ${assetName}`);
  console.log(`[Manifest]   SHA512: ${sha512}`);

  const assetPath = path.join(RELEASE_DIR, assetName);
  if (!fs.existsSync(assetPath)) {
    console.error(`[Manifest] CRITICAL: Asset file not found: ${assetPath}`);
    process.exit(1);
  }

  const manifest = {
    version,
    assetName,
    sha512,
    critical: false,
    createdAt: new Date().toISOString(),
  };

  const manifestPath = path.join(RELEASE_DIR, 'janus-update-manifest.json');
  try {
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
    console.log(`[Manifest] Generated: ${manifestPath}`);
    console.log(`[Manifest] Version: ${manifest.version}`);
    console.log(`[Manifest] SHA512: ${manifest.sha512}`);
    console.log(`[Manifest] Critical: ${manifest.critical}`);
  } catch (err) {
    console.error('[Manifest] Failed to write manifest:', err.message);
    process.exit(1);
  }
}

main();
