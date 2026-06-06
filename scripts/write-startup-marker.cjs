const fs = require('fs');
const path = require('path');

// Keep startup telemetry alongside other versioned dev logs.
const logDir = path.join(process.cwd(), "documentation", "logs");
const logFile = path.join(logDir, "janus_startup_telemetry.log");

try {
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  const marker = {
    marker: "npm_start",
    timestamp: new Date().toISOString(),
    metadata: {}
  };

  fs.appendFileSync(logFile, JSON.stringify(marker) + "\n", "utf8");
  console.log("[Startup Telemetry] Wrote npm_start marker");
} catch (e) {
  console.error("[Startup Telemetry] Failed to write npm_start marker:", e);
}
