import {
  dockClose,
  dockMinimize,
  getDockModuleState,
  subscribeWindowState,
} from "./window-state.js";
import { openModal, bringToFront } from "./modal-api.js";

document.addEventListener("DOMContentLoaded", () => {
  const galleryView = document.getElementById("gallery-view");
  const galleryWindow = document.getElementById("gallery-window");
  const galleryNavBtn = document.getElementById("sidebar-nav-gallery");
  const closeGalleryBtn = document.getElementById("close-gallery-btn");
  const minimizeGalleryBtn = document.getElementById("gallery-minimize-btn");
  const resetGalleryBtn = document.getElementById("gallery-reset-btn");
  const galleryContent = document.getElementById("gallery-content");

  let prevGalleryVisible = false;

  function isGalleryPanelVisible() {
    const m = getDockModuleState("gallery");
    return !!(m?.isOpen && !m?.minimized);
  }

  function syncGalleryNav() {
    if (!galleryNavBtn) return;
    const visible = isGalleryPanelVisible();
    galleryNavBtn.setAttribute("aria-pressed", visible ? "true" : "false");
    galleryNavBtn.classList.toggle("sidebar-nav-item--active", visible);
  }

  function syncGalleryFromDockState() {
    const visible = isGalleryPanelVisible();
    if (galleryView) {
      galleryView.style.display = visible ? "flex" : "none";
    }
    if (visible && !prevGalleryVisible) {
      loadImages();
    }
    prevGalleryVisible = visible;
    syncGalleryNav();
  }

  async function loadImages() {
    if (!galleryContent) return;
    try {
      const response = await fetch("/api/images");

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const responseText = await response.text();
        throw new TypeError(
          `Falscher Antworttyp vom Server erhalten. Erwartet: JSON, Bekommen: HTML/Text. Antwort: ${responseText.substring(0, 100)}...`
        );
      }

      if (!response.ok) {
        throw new Error(`HTTP-Fehler! Status: ${response.status}`);
      }

      const data = await response.json();

      galleryContent.innerHTML = "";
      if (data.images && data.images.length > 0) {
        data.images.forEach((imageUrl) => {
          const img = document.createElement("img");
          img.src = imageUrl;
          img.alt = "Generiertes Bild";
          img.addEventListener("click", () => {
            window.open(imageUrl, "_blank");
          });
          galleryContent.appendChild(img);
        });
      } else {
        galleryContent.innerHTML = '<p style="color: #ccc;">Noch keine Bilder erstellt.</p>';
      }
    } catch (error) {
      console.error("Fehler beim Laden der Bilder:", error);
      galleryContent.innerHTML =
        '<p style="color: #f88;">Bilder konnten nicht geladen werden. Prüfen Sie die Entwicklerkonsole für Details.</p>';
    }
  }

  subscribeWindowState(() => syncGalleryFromDockState());
  syncGalleryFromDockState();

  if (galleryNavBtn) {
    galleryNavBtn.addEventListener("click", () => {
      if (isGalleryPanelVisible()) {
        dockMinimize("gallery", true);
      } else {
        openModal({ type: "gallery" });
      }
    });
  }

  if (minimizeGalleryBtn) {
    minimizeGalleryBtn.addEventListener("click", () => {
      dockMinimize("gallery", true);
    });
  }

  if (closeGalleryBtn) {
    closeGalleryBtn.addEventListener("click", () => {
      dockClose("gallery");
    });
  }
  if (resetGalleryBtn && galleryWindow) {
    resetGalleryBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      galleryWindow.style.left = "0px";
      galleryWindow.style.top = "0px";
      galleryWindow.style.width = "";
      galleryWindow.style.height = "";
    });
  }

  // --- Drag & Drop Funktionalität ---
  let isDragging = false;
  let offsetX;
  let offsetY;

  const header = document.getElementById("gallery-header");

  if (header && galleryWindow) {
    header.addEventListener("mousedown", (e) => {
      if (e.target.closest("button")) return;
      bringToFront("gallery");
      isDragging = true;
      offsetX = e.clientX - galleryWindow.offsetLeft;
      offsetY = e.clientY - galleryWindow.offsetTop;
      e.preventDefault();
    });
  }

  document.addEventListener("mousemove", (e) => {
    if (!isDragging || !galleryWindow) return;

    let newX = e.clientX - offsetX;
    let newY = e.clientY - offsetY;

    const maxX = window.innerWidth - galleryWindow.offsetWidth;
    const maxY = window.innerHeight - galleryWindow.offsetHeight;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    galleryWindow.style.left = `${newX}px`;
    galleryWindow.style.top = `${newY}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
  });

  if (galleryWindow) {
    const resizeHandle = document.createElement("div");
    resizeHandle.style.width = "15px";
    resizeHandle.style.height = "15px";
    resizeHandle.style.position = "absolute";
    resizeHandle.style.right = "0";
    resizeHandle.style.bottom = "0";
    resizeHandle.style.cursor = "se-resize";
    galleryWindow.appendChild(resizeHandle);

    let isResizing = false;

    resizeHandle.addEventListener("mousedown", function (e) {
      isResizing = true;
      e.stopPropagation();
      e.preventDefault();
    });

    document.addEventListener("mousemove", function (e) {
      if (!isResizing) return;

      const newWidth = e.clientX - galleryWindow.offsetLeft;
      const newHeight = e.clientY - galleryWindow.offsetTop;

      galleryWindow.style.width = `${Math.max(300, newWidth)}px`;
      galleryWindow.style.height = `${Math.max(200, newHeight)}px`;
    });

    document.addEventListener("mouseup", function () {
      isResizing = false;
    });
  }

  window.isGalleryVisible = () => isGalleryPanelVisible();
});
