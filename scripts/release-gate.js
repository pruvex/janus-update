#!/usr/bin/env node
/**
 * Janus Release-Gate
 * Blockiert electron-builder Release-Runs, wenn:
 *   - aktueller Branch != master
 *   - working tree dirty (uncommitted changes)
 *   - HEAD nicht mit backup/master synchron
 *
 * Aufruf: node scripts/release-gate.js
 */
const { execSync } = require('child_process');

function sh(cmd) {
  return execSync(cmd, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
}

function fail(msg) {
  console.error(`[RELEASE-GATE BLOCKED] ${msg}`);
  process.exit(1);
}

try {
  const branch = sh('git rev-parse --abbrev-ref HEAD');
  if (branch !== 'master') {
    fail(`Release darf nur von 'master' ausgeloest werden (aktuell: '${branch}').`);
  }

  const dirty = sh('git status --porcelain');
  if (dirty) {
    fail(`Dirty working tree - bitte commit/stash:\n${dirty}`);
  }

  // Sicherheit: backup/master muss existieren und HEAD entsprechen
  try {
    sh('git fetch backup master --quiet');
    const local = sh('git rev-parse HEAD');
    const remote = sh('git rev-parse backup/master');
    if (local !== remote) {
      fail(`HEAD (${local.slice(0, 7)}) != backup/master (${remote.slice(0, 7)}). Erst: git push backup master`);
    }
  } catch (e) {
    console.warn(`[RELEASE-GATE WARN] backup/master konnte nicht verifiziert werden: ${e.message}`);
  }

  console.log('[RELEASE-GATE OK] Branch=master, clean, synced with backup/master.');
  process.exit(0);
} catch (err) {
  fail(`Unerwarteter Fehler: ${err.message}`);
}
