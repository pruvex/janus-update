#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function timestampForFile(date = new Date()) {
  return date.toISOString().replace(/[:.]/g, "-");
}

function createLogStreams(prefix) {
  const logDir = path.join(process.cwd(), "debug_logs");
  ensureDir(logDir);
  const stamp = timestampForFile();
  const outPath = path.join(logDir, `${prefix}_${stamp}.out.log`);
  const errPath = path.join(logDir, `${prefix}_${stamp}.err.log`);
  return {
    outPath,
    errPath,
    outStream: fs.createWriteStream(outPath, { flags: "a" }),
    errStream: fs.createWriteStream(errPath, { flags: "a" }),
  };
}

function forwardStream(stream, sink, target) {
  stream.on("data", (chunk) => {
    sink.write(chunk);
    target.write(chunk);
  });
}

function runWithLogs(command, args, options = {}) {
  const { label, logPrefix, env = {} } = options;
  const logs = createLogStreams(logPrefix);
  console.log(`[${label}] writing logs to ${path.relative(process.cwd(), logs.outPath)} and ${path.relative(process.cwd(), logs.errPath)}`);

  const child = spawn(command, args, {
    cwd: process.cwd(),
    env: { ...process.env, ...env },
    shell: true,
    stdio: ["inherit", "pipe", "pipe"],
  });

  forwardStream(child.stdout, process.stdout, logs.outStream);
  forwardStream(child.stderr, process.stderr, logs.errStream);

  child.on("close", (code) => {
    logs.outStream.end();
    logs.errStream.end();
    process.exit(code || 0);
  });

  child.on("error", (error) => {
    logs.errStream.write(`${error.stack || error.message}\n`);
    logs.outStream.end();
    logs.errStream.end();
    console.error(`[${label}] failed to start`, error);
    process.exit(1);
  });
}

module.exports = {
  runWithLogs,
};
