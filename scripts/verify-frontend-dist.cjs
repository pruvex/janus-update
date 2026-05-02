#!/usr/bin/env node
/**
 * Prüft nach `vite build`, dass das Produktions-Bundle das Tages-Panel / Kalender-Widget enthält.
 * Verhindert „stilles“ Packen ohne aktuelle frontend/dist (Electron + Backend mounten beide darauf).
 *
 * Aufruf: node scripts/verify-frontend-dist.cjs
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
  fail('Ordner "frontend/dist" fehlt. Zuerst ausführen: npm run build (bzw. npx vite build)');
}

if (!fs.existsSync(indexHtml)) {
  fail('Datei "frontend/dist/index.html" fehlt.');
}

const html = fs.readFileSync(indexHtml, "utf8");
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
      /* ignore */
    }
  }
}

if (!found) {
  fail(
    "Keine Tages-Panel-Artefakte (calendar-day-widget / janusCloseDayPanel) im Build gefunden. " +
      "Prüfen, ob frontend/index.html die Module lädt und der Build fehlerfrei war."
  );
}

console.log("[verify-frontend-dist] OK — frontend/dist enthält Tages-Panel / Kalender-Widget-Spuren.");
