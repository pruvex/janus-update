import {
  dockOpen,
  dockMinimize,
  getDockModuleState,
  getWindowState,
  setActiveWindow,
  setDockModuleExists,
  setWindowMinimized,
  setWindowOpen,
  subscribeWindowState,
} from "./window-state.js";
import { openModal } from "./modal-api.js";

const KNOWLEDGE_PANEL_DEFAULT = Object.freeze({
  w: 900,
  h: 1270,
  x: 980,
  y: 20,
});

/** Höhe der #dock-bar; Vollflächen-UI (z. B. Image Studio) = viewport − dieser Wert. */
export const DOCK_BAR_HEIGHT_PX = 48;

export function getDockBarHeightPx() {
  const dock = document.getElementById("dock-bar");
  if (!dock) return DOCK_BAR_HEIGHT_PX;
  const h = dock.getBoundingClientRect().height;
  return Number.isFinite(h) && h > 0 ? Math.round(h) : DOCK_BAR_HEIGHT_PX;
}

/**
 * Effektive „untere Kante“ des Arbeitsbereichs oberhalb der Taskleiste.
 * Image Studio: registrierte Nutzhöhe entspricht 100vh − getDockBarHeightPx() (siehe image-studio.css).
 */
export function getImageStudioContentHeightCapPx() {
  return Math.max(0, window.innerHeight - getDockBarHeightPx());
}

function getDockTopPx() {
  const dock = document.getElementById("dock-bar");
  if (!dock) return window.innerHeight - DOCK_BAR_HEIGHT_PX;
  const rect = dock.getBoundingClientRect();
  return Number.isFinite(rect.top) ? rect.top : window.innerHeight - DOCK_BAR_HEIGHT_PX;
}

function getChatBAnchor() {
  const chatB = document.getElementById("chat-window-B");
  if (!chatB) return null;
  const rect = chatB.getBoundingClientRect();
  if (!Number.isFinite(rect.left) || !Number.isFinite(rect.top)) return null;
  return {
    x: Math.round(rect.left),
    y: Math.round(rect.top),
  };
}

function ensureKnowledgePanelGeometry() {
  const panel = document.getElementById("knowledge-center-modal");
  if (!panel) return;
  const anchor = getChatBAnchor();
  const x = anchor?.x ?? KNOWLEDGE_PANEL_DEFAULT.x;
  const y = anchor?.y ?? KNOWLEDGE_PANEL_DEFAULT.y;
  const dockTop = getDockTopPx();
  const h = Math.max(420, Math.floor(dockTop - y));
  panel.style.width = `${KNOWLEDGE_PANEL_DEFAULT.w}px`;
  panel.style.height = `${h}px`;
  panel.style.left = `${x}px`;
  panel.style.top = `${y}px`;
  panel.dataset.defaultX = String(x);
  panel.dataset.defaultY = String(y);
  panel.dataset.defaultW = String(KNOWLEDGE_PANEL_DEFAULT.w);
  panel.dataset.defaultH = String(h);
}

function applyHostVisibility(state) {
  const hostA = document.getElementById("chat-window-host-A");
  const hostB = document.getElementById("chat-window-host-B");
  if (hostA) {
    hostA.style.display = state.windows.A.minimized ? "none" : "";
  }
  if (hostB) {
    const hideB = state.windows.B.minimized || !state.windows.B.isOpen;
    hostB.style.display = hideB ? "none" : "";
  }
}

function applyDockUi(state) {
  const btnA = document.getElementById("dock-chat-a");
  const btnB = document.getElementById("dock-chat-b");
  if (btnA && btnB) {
    btnA.classList.toggle("is-active", state.activeWindowId === "A" && !state.windows.A.minimized);
    btnB.classList.toggle("is-active", state.activeWindowId === "B" && !state.windows.B.minimized);
    btnA.classList.toggle("is-minimized", state.windows.A.minimized);
    btnB.classList.toggle("is-minimized", state.windows.B.minimized || !state.windows.B.isOpen);
    btnA.style.display = state.windows.A.minimized ? "" : "none";
    btnB.style.display = state.windows.B.minimized ? "" : "none";
  }

  const btnKnowledge = document.getElementById("dock-knowledge-center");
  if (btnKnowledge) {
    const km = state.dock?.modules?.["knowledge-center"] || getDockModuleState("knowledge-center");
    const kOpen = !!km?.isOpen;
    const kMin = !!km?.minimized;
    btnKnowledge.classList.toggle("is-minimized", kMin);
    btnKnowledge.classList.toggle("is-active", kOpen && !kMin);
    btnKnowledge.style.display = kOpen && kMin ? "" : "none";
  }

  const btnImageStudio = document.getElementById("dock-image-studio");
  if (btnImageStudio) {
    const im = state.dock?.modules?.["image-studio"] || getDockModuleState("image-studio");
    const iOpen = !!im?.isOpen;
    const iMin = !!im?.minimized;
    btnImageStudio.classList.toggle("is-minimized", iMin);
    btnImageStudio.classList.toggle("is-active", iOpen && !iMin);
    btnImageStudio.style.display = iOpen && iMin ? "" : "none";
  }

  const btnGallery = document.getElementById("dock-gallery");
  if (btnGallery) {
    const gm = state.dock?.modules?.gallery || getDockModuleState("gallery");
    const gOpen = !!gm?.isOpen;
    const gMin = !!gm?.minimized;
    btnGallery.classList.toggle("is-minimized", gMin);
    btnGallery.classList.toggle("is-active", gOpen && !gMin);
    btnGallery.style.display = gOpen && gMin ? "" : "none";
  }

  const btnVideo = document.getElementById("dock-video-player");
  if (btnVideo) {
    const vm = state.dock?.modules?.["video-player"] || getDockModuleState("video-player");
    const vOpen = !!vm?.isOpen;
    const vMin = !!vm?.minimized;
    btnVideo.classList.toggle("is-minimized", vMin);
    btnVideo.classList.toggle("is-active", vOpen && !vMin);
    btnVideo.style.display = vOpen && vMin ? "" : "none";
  }

  const btnMail = document.getElementById("dock-mail");
  if (btnMail) {
    const mm = state.dock?.modules?.mail || getDockModuleState("mail");
    const mOpen = !!mm?.isOpen;
    const mMin = !!mm?.minimized;
    btnMail.classList.toggle("is-minimized", mMin);
    btnMail.classList.toggle("is-active", mOpen && !mMin);
    btnMail.style.display = mOpen && mMin ? "" : "none";
  }

  const kcPanel = document.getElementById("knowledge-center-modal");
  if (kcPanel) {
    const km = state.dock?.modules?.["knowledge-center"] || getDockModuleState("knowledge-center");
    kcPanel.classList.toggle("dock-panel--open", !!km?.isOpen && !km?.minimized);
  }

  const mailPanel = document.getElementById("mail-modal");
  if (mailPanel) {
    const mm = state.dock?.modules?.mail || getDockModuleState("mail");
    mailPanel.classList.toggle("dock-panel--open", !!mm?.isOpen && !mm?.minimized);
  }
}

function bindDockModuleButtons() {
  const btnKnowledge = document.getElementById("dock-knowledge-center");
  btnKnowledge?.addEventListener("click", () => {
    openModal({ type: "document" });
  });

  const btnImageStudio = document.getElementById("dock-image-studio");
  btnImageStudio?.addEventListener("click", () => {
    openModal({ type: "image-studio" });
  });

  const btnGallery = document.getElementById("dock-gallery");
  btnGallery?.addEventListener("click", () => {
    openModal({ type: "gallery" });
  });

  const btnVideo = document.getElementById("dock-video-player");
  btnVideo?.addEventListener("click", () => {
    const vm = getDockModuleState("video-player");
    if (vm?.payload) {
      openModal({ type: "video", payload: vm.payload });
      return;
    }
    openModal({ type: "video" });
  });

  const btnMail = document.getElementById("dock-mail");
  btnMail?.addEventListener("click", () => {
    openModal({ type: "mail" });
  });
}

function bindDockEvents() {
  const btnA = document.getElementById("dock-chat-a");
  const btnB = document.getElementById("dock-chat-b");
  if (btnA && btnB) {
    btnA.addEventListener("click", () => {
      const state = getWindowState();
      if (state.windows.A.minimized) {
        setWindowMinimized("A", false);
        setActiveWindow("A");
        return;
      }
      setActiveWindow("A");
    });

    btnB.addEventListener("click", () => {
      const state = getWindowState();
      if (state.windows.B.minimized) {
        setWindowOpen("B", true);
        setWindowMinimized("B", false);
        setActiveWindow("B");
        return;
      }
      if (!state.windows.B.isOpen) {
        setWindowOpen("B", true);
      }
      setActiveWindow("B");
    });
  }

  bindDockModuleButtons();
}

function syncDockFromState() {
  const state = getWindowState();
  applyHostVisibility(state);
  applyDockUi(state);
}

function initDock() {
  setDockModuleExists("knowledge-center", true);
  setDockModuleExists("image-studio", true);
  setDockModuleExists("gallery", true);
  setDockModuleExists("video-player", true);
  setDockModuleExists("calendar", true);
  setDockModuleExists("mail", true);
  ensureKnowledgePanelGeometry();
  bindDockEvents();
  subscribeWindowState((state) => {
    applyHostVisibility(state);
    applyDockUi(state);
  });
  syncDockFromState();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDock, { once: true });
  } else {
    initDock();
  }
}
