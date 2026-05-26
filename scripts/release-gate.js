#!/usr/bin/env node
/**
 * Janus Release-Gate
 * Hartes Preflight-Gate vor Build/Publish.
 *
 * Blockiert, wenn:
 *   - Branch nicht master ist
 *   - Working tree dirty ist
 *   - HEAD nicht exakt mit origin/master synchron ist
 *   - package.json Pflicht-Scripts fehlen
 *   - backend/version.py nicht zur package.json Version passt
 *
 * Aufruf: node scripts/release-gate.js
 */
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

function sh(cmd) {
  return execSync(cmd, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
}

function fail(msg) {
  console.error(`[RELEASE-GATE BLOCKED] ${msg}`);
  process.exit(1);
}

function hasRemote(name) {
  const remotes = sh('git remote').split(/\r?\n/).map((r) => r.trim()).filter(Boolean);
  return remotes.includes(name);
}

try {
  const branch = sh('git rev-parse --abbrev-ref HEAD');
  if (branch !== 'master') {
    fail(`Release nur von 'master' erlaubt (aktuell: '${branch}').`);
  }

  const dirty = sh('git status --porcelain');
  if (dirty) {
    fail(`Working tree nicht clean. Bitte commit/stash vor Release:\n${dirty}`);
  }

  // HEAD muss identisch zu origin/master sein (verhindert "local-only" Releases).
  sh('git fetch origin master --quiet');
  const head = sh('git rev-parse HEAD');
  const originMaster = sh('git rev-parse origin/master');
  if (head !== originMaster) {
    fail(
      `HEAD (${head.slice(0, 7)}) ist nicht origin/master (${originMaster.slice(0, 7)}).\n` +
      "Bitte zuerst: git checkout master && git pull --ff-only origin master && git push origin master"
    );
  }

  // Optionaler zweiter Sicherheitsgurt: backup/master muss bei vorhandenem remote mitziehen.
  if (hasRemote('backup')) {
    sh('git fetch backup master --quiet');
    const backupMaster = sh('git rev-parse backup/master');
    if (head !== backupMaster) {
      fail(
        `HEAD (${head.slice(0, 7)}) ist nicht backup/master (${backupMaster.slice(0, 7)}).\n` +
        'Bitte zuerst: git push backup master'
      );
    }
  }

  // package.json Pflicht-Scripts validieren.
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
  const requiredScripts = ['release:guard', 'build-all', 'build-installer', 'release'];
  const missingScripts = requiredScripts.filter((name) => !pkg.scripts || !pkg.scripts[name]);
  if (missingScripts.length > 0) {
    fail(`Pflicht-Scripts fehlen in package.json: ${missingScripts.join(', ')}`);
  }

  // Version-Sync: package.json <-> backend/version.py
  const pkgVersion = String(pkg.version || '').trim();
  const backendVersionPy = readFileSync('backend/version.py', 'utf8');
  const m = backendVersionPy.match(/APP_VERSION\s*=\s*["']([^"']+)["']/);
  const backendVersion = m ? m[1].trim() : '';
  if (!pkgVersion || !backendVersion || pkgVersion !== backendVersion) {
    fail(
      `Version-Mismatch: package.json=${pkgVersion || '<leer>'}, ` +
      `backend/version.py=${backendVersion || '<nicht gefunden>'}. ` +
      'Bitte zuerst: npm run write-version'
    );
  }

  console.log(
    `[RELEASE-GATE OK] branch=${branch}, clean=true, origin/master sync=true, version=${pkgVersion}`
  );
  process.exit(0);
} catch (err) {
  fail(`Unerwarteter Fehler: ${err.message}`);
}
