#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

function resolvePython() {
  const venvPython = path.join(process.cwd(), "backend", "venv", "Scripts", "python.exe");
  if (fs.existsSync(venvPython)) return { cmd: venvPython, args: [] };

  // Fallback 1: py launcher
  const pyProbe = spawnSync("py", ["-3.11", "-c", "import sys; print(sys.executable)"], { encoding: "utf8" });
  if (pyProbe.status === 0) return { cmd: "py", args: ["-3.11"] };

  // Fallback 2: python on PATH
  return { cmd: "python", args: [] };
}

function main() {
  const mode = process.argv[2] === "noreload" ? "noreload" : "reload";
  const python = resolvePython();
  const uvicornArgs = [
    ...python.args,
    "-m",
    "uvicorn",
    "backend.main:app",
    "--port",
    "8001",
    "--host",
    "localhost",
  ];

  if (mode === "reload") {
    uvicornArgs.push("--reload", "--reload-dir", "backend");
  }

  console.log(`[backend-start] python=${python.cmd} mode=${mode}`);
  const result = spawnSync(python.cmd, uvicornArgs, {
    stdio: "inherit",
    env: { ...process.env, PYTHONIOENCODING: "UTF-8", NODE_ENV: "development" },
    shell: true,
  });
  process.exit(result.status || 0);
}

main();
