const fs = require('fs');
const path = require('path');
const { Octokit } = require('octokit');

const REPO_OWNER = 'pruvex';
const REPO_NAME = 'janus-update';
const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');

function getVersion() {
  const packageJsonPath = path.join(PROJECT_ROOT, 'package.json');
  const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  return packageData.version;
}

function getAuthToken() {
  const token = process.env.GH_TOKEN;
  if (!token) {
    console.error('[publish] CRITICAL: GH_TOKEN environment variable is not set');
    process.exit(1);
  }
  return token;
}

function resolveChannelFile(version) {
  if (/-alpha(\.|$)/i.test(version)) {
    return 'alpha.yml';
  }
  if (/-beta(\.|$)/i.test(version)) {
    return 'beta.yml';
  }
  return 'latest.yml';
}

function checkFileExists(filePath, required = true) {
  if (!fs.existsSync(filePath)) {
    if (required) {
      console.error(`[publish] CRITICAL: required file not found: ${filePath}`);
      process.exit(1);
    }
    console.log(`[publish] Optional file not found: ${path.basename(filePath)} (skip)`);
    return null;
  }
  console.log(`[publish] Found: ${path.basename(filePath)}`);
  return filePath;
}

async function getOrCreateRelease(octokit, version) {
  const tagName = `v${version}`;
  const releaseName = `Janus Projekt ${version}`;

  const releaseNotesPath = path.join(PROJECT_ROOT, 'RELEASE_NOTES.md');
  const releaseNotes = fs.existsSync(releaseNotesPath)
    ? fs.readFileSync(releaseNotesPath, 'utf-8')
    : `Release ${version}`;

  try {
    const { data: release } = await octokit.rest.repos.getReleaseByTag({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      tag: tagName,
    });
    console.log(`[publish] Found existing release: ${release.html_url}`);
    return release;
  } catch (error) {
    if (error.status !== 404) {
      console.error(`[publish] CRITICAL: failed to check release: ${error.message}`);
      process.exit(1);
    }
  }

  const isPre = version.includes('beta') || version.includes('alpha');
  try {
    const { data: release } = await octokit.rest.repos.createRelease({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      tag_name: tagName,
      name: releaseName,
      body: releaseNotes,
      draft: false,
      prerelease: isPre,
      make_latest: 'true',
    });
    console.log(`[publish] Release created: ${release.html_url}`);
    return release;
  } catch (error) {
    console.error(`[publish] CRITICAL: failed to create release: ${error.message}`);
    process.exit(1);
  }
}

async function uploadAsset(octokit, releaseId, filePath) {
  const fileName = path.basename(filePath);
  const fileSize = fs.statSync(filePath).size;

  console.log(`[publish] Uploading ${fileName} (${(fileSize / 1024 / 1024).toFixed(2)} MB)...`);

  try {
    const { data: assets } = await octokit.rest.repos.listReleaseAssets({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      release_id: releaseId,
    });
    const existingAsset = assets.find((a) => a.name === fileName);
    if (existingAsset) {
      console.log(`[publish] Deleting existing asset: ${fileName}`);
      await octokit.rest.repos.deleteReleaseAsset({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        asset_id: existingAsset.id,
      });
    }
  } catch (error) {
    console.warn(`[publish] WARN: failed to check/delete existing assets: ${error.message}`);
  }

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
    console.log(`[publish] Uploaded: ${fileName}`);
  } catch (error) {
    console.error(`[publish] CRITICAL: failed to upload ${fileName}: ${error.message}`);
    process.exit(1);
  }
}

async function main() {
  console.log('[publish] GitHub Release Publisher');
  const version = getVersion();
  console.log(`[publish] Version: ${version}`);

  const token = getAuthToken();
  console.log(`[publish] GitHub Token prefix: ${token.substring(0, 10)}...`);

  const octokit = new Octokit({ auth: token });
  const channelFile = resolveChannelFile(version);

  console.log('[publish] Checking required files...');
  const exeFile = checkFileExists(path.join(RELEASE_DIR, `janus-setup-${version}.exe`));
  const blockmapFile = checkFileExists(path.join(RELEASE_DIR, `janus-setup-${version}.exe.blockmap`), false);
  const channelYmlFile = checkFileExists(path.join(RELEASE_DIR, channelFile), true);
  const latestYmlFile = checkFileExists(path.join(RELEASE_DIR, 'latest.yml'), false);
  const betaYmlFile = checkFileExists(path.join(RELEASE_DIR, 'beta.yml'), false);
  const alphaYmlFile = checkFileExists(path.join(RELEASE_DIR, 'alpha.yml'), false);
  const manifestFile = checkFileExists(path.join(RELEASE_DIR, 'janus-update-manifest.json'));

  console.log('[publish] Getting or creating GitHub release...');
  const release = await getOrCreateRelease(octokit, version);

  console.log('[publish] Uploading assets...');
  await uploadAsset(octokit, release.id, exeFile);
  if (blockmapFile) {
    await uploadAsset(octokit, release.id, blockmapFile);
  }
  await uploadAsset(octokit, release.id, channelYmlFile);

  if (latestYmlFile && path.basename(latestYmlFile) !== channelFile) {
    await uploadAsset(octokit, release.id, latestYmlFile);
  }
  if (betaYmlFile && path.basename(betaYmlFile) !== channelFile) {
    await uploadAsset(octokit, release.id, betaYmlFile);
  }
  if (alphaYmlFile && path.basename(alphaYmlFile) !== channelFile) {
    await uploadAsset(octokit, release.id, alphaYmlFile);
  }

  await uploadAsset(octokit, release.id, manifestFile);

  console.log(`[publish] Release published successfully: ${release.html_url}`);
}

main().catch((error) => {
  console.error('[publish] UNEXPECTED ERROR:', error);
  process.exit(1);
});
