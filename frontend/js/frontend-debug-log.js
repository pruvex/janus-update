const MAX_DEBUG_LOG_ENTRIES = 1000;
const RELEVANT_MESSAGE_PATTERN = /(error|warn|failed|failure|exception|stack|trace|ipc|api|fetch|network|request|response|stream|renderer|dom|toast|modal|model|video|image|uncaught|unhandled|timeout|abort|cors|404|500|401|403)/i;
const ORIGINAL_CONSOLE = {};
const DEBUG_LOG_BUFFER = [];

function normalizeArg(arg) {
  if (arg instanceof Error) {
    return `${arg.name}: ${arg.message}\n${arg.stack || ""}`.trim();
  }

  if (typeof arg === "string") {
    return arg;
  }

  try {
    return JSON.stringify(arg);
  } catch (_error) {
    return String(arg);
  }
}

function pushDebugEntry(level, source, args) {
  const message = args.map(normalizeArg).join(" ").trim();
  if (!message) {
    return;
  }

  DEBUG_LOG_BUFFER.push({
    timestamp: new Date().toISOString(),
    level,
    source,
    message,
    url: window.location.href,
  });

  if (DEBUG_LOG_BUFFER.length > MAX_DEBUG_LOG_ENTRIES) {
    DEBUG_LOG_BUFFER.splice(0, DEBUG_LOG_BUFFER.length - MAX_DEBUG_LOG_ENTRIES);
  }
}

function installConsoleInterceptors() {
  ["log", "info", "warn", "error", "debug"].forEach((level) => {
    if (typeof console[level] !== "function" || ORIGINAL_CONSOLE[level]) {
      return;
    }

    ORIGINAL_CONSOLE[level] = console[level].bind(console);
    console[level] = (...args) => {
      pushDebugEntry(level, "console", args);
      ORIGINAL_CONSOLE[level](...args);
    };
  });
}

function installRuntimeErrorInterceptors() {
  window.addEventListener("error", (event) => {
    pushDebugEntry("error", "window.error", [
      event.message || "Uncaught error",
      `${event.filename || "unknown"}:${event.lineno || 0}:${event.colno || 0}`,
      event.error || "",
    ]);
  });

  window.addEventListener("unhandledrejection", (event) => {
    pushDebugEntry("error", "window.unhandledrejection", [event.reason || "Unhandled promise rejection"]);
  });
}

function installFetchInterceptor() {
  if (typeof window.fetch !== "function" || window.__janusDebugFetchInstalled) {
    return;
  }

  window.__janusDebugFetchInstalled = true;
  const originalFetch = window.fetch.bind(window);

  window.fetch = async (...args) => {
    const startedAt = performance.now();
    const requestUrl = String(args[0]?.url || args[0] || "unknown");

    try {
      const response = await originalFetch(...args);
      if (!response.ok) {
        pushDebugEntry("warn", "fetch", [
          `${response.status} ${response.statusText}`,
          requestUrl,
          `${Math.round(performance.now() - startedAt)}ms`,
        ]);
      }
      return response;
    } catch (error) {
      pushDebugEntry("error", "fetch", [requestUrl, error]);
      throw error;
    }
  };
}

function formatEntry(entry) {
  return `- ${entry.timestamp} [${entry.level.toUpperCase()}] ${entry.source}: ${entry.message}`;
}

function buildFrontendLogMarkdown(entries, metadata = {}) {
  const relevantEntries = entries.filter((entry) => {
    return entry.level === "error" || entry.level === "warn" || RELEVANT_MESSAGE_PATTERN.test(entry.message);
  });

  const now = new Date().toISOString();
  const firstTimestamp = relevantEntries[0]?.timestamp || entries[0]?.timestamp || "N/A";
  const lastTimestamp = relevantEntries[relevantEntries.length - 1]?.timestamp || entries[entries.length - 1]?.timestamp || "N/A";
  const rawCount = entries.length;
  const omittedCount = Math.max(rawCount - relevantEntries.length, 0);

  return [
    "# Frontend Debug Log",
    "",
    `Generated: ${now}`,
    `URL: ${window.location.href}`,
    `User Agent: ${navigator.userAgent}`,
    `Time Window: ${firstTimestamp} – ${lastTimestamp}`,
    `Raw Entries Buffered: ${rawCount}`,
    `Relevant Entries Exported: ${relevantEntries.length}`,
    `Omitted Noise Entries: ${omittedCount}`,
    metadata.reason ? `Reason: ${metadata.reason}` : "Reason: Skill 6 frontend debug export",
    "",
    "## Relevant Frontend Events",
    "",
    relevantEntries.length ? relevantEntries.map(formatEntry).join("\n") : "Keine relevanten error/warn/API/IPC/Stacktrace-Einträge im Buffer gefunden.",
    "",
    "## Export Notes",
    "",
    "- Enthält nur gefilterte Renderer-/Frontend-Ereignisse aus dem aktuellen App-Fenster.",
    "- Noise wurde ausgelassen: normale Info-/Debug-Ausgaben ohne Fehler-/API-/IPC-Bezug.",
    "- Wenn der Fehler reproduziert wurde, aber hier nichts erscheint, bitte zusätzlich den sichtbaren Ist-Zustand im Skill-6-Paket beschreiben.",
    "",
  ].join("\n");
}

async function exportFrontendLog(metadata = {}) {
  const content = buildFrontendLogMarkdown([...DEBUG_LOG_BUFFER], metadata);

  if (!window.electron?.writeFrontendDebugLog) {
    throw new Error("Frontend debug log IPC is not available");
  }

  const result = await window.electron.writeFrontendDebugLog({ content });
  if (!result?.success) {
    throw new Error(result?.error || "Frontend debug log export failed");
  }

  return result;
}

function clearFrontendLog() {
  DEBUG_LOG_BUFFER.length = 0;
  pushDebugEntry("info", "frontend-debug-log", ["Frontend debug log buffer cleared"]);
}

function installExportHotkey() {
  window.addEventListener("keydown", async (event) => {
    if (!event.ctrlKey || !event.shiftKey || event.key.toLowerCase() !== "l") {
      return;
    }

    event.preventDefault();
    try {
      const result = await exportFrontendLog({ reason: "Manual Ctrl+Shift+L Skill 6 frontend debug export" });
      window.alert(`Frontend-Log exportiert:\n${result.path}`);
    } catch (error) {
      window.alert(`Frontend-Log Export fehlgeschlagen:\n${error.message}`);
    }
  });
}

installConsoleInterceptors();
installRuntimeErrorInterceptors();
installFetchInterceptor();
installExportHotkey();
pushDebugEntry("info", "frontend-debug-log", ["Frontend debug log collector initialized"]);

window.janusDebugLogs = {
  exportFrontendLog,
  clearFrontendLog,
  getBufferSize: () => DEBUG_LOG_BUFFER.length,
};
