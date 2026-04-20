import { API_BASE_URL } from "./config.js";
import {
  dockClose,
  dockMinimize,
  dockOpen,
  getDockModuleState,
  setDockModuleExists,
  subscribeWindowState,
} from "./window-state.js";
import { openModal, closeModal, bringToFront } from "./modal-api.js";

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("knowledge-center-modal");
  const modalHeader = modal?.querySelector(".dock-panel-header");
  const closeBtn = document.getElementById("close-knowledge-center-btn");
  const minimizeBtn = document.getElementById("knowledge-center-minimize-btn");
  const resetBtn = document.getElementById("knowledge-center-reset-btn");
  const list = document.getElementById("knowledge-doc-list");
  const preview = document.getElementById("knowledge-pdf-preview");
  const emptyState = document.getElementById("knowledge-preview-empty");
  const docTitleEl = document.getElementById("knowledge-header-doc-title");

  const syncHeaderDocTitle = (text) => {
    if (!docTitleEl) return;
    docTitleEl.textContent = text;
    docTitleEl.title = text;
  };

  if (!modal || !closeBtn || !list || !preview || !emptyState) {
    console.warn("Knowledge Center UI not fully available in current view.");
    return;
  }

  let isDragging = false;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  let currentDocs = [];
  let currentDocId = null;
  let currentBlobUrl = null;
  let docsLoadedOnce = false;
  const DEFAULT_GEOMETRY = Object.freeze({ w: 900, h: 1270, x: 980, y: 20 });
  const getDockTopPx = () => {
    const dock = document.getElementById("dock-bar");
    if (!dock) return window.innerHeight - 48;
    const rect = dock.getBoundingClientRect();
    return Number.isFinite(rect.top) ? rect.top : window.innerHeight - 48;
  };

  const getChatBAnchor = () => {
    const chatB = document.getElementById("chat-window-B");
    const rectB = chatB?.getBoundingClientRect?.();
    const chatBVisible =
      !!rectB &&
      Number.isFinite(rectB.left) &&
      Number.isFinite(rectB.top) &&
      rectB.width > 0 &&
      rectB.height > 0;
    if (chatBVisible) {
      return {
        x: Math.round(rectB.left),
        y: Math.round(rectB.top),
      };
    }
    // Fallback when B is hidden: reconstruct B anchor from A geometry.
    const chatA = document.getElementById("chat-window-A");
    const rectA = chatA?.getBoundingClientRect?.();
    const chatAVisible =
      !!rectA &&
      Number.isFinite(rectA.left) &&
      Number.isFinite(rectA.top) &&
      rectA.width > 0 &&
      rectA.height > 0;
    if (!chatAVisible) return null;
    return {
      x: Math.round(rectA.left + rectA.width + 1),
      y: Math.round(rectA.top),
    };
  };

  /** Nur fürs Dragging begrenzen; initiale Dock-Position bleibt exakt auf Chat-B-Ecke. */
  const clampToViewport = (x, y) => {
    const width = modal.offsetWidth || 600;
    const height = modal.offsetHeight || 700;
    const maxX = Math.max(0, window.innerWidth - width);
    const maxY = Math.max(0, window.innerHeight - height);
    return {
      x: Math.min(Math.max(x, 0), maxX),
      y: Math.min(Math.max(y, 0), maxY),
    };
  };

  const placeWidgetNextToChat = () => {
    const anchor = getChatBAnchor();
    const rawX = anchor?.x ?? (Number(modal.dataset.defaultX) || DEFAULT_GEOMETRY.x);
    const rawY = anchor?.y ?? (Number(modal.dataset.defaultY) || DEFAULT_GEOMETRY.y);
    const w = Number(modal.dataset.defaultW) || DEFAULT_GEOMETRY.w;
    const dockTop = getDockTopPx();
    const topPx = rawY;
    const h = Math.max(420, Math.floor(dockTop - topPx));
    modal.style.width = `${w}px`;
    modal.style.height = `${h}px`;
    modal.style.left = `${rawX}px`;
    modal.style.top = `${rawY}px`;
    modal.dataset.positioned = "true";
    modal.dataset.defaultH = String(h);
  };

  const setPreview = async (doc) => {
    if (!doc || !doc.id) {
      currentDocId = null;
      preview.style.display = "none";
      preview.removeAttribute("src");
      emptyState.style.display = "flex";
      emptyState.textContent = "Kein Dokument ausgewählt.";
      syncHeaderDocTitle("Kein Dokument ausgewählt");
      if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
        currentBlobUrl = null;
      }
      return;
    }

    currentDocId = doc.id;
    const filename = doc.filename || `Dokument ${doc.id}`;
    preview.style.display = "none";
    emptyState.style.display = "flex";
    emptyState.textContent = `Lade Vorschau: ${filename}`;
    syncHeaderDocTitle(filename);

    list.querySelectorAll(".knowledge-doc-item").forEach((item) => {
      item.classList.toggle("active", Number(item.dataset.docId) === Number(doc.id));
    });

    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/files/${doc.id}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const blob = await response.blob();
      if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
      }

      currentBlobUrl = URL.createObjectURL(blob);
      preview.src = `${currentBlobUrl}#zoom=74`;
      preview.style.display = "block";
      emptyState.style.display = "none";
    } catch (error) {
      console.error("Knowledge Center: PDF konnte nicht geladen werden", error);
      preview.style.display = "none";
      emptyState.style.display = "flex";
      emptyState.textContent = "PDF konnte nicht geladen werden.";
      syncHeaderDocTitle(`${filename} — Fehler beim Laden`);
    }
  };

  const currentDockState = () =>
    getDockModuleState("knowledge-center") || { isOpen: false, minimized: false, exists: true };

  const renderDocs = (docs, preferredDocId) => {
    list.innerHTML = "";

    if (!Array.isArray(docs) || docs.length === 0) {
      const li = document.createElement("li");
      li.textContent = "Keine Dokumente vorhanden.";
      li.style.color = "#6b7280";
      list.appendChild(li);
      setPreview(null);
      return;
    }

    docs.forEach((doc) => {
      const li = document.createElement("li");
      li.className = "knowledge-doc-item";
      li.dataset.docId = String(doc.id);

      const name = document.createElement("div");
      name.className = "knowledge-doc-name";
      name.textContent = doc.filename;
      li.appendChild(name);

      li.addEventListener("click", () => {
        setPreview(doc);
      });
      list.appendChild(li);
    });

    const selected = docs.find((doc) => Number(doc.id) === Number(preferredDocId))
      || docs.find((doc) => Number(doc.id) === Number(currentDocId))
      || docs[0];

    setPreview(selected);
  };

  const loadDocs = async (preferredDocId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/documents`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const docs = await response.json();
      currentDocs = Array.isArray(docs) ? docs : [];
      renderDocs(currentDocs, preferredDocId);
    } catch (error) {
      console.error("Knowledge Center: Dokumente konnten nicht geladen werden", error);
      list.innerHTML = "<li style=\"color:#b91c1c\">Fehler beim Laden der Dokumente.</li>";
      void setPreview(null);
      syncHeaderDocTitle("Dokumente konnten nicht geladen werden");
    }
  };

  const openKnowledgeCenter = async (documentId, forceReload = false) => {
    openModal({ type: "document", payload: { docId: documentId } });
    placeWidgetNextToChat();
    // 💎 FILE-GUARD SYNC: Always reload documents on modal open to trigger Backend File Guard
    await loadDocs(documentId);
  };

  const closeKnowledgeCenter = ({ release = false } = {}) => {
    closeModal("knowledge-center");
    if (release) modal.dataset.positioned = "false";
    if (currentBlobUrl) {
      URL.revokeObjectURL(currentBlobUrl);
      currentBlobUrl = null;
    }
  };
  const minimizeKnowledgeCenter = () => dockMinimize("knowledge-center", true);

  closeBtn.addEventListener("click", closeKnowledgeCenter);
  minimizeBtn?.addEventListener("click", minimizeKnowledgeCenter);
  resetBtn?.addEventListener("click", () => placeWidgetNextToChat());

  // NEU: Focus-to-Front bei Klick auf Panel
  modal?.addEventListener("mousedown", () => { bringToFront("knowledge-center"); });

  setDockModuleExists("knowledge-center", true);

  if (modalHeader) {
    modalHeader.addEventListener("mousedown", (event) => {
      isDragging = true;
      dragOffsetX = event.clientX - modal.offsetLeft;
      dragOffsetY = event.clientY - modal.offsetTop;
      modal.dataset.positioned = "true";
      event.preventDefault();
    });
  }

  document.addEventListener("mousemove", (event) => {
    if (!isDragging) return;
    const clamped = clampToViewport(event.clientX - dragOffsetX, event.clientY - dragOffsetY);
    modal.style.left = `${clamped.x}px`;
    modal.style.top = `${clamped.y}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
  });

  const openBridge = async (documentId, options = {}) => {
    const fromTaskbarDock = options.fromTaskbarDock === true;
    const isToggleIntent =
      !fromTaskbarDock && (documentId === null || typeof documentId === "undefined");

    if (isToggleIntent && currentDockState().isOpen && !currentDockState().minimized) {
      dockMinimize("knowledge-center", true);
      return;
    }

    await openKnowledgeCenter(documentId);
  };

  window.onKnowledgeModalOpen = (documentId) => {
    void openBridge(documentId);
  };
  window.openJanusKnowledge = (documentId) => {
    void openBridge(documentId);
  };

  window.addEventListener("open-knowledge-center", (e) => {
    const documentId = e?.detail?.documentId;
    const fromTaskbarDock = e?.detail?.fromTaskbarDock === true;
    void openBridge(documentId, { fromTaskbarDock });
  });

  let prevKnowledgeVisible = false;
  let lastProcessedDocId = null;

  const syncKnowledgeFromDockState = () => {
    const m = getDockModuleState("knowledge-center");
    const visible = !!m?.isOpen && !m?.minimized;

    modal.classList.toggle("dock-panel--open", visible);

    document
      .getElementById("btn-react-knowledge")
      ?.classList.toggle("sidebar-nav-item--active", visible);

    if (visible && !prevKnowledgeVisible) {
      placeWidgetNextToChat();
    }

    // 💎 FILE-GUARD SYNC: Always reload documents when modal becomes visible
    // This ensures the Backend File Guard (Task 038) can clean up ghost files
    if (visible && !prevKnowledgeVisible) {
      const currentDocId = m?.payload?.docId ?? null;
      void loadDocs(currentDocId);
      lastProcessedDocId = currentDocId;
    } else if (visible) {
      // Also reload if docId changes while already visible
      const currentDocId = m?.payload?.docId ?? null;
      if (currentDocId !== lastProcessedDocId) {
        void loadDocs(currentDocId);
        lastProcessedDocId = currentDocId;
      }
    }

    prevKnowledgeVisible = visible;
  };

  subscribeWindowState(() => syncKnowledgeFromDockState());
  syncKnowledgeFromDockState();

  requestAnimationFrame(() => {
    if (modal.dataset.positioned !== "true") {
      placeWidgetNextToChat();
    }
  });
});
