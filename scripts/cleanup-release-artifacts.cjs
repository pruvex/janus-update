#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const repoRoot = path.join(__dirname, "..");
const releaseDir = path.join(repoRoot, "release");
const pkg = require(path.join(repoRoot, "package.json"));
const version = pkg.version;

if (!fs.existsSync(releaseDir)) {
  console.log("[cleanup-release-artifacts] release directory missing, skip.");
  process.exit(0);
}

const keep = new Set([
  `janus-setup-${version}.exe`,
  "beta.yml",
  "janus-update-manifest.json",
  "builder-debug.yml",
]);

const entries = fs.readdirSync(releaseDir, { withFileTypes: true });
let deleted = 0;

for (const ent of entries) {
  if (!ent.isFile()) continue;
  const name = ent.name;
  const isOldInstaller =
    /^janus-setup-.*\.exe$/i.test(name) && !keep.has(name);
  const isOldBlockmap = /^janus-setup-.*\.exe\.blockmap$/i.test(name);
  const isLatestYml = /^latest\.yml$/i.test(name);

  if (isOldInstaller || isOldBlockmap || isLatestYml) {
    fs.unlinkSync(path.join(releaseDir, name));
    deleted += 1;
  }
}

console.log(
  `[cleanup-release-artifacts] done. kept installer=janus-setup-${version}.exe, deleted=${deleted}`
);
