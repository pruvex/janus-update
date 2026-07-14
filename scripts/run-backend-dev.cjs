#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { runWithLogs } = require("./dev-log-utils.cjs");

function resolvePython() {
  const venvPython = path.join(process.cwd(), "backend", "venv", "Scripts", "python.exe");
  if (fs.existsSync(venvPython)) return { cmd: venvPython, args: [] };

  // Fallback 1: py launcher
  const pyProbe = spawnSync("py", ["-3.11", "-c", "import sys; print(sys.executable)"], { encoding: "utf8" });
  if (pyProbe.status === 0) return { cmd: "py", args: ["-3.11"] };

  // Fallback 2: python on PATH
  return { cmd: "python", args: [] };
}

function resolveCodexBackendEnvironment(projectRoot = process.cwd()) {
  const runtimePath = path.join(
    projectRoot,
    "node_modules",
    "@openai",
    "codex-win32-x64",
    "vendor",
    "x86_64-pc-windows-msvc",
    "bin",
    "codex.exe"
  );
  const appDataRoot = process.env.APPDATA || path.join(require("os").homedir(), "AppData", "Roaming");
  const codexHome = path.join(appDataRoot, "Janus Projekt", "codex-home");

  return {
    JANUS_CODEX_RUNTIME_PATH: runtimePath,
    JANUS_CODEX_HOME: codexHome,
    JANUS_CODEX_CREDENTIALS_STORE: "keyring",
  };
}

function main() {
  const mode = process.argv[2] === "noreload" ? "noreload" : "reload";
  const python = resolvePython();
  const codexEnv = resolveCodexBackendEnvironment();
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
  runWithLogs(python.cmd, uvicornArgs, {
    label: "backend-start",
    logPrefix: "runtime_backend",
    env: {
      PYTHONIOENCODING: "UTF-8",
      NODE_ENV: "development",
      ...codexEnv,
    },
  });
}

module.exports = {
  resolveCodexBackendEnvironment,
};

if (require.main === module) {
  main();
}
