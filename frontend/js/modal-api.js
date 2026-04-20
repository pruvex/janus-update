/**
 * Janus MCL (Modal Contract Layer) — stateless facade.
 * Single source of truth: window-state.js (dock.modules). This module only validates, routes, and applies Z-stack.
 *
 * @see documentation/Planned Features/UNIVERSAL_MODAL_SYSTEM_DIAMOND_DOSSIER.md
 */

import {
  dockClose,
  dockOpen,
  getDockModuleState,
  getWindowState,
  registerDockModule,
  subscribeWindowState,
  updateDockModuleZIndex,
} from "./window-state.js";

/** Contract type → Dock-Modul-ID (bestehende Hosts + geplante Player). */
export const RENDERER_MAP = Object.freeze({
  document: "knowledge-center",
  "image-studio": "image-studio",
  gallery: "gallery",
  video: "video-player",
  image: "image-viewer",
});

const SUPPORTED_TYPES = Object.freeze(Object.keys(RENDERER_MAP));
const YOUTUBE_URL_RE = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?|youtu\.be\/|youtube\.com\/embed\/)/i;
const VIMEO_URL_RE = /(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/|player\.vimeo\.com\/video\/)/i;

/** Basis-Z; jede Öffnung / Fokussierung erhöht den globalen Zähler (kein persistierter Modal-Stack im MCL). */
const Z_BASE = 100;
let zCounter = Z_BASE;

function bumpZIndex() {
  zCounter += 1;
  return zCounter;
}

/** Dock-Modul-ID → DOM-Host (für Z-Index-Sync). */
const DOCK_HOST_ELEMENT_IDS = Object.freeze({
  "knowledge-center": "knowledge-center-modal",
  "image-studio": "image-studio-modal",
  gallery: "gallery-window",
  "image-viewer": "image-modal",
  "video-player": "video-player-modal",
  "transcript": "transcript-modal",
});

function emitModalEvent(modalId, event, context = {}) {
  try {
    window.dispatchEvent(
      new CustomEvent("janus:modal-event", {
        detail: { modalId, event, context },
      })
    );
  } catch {
    /* ignore */
  }
}

function getOpenModulesOrderedByAge() {
  const modules = getWindowState()?.dock?.modules || {};
  return Object.entries(modules)
    .filter(([, mod]) => !!mod?.isOpen && !mod?.minimized)
    .sort((a, b) => Number((a[1] || {}).zIndex || 0) - Number((b[1] || {}).zIndex || 0));
}

function maybeApplySoftModalLimit(nextModuleId) {
  const openNow = getOpenModulesOrderedByAge();
  const openIds = new Set(openNow.map(([id]) => id));
  if (openIds.has(nextModuleId)) return;
  if (openNow.length < 4) return;
  const oldest = openNow[0]?.[0];
  if (!oldest || oldest === nextModuleId) return;
  registerDockModule(oldest, { isOpen: true, minimized: true });
  emitModalEvent(oldest, "minimized", { reason: "fifo-soft-limit" });
}

function assertModalId(modalId) {
  if (typeof modalId !== "string" || !modalId.trim()) {
    throw new Error(`[MCL] Invalid modalId: ${modalId}`);
  }
}

/**
 * Wendet `dock.modules[*].zIndex` auf die bekannten Panel-Hosts an.
 */
function applyDockZIndicesFromState(snap) {
  const modules = snap?.dock?.modules || {};
  for (const [moduleId, elId] of Object.entries(DOCK_HOST_ELEMENT_IDS)) {
    const el = document.getElementById(elId);
    if (!el) continue;
    const mod = modules[moduleId];
    const z = mod?.zIndex;
    if (Number.isFinite(z)) {
      el.style.zIndex = String(z);
    }
  }
}

function initMclZStackSync() {
  const run = () => applyDockZIndicesFromState(getWindowState());
  subscribeWindowState((snap) => applyDockZIndicesFromState(snap));
  if (typeof document === "undefined") return;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
  } else {
    run();
  }
}

initMclZStackSync();
if (typeof window !== "undefined") {
  window.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const topmost = getOpenModulesOrderedByAge().at(-1)?.[0];
    if (!topmost) return;
    closeModal(topmost);
  });
}

/**
 * Öffnet ein Modal gemäß MCL-Request. Delegiert komplett an window-state.
 * @param {{ type: string, payload?: unknown, options?: { position?: { x?: number, y?: number }, size?: { w?: number, h?: number } } }} request
 * @returns {string | null} Dock-Modul-ID oder null bei Fehler
 */
export function openModal(request) {
  if (!request || typeof request.type !== "string") {
    console.error("[MCL] openModal: request.type (string) is required");
    return null;
  }
  const t = request.type.trim();
  if (!SUPPORTED_TYPES.includes(t)) {
    console.error(`[MCL] Unsupported modal type: ${t}`);
    return null;
  }
  const moduleId = RENDERER_MAP[t];
  if (!moduleId) {
    console.error(`[MCL] No renderer mapping for type: ${t}`);
    return null;
  }

  maybeApplySoftModalLimit(moduleId);
  const z = bumpZIndex();
  const opts = request.options && typeof request.options === "object" ? request.options : {};
  const existing = getDockModuleState(moduleId);

  // UX-Fix: if video modal is already visible, update payload + focus only.
  if (moduleId === "video-player" && existing?.isOpen && !existing?.minimized) {
    registerDockModule(moduleId, {
      type: t,
      payload: request.payload ?? existing.payload ?? null,
      zIndex: z,
      position: opts.position ?? existing.position ?? null,
      size: opts.size ?? existing.size ?? null,
    });
    bringToFront(moduleId);
    emitModalEvent(moduleId, "updated", { type: t, payload: request.payload });
    return moduleId;
  }

  registerDockModule(moduleId, {
    type: t,
    payload: request.payload ?? null,
    zIndex: z,
    position: opts.position ?? null,
    size: opts.size ?? null,
  });
  dockOpen(moduleId);
  applyDockZIndicesFromState(getWindowState());
  emitModalEvent(moduleId, "opened", { type: t, payload: request.payload });
  return moduleId;
}

export function isVideoUrl(url) {
  const s = String(url || "").trim();
  if (!s) return false;
  return YOUTUBE_URL_RE.test(s) || VIMEO_URL_RE.test(s);
}

export function closeModal(modalId) {
  assertModalId(modalId);
  dockClose(modalId.trim());
  applyDockZIndicesFromState(getWindowState());
  emitModalEvent(modalId.trim(), "closed", { reason: "api" });
}

/**
 * Fokus / Z-Order: erhöht zIndex für das Dock-Modul (Basis {@link Z_BASE}).
 */
export function bringToFront(modalId) {
  assertModalId(modalId);
  const id = modalId.trim();
  const m = getDockModuleState(id);
  if (!m) {
    console.warn(`[MCL] bringToFront: unknown module "${id}"`);
    return;
  }
  const z = bumpZIndex();
  updateDockModuleZIndex(id, z);
  applyDockZIndicesFromState(getWindowState());
  emitModalEvent(id, "focus", {});
}

export { Z_BASE };

// Global export for legacy code compatibility
if (typeof window !== "undefined") {
  window.openModal = openModal;
  window.closeModal = closeModal;
  window.bringToFront = bringToFront;
}
