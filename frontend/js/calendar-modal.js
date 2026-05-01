/**
 * Janus Calendar Modal — MCL Dock-Modul "calendar" (TASK-058 Shell).
 * Öffnen: openModal({ type: "calendar" }) oder window.dockOpen("calendar") (modal-api).
 */

import {
  dockClose,
  dockMinimize,
  getDockModuleState,
  subscribeWindowState,
} from "./window-state.js";
import { bringToFront } from "./modal-api.js";

const MODULE_ID = "calendar";

function isCalendarPanelVisible() {
  const m = getDockModuleState(MODULE_ID);
  return !!(m?.isOpen && !m?.minimized);
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarView = document.getElementById("calendar-view");
  const calendarHost = document.getElementById("calendar-modal");
  const navBtn = document.getElementById("sidebar-nav-calendar");
  const closeBtn = document.getElementById("close-calendar-btn");
  const minimizeBtn = document.getElementById("calendar-minimize-btn");
  const resetBtn = document.getElementById("calendar-reset-btn");
  const header = document.getElementById("calendar-header");

  let prevVisible = false;

  function syncNavActive() {
    if (!navBtn) return;
    const visible = isCalendarPanelVisible();
    navBtn.setAttribute("aria-pressed", visible ? "true" : "false");
    navBtn.classList.toggle("sidebar-nav-item--active", visible);
  }

  function syncFromDockState() {
    const visible = isCalendarPanelVisible();
    if (calendarView) {
      calendarView.style.display = visible ? "flex" : "none";
    }
    if (visible && !prevVisible && calendarHost) {
      try {
        bringToFront(MODULE_ID);
      } catch {
        /* ignore */
      }
    }
    prevVisible = visible;
    syncNavActive();
  }

  subscribeWindowState(() => syncFromDockState());
  syncFromDockState();

  minimizeBtn?.addEventListener("click", () => {
    dockMinimize(MODULE_ID, true);
  });

  closeBtn?.addEventListener("click", () => {
    dockClose(MODULE_ID);
  });

  if (resetBtn && calendarHost) {
    resetBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      calendarHost.style.left = "0px";
      calendarHost.style.top = "0px";
      calendarHost.style.width = "";
      calendarHost.style.height = "";
    });
  }

  let isDragging = false;
  let offsetX = 0;
  let offsetY = 0;

  if (header && calendarHost) {
    header.addEventListener("mousedown", (e) => {
      if (e.target.closest("button")) return;
      bringToFront(MODULE_ID);
      isDragging = true;
      offsetX = e.clientX - calendarHost.offsetLeft;
      offsetY = e.clientY - calendarHost.offsetTop;
      e.preventDefault();
    });
  }

  document.addEventListener("mousemove", (e) => {
    if (!isDragging || !calendarHost) return;
    let newX = e.clientX - offsetX;
    let newY = e.clientY - offsetY;
    const maxX = window.innerWidth - calendarHost.offsetWidth;
    const maxY = window.innerHeight - calendarHost.offsetHeight;
    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));
    calendarHost.style.left = `${newX}px`;
    calendarHost.style.top = `${newY}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
  });
});
