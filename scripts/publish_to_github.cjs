const fs = require('fs');
const path = require('path');
const { Octokit } = require('octokit');

// Configuration
const REPO_OWNER = 'pruvex';
const REPO_NAME = 'janus-update';
const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');

// Read version from package.json
function getVersion() {
  const packageJsonPath = path.join(PROJECT_ROOT, 'package.json');
  const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  return packageData.version;
}

// Read GH_TOKEN from environment
function getAuthToken() {
  const token = process.env.GH_TOKEN;
  if (!token) {
    console.error('🚨 CRITICAL: GH_TOKEN environment variable is not set');
    process.exit(1);
  }
  return token;
}

// Check if file exists (optional)
function checkFileExists(filePath, required = true) {
  if (!fs.existsSync(filePath)) {
    if (required) {
      console.error(`🚨 CRITICAL: Required file not found: ${filePath}`);
      process.exit(1);
    } else {
      console.log(`⚠️  Optional file not found: ${path.basename(filePath)} (will skip)`);
      return null;
    }
  }
  console.log(`✅ Found: ${path.basename(filePath)}`);
  return filePath;
}

// Get existing release or create new one
async function getOrCreateRelease(octokit, version) {
  const tagName = `v${version}`;
  const releaseName = `Janus Projekt ${version}`;
  
  // Read release notes
  const releaseNotesPath = path.join(PROJECT_ROOT, 'RELEASE_NOTES.md');
  let releaseNotes = '';
  if (fs.existsSync(releaseNotesPath)) {
    releaseNotes = fs.readFileSync(releaseNotesPath, 'utf-8');
  } else {
    releaseNotes = `Release ${version}`;
  }

  // Check if release exists
  try {
    const { data: release } = await octokit.rest.repos.getReleaseByTag({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      tag: tagName,
    });
    console.log(`✅ Found existing release: ${release.html_url}`);
    return release;
  } catch (error) {
    if (error.status !== 404) {
      console.error(`🚨 CRITICAL: Failed to check release: ${error.message}`);
      process.exit(1);
    }
  }

  // Determine if this should be marked as latest
  // For beta-only projects, mark the latest beta as latest
  // For stable projects, only mark stable releases as latest
  const isBeta = version.includes('beta') || version.includes('alpha');
  const makeLatest = isBeta ? "true" : "true";

  // Create new release
  try {
    const { data: release } = await octokit.rest.repos.createRelease({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      tag_name: tagName,
      name: releaseName,
      body: releaseNotes,
      draft: false,
      prerelease: isBeta,
      make_latest: makeLatest,
    });
    console.log(`✅ Release created: ${release.html_url}`);
    return release;
  } catch (error) {
    console.error(`🚨 CRITICAL: Failed to create release: ${error.message}`);
    process.exit(1);
  }
}

// Upload asset to release
async function uploadAsset(octokit, releaseId, filePath) {
  const fileName = path.basename(filePath);
  const fileSize = fs.statSync(filePath).size;

  console.log(`📤 Uploading ${fileName} (${(fileSize / 1024 / 1024).toFixed(2)} MB)...`);

  // Check if asset already exists and delete it
  try {
    const { data: assets } = await octokit.rest.repos.listReleaseAssets({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      release_id: releaseId,
    });
    const existingAsset = assets.find(a => a.name === fileName);
    if (existingAsset) {
      console.log(`🗑️  Deleting existing asset: ${fileName}`);
      await octokit.rest.repos.deleteReleaseAsset({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        asset_id: existingAsset.id,
      });
    }
  } catch (error) {
    console.warn(`⚠️  Failed to check/delete existing assets: ${error.message}`);
  }

  // Upload asset
  try {
    await octokit.rest.repos.uploadReleaseAsset({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      release_id: releaseId,
      name: fileName,
      data: fs.createReadStream(filePath),
      headers: {
        'content-length': fileSize,
        'content-type': 'application/octet-stream',
      },
    });
    console.log(`✅ Uploaded: ${fileName}`);
  } catch (error) {
    console.error(`🚨 CRITICAL: Failed to upload ${fileName}: ${error.message}`);
    process.exit(1);
  }
}

// Main function
async function main() {
  console.log('🚀 GitHub Release Publisher');
  console.log('================================');
  
  const version = getVersion();
  console.log(`📦 Version: ${version}`);
  
  const token = getAuthToken();
  console.log(`🔑 GitHub Token: ${token.substring(0, 10)}...`);
  
  const octokit = new Octokit({ auth: token });
  
  // Check required files
  console.log('\n📋 Checking required files...');
  const exeFile = checkFileExists(path.join(RELEASE_DIR, `janus-setup-${version}.exe`));
  const blockmapFile = checkFileExists(path.join(RELEASE_DIR, `janus-setup-${version}.exe.blockmap`), false);
  const latestYmlFile = checkFileExists(path.join(RELEASE_DIR, 'latest.yml'));
  const manifestFile = checkFileExists(path.join(RELEASE_DIR, 'janus-update-manifest.json'));

  // Get or create release
  console.log('\n📝 Getting or creating GitHub release...');
  const release = await getOrCreateRelease(octokit, version);

  // Upload assets
  console.log('\n📤 Uploading assets...');
  await uploadAsset(octokit, release.id, exeFile);
  if (blockmapFile) {
    await uploadAsset(octokit, release.id, blockmapFile);
  }
  await uploadAsset(octokit, release.id, latestYmlFile);
  await uploadAsset(octokit, release.id, manifestFile);
  
  console.log('\n✅ Release published successfully!');
  console.log(`🔗 ${release.html_url}`);
}

main().catch((error) => {
  console.error('🚨 UNEXPECTED ERROR:', error);
  process.exit(1);
});
