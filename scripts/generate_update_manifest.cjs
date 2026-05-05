const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');

async function main() {
  // 1. Read version from package.json
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

  // 2. Read latest.yml (Single Source of Truth from electron-builder)
  const latestYmlPath = path.join(RELEASE_DIR, 'latest.yml');
  if (!fs.existsSync(latestYmlPath)) {
    console.error(`🚨 CRITICAL: latest.yml not found at ${latestYmlPath}`);
    console.error(`🚨 Ensure electron-builder has completed successfully before generating the manifest.`);
    process.exit(1);
  }

  console.log(`[Manifest] Reading latest.yml...`);

  let latestYmlContent;
  try {
    latestYmlContent = fs.readFileSync(latestYmlPath, 'utf-8');
  } catch (err) {
    console.error('[Manifest] Failed to read latest.yml:', err.message);
    process.exit(1);
  }

  // 3. Parse YAML and extract SHA512 and filename
  let latestData;
  try {
    latestData = yaml.load(latestYmlContent);
  } catch (err) {
    console.error('[Manifest] Failed to parse latest.yml:', err.message);
    process.exit(1);
  }

  if (!latestData || !latestData.sha512 || !latestData.path) {
    console.error('🚨 CRITICAL: latest.yml is missing required fields (sha512 or path)');
    process.exit(1);
  }

  const sha512 = latestData.sha512;
  const assetName = latestData.path;

  console.log(`[Manifest] Extracted from latest.yml:`);
  console.log(`[Manifest]   Asset: ${assetName}`);
  console.log(`[Manifest]   SHA512: ${sha512}`);

  // 4. Validate that the asset file exists
  const assetPath = path.join(RELEASE_DIR, assetName);
  if (!fs.existsSync(assetPath)) {
    console.error(`🚨 CRITICAL: Asset file not found: ${assetPath}`);
    process.exit(1);
  }

  // 5. Build manifest object (ATOMIC: direct derivation from latest.yml)
  const manifest = {
    version,
    assetName,
    sha512,
    critical: false,
    createdAt: new Date().toISOString(),
  };

  // 6. Write manifest JSON
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
