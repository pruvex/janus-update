#!/usr/bin/env node
/**
 * Verifies production frontend artifacts for packaging safety:
 * 1) frontend/dist and index.html exist
 * 2) all ./assets/* references in index.html resolve to real files
 * 3) day-panel markers are present in built output
 *
 * Usage: node scripts/verify-frontend-dist.cjs
 */
const fs = require("fs");
const path = require("path");

const repoRoot = path.join(__dirname, "..");
const distDir = path.join(repoRoot, "frontend", "dist");
const indexHtml = path.join(distDir, "index.html");

function walkFiles(dir, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walkFiles(p, acc);
    else acc.push(p);
  }
  return acc;
}

function fail(msg) {
  console.error(`[verify-frontend-dist] ${msg}`);
  process.exit(1);
}

if (!fs.existsSync(distDir)) {
  fail('Directory "frontend/dist" is missing. Run: npm run build');
}

if (!fs.existsSync(indexHtml)) {
  fail('File "frontend/dist/index.html" is missing.');
}

const html = fs.readFileSync(indexHtml, "utf8");
const assetRefs = Array.from(
  html.matchAll(/(?:src|href)=["']\.\/(assets\/[^"']+)["']/g),
  (m) => m[1]
);

if (!assetRefs.length) {
  fail('No "./assets/..." references found in frontend/dist/index.html.');
}

const missingAssets = assetRefs.filter((rel) => !fs.existsSync(path.join(distDir, rel)));
if (missingAssets.length) {
  fail(`Missing referenced assets: ${missingAssets.join(", ")}`);
}

const markers = ["calendar-day-widget", "janusCloseDayPanel", "calendar-day-widget-rail"];
let found = markers.some((m) => html.includes(m));

if (!found) {
  const bundleLike = walkFiles(distDir).filter((f) => /\.(js|mjs|css|html)$/i.test(f));
  for (const f of bundleLike) {
    try {
      const c = fs.readFileSync(f, "utf8");
      if (markers.some((m) => c.includes(m))) {
        found = true;
        break;
      }
    } catch {
      // ignore unreadable file
    }
  }
}

if (!found) {
  fail(
    "No day-panel markers found in frontend build output. Check frontend wiring/build integrity."
  );
}

console.log(
  `[verify-frontend-dist] OK - ${assetRefs.length} asset refs resolved and day-panel markers present.`
);
