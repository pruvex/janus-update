/**
 * Dual-window workspace: central client state (Dossier 1 / Layout 7).
 * DOM ids use suffixes -A and -B; primary pane for legacy bindings is A.
 */

/** localStorage: aktive Chats + Fenster-B-Sichtbarkeit (keine Fenster-Positionen/-Größen) */
export const WINDOW_WORKSPACE_STORAGE_KEY = "janus_window_workspace_v1";

export const WINDOW_IDS = Object.freeze(["A", "B"]);
export const PRIMARY_WINDOW_ID = "A";
export const SECONDARY_WINDOW_ID = "B";

/** @typedef {"A" | "B"} WindowId */

function cloneState(s) {
  return {
    layout: s.layout,
    activeWindowId: s.activeWindowId,
    windows: {
      A: { ...s.windows.A },
      B: { ...s.windows.B },
    },
    dock: {
      modules: Object.fromEntries(
        Object.entries(s.dock?.modules || {}).map(([k, v]) => [k, { ...v }])
      ),
    },
  };
}

/** MCL-Felder pro Dock-Modul (Single Source of Truth; modal-api.js ist nur Fassade). */
function dockModuleShape(overrides = {}) {
  return {
    exists: false,
    isOpen: false,
    minimized: false,
    /** @type {string | null} MCL renderer / contract type */
    type: null,
    /** @type {unknown} last modal_request payload */
    payload: null,
    /** @type {number} stack order (MCL Z-Stack, basis 100) */
    zIndex: 100,
    /** @type {{ x?: number, y?: number } | null} */
    position: null,
    /** @type {{ w?: number, h?: number } | null} */
    size: null,
    ...overrides,
  };
}

function createInitialState() {
  return {
    layout: "split",
    activeWindowId: "A",
    windows: {
      A: {
        activeChatId: null,
        isActive: true,
        isOpen: true,
        minimized: false,
        /** @type {string | null} null = Sidebar-Standard */
        provider: null,
        /** @type {string | null} null = Sidebar-Standard */
        modelId: null,
      },
      B: {
        activeChatId: null,
        isActive: false,
        isOpen: true,
        minimized: false,
        /** @type {string | null} */
        provider: null,
        /** @type {string | null} */
        modelId: null,
      },
    },
    dock: {
      modules: {
        "knowledge-center": dockModuleShape({
          exists: true,
        }),
        "image-studio": dockModuleShape({
          exists: true,
        }),
        gallery: dockModuleShape({
          exists: true,
        }),
        "image-viewer": dockModuleShape({
          exists: true,
        }),
        "video-player": dockModuleShape({
          exists: false,
        }),
        calendar: dockModuleShape({
          exists: true,
        }),
      },
    },
  };
}

let state = createInitialState();

function readPersistedWorkspace() {
  try {
    const raw = localStorage.getItem(WINDOW_WORKSPACE_STORAGE_KEY);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (!o || o.v !== 1 || typeof o !== "object") return null;
    return o;
  } catch {
    return null;
  }
}

/** Nach Neustart: Chat-IDs + aktives Fenster + isOpen(B) — ohne Layout-Daten */
function applyPersistedWorkspaceSnapshot() {
  const p = readPersistedWorkspace();
  if (!p) return;

  const activeWindowId = p.activeWindowId === "B" ? "B" : "A";
  const n = (x) => {
    if (x === null || x === undefined || x === "") return null;
    const num = Number(x);
    return Number.isFinite(num) ? num : null;
  };
  const chatA = n(p.chatA);
  const chatB = n(p.chatB);
  const isOpenB = p.isOpenB !== false;

  state = {
    ...state,
    activeWindowId,
    windows: {
      A: {
        ...state.windows.A,
        activeChatId: chatA,
        isActive: activeWindowId === "A",
      },
      B: {
        ...state.windows.B,
        activeChatId: chatB,
        isOpen: isOpenB,
        isActive: activeWindowId === "B",
      },
    },
  };
}

applyPersistedWorkspaceSnapshot();

const listeners = new Set();

function persistWorkspaceToStorage() {
  try {
    const payload = {
      v: 1,
      activeWindowId: state.activeWindowId,
      chatA: state.windows.A.activeChatId,
      chatB: state.windows.B.activeChatId,
      isOpenB: state.windows.B.isOpen,
    };
    localStorage.setItem(WINDOW_WORKSPACE_STORAGE_KEY, JSON.stringify(payload));
  } catch (e) {
    console.warn("[window-state] persistWorkspaceToStorage failed:", e);
  }
}

function assertWindowId(id) {
  if (id !== "A" && id !== "B") {
    throw new Error(`Invalid window id: ${id}`);
  }
}

function emit() {
  const snap = cloneState(state);
  for (const fn of listeners) {
    try {
      fn(snap);
    } catch (e) {
      console.error("[window-state] listener error:", e);
    }
  }
  try {
    window.dispatchEvent(new CustomEvent("janus:window-state", { detail: snap }));
  } catch {
    /* ignore */
  }
  persistWorkspaceToStorage();
}

function assertDockModuleId(moduleId) {
  if (typeof moduleId !== "string" || !moduleId.trim()) {
    throw new Error(`Invalid dock module id: ${moduleId}`);
  }
}

/**
 * Maps logical id stem to the primary pane element id, e.g. "user-input" -> "user-input-A".
 * For arbitrary window: use with second arg in a later sprint.
 */
export function paneId(baseId, windowId = PRIMARY_WINDOW_ID) {
  assertWindowId(windowId);
  return `${baseId}-${windowId}`;
}

export function getWindowState() {
  return cloneState(state);
}

/** Aktives Fenster (Fokus für Sidebar → Chat-Laden, Composer). */
export function getActiveWindowId() {
  return state.activeWindowId;
}

/** Geladener Chat pro Fenster (Quelle für sendMessage / API chat_id). */
export function getActiveChatIdForWindow(windowId) {
  assertWindowId(windowId);
  const id = state.windows[windowId]?.activeChatId;
  return id == null ? null : id;
}

export function subscribeWindowState(fn) {
  if (typeof fn !== "function") return () => {};
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function setActiveWindow(windowId) {
  assertWindowId(windowId);
  state = {
    ...state,
    activeWindowId: windowId,
    windows: {
      A: { ...state.windows.A, isActive: windowId === "A" },
      B: { ...state.windows.B, isActive: windowId === "B" },
    },
  };
  emit();
  syncActiveWindowDom();
}

export function setChatForWindow(windowId, chatId) {
  assertWindowId(windowId);
  state = {
    ...state,
    windows: {
      ...state.windows,
      [windowId]: { ...state.windows[windowId], activeChatId: chatId },
    },
  };
  emit();
}

function normalizeLlmOverride(val) {
  if (val === "" || val === undefined || val === null) return null;
  return String(val);
}

export function setWindowProvider(windowId, val) {
  assertWindowId(windowId);
  const provider = normalizeLlmOverride(val);
  state = {
    ...state,
    windows: {
      ...state.windows,
      [windowId]: { ...state.windows[windowId], provider },
    },
  };
  emit();
}

export function setWindowModel(windowId, val) {
  assertWindowId(windowId);
  const modelId = normalizeLlmOverride(val);
  state = {
    ...state,
    windows: {
      ...state.windows,
      [windowId]: { ...state.windows[windowId], modelId },
    },
  };
  emit();
}

export function setWindowOpen(windowId, isOpen) {
  assertWindowId(windowId);
  const open = !!isOpen;
  state = {
    ...state,
    windows: {
      ...state.windows,
      [windowId]: {
        ...state.windows[windowId],
        isOpen: open,
        minimized: open ? false : state.windows[windowId].minimized,
      },
    },
  };
  emit();
}

export function setWindowMinimized(windowId, minimized) {
  assertWindowId(windowId);
  const nextMin = !!minimized;
  let nextActive = state.activeWindowId;
  const winA = state.windows.A;
  const winB = state.windows.B;

  if (nextMin && state.activeWindowId === windowId) {
    if (windowId === "A" && winB.isOpen && !winB.minimized) nextActive = "B";
    if (windowId === "B" && !winA.minimized) nextActive = "A";
  }

  state = {
    ...state,
    activeWindowId: nextActive,
    windows: {
      A: {
        ...state.windows.A,
        isActive: nextActive === "A",
        ...(windowId === "A" ? { minimized: nextMin } : {}),
      },
      B: {
        ...state.windows.B,
        isActive: nextActive === "B",
        ...(windowId === "B" ? { minimized: nextMin } : {}),
      },
    },
  };
  emit();
  syncActiveWindowDom();
}

export function setLayout(layout) {
  if (layout !== "split" && layout !== "single") {
    throw new Error(`Invalid layout: ${layout}`);
  }
  state = { ...state, layout };
  emit();
}

export function getDockModuleState(moduleId) {
  assertDockModuleId(moduleId);
  const m = state.dock?.modules?.[moduleId];
  return m ? { ...m } : null;
}

/**
 * Registriert oder aktualisiert ein Dock-Modul inkl. MCL-Metadaten (type, payload, zIndex, position, size).
 * Setzt immer `exists: true`.
 */
export function registerDockModule(moduleId, config) {
  assertDockModuleId(moduleId);
  if (config != null && typeof config !== "object") {
    throw new Error("[window-state] registerDockModule: config must be a plain object");
  }
  const prev = state.dock.modules[moduleId] || dockModuleShape();
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: { ...prev, ...(config || {}), exists: true },
      },
    },
  };
  emit();
}

/** Dynamischer Z-Stack (MCL): höherer Wert = weiter vorne. */
export function updateDockModuleZIndex(moduleId, z) {
  assertDockModuleId(moduleId);
  const zi = Number(z);
  if (!Number.isFinite(zi)) {
    throw new Error(`[window-state] Invalid z-index: ${z}`);
  }
  const prev = state.dock.modules[moduleId] || dockModuleShape({ exists: true });
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: { ...prev, zIndex: Math.round(zi) },
      },
    },
  };
  emit();
}

export function setDockModuleExists(moduleId, exists) {
  assertDockModuleId(moduleId);
  const prev = state.dock.modules[moduleId] || dockModuleShape();
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: { ...prev, exists: !!exists },
      },
    },
  };
  emit();
}

export function dockOpen(moduleId) {
  assertDockModuleId(moduleId);
  const prev = state.dock.modules[moduleId] || dockModuleShape({ exists: true });
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: { ...prev, exists: true, isOpen: true, minimized: false },
      },
    },
  };
  emit();
}

export function dockMinimize(moduleId, minimized = true) {
  assertDockModuleId(moduleId);
  const prev = state.dock.modules[moduleId] || dockModuleShape({ exists: true });
  const min = !!minimized;
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: {
          ...prev,
          exists: true,
          isOpen: min ? true : prev.isOpen || true,
          minimized: min,
        },
      },
    },
  };
  emit();
}

export function dockClose(moduleId) {
  assertDockModuleId(moduleId);
  const prev = state.dock.modules[moduleId] || dockModuleShape({ exists: true });
  state = {
    ...state,
    dock: {
      ...state.dock,
      modules: {
        ...state.dock.modules,
        [moduleId]: { ...prev, exists: true, isOpen: false, minimized: false },
      },
    },
  };
  emit();
}

export function openSecondWindow() {
  setWindowOpen("B", true);
}

export function closeSecondWindow() {
  setWindowOpen("B", false);
  setActiveWindow("A");
}

export function syncActiveWindowDom() {
  const winA = document.getElementById("chat-window-A");
  const winB = document.getElementById("chat-window-B");
  if (!winA || !winB) return;

  const active = state.activeWindowId;
  winA.classList.toggle("window-active", active === "A");
  winB.classList.toggle("window-active", active === "B");
  winA.setAttribute("aria-current", active === "A" ? "true" : "false");
  winB.setAttribute("aria-current", active === "B" ? "true" : "false");
}

function onChatWindowPointerDown(windowId) {
  return () => {
    try {
      setActiveWindow(windowId);
    } catch (e) {
      console.warn("[window-state]", e);
    }
  };
}

export function initWindowStateDom() {
  const winA = document.getElementById("chat-window-A");
  const winB = document.getElementById("chat-window-B");
  if (!winA || !winB) return;

  winA.addEventListener("pointerdown", onChatWindowPointerDown("A"));
  winB.addEventListener("pointerdown", onChatWindowPointerDown("B"));
  syncActiveWindowDom();
}

function boot() {
  initWindowStateDom();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
}
