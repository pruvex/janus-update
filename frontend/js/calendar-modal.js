/**
 * Janus Calendar Modal — TASK-058 Phase 1–2 (MCL Dock-Modul "calendar").
 */

import {
  dockClose,
  dockMinimize,
  getDockModuleState,
  subscribeWindowState,
} from "./window-state.js";
import { bringToFront } from "./modal-api.js";
import { API_BASE_URL } from "./config.js";

const MODULE_ID = "calendar";

/** @type {Array<Record<string, unknown>>} */
let localEvents = [];
/** @type {Array<{event_a?: string, event_b?: string}>} */
let localConflicts = [];
/** @type {Set<string>} */
let conflictIds = new Set();
/** @type {string | null} */
let editingEventId = null;
let filterPreset = "week"; // today | week | month | custom
/** ISO date strings YYYY-MM-DD for custom preset */
let customRangeStartStr = "";
let customRangeEndStr = "";

function isCalendarPanelVisible() {
  const m = getDockModuleState(MODULE_ID);
  return !!(m?.isOpen && !m?.minimized);
}

function normEvent(ev) {
  const raw = /** @type {Record<string, unknown>} */ (ev || {});
  return {
    id: String(raw.id ?? ""),
    title: String(raw.title ?? raw.summary ?? "(Kein Titel)"),
    start: raw.start,
    end: raw.end,
    description: raw.description ?? null,
    location: raw.location ?? null,
    attendees: Array.isArray(raw.attendees) ? raw.attendees : [],
    source: raw.source ?? "google",
    recurrence_rule: raw.recurrence_rule ?? null,
    is_all_day: !!raw.is_all_day,
  };
}

function mergeEvents(list) {
  return (Array.isArray(list) ? list : []).map(normEvent).filter((e) => e.id);
}

function applyConflicts(conflicts) {
  localConflicts = Array.isArray(conflicts) ? conflicts : [];
  conflictIds = new Set();
  localConflicts.forEach((c) => {
    if (c.event_a) conflictIds.add(String(c.event_a));
    if (c.event_b) conflictIds.add(String(c.event_b));
  });
}

function startOfDay(d) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

function endOfDay(d) {
  const x = new Date(d);
  x.setHours(23, 59, 59, 999);
  return x;
}

function mondayOfWeek(d) {
  const x = startOfDay(d);
  const day = x.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  x.setDate(x.getDate() + diff);
  return x;
}

function sundayOfWeek(d) {
  const m = mondayOfWeek(d);
  const s = new Date(m);
  s.setDate(s.getDate() + 6);
  return endOfDay(s);
}

function startOfMonth(d) {
  const x = new Date(d.getFullYear(), d.getMonth(), 1);
  return startOfDay(x);
}

function endOfMonth(d) {
  const x = new Date(d.getFullYear(), d.getMonth() + 1, 0);
  return endOfDay(x);
}

function getFilterRange() {
  const now = new Date();
  if (filterPreset === "today") {
    return { start: startOfDay(now), end: endOfDay(now) };
  }
  if (filterPreset === "week") {
    return { start: mondayOfWeek(now), end: sundayOfWeek(now) };
  }
  if (filterPreset === "month") {
    return { start: startOfMonth(now), end: endOfMonth(now) };
  }
  if (filterPreset === "custom" && customRangeStartStr && customRangeEndStr) {
    const a = startOfDay(new Date(customRangeStartStr + "T12:00:00"));
    const b = endOfDay(new Date(customRangeEndStr + "T12:00:00"));
    if (a > b) return { start: b, end: a };
    return { start: a, end: b };
  }
  const end = new Date(now);
  end.setDate(end.getDate() + 7);
  return { start: startOfDay(now), end: endOfDay(end) };
}

function buildEventsQuery() {
  const { start, end } = getFilterRange();
  const sp = new URLSearchParams();
  sp.set("start", start.toISOString());
  sp.set("end", end.toISOString());
  return `?${sp.toString()}`;
}

async function apiFetchCalendar(method, endpoint, body = null) {
  const token = localStorage.getItem("auth_token");
  /** @type {Record<string, string>} */
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, options);

  if (response.status === 401) {
    if (window.attemptSilentLogin) await window.attemptSilentLogin();
    const newToken = localStorage.getItem("auth_token");
    if (newToken) headers.Authorization = `Bearer ${newToken}`;
    const retry = await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, {
      ...options,
      headers: { ...headers },
    });
    if (!retry.ok) throw new Error(`API Error: ${retry.status}`);
    if (retry.status === 204) return null;
    return retry.json();
  }

  if (!response.ok) {
    const t = await response.text().catch(() => "");
    throw new Error(`API Error: ${response.status} ${response.statusText} ${t.slice(0, 200)}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

function sourceGoogleEnabled() {
  const el = document.getElementById("calendar-source-google");
  return !el || el.checked;
}

function eventsForDisplay() {
  if (!sourceGoogleEnabled()) return [];
  return localEvents;
}

function formatTime(isoString) {
  if (!isoString) return "";
  return new Date(String(isoString)).toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(isoString) {
  if (!isoString) return "";
  return new Date(String(isoString)).toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function toDatetimeLocalValue(iso) {
  const d = new Date(String(iso));
  if (Number.isNaN(d.getTime())) return "";
  const x = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return x.toISOString().slice(0, 16);
}

/**
 * Aktiviert/deaktiviert Inline-Bearbeitung für eine Event-Card (TASK-058 Phase 2).
 * @param {string | null} eventId
 */
export function toggleEditMode(eventId) {
  editingEventId = editingEventId === eventId ? null : eventId;
  renderAgendaView(eventsForDisplay());
}

function closeDetailPanel() {
  const panel = document.getElementById("calendar-detail-panel");
  if (panel) panel.hidden = true;
}

function openDetailPanel(ev) {
  const panel = document.getElementById("calendar-detail-panel");
  const titleEl = document.getElementById("calendar-detail-title");
  const bodyEl = document.getElementById("calendar-detail-body");
  if (!panel || !titleEl || !bodyEl) return;

  titleEl.textContent = ev.title;
  bodyEl.textContent = "";

  const dl = document.createElement("dl");

  function addPair(label, node) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.appendChild(node);
    dl.appendChild(dt);
    dl.appendChild(dd);
  }

  const when = document.createDocumentFragment();
  when.appendChild(
    document.createTextNode(`${formatDate(ev.start)}, ${formatTime(ev.start)} – ${formatTime(ev.end)}`)
  );
  addPair("Zeitraum", when);

  const loc = document.createElement("span");
  loc.textContent = ev.location ? String(ev.location) : "(Kein Ort)";
  addPair("Ort", loc);

  const desc = document.createElement("pre");
  desc.style.whiteSpace = "pre-wrap";
  desc.style.margin = "0";
  desc.style.fontFamily = "inherit";
  desc.textContent = ev.description ? String(ev.description) : "(Keine Beschreibung)";
  addPair("Beschreibung", desc);

  if (Array.isArray(ev.attendees) && ev.attendees.length > 0) {
    const ul = document.createElement("ul");
    ev.attendees.forEach((a) => {
      const li = document.createElement("li");
      li.textContent = String(a);
      ul.appendChild(li);
    });
    addPair("Teilnehmer", ul);
  } else {
    const em = document.createElement("em");
    em.textContent = "Keine Teilnehmerliste";
    addPair("Teilnehmer", em);
  }

  if (ev.recurrence_rule) {
    const code = document.createElement("code");
    code.textContent = String(ev.recurrence_rule);
    addPair("Wiederholung", code);
  }

  bodyEl.appendChild(dl);
  panel.hidden = false;
}

async function saveInlineEdit(eventId) {
  const card = document.querySelector(`.calendar-event-card[data-event-id="${escapeCssAttr(eventId)}"]`);
  if (!card) return;

  /** @type {HTMLInputElement | null} */
  const titleInput = card.querySelector(".event-edit-title");
  /** @type {HTMLInputElement | null} */
  const startInput = card.querySelector(".event-edit-start");
  /** @type {HTMLInputElement | null} */
  const endInput = card.querySelector(".event-edit-end");

  const title = titleInput?.value?.trim();
  const startVal = startInput?.value;
  const endVal = endInput?.value;
  if (!title || !startVal || !endVal) {
    showToast("Titel und Zeiten sind erforderlich", "error");
    return;
  }

  const startIso = new Date(startVal).toISOString();
  const endIso = new Date(endVal).toISOString();
  if (new Date(endIso) <= new Date(startIso)) {
    showToast("Ende muss nach Start liegen", "error");
    return;
  }

  const prev = localEvents.map((e) => ({ ...e }));
  const optimistic = mergeEvents(localEvents).map((e) =>
    e.id === eventId ? { ...e, title, start: startIso, end: endIso } : e
  );
  localEvents = optimistic;
  editingEventId = null;
  renderAgendaView(eventsForDisplay());

  try {
    const updated = await apiFetchCalendar("PUT", `/events/${encodeURIComponent(eventId)}`, {
      title,
      start: startIso,
      end: endIso,
    });
    const merged = mergeEvents(localEvents).map((e) =>
      e.id === eventId ? normEvent(updated) : e
    );
    localEvents = merged;
    renderAgendaView(eventsForDisplay());
    showToast("Termin gespeichert", "success");
    await loadCalendarEvents({ preserveScroll: true });
  } catch (error) {
    localEvents = prev;
    editingEventId = eventId;
    renderAgendaView(eventsForDisplay());
    console.error("saveInlineEdit failed:", error);
    showToast("Speichern fehlgeschlagen", "error");
  }
}

function renderAgendaView(events) {
  const container = document.getElementById("calendar-agenda");
  if (!container) return;

  container.innerHTML = "";

  if (!events || events.length === 0) {
    const msg = sourceGoogleEnabled()
      ? "Keine Termine im gewählten Zeitraum"
      : 'Quelle "Google" ist deaktiviert — keine Anzeige';
    container.innerHTML = `<div class="calendar-empty">${msg}</div>`;
    return;
  }

  const grouped = {};
  events.forEach((event) => {
    const dk = formatDate(event.start);
    if (!grouped[dk]) grouped[dk] = [];
    grouped[dk].push(event);
  });

  const sortedDates = Object.keys(grouped).sort((a, b) => {
    const dateA = new Date(grouped[a][0].start);
    const dateB = new Date(grouped[b][0].start);
    return dateA - dateB;
  });

  sortedDates.forEach((dateKey) => {
    const dateHeader = document.createElement("div");
    dateHeader.className = "calendar-date-header";
    dateHeader.textContent = dateKey;
    container.appendChild(dateHeader);

    grouped[dateKey].forEach((event) => {
      const card = document.createElement("div");
      card.className = "calendar-event-card";
      if (conflictIds.has(event.id)) card.classList.add("calendar-event-card--conflict");
      card.dataset.eventId = event.id;

      if (editingEventId === event.id) {
        card.innerHTML = `
          <div class="event-edit-fields">
            <input type="text" class="event-edit-title form-group input" value="${escapeAttr(event.title)}" />
            <input type="datetime-local" class="event-edit-start" value="${toDatetimeLocalValue(event.start)}" />
            <input type="datetime-local" class="event-edit-end" value="${toDatetimeLocalValue(event.end)}" />
          </div>
          <div class="event-edit-actions">
            <button type="button" class="event-btn-save" data-action="save">Speichern</button>
            <button type="button" class="event-btn-cancel" data-action="cancel">Abbrechen</button>
          </div>
          <button class="event-delete-btn" type="button" data-action="delete" title="Termin löschen">×</button>
        `;
      } else {
        card.innerHTML = `
          <div class="event-title-row">
            <div class="event-title event-title--editable" data-edit-trigger="title">${escapeHtml(event.title)}</div>
          </div>
          <div class="event-time event-time--editable" data-edit-trigger="time">${formatTime(event.start)} - ${formatTime(event.end)}</div>
          ${
            event.location
              ? `<div class="event-location">${escapeHtml(String(event.location))}</div>`
              : ""
          }
          <div class="event-card-actions">
            <button type="button" class="event-more-btn" data-action="detail">Mehr Info</button>
          </div>
          <button class="event-delete-btn" type="button" data-action="delete" title="Termin löschen">×</button>
        `;
      }

      container.appendChild(card);
    });
  });

  container.querySelectorAll(".calendar-event-card").forEach((card) => {
    const id = card.getAttribute("data-event-id");
    if (!id) return;

    card.querySelector('[data-edit-trigger="title"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleEditMode(id);
    });
    card.querySelector('[data-edit-trigger="time"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleEditMode(id);
    });

    card.querySelector('[data-action="save"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      saveInlineEdit(id);
    });
    card.querySelector('[data-action="cancel"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleEditMode(null);
    });

    card.querySelector('[data-action="delete"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteCalendarEvent(id);
    });

    card.querySelector('[data-action="detail"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      const ev = mergeEvents(localEvents).find((x) => x.id === id);
      if (ev) openDetailPanel(ev);
    });
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
}

function escapeCssAttr(s) {
  const id = String(s);
  return typeof CSS !== "undefined" && typeof CSS.escape === "function" ? CSS.escape(id) : id.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

async function loadCalendarEvents() {
  try {
    const q = buildEventsQuery();
    const data = await apiFetchCalendar("GET", `/events${q}`);
    localEvents = mergeEvents(data.events || []);
    applyConflicts(data.conflicts || []);
    renderAgendaView(eventsForDisplay());
    return localEvents;
  } catch (error) {
    console.error("Failed to load calendar events:", error);
    showToast("Fehler beim Laden der Termine", "error");
    return [];
  }
}

async function createCalendarEvent(eventPayload) {
  const tempId = "temp-" + Date.now();
  const tempEvent = normEvent({
    id: tempId,
    ...eventPayload,
    source: "google",
  });

  const prevEvents = [...localEvents];
  localEvents.push(tempEvent);
  renderAgendaView(eventsForDisplay());

  try {
    const result = await apiFetchCalendar("POST", "/events", eventPayload);
    localEvents = localEvents.filter((e) => e.id !== tempId);
    localEvents.push(normEvent(result));
    renderAgendaView(eventsForDisplay());
    await loadCalendarEvents();
    showToast("Termin erstellt", "success");
    return result;
  } catch (error) {
    localEvents = prevEvents;
    renderAgendaView(eventsForDisplay());
    console.error("Failed to create calendar event:", error);
    showToast("Fehler beim Erstellen des Termins", "error");
    throw error;
  }
}

async function deleteCalendarEvent(eventId) {
  if (!confirm("Termin wirklich löschen?")) return;

  const event = localEvents.find((e) => String(e.id) === eventId);
  if (!event) return;

  const snapshot = [...localEvents];
  localEvents = localEvents.filter((e) => String(e.id) !== eventId);
  if (editingEventId === eventId) editingEventId = null;
  renderAgendaView(eventsForDisplay());

  try {
    await apiFetchCalendar("DELETE", `/events/${encodeURIComponent(eventId)}`);
    await loadCalendarEvents();
    showToast("Termin gelöscht", "success");
  } catch (error) {
    localEvents = snapshot;
    renderAgendaView(eventsForDisplay());
    console.error("Failed to delete calendar event:", error);
    showToast("Fehler beim Löschen des Termins", "error");
    throw error;
  }
}

function showToast(message, type = "info") {
  if (window.showToast) {
    window.showToast(message, type);
    return;
  }
  const toast = document.createElement("div");
  toast.className = `calendar-toast calendar-toast--${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    background: ${type === "success" ? "#4caf50" : type === "error" ? "#f44336" : "#2196f3"};
    color: white;
    border-radius: 4px;
    z-index: 10000;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function syncFilterUi() {
  document.querySelectorAll(".calendar-filter-btn").forEach((btn) => {
    const preset = btn.getAttribute("data-filter");
    btn.classList.toggle("calendar-filter-btn--active", preset === filterPreset);
  });
  const customBox = document.getElementById("calendar-custom-range");
  if (customBox) customBox.hidden = filterPreset !== "custom";
}

function initCalendarFilters() {
  document.querySelectorAll(".calendar-filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const preset = btn.getAttribute("data-filter");
      if (!preset) return;
      filterPreset = preset;
      syncFilterUi();
      loadCalendarEvents();
    });
  });

  document.getElementById("calendar-apply-custom-range")?.addEventListener("click", () => {
    const s = document.getElementById("calendar-range-start");
    const e = document.getElementById("calendar-range-end");
    customRangeStartStr = s?.value || "";
    customRangeEndStr = e?.value || "";
    if (!customRangeStartStr || !customRangeEndStr) {
      showToast("Bitte Von- und Bis-Datum wählen", "error");
      return;
    }
    filterPreset = "custom";
    syncFilterUi();
    loadCalendarEvents();
  });

  document.getElementById("calendar-source-google")?.addEventListener("change", () => {
    renderAgendaView(eventsForDisplay());
  });

  document.getElementById("calendar-detail-close")?.addEventListener("click", closeDetailPanel);

  const t = new Date();
  const ws = document.getElementById("calendar-range-start");
  const we = document.getElementById("calendar-range-end");
  if (ws instanceof HTMLInputElement) {
    ws.valueAsDate = t;
  }
  if (we instanceof HTMLInputElement) {
    const plus = new Date(t);
    plus.setDate(plus.getDate() + 7);
    we.valueAsDate = plus;
  }

  syncFilterUi();
}

function showCreateEventForm() {
  const container = document.getElementById("calendar-agenda");
  if (!container) return;

  if (document.getElementById("create-event-form")) return;

  const form = document.createElement("div");
  form.id = "create-event-form";
  form.className = "calendar-create-form";
  form.innerHTML = `
    <div class="form-header">
      <h3>Neuer Termin</h3>
      <button type="button" class="form-close-btn">×</button>
    </div>
    <form id="event-form">
      <div class="form-group">
        <label for="event-summary">Titel</label>
        <input type="text" id="event-summary" required placeholder="Termin-Titel">
      </div>
      <div class="form-group">
        <label for="event-start">Startzeit</label>
        <input type="datetime-local" id="event-start" required>
      </div>
      <div class="form-group">
        <label for="event-end">Endzeit</label>
        <input type="datetime-local" id="event-end" required>
      </div>
      <div class="form-group">
        <label for="event-location">Ort (optional)</label>
        <input type="text" id="event-location" placeholder="Ort">
      </div>
      <div class="form-group">
        <label for="event-description">Beschreibung (optional)</label>
        <textarea id="event-description" rows="3" placeholder="Beschreibung"></textarea>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary">Termin erstellen</button>
        <button type="button" class="btn-secondary cancel-btn">Abbrechen</button>
      </div>
    </form>
  `;

  container.prepend(form);

  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  /** @type {HTMLInputElement | null} */
  const startEl = document.getElementById("event-start");
  /** @type {HTMLInputElement | null} */
  const endEl = document.getElementById("event-end");
  if (startEl) startEl.value = now.toISOString().slice(0, 16);
  const endTime = new Date(now.getTime() + 60 * 60 * 1000);
  if (endEl) endEl.value = endTime.toISOString().slice(0, 16);

  form.querySelector(".form-close-btn")?.addEventListener("click", () => form.remove());
  form.querySelector(".cancel-btn")?.addEventListener("click", () => form.remove());

  document.getElementById("event-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const summary = /** @type {HTMLInputElement} */ (document.getElementById("event-summary")).value;
    const startTime = /** @type {HTMLInputElement} */ (document.getElementById("event-start")).value;
    const endTimeVal = /** @type {HTMLInputElement} */ (document.getElementById("event-end")).value;
    const location = /** @type {HTMLInputElement} */ (document.getElementById("event-location")).value;
    const description = /** @type {HTMLTextAreaElement} */ (document.getElementById("event-description")).value;

    const eventPayload = {
      title: summary.trim(),
      start: new Date(startTime).toISOString(),
      end: new Date(endTimeVal).toISOString(),
      timezone: "Europe/Berlin",
      location: location?.trim() || null,
      description: description?.trim() || null,
    };

    try {
      await createCalendarEvent(eventPayload);
      form.remove();
    } catch {
      /* Fehler bereits behandelt */
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initCalendarFilters();

  const calendarView = document.getElementById("calendar-view");
  const calendarHost = document.getElementById("calendar-modal");
  const navBtn = document.getElementById("sidebar-nav-calendar");
  const closeBtn = document.getElementById("close-calendar-btn");
  const minimizeBtn = document.getElementById("calendar-minimize-btn");
  const resetBtn = document.getElementById("calendar-reset-btn");
  const header = document.getElementById("calendar-header");
  const createEventBtn = document.getElementById("create-event-btn");

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
        loadCalendarEvents();
      } catch {
        /* ignore */
      }
    }
    if (!visible) closeDetailPanel();
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

  createEventBtn?.addEventListener("click", () => showCreateEventForm());

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
