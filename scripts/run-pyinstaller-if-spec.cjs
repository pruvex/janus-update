#!/usr/bin/env node
const fs = require("fs");
const { spawnSync } = require("child_process");

const candidates = [
  "janus_backend.spec",
  "backend/janus_backend.spec",
];

const spec = candidates.find((p) => fs.existsSync(p));
if (!spec) {
  console.log("[build-all] No janus_backend.spec found, skip PyInstaller and reuse existing dist/janus_backend.exe");
  process.exit(0);
}

console.log(`[build-all] Running PyInstaller with spec: ${spec}`);
const result = spawnSync("python", ["-m", "PyInstaller", spec, "--clean", "--noconfirm"], {
  stdio: "inherit",
  shell: true,
});
process.exit(result.status || 0);
