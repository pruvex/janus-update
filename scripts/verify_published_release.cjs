const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const yaml = require('js-yaml');
const { Octokit } = require('octokit');

const REPO_OWNER = 'pruvex';
const REPO_NAME = 'janus-update';
const PROJECT_ROOT = path.join(__dirname, '..');
const RELEASE_DIR = path.join(PROJECT_ROOT, 'release');
const EVIDENCE_DIR = path.join(PROJECT_ROOT, 'documentation', 'release');

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

function sha256(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', reject);
  });
}

function parseArgs(argv) {
  return {
    writeEvidence: argv.includes('--write-evidence'),
  };
}

function getExpectedAssets(version, manifest, latest) {
  const installerName = manifest.assetName || latest.path || `janus-setup-${version}.exe`;
  const expected = [
    {
      name: installerName,
      path: path.join(RELEASE_DIR, installerName),
      required: true,
      role: 'installer',
    },
    {
      name: 'latest.yml',
      path: path.join(RELEASE_DIR, 'latest.yml'),
      required: true,
      role: 'electron-latest-metadata',
    },
    {
      name: 'janus-update-manifest.json',
      path: path.join(RELEASE_DIR, 'janus-update-manifest.json'),
      required: true,
      role: 'janus-update-manifest',
    },
  ];

  const blockmapName = `${installerName}.blockmap`;
  const blockmapPath = path.join(RELEASE_DIR, blockmapName);
  if (fs.existsSync(blockmapPath)) {
    expected.push({
      name: blockmapName,
      path: blockmapPath,
      required: true,
      role: 'electron-differential-blockmap',
    });
  }

  return expected;
}

function normalizeDigest(digest) {
  if (typeof digest !== 'string') {
    return '';
  }
  return digest.startsWith('sha256:') ? digest.slice('sha256:'.length).toLowerCase() : digest.toLowerCase();
}

function buildEvidenceMarkdown({ version, release, verification, missing, unexpectedRelevant }) {
  const now = new Date().toISOString();
  const rows = verification.map((item) => (
    `| \`${item.name}\` | ${item.githubState} | ${item.githubSize} | ${item.localSize} | \`${item.githubDigest || 'missing'}\` | \`${item.localSha256}\` | ${item.result} |`
  ));

  return [
    `# Published Release Verification - ${version}`,
    '',
    '## Decision',
    '',
    missing.length === 0 && verification.every((item) => item.result === 'PASS') ? 'PUBLISHED PASS.' : 'PUBLISHED FAIL.',
    '',
    '## Release',
    '',
    `- Version: \`${version}\``,
    `- Tag: \`${release.tag_name}\``,
    `- Release: \`${release.name}\``,
    `- URL: ${release.html_url}`,
    `- Prerelease: \`${release.prerelease}\``,
    `- Draft: \`${release.draft}\``,
    `- Verified at: \`${now}\``,
    '',
    '## Asset Verification',
    '',
    '| Asset | GitHub state | GitHub size | Local size | GitHub digest | Local SHA256 | Result |',
    '|---|---|---:|---:|---|---|---:|',
    ...rows,
    '',
    `Missing expected assets: ${missing.length === 0 ? 'none' : missing.map((name) => `\`${name}\``).join(', ')}`,
    '',
    `Unexpected same-version assets: ${unexpectedRelevant.length === 0 ? 'none' : unexpectedRelevant.map((name) => `\`${name}\``).join(', ')}`,
    '',
    '## Policy',
    '',
    'This evidence contains file names, sizes and cryptographic hashes only. It does not contain raw secrets, tokens, cookies, tester data, prompts or file payloads.',
    '',
  ].join('\n');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const packagePath = path.join(PROJECT_ROOT, 'package.json');
  const latestPath = path.join(RELEASE_DIR, 'latest.yml');
  const manifestPath = path.join(RELEASE_DIR, 'janus-update-manifest.json');

  const pkg = readJson(packagePath, 'package.json');
  const latest = readYaml(latestPath, 'latest.yml');
  const manifest = readJson(manifestPath, 'janus-update-manifest.json');
  const version = pkg.version;
  const tagName = `v${version}`;

  ensure(typeof version === 'string' && version.length > 0, 'package.json.version missing');
  ensure(latest.version === version, `latest.yml version mismatch: ${latest.version} !== ${version}`);
  ensure(manifest.version === version, `manifest version mismatch: ${manifest.version} !== ${version}`);
  ensure(latest.path === manifest.assetName, `manifest asset mismatch: ${manifest.assetName} !== ${latest.path}`);
  ensure(latest.sha512 === manifest.sha512, 'manifest/latest sha512 mismatch');

  const token = process.env.GH_TOKEN;
  ensure(typeof token === 'string' && token.length > 0, 'GH_TOKEN environment variable is not set');

  const expectedAssets = getExpectedAssets(version, manifest, latest);
  for (const asset of expectedAssets) {
    ensure(fs.existsSync(asset.path), `Local release artifact missing: ${asset.path}`);
  }

  const octokit = new Octokit({ auth: token });
  const release = (await octokit.rest.repos.getReleaseByTag({
    owner: REPO_OWNER,
    repo: REPO_NAME,
    tag: tagName,
  })).data;

  ensure(release.tag_name === tagName, `Release tag mismatch: ${release.tag_name} !== ${tagName}`);
  ensure(release.draft === false, 'Release is still a draft');
  ensure(release.prerelease === version.includes('beta') || version.includes('alpha'), 'Release prerelease flag does not match version channel');

  const assets = (await octokit.rest.repos.listReleaseAssets({
    owner: REPO_OWNER,
    repo: REPO_NAME,
    release_id: release.id,
    per_page: 100,
  })).data;

  const verification = [];
  for (const expected of expectedAssets) {
    const githubAsset = assets.find((asset) => asset.name === expected.name);
    const localSize = fs.statSync(expected.path).size;
    const localSha256 = await sha256(expected.path);

    if (!githubAsset) {
      verification.push({
        name: expected.name,
        githubState: 'missing',
        githubSize: 0,
        localSize,
        githubDigest: '',
        localSha256,
        result: 'FAIL',
        notes: 'missing on GitHub release',
      });
      continue;
    }

    const githubSha256 = normalizeDigest(githubAsset.digest);
    const digestMatches = githubSha256 === localSha256;
    const sizeMatches = githubAsset.size === localSize;
    const stateMatches = githubAsset.state === 'uploaded';

    verification.push({
      name: expected.name,
      role: expected.role,
      githubState: githubAsset.state,
      githubSize: githubAsset.size,
      localSize,
      githubDigest: githubAsset.digest || '',
      localSha256,
      browserDownloadUrl: githubAsset.browser_download_url,
      result: stateMatches && sizeMatches && digestMatches ? 'PASS' : 'FAIL',
      notes: [
        stateMatches ? '' : `state=${githubAsset.state}`,
        sizeMatches ? '' : `size ${githubAsset.size} !== ${localSize}`,
        digestMatches ? '' : `digest ${githubAsset.digest || 'missing'} !== sha256:${localSha256}`,
      ].filter(Boolean).join('; '),
    });
  }

  const missing = verification.filter((item) => item.result === 'FAIL' && item.githubState === 'missing').map((item) => item.name);
  const expectedNames = new Set(expectedAssets.map((asset) => asset.name));
  const unexpectedRelevant = assets
    .filter((asset) => asset.name.includes(version) && !expectedNames.has(asset.name))
    .map((asset) => asset.name);
  const failed = verification.filter((item) => item.result !== 'PASS');

  const summary = {
    schemaVersion: 'janus.release-verification.v1',
    status: failed.length === 0 && missing.length === 0 ? 'PASS' : 'FAIL',
    repository: `${REPO_OWNER}/${REPO_NAME}`,
    version,
    tagName,
    releaseUrl: release.html_url,
    prerelease: release.prerelease,
    draft: release.draft,
    assets: verification,
    missing,
    unexpectedRelevant,
    verifiedAt: new Date().toISOString(),
  };

  if (args.writeEvidence) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
    const jsonPath = path.join(EVIDENCE_DIR, `PUBLISHED_RELEASE_VERIFICATION_${version}.json`);
    const mdPath = path.join(EVIDENCE_DIR, `PUBLISHED_RELEASE_VERIFICATION_${version}.md`);
    fs.writeFileSync(jsonPath, JSON.stringify(summary, null, 2), 'utf-8');
    fs.writeFileSync(mdPath, buildEvidenceMarkdown({ version, release, verification, missing, unexpectedRelevant }), 'utf-8');
    summary.evidenceJson = path.relative(PROJECT_ROOT, jsonPath).replaceAll(path.sep, '/');
    summary.evidenceMarkdown = path.relative(PROJECT_ROOT, mdPath).replaceAll(path.sep, '/');
  }

  console.log(JSON.stringify(summary, null, 2));

  if (summary.status !== 'PASS') {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`release:verify-published FAIL: ${err.message}`);
  process.exit(1);
});
