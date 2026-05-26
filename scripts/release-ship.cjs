#!/usr/bin/env node
const fs = require("fs");
const cp = require("child_process");

function sh(cmd, opts = {}) {
  return cp.execSync(cmd, {
    stdio: opts.stdio || ["ignore", "pipe", "pipe"],
    encoding: "utf8",
  }).trim();
}

function run(cmd) {
  cp.execSync(cmd, { stdio: "inherit" });
}

function parseVersion(v) {
  const m = String(v || "").trim().match(/^(\d+)\.(\d+)\.(\d+)-beta\.(\d+)$/);
  if (!m) return null;
  return {
    major: Number(m[1]),
    minor: Number(m[2]),
    patch: Number(m[3]),
    beta: Number(m[4]),
  };
}

function nextBeta(v) {
  const parsed = parseVersion(v);
  if (!parsed) {
    throw new Error(`Version '${v}' hat nicht das erwartete Format x.y.z-beta.n`);
  }
  return `${parsed.major}.${parsed.minor}.${parsed.patch}-beta.${parsed.beta + 1}`;
}

function tagExistsOnOrigin(version) {
  const tag = `refs/tags/v${version}`;
  const out = sh(`git ls-remote --tags origin ${tag}`);
  return Boolean(String(out || "").trim());
}

function resolveTargetVersion(currentVersion, explicitVersion) {
  if (explicitVersion) return explicitVersion;
  let candidate = nextBeta(currentVersion);
  for (let i = 0; i < 25; i += 1) {
    if (!tagExistsOnOrigin(candidate)) return candidate;
    candidate = nextBeta(candidate);
  }
  throw new Error("Konnte keine freie Beta-Version in den naechsten 25 Schritten finden.");
}

function commitIfChanged(message, paths) {
  run(`git add ${paths.join(" ")}`);
  const staged = sh("git diff --cached --name-only");
  if (!staged) return false;
  run(`git commit -m "${message}"`);
  return true;
}

function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || args.includes("-h")) {
    console.log("Usage: npm run release:ship [-- <version>] [--dry-run]");
    return;
  }
  const dryRun = args.includes("--dry-run");
  const explicitVersion = args.find((a) => !a.startsWith("-")) || "";
  const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  const currentVersion = String(pkg.version || "").trim();
  const targetVersion = resolveTargetVersion(currentVersion, explicitVersion);

  console.log(`[release:ship] Start: current=${currentVersion} target=${targetVersion} dryRun=${dryRun}`);
  run("npm run release:guard");
  if (dryRun) {
    console.log("[release:ship] DRY RUN OK");
    return;
  }

  run(`npm version ${targetVersion} --no-git-tag-version`);
  run("npm run write-version");

  commitIfChanged(
    `chore(release): bump version to ${targetVersion}`,
    ["package.json", "package-lock.json", "backend/version.py"]
  );

  run("git push origin master");
  try {
    run("git push backup master");
  } catch (_) {
    console.warn("[release:ship] WARN: push backup master fehlgeschlagen (origin war erfolgreich).");
  }

  run("npm run release");

  const notesCommitted = commitIfChanged(
    `docs(release): sync generated release notes for ${targetVersion}`,
    ["release_notes.md", "RELEASE_NOTES.md"]
  );
  if (notesCommitted) {
    run("git push origin master");
    try {
      run("git push backup master");
    } catch (_) {
      console.warn("[release:ship] WARN: backup push fuer release notes fehlgeschlagen.");
    }
  }

  console.log(`[release:ship] DONE: ${targetVersion}`);
}

try {
  main();
} catch (err) {
  console.error(`[release:ship] FAILED: ${err.message}`);
  process.exit(1);
}
