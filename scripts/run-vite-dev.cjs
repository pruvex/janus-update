#!/usr/bin/env node
const { runWithLogs } = require("./dev-log-utils.cjs");

runWithLogs("vite", [], {
  label: "vite-start",
  logPrefix: "runtime_vite",
  env: { NODE_ENV: "development" },
});
