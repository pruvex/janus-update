/**
 * Janus Calendar Modal — TASK-058 Phase 1–3 (MCL Dock-Modul "calendar").
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
/** Rechtes Detail-Panel — zuletzt geöffneter Termin (für Re-Sync nach renderCalendar). */
let detailPanelEventId = null;
/** AbortController für Panel-Listeners beim Schließen/Neuöffnen. */
let detailPanelAbort = null;
let filterPreset = "week"; // today | week | month | custom
/** ISO date strings YYYY-MM-DD for custom preset */
let customRangeStartStr = "";
let customRangeEndStr = "";
/** @type {"day" | "week" | "month"} */
let calendarViewMode = "week";
/** Ankerdatum (lokaler Tagesbeginn) für Tag-/Wochenansicht */
let calendarViewAnchor = new Date();
let calendarMiniMonthAnchor = new Date();
let calendarSearchTerm = "";
let calendarPollTimer = null;
/** @type {Promise<Array<Record<string, unknown>>> | null} */
let calendarLoadInFlight = null;
let lastCalendarLoadAt = 0;
let syncFromDockStateRunning = false;

/**
 * Liest die CSS-Variable :root `--cal-hour-height` (gleiche Source of Truth wie das Raster).
 * @returns {number}
 */
function getCalHourHeightPx() {
  const raw =
    typeof document !== "undefined"
      ? getComputedStyle(document.documentElement).getPropertyValue("--cal-hour-height").trim()
      : "";
  const n = Number.parseFloat(raw.replace("px", ""));
  return Number.isFinite(n) && n > 0 ? n : 60;
}

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

function resetCalendarViewAnchorToToday() {
  calendarViewAnchor = startOfDay(new Date());
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
  if (filterPreset === "custom" && customRangeStartStr && customRangeEndStr) {
    const a = startOfDay(new Date(customRangeStartStr + "T12:00:00"));
    const b = endOfDay(new Date(customRangeEndStr + "T12:00:00"));
    if (a > b) return { start: b, end: a };
    return { start: a, end: b };
  }
  if (calendarViewMode === "day") {
    return { start: startOfDay(calendarViewAnchor), end: endOfDay(calendarViewAnchor) };
  }
  if (calendarViewMode === "week") {
    return { start: mondayOfWeek(calendarViewAnchor), end: sundayOfWeek(calendarViewAnchor) };
  }
  if (calendarViewMode === "month") {
    return { start: startOfMonth(calendarViewAnchor), end: endOfMonth(calendarViewAnchor) };
  }
  if (filterPreset === "today") {
    return { start: startOfDay(now), end: endOfDay(now) };
  }
  if (filterPreset === "week") {
    return { start: mondayOfWeek(now), end: sundayOfWeek(now) };
  }
  if (filterPreset === "month") {
    return { start: startOfMonth(now), end: endOfMonth(now) };
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
  const events = localEvents;
  const q = calendarSearchTerm.trim().toLowerCase();
  if (!q) return events;
  return events.filter((event) => {
    const ev = normEvent(event);
    return [ev.title, ev.location, ev.description]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q));
  });
}

function isSameLocalDate(a, b) {
  return (
    a instanceof Date &&
    b instanceof Date &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function eventDurationMinutes(ev) {
  const s = new Date(String(ev.start));
  const e = new Date(String(ev.end));
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return 0;
  return Math.max(0, Math.round((e.getTime() - s.getTime()) / 60000));
}

/** @param {ReturnType<typeof normEvent>} ev */
function eventAdaptiveDurationClass(ev) {
  if (ev.is_all_day) return "cal-event--normal";
  const mins = eventDurationMinutes(ev);
  if (mins < 20) return "cal-event--ultra-short";
  if (mins < 45) return "cal-event--short";
  return "cal-event--normal";
}

function eventTone(ev) {
  const title = String(ev.title || "").toLowerCase();
  if (title.includes("focus") || title.includes("fokus")) return "focus";
  if (title.includes("projekt") || title.includes("project")) return "project";
  if (title.includes("call") || title.includes("zoom") || title.includes("meeting")) return "meeting";
  if (title.includes("sport") || title.includes("pause") || title.includes("essen")) return "personal";
  return "default";
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
  renderCalendar();
}

function calendarModalVisibleDom() {
  const el = document.getElementById("calendar-view");
  return !!(el && el.style.display !== "none");
}

/** @typedef {{ start: Date, endExclusive: Date }} ColumnBounds */

function columnDayBounds(midnightSeed) {
  const d = midnightSeed instanceof Date ? midnightSeed : new Date(midnightSeed);
  const start = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const endExclusive = new Date(start);
  endExclusive.setDate(endExclusive.getDate() + 1);
  return { start, endExclusive };
}

/**
 * Berechnet top/height in px für einen zeitbezogenen Event-Ausschnitt an einem lokalem Kalendertag.
 * @returns {{ top: number, height: number } | null}
 */
function timedEventGeom(ev, bounds) {
  if (ev.is_all_day) return null;
  const s = new Date(String(ev.start));
  const e = new Date(String(ev.end));
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return null;

  const os = Math.max(s.getTime(), bounds.start.getTime());
  const oe = Math.min(e.getTime(), bounds.endExclusive.getTime());
  if (oe <= os) return null;

  const hourHeight = getCalHourHeightPx();
  const minsFromMidnight = (os - bounds.start.getTime()) / 60000;
  const durMin = (oe - os) / 60000;

  /** top = (Stunden + Minuten/60) * hourHeight; height wie gefordert */
  const fracHoursStart = minsFromMidnight / 60;
  const top = fracHoursStart * hourHeight;
  const height = (durMin / 60) * hourHeight;
  return { top, height };
}

function overlapAllDay(ev, bounds) {
  if (!ev.is_all_day) return false;
  const s = new Date(String(ev.start));
  const e = new Date(String(ev.end));
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return false;
  const dayStartTs = bounds.start.getTime();
  const dayNextTs = bounds.endExclusive.getTime();
  return e.getTime() > dayStartTs && s.getTime() < dayNextTs;
}

/** @typedef {ReturnType<typeof normEvent>} CalEventNorm */

/** @returns {HTMLElement} */
function buildEventCardElement(event) {
  const card = document.createElement("div");
  card.className = "calendar-event-card";
  card.classList.add(`calendar-event-card--${eventTone(event)}`);
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
    card.classList.add(eventAdaptiveDurationClass(event));
    card.innerHTML = `
          <div class="event-card-primary">
            <div class="event-title-row">
              <div class="event-title event-title--editable" data-edit-trigger="title">${escapeHtml(event.title)}</div>
            </div>
            <div class="event-time event-time--editable" data-edit-trigger="time">${formatTime(event.start)} – ${formatTime(event.end)}</div>
          </div>
          ${
            event.location
              ? `<div class="event-location">${escapeHtml(String(event.location))}</div>`
              : ""
          }
          ${
            event.description
              ? `<div class="event-description">${escapeHtml(String(event.description))}</div>`
              : ""
          }
          <button class="event-delete-btn" type="button" data-action="delete" title="Termin löschen">×</button>
        `;
  }
  return card;
}

/**
 * Inline-Bearbeitung per Klick nur in der Agenda-Liste; Timeline öffnet per Kachel-Klick immer das Detail-Panel.
 * @param {{ timeline?: boolean }} [opts]
 */
function bindEventCardListeners(card, eventId, opts = {}) {
  const isTimelineTile = !!opts.timeline;

  bindOpenDetailPanelOnCard(card, eventId);

  if (!isTimelineTile) {
    card.querySelector('[data-edit-trigger="title"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleEditMode(eventId);
    });
    card.querySelector('[data-edit-trigger="time"]')?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleEditMode(eventId);
    });
  }
  card.querySelector('[data-action="save"]')?.addEventListener("click", (e) => {
    e.stopPropagation();
    saveInlineEdit(eventId);
  });
  card.querySelector('[data-action="cancel"]')?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleEditMode(null);
  });
  card.querySelector('[data-action="delete"]')?.addEventListener("click", (e) => {
    e.stopPropagation();
    deleteCalendarEvent(eventId);
  });
}

/** @returns {HTMLElement} */
function buildHourLabelsRail() {
  const hh = getCalHourHeightPx();
  const rail = document.createElement("div");
  rail.className = "calendar-hours-rail";
  for (let h = 0; h < 24; h += 1) {
    const label = document.createElement("div");
    label.className = "calendar-hour-label";
    label.style.top = `${h * hh}px`;
    label.textContent = `${String(h).padStart(2, "0")}:00`;
    rail.appendChild(label);
  }
  return rail;
}

function renderTimedColumn(events, bounds) {
  const surface = document.createElement("div");
  surface.className = "calendar-grid-surface";

  const gridContent = document.createElement("div");
  gridContent.className = "calendar-grid-content";

  const layer = document.createElement("div");
  layer.className = "calendar-events-abs-layer";

  events.forEach((event) => {
    const geom = timedEventGeom(event, bounds);
    if (!geom) return;
    const slot = document.createElement("div");
    slot.className = "calendar-timeline-slot";
    slot.dataset.eventId = event.id;
    slot.style.top = `${geom.top}px`;
    slot.style.height = `${geom.height}px`;

    slot.appendChild(buildEventCardElement(event));
    bindEventCardListeners(slot.querySelector(".calendar-event-card"), event.id, { timeline: true });
    layer.appendChild(slot);
  });

  gridContent.appendChild(layer);
  surface.appendChild(gridContent);
  return surface;
}

/** @type {"synced"|"syncing"|"error"} */
let calendarSyncUi = "synced";

function syncCalendarViewToggleUi() {
  document.querySelectorAll(".calendar-view-btn").forEach((btn) => {
    const v = btn.getAttribute("data-view");
    const active = v === calendarViewMode;
    btn.classList.toggle("calendar-view-btn--active", active);
    btn.setAttribute("aria-selected", active ? "true" : "false");
  });
}

function startCalendarPoll() {
  if (calendarPollTimer !== null) {
    clearInterval(calendarPollTimer);
    calendarPollTimer = null;
  }
  calendarPollTimer = setInterval(() => loadCalendarEvents({ silentPolling: true }), 60000);
}

function stopCalendarPoll() {
  if (calendarPollTimer !== null) {
    clearInterval(calendarPollTimer);
    calendarPollTimer = null;
  }
}

function setSyncStatus(mode) {
  calendarSyncUi = mode;
  const el = document.getElementById("calendar-sync-status");
  if (!el) return;
  el.classList.remove("calendar-sync-status--syncing", "calendar-sync-status--error");
  if (mode === "syncing") {
    el.textContent = "Synchronisiere...";
    el.classList.add("calendar-sync-status--syncing");
  } else if (mode === "error") {
    el.textContent = "Sync-Fehler";
    el.classList.add("calendar-sync-status--error");
  } else {
    el.textContent = "Synchronisiert";
  }
}

function dashboardEvents() {
  return sourceGoogleEnabled() ? mergeEvents(localEvents) : [];
}

function eventsForDay(events, day) {
  const bounds = columnDayBounds(day);
  return events.filter((ev) => {
    const s = new Date(String(ev.start));
    const e = new Date(String(ev.end));
    return !Number.isNaN(s.getTime()) && !Number.isNaN(e.getTime()) && e > bounds.start && s < bounds.endExclusive;
  });
}

function formatHourAmount(minutes) {
  if (minutes <= 0) return "0h";
  const hours = minutes / 60;
  return hours >= 1 ? `${hours.toLocaleString("de-DE", { maximumFractionDigits: 1 })}h` : `${minutes}m`;
}

function updatePeriodLabel() {
  const el = document.getElementById("calendar-period-label");
  if (!el) return;
  if (calendarViewMode === "day") {
    el.textContent = calendarViewAnchor.toLocaleDateString("de-DE", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    return;
  }
  if (calendarViewMode === "month") {
    el.textContent = calendarViewAnchor.toLocaleDateString("de-DE", {
      month: "long",
      year: "numeric",
    });
    return;
  }
  const start = mondayOfWeek(calendarViewAnchor);
  const end = sundayOfWeek(calendarViewAnchor);
  el.textContent = `${start.toLocaleDateString("de-DE", { day: "numeric", month: "short" })} - ${end.toLocaleDateString("de-DE", { day: "numeric", month: "short", year: "numeric" })}`;
}

function renderMiniMonth() {
  const grid = document.getElementById("calendar-mini-month");
  const label = document.getElementById("calendar-mini-month-label");
  if (!grid) return;

  const monthStart = startOfMonth(calendarMiniMonthAnchor);
  if (label) {
    label.textContent = monthStart.toLocaleDateString("de-DE", { month: "long", year: "numeric" });
  }

  grid.innerHTML = "";
  ["M", "D", "M", "D", "F", "S", "S"].forEach((day) => {
    const el = document.createElement("span");
    el.className = "calendar-mini-dow";
    el.textContent = day;
    grid.appendChild(el);
  });

  const first = mondayOfWeek(monthStart);
  const today = startOfDay(new Date());
  for (let i = 0; i < 42; i += 1) {
    const d = new Date(first);
    d.setDate(first.getDate() + i);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "calendar-mini-day";
    btn.textContent = String(d.getDate());
    btn.classList.toggle("calendar-mini-day--muted", d.getMonth() !== monthStart.getMonth());
    btn.classList.toggle("calendar-mini-day--today", isSameLocalDate(d, today));
    btn.classList.toggle("calendar-mini-day--selected", isSameLocalDate(d, calendarViewAnchor));
    btn.addEventListener("click", () => {
      calendarViewAnchor = startOfDay(d);
      if (calendarViewMode === "month") filterPreset = "month";
      syncFilterUi();
      loadCalendarEvents();
    });
    grid.appendChild(btn);
  }
}

function updatePlanningSidebar(events) {
  const all = mergeEvents(events || []);
  const todayEvents = eventsForDay(all, new Date()).sort((a, b) => new Date(String(a.start)) - new Date(String(b.start)));
  const focusMinutes = todayEvents
    .filter((ev) => eventTone(ev) === "focus")
    .reduce((sum, ev) => sum + eventDurationMinutes(ev), 0);
  const busyMinutes = todayEvents.reduce((sum, ev) => sum + eventDurationMinutes(ev), 0);
  const load = Math.min(100, Math.round((busyMinutes / (8 * 60)) * 100));

  const eventsEl = document.getElementById("calendar-stat-events");
  const focusEl = document.getElementById("calendar-stat-focus");
  const loadEl = document.getElementById("calendar-stat-load");
  const meterEl = document.getElementById("calendar-load-meter-fill");
  if (eventsEl) eventsEl.textContent = String(todayEvents.length);
  if (focusEl) focusEl.textContent = formatHourAmount(focusMinutes);
  if (loadEl) loadEl.textContent = `${load}%`;
  if (meterEl) meterEl.style.width = `${load}%`;

  const nextEl = document.getElementById("calendar-next-event-card");
  if (nextEl) {
    const now = new Date();
    const next = all
      .filter((ev) => new Date(String(ev.end)) >= now)
      .sort((a, b) => new Date(String(a.start)) - new Date(String(b.start)))[0];
    if (!next) {
      nextEl.innerHTML = '<div class="calendar-muted">Kein kommender Termin</div>';
    } else {
      nextEl.innerHTML = `
        <div class="calendar-next-event-dot calendar-next-event-dot--${eventTone(next)}"></div>
        <div class="calendar-next-event-title">${escapeHtml(next.title)}</div>
        <div class="calendar-next-event-time">${formatTime(next.start)} - ${formatTime(next.end)}</div>
        ${next.location ? `<div class="calendar-next-event-location">${escapeHtml(String(next.location))}</div>` : ""}
        <button type="button" class="calendar-next-event-action" data-event-id="${escapeAttr(next.id)}">Details öffnen</button>
      `;
      nextEl.querySelector(".calendar-next-event-action")?.addEventListener("click", () => openDetailPanel(next));
    }
  }
}

function renderCalendar() {
  const events = eventsForDisplay();
  updatePeriodLabel();
  renderMiniMonth();
  updatePlanningSidebar(dashboardEvents());

  const container = document.getElementById("calendar-agenda");
  if (!container) return;

  container.className = "";

  const evs = mergeEvents(events);
  calendarViewAnchor = startOfDay(calendarViewAnchor);

  if (!sourceGoogleEnabled()) {
    const formRef = stashCreateForm();
    container.innerHTML = `<div class="calendar-empty">Quelle "Google" ist deaktiviert</div>`;
    if (formRef) container.prepend(formRef);
    syncCalendarDetailPanelIfOpen();
    return;
  }

  if (calendarViewMode === "day") {
    renderDayViewBody(container, evs);
  } else if (calendarViewMode === "week") {
    renderWeekViewBody(container, evs);
  } else {
    container.classList.add("calendar-agenda-pane", "calendar-month-planning-pane");
    renderAgendaBody(container, evs);
  }
  syncCalendarDetailPanelIfOpen();
}

function hideEventDetails() {
  detailPanelAbort?.abort();
  detailPanelAbort = null;
  detailPanelEventId = null;
  const panel = document.getElementById("calendar-detail-panel");
  if (panel) panel.hidden = true;
  document.getElementById("calendar-modal")?.classList.remove("calendar-detail-open");
}

function closeDetailPanel() {
  hideEventDetails();
}

/**
 * Stoppt Event-Bubbling, damit keine fremden Click-Listener feuern.
 * @param {MouseEvent} event
 */
function handleDetailCloseClick(event) {
  event.preventDefault();
  event.stopPropagation();
  if (typeof event.stopImmediatePropagation === "function") {
    event.stopImmediatePropagation();
  }
  hideEventDetails();
}

function openDetailPanel(ev) {
  const panel = document.getElementById("calendar-detail-panel");
  const bodyEl = document.getElementById("calendar-detail-body");
  if (!panel || !bodyEl) return;

  const ne = normEvent(ev);
  detailPanelAbort?.abort();
  detailPanelAbort = new AbortController();
  detailPanelEventId = ne.id;
  populateCalendarDetailPanel(ne);
  document.getElementById("calendar-modal")?.classList.add("calendar-detail-open");
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
  renderCalendar();

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
    renderCalendar();
    showToast("Termin gespeichert", "success");
    await loadCalendarEvents({ preserveScroll: true });
  } catch (error) {
    localEvents = prev;
    editingEventId = eventId;
    renderCalendar();
    console.error("saveInlineEdit failed:", error);
    showToast("Speichern fehlgeschlagen", "error");
  }
}

function renderAgendaBody(container, events) {
  const formRef = container.querySelector("#create-event-form");
  container.innerHTML = "";

  if (!events || events.length === 0) {
    const msg = sourceGoogleEnabled()
      ? "Keine Termine im gewählten Zeitraum"
      : 'Quelle "Google" ist deaktiviert — keine Anzeige';
    container.innerHTML = `<div class="calendar-empty">${msg}</div>`;
    if (formRef) container.appendChild(formRef);
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
      const card = buildEventCardElement(event);
      container.appendChild(card);
      bindEventCardListeners(card, event.id);
    });
  });

  if (formRef) container.prepend(formRef);
}

function stashCreateForm() {
  const container = document.getElementById("calendar-agenda");
  const form = container?.querySelector("#create-event-form");
  return form ?? null;
}

function renderDayViewBody(container, events) {
  const formRef = stashCreateForm();
  const bounds = columnDayBounds(calendarViewAnchor);
  const alldays = events.filter((ev) => overlapAllDay(ev, bounds));

  const root = document.createElement("div");
  root.className = "calendar-time-root";
  if (isSameLocalDate(bounds.start, new Date())) root.classList.add("calendar-time-root--today");

  const title = document.createElement("div");
  title.className = "calendar-week-title";
  title.textContent = bounds.start.toLocaleDateString("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  root.appendChild(title);

  const head = document.createElement("div");
  head.className = "calendar-day-allday";
  const alb = document.createElement("div");
  alb.className = "calendar-allday-label";
  alb.textContent = "Ganztägig";
  head.appendChild(alb);
  const row = document.createElement("div");
  row.className = "calendar-allday-row";
  alldays.forEach((e) => appendAllDayChip(row, e));
  head.appendChild(row);
  root.appendChild(head);

  const scroll = document.createElement("div");
  scroll.className = "calendar-day-scroll";

  const tw = document.createElement("div");
  tw.className = "calendar-day-timeline-wrap";
  tw.appendChild(buildHourLabelsRail());

  tw.appendChild(renderTimedColumn(events, bounds));
  scroll.appendChild(tw);
  root.appendChild(scroll);

  container.innerHTML = "";
  container.appendChild(root);
  if (formRef) container.prepend(formRef);
}

function renderWeekViewBody(container, events) {
  const formRef = stashCreateForm();
  const mon = mondayOfWeek(calendarViewAnchor);
  const root = document.createElement("div");
  root.className = "calendar-week-shell";

  const title = document.createElement("div");
  title.className = "calendar-week-title";
  title.textContent = `Woche ${mon.toLocaleDateString("de-DE", { day: "numeric", month: "short" })} — ${sundayOfWeek(mon).toLocaleDateString("de-DE", { day: "numeric", month: "short", year: "numeric" })}`;
  root.appendChild(title);

  /** @type {{ bounds: ColumnBounds }[]} */
  const columns = [];
  for (let i = 0; i < 7; i += 1) {
    const d = new Date(mon);
    d.setDate(d.getDate() + i);
    columns.push({ bounds: columnDayBounds(d) });
  }

  const dowRow = document.createElement("div");
  dowRow.className = "calendar-week-top";
  const today = startOfDay(new Date());
  columns.forEach((col) => {
    const dow = document.createElement("div");
    dow.className = "calendar-week-dow";
    if (isSameLocalDate(col.bounds.start, today)) dow.classList.add("calendar-week-dow--today");
    dow.textContent = col.bounds.start.toLocaleDateString("de-DE", { weekday: "short", day: "numeric" });
    dowRow.appendChild(dow);
  });
  root.appendChild(dowRow);

  const adWrap = document.createElement("div");
  adWrap.className = "calendar-week-alldays";
  columns.forEach((col) => {
    const cel = document.createElement("div");
    cel.className = "calendar-week-col";
    const rr = document.createElement("div");
    rr.className = "calendar-allday-row";
    events.filter((ev) => overlapAllDay(ev, col.bounds)).forEach((e) => appendAllDayChip(rr, e));
    cel.appendChild(rr);
    adWrap.appendChild(cel);
  });
  root.appendChild(adWrap);

  const weekScroll = document.createElement("div");
  weekScroll.className = "calendar-week-scroll";
  const inner = document.createElement("div");
  inner.className = "calendar-week-rows";
  inner.appendChild(buildHourLabelsRail());

  const colsWrap = document.createElement("div");
  colsWrap.className = "calendar-week-columns";

  columns.forEach((col) => {
    const c = document.createElement("div");
    c.className = "calendar-week-col";
    if (isSameLocalDate(col.bounds.start, today)) c.classList.add("calendar-week-col--today");
    c.appendChild(renderTimedColumn(events, col.bounds));
    colsWrap.appendChild(c);
  });

  inner.appendChild(colsWrap);
  weekScroll.appendChild(inner);

  root.appendChild(weekScroll);

  container.innerHTML = "";
  container.appendChild(root);
  if (formRef) container.prepend(formRef);
}

function appendAllDayChip(row, ev) {
  const chip = document.createElement("div");
  chip.className = "calendar-allday-chip";
  chip.textContent = ev.title;
  if (conflictIds.has(ev.id)) chip.classList.add("calendar-event-card--conflict");
  chip.dataset.eventId = ev.id;
  chip.addEventListener("click", () => openDetailPanel(ev));
  chip.title = `${formatDate(ev.start)} — ${ev.title}`;
  row.appendChild(chip);
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

function calendarDetailPanelFieldEditingActive() {
  return !!document.querySelector("#calendar-detail-body .calendar-detail-field--active");
}

function formatCalendarDetailPanelWhenRead(ev) {
  const e = normEvent(ev);
  if (e.is_all_day) return `${formatDate(e.start)} — ganztägig`;
  return `${formatDate(e.start)}, ${formatTime(e.start)} – ${formatTime(e.end)}`;
}

/** @returns {string[]} */
function parseCalendarDetailParticipantInput(text) {
  const chunks = String(text ?? "")
    .split(/[,;\s\n\r]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set(chunks)];
}

function deactivateOtherCalendarDetailFields(bodyRoot, /** @type {HTMLElement} */ keep) {
  bodyRoot.querySelectorAll(".calendar-detail-field--active").forEach((node) => {
    if (!(node instanceof HTMLElement)) return;
    if (node === keep) return;
    node.classList.remove("calendar-detail-field--active");
    node.querySelectorAll(".calendar-detail-read").forEach((r) => {
      if (r instanceof HTMLElement) r.hidden = false;
    });
    node.querySelectorAll(".calendar-detail-edit").forEach((el) => {
      if (el instanceof HTMLElement) el.hidden = true;
    });
    const inp = /** @type {HTMLInputElement | HTMLTextAreaElement | null} */ (
      node.querySelector("input, textarea")
    );
    if (inp?.dataset.detailBaseline !== undefined) {
      inp.value = inp.dataset.detailBaseline ?? "";
    }
    const readWhen = /** @type {HTMLElement | null} */ (node.querySelector(".calendar-detail-field--when .calendar-detail-read"));
    if (readWhen instanceof HTMLElement && node.dataset.detailWhenBaseline !== undefined) {
      readWhen.textContent = node.dataset.detailWhenBaseline ?? "";
    }
    const inpS = /** @type {HTMLInputElement | null} */ (node.querySelector("[data-datetime=start]"));
    const inpE = /** @type {HTMLInputElement | null} */ (node.querySelector("[data-datetime=end]"));
    if (
      inpS &&
      inpE &&
      inpS.dataset.detailBaseline !== undefined &&
      inpE.dataset.detailBaseline !== undefined
    ) {
      inpS.value = inpS.dataset.detailBaseline ?? "";
      inpE.value = inpE.dataset.detailBaseline ?? "";
    }
  });
}

/**
 * Aktualisiert den geöffneten Detail‑Inhalt ohne laufende Inline‑Bearbeitung zu zerstören.
 */
function syncCalendarDetailPanelIfOpen() {
  const panel = document.getElementById("calendar-detail-panel");
  const bodyEl = document.getElementById("calendar-detail-body");
  if (!panel || !bodyEl || panel.hidden || !detailPanelEventId) return;
  if (calendarDetailPanelFieldEditingActive()) return;
  if (!sourceGoogleEnabled()) return;
  const raw = mergeEvents(localEvents).find((e) => e.id === detailPanelEventId);
  const titleEl = document.getElementById("calendar-detail-title");
  if (!raw) {
    hideEventDetails();
    return;
  }
  const ne = normEvent(raw);
  if (titleEl) titleEl.textContent = ne.title;
  detailPanelAbort?.abort();
  detailPanelAbort = new AbortController();
  populateCalendarDetailPanel(ne);
}

function populateCalendarDetailPanel(ev) {
  const titleEl = document.getElementById("calendar-detail-title");
  const bodyEl = document.getElementById("calendar-detail-body");
  const ac = detailPanelAbort;
  if (!bodyEl || !ac) return;
  if (titleEl) titleEl.textContent = normEvent(ev).title;
  buildAndWireCalendarDetailBody(bodyEl, normEvent(ev), ac.signal);
}

/**
 * PUT mit Teilfeldern; lokaler Optimismus + Refresh wie Agenda‑Inline‑Speichern.
 * @param {string} eventId
 * @param {Record<string, unknown>} patch
 */
async function patchCalendarEventFromDetail(eventId, patch) {
  const prev = mergeEvents(localEvents).map((e) => ({ ...e }));
  const optimistic = mergeEvents(localEvents).map((e) => {
    if (e.id !== eventId) return e;
    return normEvent({ ...e, ...patch });
  });
  localEvents = optimistic;
  renderCalendar();
  try {
    const updated = await apiFetchCalendar("PUT", `/events/${encodeURIComponent(eventId)}`, patch);
    localEvents = mergeEvents(localEvents).map((e) => (e.id === eventId ? normEvent(updated) : e));
    renderCalendar();
    showToast("Gespeichert", "success");
    await loadCalendarEvents({ preserveScroll: true });
  } catch (err) {
    localEvents = prev;
    renderCalendar();
    console.error("patchCalendarEventFromDetail:", err);
    showToast("Speichern fehlgeschlagen", "error");
  }
}

/**
 * @param {HTMLElement} bodyEl
 * @param {CalEventNorm} ev
 * @param {AbortSignal} signal
 */
function buildAndWireCalendarDetailBody(bodyEl, ev, signal) {
  bodyEl.textContent = "";
  const dl = document.createElement("dl");
  dl.className = "calendar-detail-dl";

  dl.appendChild(buildCalendarDetailWhenRow(ev, signal));

  dl.appendChild(
    buildCalendarDetailBlurRow(ev, "location", {
      signal,
      placeholder: "Ort hinzufügen …",
      emptyRead: "(Kein Ort)",
    })
  );

  dl.appendChild(
    buildCalendarDetailBlurRow(ev, "description", {
      signal,
      multiline: true,
      placeholder: "Beschreibung …",
      emptyRead: "(Keine Beschreibung)",
    })
  );

  dl.appendChild(buildCalendarDetailParticipantsRow(ev, signal));

  if (ev.recurrence_rule) {
    const wrap = document.createElement("div");
    wrap.className = "calendar-detail-field calendar-detail-field--static";
    const dt = document.createElement("dt");
    dt.textContent = "Wiederholung";
    const dd = document.createElement("dd");
    const code = document.createElement("code");
    code.textContent = String(ev.recurrence_rule);
    dd.appendChild(code);
    wrap.append(dt, dd);
    dl.appendChild(wrap);
  }

  bodyEl.appendChild(dl);
}

/**
 * @param {CalEventNorm} ev
 * @param {AbortSignal} signal
 */
function buildCalendarDetailWhenRow(ev, signal) {
  const wrap = document.createElement("div");
  wrap.className = "calendar-detail-field calendar-detail-field--when";
  wrap.dataset.field = "when";

  const dt = document.createElement("dt");
  dt.textContent = "Zeitraum";

  const dd = document.createElement("dd");

  const read = document.createElement("button");
  read.type = "button";
  read.className = "calendar-detail-read";
  read.textContent = formatCalendarDetailPanelWhenRead(ev);
  read.title = ev.is_all_day
    ? "Ganztägige Termine bitte direkt im Google Kalender verschieben."
    : "Klicken zum Bearbeiten";

  const edit = document.createElement("div");
  edit.className = "calendar-detail-edit";
  edit.hidden = true;

  const startInp = document.createElement("input");
  startInp.type = "datetime-local";
  startInp.dataset.datetime = "start";
  startInp.className = "calendar-detail-input";
  startInp.value = toDatetimeLocalValue(ev.start);

  const endInp = document.createElement("input");
  endInp.type = "datetime-local";
  endInp.dataset.datetime = "end";
  endInp.className = "calendar-detail-input";
  endInp.value = toDatetimeLocalValue(ev.end);

  wrap.dataset.detailWhenBaseline = read.textContent;
  startInp.dataset.detailBaseline = startInp.value;
  endInp.dataset.detailBaseline = endInp.value;

  if (ev.is_all_day) {
    read.disabled = true;
    read.classList.add("calendar-detail-read--disabled");
  }

  const actions = document.createElement("div");
  actions.className = "calendar-detail-inline-actions";

  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "calendar-detail-inline-btn calendar-detail-inline-btn--primary";
  saveBtn.textContent = "Übernehmen";

  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "calendar-detail-inline-btn";
  cancelBtn.textContent = "Abbrechen";

  actions.append(saveBtn, cancelBtn);
  edit.append(startInp, endInp, actions);

  dd.append(read, edit);
  wrap.append(dt, dd);

  if (!ev.is_all_day) {
    /** @returns {Promise<void>} */
    async function commitWhen() {
      const sv = startInp.value;
      const vv = endInp.value;
      if (!sv || !vv) {
        showToast("Start und Ende ausfüllen", "error");
        return;
      }
      const sIso = new Date(sv).toISOString();
      const eIso = new Date(vv).toISOString();
      if (new Date(eIso) <= new Date(sIso)) {
        showToast("Ende muss nach Start liegen", "error");
        return;
      }
      if (
        sIso === new Date(String(ev.start)).toISOString() &&
        eIso === new Date(String(ev.end)).toISOString()
      ) {
        wrap.classList.remove("calendar-detail-field--active");
        read.hidden = false;
        edit.hidden = true;
        return;
      }
      await patchCalendarEventFromDetail(ev.id, { start: sIso, end: eIso });
    }

    function closeEdit() {
      wrap.classList.remove("calendar-detail-field--active");
      read.hidden = false;
      edit.hidden = true;
      startInp.value = startInp.dataset.detailBaseline ?? "";
      endInp.value = endInp.dataset.detailBaseline ?? "";
      read.textContent = wrap.dataset.detailWhenBaseline ?? read.textContent;
    }

    read.addEventListener(
      "click",
      () => {
        deactivateOtherCalendarDetailFields(document.getElementById("calendar-detail-body") ?? dd, wrap);
        wrap.classList.add("calendar-detail-field--active");
        read.hidden = true;
        edit.hidden = false;
        startInp.focus();
      },
      { signal }
    );

    cancelBtn.addEventListener("click", () => closeEdit(), { signal });
    saveBtn.addEventListener("click", () => void commitWhen(), { signal });

    /** @param {KeyboardEvent} e */
    function onKeyStart(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        closeEdit();
      }
    }
    startInp.addEventListener("keydown", onKeyStart, { signal });
    endInp.addEventListener("keydown", onKeyStart, { signal });
    endInp.addEventListener(
      "keydown",
      (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          void commitWhen();
        }
      },
      { signal }
    );
  }

  return wrap;
}

/**
 * @param {CalEventNorm} ev
 * @param {"location"|"description"} field
 */
function buildCalendarDetailBlurRow(ev, field, { signal, placeholder, emptyRead, multiline = false }) {
  const wrap = document.createElement("div");
  wrap.className = "calendar-detail-field";
  wrap.dataset.field = field;

  const baseline = field === "location" ? (ev.location ? String(ev.location) : "") : (ev.description ? String(ev.description) : "");

  const dt = document.createElement("dt");
  dt.textContent = field === "location" ? "Ort" : "Beschreibung";

  const dd = document.createElement("dd");

  const read = multiline
    ? Object.assign(document.createElement("div"), {
        tabIndex: 0,
      })
    : document.createElement("button");

  if (!(read instanceof HTMLButtonElement)) {
    read.role = "button";
  } else read.type = "button";

  read.className =
    multiline ?
      `calendar-detail-read calendar-detail-read--block ${field === "description" ? "calendar-detail-read--pre" : ""}`
    : `calendar-detail-read calendar-detail-read--block`;

  const displayText = baseline.trim().length === 0 ? emptyRead : baseline;
  if (multiline) read.textContent = displayText;
  else read.textContent = displayText;
  read.title = "Klicken zum Bearbeiten";

  const edit = document.createElement("div");
  edit.className = "calendar-detail-edit";
  edit.hidden = true;

  const inp =
    multiline ?
      document.createElement("textarea")
    : document.createElement("input");
  if (inp instanceof HTMLInputElement) {
    inp.type = "text";
  }
  inp.className =
    multiline ? "calendar-detail-textarea calendar-detail-input" : "calendar-detail-input";
  inp.placeholder = placeholder;
  inp.value = baseline;
  inp.dataset.detailBaseline = baseline;

  const hint = document.createElement("span");
  hint.className = "calendar-detail-save-hint";
  hint.hidden = multiline === false;
  hint.textContent = "Strg+Enter speichern · Escape schließen";

  edit.append(inp, hint);

  dd.append(read, edit);
  wrap.append(dt, dd);

  const bodyRoot = /** @returns {HTMLElement} */ () =>
    document.getElementById("calendar-detail-body") ?? document.body;

  /** @returns {Promise<void>} */
  async function commit() {
    const raw = inp.value.trim();
    const unchanged = raw === baseline;
    if (unchanged) {
      wrap.classList.remove("calendar-detail-field--active");
      read.hidden = false;
      edit.hidden = true;
      return;
    }
    if (field === "location") {
      await patchCalendarEventFromDetail(ev.id, { location: raw === "" ? "" : raw });
    } else {
      await patchCalendarEventFromDetail(ev.id, { description: raw });
    }
  }

  function closeEditRollback() {
    wrap.classList.remove("calendar-detail-field--active");
    read.hidden = false;
    edit.hidden = true;
    inp.value = inp.dataset.detailBaseline ?? "";
    const lbl = inp.value.trim().length === 0 ? emptyRead : inp.value;
    read.textContent = lbl;
  }

  const openEditor = () => {
    deactivateOtherCalendarDetailFields(bodyRoot(), wrap);
    wrap.classList.add("calendar-detail-field--active");
    read.hidden = true;
    edit.hidden = false;
    inp.focus();
    if ("select" in inp && typeof inp.select === "function") inp.select();
  };

  read.addEventListener("click", () => openEditor(), { signal });
  read.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openEditor();
      }
    },
    { signal }
  );

  inp.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeEditRollback();
      }
      if (multiline ? e.ctrlKey && e.key === "Enter" : e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void commit();
      }
    },
    { signal }
  );

  inp.addEventListener(
    "blur",
    () => {
      setTimeout(() => {
        if (!wrap.classList.contains("calendar-detail-field--active")) return;
        const active =
          typeof document.activeElement?.closest === "function" ?
            /** @type {HTMLElement | null} */ (
              document.activeElement?.closest(".calendar-detail-field")
            )
          : null;
        if (active === wrap) return;
        if (wrap.contains(document.activeElement)) return;
        void commit();
      }, 170);
    },
    { signal }
  );

  return wrap;
}

/**
 * @param {CalEventNorm} ev
 * @param {AbortSignal} signal
 */
function buildCalendarDetailParticipantsRow(ev, signal) {
  const wrap = document.createElement("div");
  wrap.className = "calendar-detail-field calendar-detail-field--attendees";
  wrap.dataset.field = "attendees";

  const baselineList = Array.isArray(ev.attendees) ? [...ev.attendees].map(String) : [];
  const baselineText = baselineList.join("\n");

  const dt = document.createElement("dt");
  dt.textContent = "Teilnehmer";

  const dd = document.createElement("dd");

  const read = document.createElement("button");
  read.type = "button";
  read.className = `calendar-detail-read calendar-detail-read--block`;
  read.textContent =
    baselineList.length === 0 ? "Keine Teilnehmer — hier klicken" : baselineList.join(", ");
  read.title = "Teilnehmer bearbeiten (E‑Mails, eine pro Zeile)";

  const edit = document.createElement("div");
  edit.className = "calendar-detail-edit";
  edit.hidden = true;

  const ta = document.createElement("textarea");
  ta.className = "calendar-detail-textarea calendar-detail-input";
  ta.rows = 5;
  ta.placeholder = "E‑Mail-Adressen, durch Zeilenumbruch oder Komma getrennt";
  ta.value = baselineText;
  ta.dataset.detailBaseline = baselineText;

  const hint = document.createElement("span");
  hint.className = "calendar-detail-save-hint";
  hint.textContent = "Übernehmen speichern · Escape bricht ohne Speichern ab";

  const actions = document.createElement("div");
  actions.className = "calendar-detail-inline-actions";

  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "calendar-detail-inline-btn calendar-detail-inline-btn--primary";
  saveBtn.textContent = "Übernehmen";

  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "calendar-detail-inline-btn";
  cancelBtn.textContent = "Abbrechen";

  actions.append(saveBtn, cancelBtn);
  edit.append(ta, hint, actions);

  dd.append(read, edit);
  wrap.append(dt, dd);

  const bodyRoot = () => document.getElementById("calendar-detail-body") ?? document.body;

  /** @returns {boolean} */
  function arraySeqEq(/** @type {string[]} */ a, /** @type {string[]} */ b) {
    return a.length === b.length && a.every((v, i) => v === b[i]);
  }

  /** @returns {Promise<void>} */
  async function commit() {
    const next = parseCalendarDetailParticipantInput(ta.value);
    if (arraySeqEq(next, baselineList)) {
      wrap.classList.remove("calendar-detail-field--active");
      read.hidden = false;
      edit.hidden = true;
      return;
    }
    await patchCalendarEventFromDetail(ev.id, { attendees: next });
  }

  function closeEditRollback() {
    wrap.classList.remove("calendar-detail-field--active");
    read.hidden = false;
    edit.hidden = true;
    ta.value = ta.dataset.detailBaseline ?? "";
    read.textContent =
      baselineList.length === 0 ? "Keine Teilnehmer — hier klicken" : baselineList.join(", ");
  }

  function openEditor() {
    deactivateOtherCalendarDetailFields(bodyRoot(), wrap);
    wrap.classList.add("calendar-detail-field--active");
    read.hidden = true;
    edit.hidden = false;
    ta.focus();
  }

  read.addEventListener("click", () => openEditor(), { signal });
  ta.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeEditRollback();
      }
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        void commit();
      }
    },
    { signal }
  );
  ta.addEventListener(
    "blur",
    () => {
      setTimeout(() => {
        if (!wrap.classList.contains("calendar-detail-field--active")) return;
        if (wrap.contains(document.activeElement)) return;
        void commit();
      }, 170);
    },
    { signal }
  );
  cancelBtn.addEventListener("click", () => closeEditRollback(), { signal });
  saveBtn.addEventListener("click", () => void commit(), { signal });

  return wrap;
}

/**
 * Detail-Öffnung per Kachel-Klick — Inline nur per Doppelklick (Titel/Zeit), damit Detail-Panel der Standard ist.
 */
function bindOpenDetailPanelOnCard(card, eventId) {
  card.addEventListener("click", (e) => {
    const target = e.target instanceof Element ? e.target : null;
    if (!target) return;
    if (target.closest(".event-delete-btn")) return;
    if (target.closest("button")) return;
    if (target.closest("input") || target.closest("textarea")) return;
    if (editingEventId === eventId) return;

    const ev = mergeEvents(localEvents).find((x) => x.id === eventId);
    if (ev) openDetailPanel(ev);
  });
}

/** @typedef {{ summary: string, actions: Array<{ type: string, event_id?: string | null, payload?: Record<string, unknown> }>, risk_level: string }} CalendarAIPlanData */

/** @type {CalendarAIPlanData | null} */
let pendingAiPlan = null;

const CALENDAR_AI_QUICK_COMMANDS = {
  optimize_day:
    "Optimiere meinen Kalender für weniger Kontextwechsel: gruppiere Termine sinnvoll und schlage mindestens einen 2‑Stunden‑Fokusblock in einem freien Slot vor. Bestehende Termine nicht löschen, höchstens verschieben wenn der Auftrag passt.",
  focus_block:
    "Blockiere ein 2‑Stunden‑Fokusfenster für Tiefarbeit mit dem Titel «Fokuszeit» — wähle den nächstmöglichen freien Slot heute oder morgen und lege dafür ein neues Kalenderereignis an.",
};

function localYYYYMMDD(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function aiPlanReferenceDate() {
  return localYYYYMMDD(calendarViewAnchor || new Date());
}

function eventSnapshotLine(ev) {
  if (!ev) return "—";
  return `${ev.title} · ${formatDate(ev.start)} ${formatTime(ev.start)}–${formatTime(ev.end)}`;
}

function mergedPreviewLine(baseEv, payload) {
  /** @type {Record<string, unknown>} */
  const p = typeof payload === "object" && payload !== null ? payload : {};
  const title = typeof p.title === "string" && p.title.trim() ? p.title : baseEv?.title || "(Ohne Titel)";
  const start = typeof p.start === "string" ? p.start : baseEv?.start;
  const end = typeof p.end === "string" ? p.end : baseEv?.end;
  return `${title} · ${start ? `${formatDate(String(start))} ${formatTime(String(start))}` : "?"}–${end ? formatTime(String(end)) : "?"}`;
}

function findMergedEventById(eventId) {
  return mergeEvents(localEvents).find((e) => String(e.id) === String(eventId));
}

/**
 * @param {{ type: string, event_id?: string | null, payload?: Record<string, unknown> }} action
 * @returns {{ before: string, after: string }}
 */
function describeAiActionDiff(action) {
  const pl = action.payload || {};
  if (action.type === "create") {
    const line = mergedPreviewLine(null, pl);
    return { before: "—", after: line };
  }
  const ev = action.event_id ? findMergedEventById(action.event_id) : undefined;
  if (action.type === "delete") {
    return { before: ev ? eventSnapshotLine(ev) : "(Unbekanntes Event)", after: "(löschen)" };
  }
  if (action.type === "update" || action.type === "move") {
    return { before: ev ? eventSnapshotLine(ev) : "(Unbekannt)", after: mergedPreviewLine(ev, pl) };
  }
  return { before: "—", after: JSON.stringify(pl) };
}

function hideAiPlanOverlay() {
  const ov = document.getElementById("calendar-ai-overlay");
  if (ov) ov.hidden = true;
  pendingAiPlan = null;
}

/**
 * @param {CalendarAIPlanData} plan
 */
function renderAiPlanOverlay(plan) {
  pendingAiPlan = plan;
  const ov = document.getElementById("calendar-ai-overlay");
  const sumEl = document.getElementById("calendar-ai-plan-summary");
  const riskEl = document.getElementById("calendar-ai-plan-risk");
  const listEl = document.getElementById("calendar-ai-plan-actions");
  if (!ov || !sumEl || !riskEl || !listEl) return;

  sumEl.textContent = plan.summary || "";
  riskEl.textContent = `Risiko: ${plan.risk_level || "low"}`;
  riskEl.classList.remove("calendar-ai-plan-risk--high", "calendar-ai-plan-risk--medium");
  if (plan.risk_level === "high") riskEl.classList.add("calendar-ai-plan-risk--high");
  else if (plan.risk_level === "medium") riskEl.classList.add("calendar-ai-plan-risk--medium");

  listEl.innerHTML = "";
  (plan.actions || []).forEach((action, idx) => {
    const { before, after } = describeAiActionDiff(action);
    const li = document.createElement("li");
    li.className = "calendar-ai-diff-item";

    const type = document.createElement("div");
    type.className = "calendar-ai-diff-type";
    type.textContent = `${idx + 1}. ${action.type}${action.event_id ? ` · ${action.event_id}` : ""}`;
    li.appendChild(type);

    const r1 = document.createElement("div");
    r1.className = "calendar-ai-diff-row";
    const l1 = document.createElement("span");
    l1.className = "calendar-ai-diff-label";
    l1.textContent = "Vorher: ";
    r1.appendChild(l1);
    r1.appendChild(document.createTextNode(before));

    const r2 = document.createElement("div");
    r2.className = "calendar-ai-diff-row";
    const l2 = document.createElement("span");
    l2.className = "calendar-ai-diff-label";
    l2.textContent = "Nachher: ";
    r2.appendChild(l2);
    r2.appendChild(document.createTextNode(after));

    li.appendChild(r1);
    li.appendChild(r2);
    listEl.appendChild(li);
  });

  ov.hidden = false;
}

/**
 * @param {string} command
 */
async function requestCalendarAiPlan(command) {
  const trimmed = command.trim();
  if (!trimmed) {
    showToast("Bitte einen Befehl eingeben", "error");
    return null;
  }
  const btn = document.getElementById("calendar-ai-plan-btn");
  if (btn) btn.disabled = true;
  try {
    /** @type {CalendarAIPlanData} */
    const plan = await apiFetchCalendar("POST", "/ai/plan", {
      command: trimmed,
      date: aiPlanReferenceDate(),
      context: {
        preferences: { deep_work_preference: true },
        calendar_view_mode: calendarViewMode,
      },
    });
    renderAiPlanOverlay(plan);
    return plan;
  } catch (err) {
    console.error("AI plan failed:", err);
    showToast(`KI‑Plan fehlgeschlagen: ${err instanceof Error ? err.message : String(err)}`, "error");
    return null;
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function executePendingAiPlan() {
  const plan = pendingAiPlan;
  if (!plan?.actions?.length) {
    showToast("Keine Aktionen zum Anwenden", "info");
    return;
  }

  const applyBtn = document.getElementById("calendar-ai-plan-apply");
  const cancelBtn = document.getElementById("calendar-ai-plan-cancel");
  if (applyBtn) applyBtn.disabled = true;
  if (cancelBtn) cancelBtn.disabled = true;

  try {
    for (let i = 0; i < plan.actions.length; i += 1) {
      const a = plan.actions[i];
      const pl = a.payload || {};
      if (a.type === "create") {
        const title = typeof pl.title === "string" ? pl.title.trim() : "";
        const start = typeof pl.start === "string" ? pl.start : "";
        const end = typeof pl.end === "string" ? pl.end : "";
        if (!title || !start || !end) throw new Error(`Aktion ${i + 1} (create): Titel/Zeiten fehlen`);
        await apiFetchCalendar("POST", "/events", {
          title,
          start,
          end,
          timezone: typeof pl.timezone === "string" ? pl.timezone : "Europe/Berlin",
          location: pl.location ?? null,
          description: pl.description ?? null,
        });
      } else if (a.type === "update" || a.type === "move") {
        if (!a.event_id) throw new Error(`Aktion ${i + 1}: event_id fehlt`);
        const body = {};
        if (typeof pl.title === "string") body.title = pl.title;
        if (typeof pl.start === "string") body.start = pl.start;
        if (typeof pl.end === "string") body.end = pl.end;
        if (typeof pl.location === "string") body.location = pl.location;
        if (typeof pl.description === "string") body.description = pl.description;
        if (typeof pl.timezone === "string") body.timezone = pl.timezone;
        if (typeof pl.is_all_day === "boolean") body.is_all_day = pl.is_all_day;
        if (Object.keys(body).length === 0) throw new Error(`Aktion ${i + 1}: keine Felder zum Aktualisieren`);
        await apiFetchCalendar("PUT", `/events/${encodeURIComponent(a.event_id)}`, body);
      } else if (a.type === "delete") {
        if (!a.event_id) throw new Error(`Aktion ${i + 1}: event_id fehlt`);
        await apiFetchCalendar("DELETE", `/events/${encodeURIComponent(a.event_id)}`);
      } else {
        throw new Error(`Unbekannte Aktion: ${a.type}`);
      }
    }
    hideAiPlanOverlay();
    await loadCalendarEvents({ preserveScroll: true });
    showToast("KI‑Plan angewendet", "success");
  } catch (err) {
    console.error("executePendingAiPlan:", err);
    showToast(`Anwenden fehlgeschlagen: ${err instanceof Error ? err.message : String(err)}`, "error");
  } finally {
    if (applyBtn) applyBtn.disabled = false;
    if (cancelBtn) cancelBtn.disabled = false;
  }
}

function initCalendarAiControls() {
  document.getElementById("calendar-ai-plan-btn")?.addEventListener("click", async () => {
    const ta = /** @type {HTMLTextAreaElement | null} */ (document.getElementById("calendar-ai-command"));
    await requestCalendarAiPlan(ta?.value || "");
  });

  document.querySelectorAll("[data-ai-quick]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const key = btn.getAttribute("data-ai-quick");
      const cmd = key && CALENDAR_AI_QUICK_COMMANDS[/** @type {keyof typeof CALENDAR_AI_QUICK_COMMANDS} */ (key)];
      if (!cmd) return;
      const ta = /** @type {HTMLTextAreaElement | null} */ (document.getElementById("calendar-ai-command"));
      if (ta) ta.value = cmd;
      await requestCalendarAiPlan(cmd);
    });
  });

  document.getElementById("calendar-ai-plan-apply")?.addEventListener("click", () => executePendingAiPlan());
  document.getElementById("calendar-ai-plan-cancel")?.addEventListener("click", () => hideAiPlanOverlay());
  document.getElementById("calendar-ai-overlay-backdrop")?.addEventListener("click", () => hideAiPlanOverlay());
}

/**
 * @param {{ preserveScroll?: boolean, silentPolling?: boolean }} [options]
 */
async function loadCalendarEvents(options = {}) {
  const { preserveScroll = false, silentPolling = false } =
    typeof options === "object" && options !== null ? options : {};

  if (silentPolling) {
    if (!isCalendarPanelVisible()) return localEvents;
    if (!calendarModalVisibleDom()) return localEvents;
    if (editingEventId !== null) return localEvents;
    if (calendarDetailPanelFieldEditingActive()) return localEvents;
    const now = Date.now();
    if (now - lastCalendarLoadAt < 5000) return localEvents;
  }

  if (calendarLoadInFlight) {
    return calendarLoadInFlight;
  }

  /** @type {HTMLElement | null} */
  const scrollEl = preserveScroll
    ? document.querySelector(".calendar-content-pane")
    : null;
  const prevScrollTop = scrollEl ? scrollEl.scrollTop : 0;

  setSyncStatus("syncing");

  const run = (async () => {
    const q = buildEventsQuery();
    const data = await apiFetchCalendar("GET", `/events${q}`);
    localEvents = mergeEvents(data.events || []);
    applyConflicts(data.conflicts || []);
    renderCalendar();
    setSyncStatus("synced");
    lastCalendarLoadAt = Date.now();

    if (preserveScroll && scrollEl) {
      requestAnimationFrame(() => {
        scrollEl.scrollTop = prevScrollTop;
      });
    }

    return localEvents;
  })().catch((error) => {
    console.error("Failed to load calendar events:", error);
    setSyncStatus("error");
    if (!silentPolling) {
      showToast("Fehler beim Laden der Termine", "error");
    }
    return [];
  }).finally(() => {
    calendarLoadInFlight = null;
  });
  calendarLoadInFlight = run;
  return run;
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
  renderCalendar();

  try {
    const result = await apiFetchCalendar("POST", "/events", eventPayload);
    localEvents = localEvents.filter((e) => e.id !== tempId);
    localEvents.push(normEvent(result));
    renderCalendar();
    await loadCalendarEvents();
    showToast("Termin erstellt", "success");
    return result;
  } catch (error) {
    localEvents = prevEvents;
    renderCalendar();
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
  renderCalendar();

  try {
    await apiFetchCalendar("DELETE", `/events/${encodeURIComponent(eventId)}`);
    await loadCalendarEvents();
    showToast("Termin gelöscht", "success");
  } catch (error) {
    localEvents = snapshot;
    renderCalendar();
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
      if (preset === "today") {
        calendarViewMode = "day";
        calendarViewAnchor = startOfDay(new Date());
      } else if (preset === "week") {
        calendarViewMode = "week";
        calendarViewAnchor = startOfDay(new Date());
      } else if (preset === "month") {
        calendarViewMode = "month";
        calendarViewAnchor = startOfDay(new Date());
        calendarMiniMonthAnchor = startOfMonth(calendarViewAnchor);
      }
      syncFilterUi();
      syncCalendarViewToggleUi();
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
    renderCalendar();
  });

  document.querySelectorAll(".calendar-quick-nav-btn[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const preset = btn.getAttribute("data-filter");
      if (!preset) return;
      filterPreset = preset;
      calendarViewMode = preset === "today" ? "day" : preset === "month" ? "month" : "week";
      calendarViewAnchor = startOfDay(new Date());
      syncFilterUi();
      syncCalendarViewToggleUi();
      loadCalendarEvents();
    });
  });

  syncCalendarViewToggleUi();

  document.querySelectorAll(".calendar-view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = btn.getAttribute("data-view");
      if (v !== "day" && v !== "week" && v !== "month") return;
      calendarViewMode = v;
      filterPreset = v === "day" ? "today" : v;
      syncCalendarViewToggleUi();
      syncFilterUi();
      loadCalendarEvents();
    });
  });

  document.getElementById("calendar-search-input")?.addEventListener("input", (event) => {
    const target = event.target;
    calendarSearchTerm = target instanceof HTMLInputElement ? target.value : "";
    renderCalendar();
  });

  document.getElementById("calendar-prev-btn")?.addEventListener("click", () => {
    if (calendarViewMode === "day") calendarViewAnchor.setDate(calendarViewAnchor.getDate() - 1);
    else if (calendarViewMode === "week") calendarViewAnchor.setDate(calendarViewAnchor.getDate() - 7);
    else calendarViewAnchor.setMonth(calendarViewAnchor.getMonth() - 1);
    calendarViewAnchor = startOfDay(calendarViewAnchor);
    if (calendarViewMode === "month") calendarMiniMonthAnchor = startOfMonth(calendarViewAnchor);
    loadCalendarEvents();
  });

  document.getElementById("calendar-next-btn")?.addEventListener("click", () => {
    if (calendarViewMode === "day") calendarViewAnchor.setDate(calendarViewAnchor.getDate() + 1);
    else if (calendarViewMode === "week") calendarViewAnchor.setDate(calendarViewAnchor.getDate() + 7);
    else calendarViewAnchor.setMonth(calendarViewAnchor.getMonth() + 1);
    calendarViewAnchor = startOfDay(calendarViewAnchor);
    if (calendarViewMode === "month") calendarMiniMonthAnchor = startOfMonth(calendarViewAnchor);
    loadCalendarEvents();
  });

  document.getElementById("calendar-today-btn")?.addEventListener("click", () => {
    calendarViewAnchor = startOfDay(new Date());
    calendarMiniMonthAnchor = startOfMonth(calendarViewAnchor);
    loadCalendarEvents();
  });

  document.getElementById("calendar-mini-prev-btn")?.addEventListener("click", () => {
    calendarMiniMonthAnchor.setMonth(calendarMiniMonthAnchor.getMonth() - 1);
    renderMiniMonth();
  });

  document.getElementById("calendar-mini-next-btn")?.addEventListener("click", () => {
    calendarMiniMonthAnchor.setMonth(calendarMiniMonthAnchor.getMonth() + 1);
    renderMiniMonth();
  });

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
  renderMiniMonth();
  updatePeriodLabel();
}

function showCreateEventForm() {
  if (document.getElementById("calendar-create-dialog-overlay")) return;

  const host = document.body;
  const overlay = document.createElement("div");
  overlay.id = "calendar-create-dialog-overlay";
  overlay.className = "calendar-create-dialog-overlay";
  overlay.innerHTML = `
    <div class="calendar-create-dialog-backdrop" data-close="backdrop"></div>
    <div class="calendar-create-dialog-window" role="dialog" aria-modal="true" aria-label="Neuen Termin erstellen">
      <div class="calendar-create-form">
        <div class="form-header">
          <h3>Neuer Termin</h3>
          <button type="button" class="form-close-btn" data-close="x">×</button>
        </div>
        <form id="calendar-create-event-form">
          <div class="form-group">
            <label for="calendar-create-summary">Titel</label>
            <input type="text" id="calendar-create-summary" required placeholder="Termin-Titel">
          </div>
          <div class="form-group">
            <label for="calendar-create-start">Startzeit</label>
            <input type="datetime-local" id="calendar-create-start" required>
            <div class="calendar-duration-buttons">
              <button type="button" class="duration-btn" data-minutes="15">15m</button>
              <button type="button" class="duration-btn" data-minutes="30">30m</button>
              <button type="button" class="duration-btn" data-minutes="60">1h</button>
              <button type="button" class="duration-btn" data-minutes="120">2h</button>
              <button type="button" class="duration-btn" data-minutes="180">3h</button>
            </div>
          </div>
          <div class="form-group">
            <label for="event-is-all-day" class="checkbox-label">
              <input type="checkbox" id="event-is-all-day">
              <span>Ganztägig</span>
            </label>
          </div>
          <div class="form-group">
            <label for="calendar-create-end">Endzeit</label>
            <input type="datetime-local" id="calendar-create-end" required>
          </div>
          <div class="form-group">
            <label for="calendar-create-location">Ort (optional)</label>
            <input type="text" id="calendar-create-location" placeholder="Ort">
          </div>
          <div class="form-group">
            <label for="calendar-create-description">Beschreibung (optional)</label>
            <textarea id="calendar-create-description" rows="3" placeholder="Beschreibung"></textarea>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-primary">Termin erstellen</button>
            <button type="button" class="btn-secondary" data-close="cancel">Abbrechen</button>
          </div>
        </form>
      </div>
    </div>
  `;
  host.appendChild(overlay);

  const closeDialog = () => overlay.remove();
  overlay.querySelectorAll("[data-close]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeDialog();
    });
  });

  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  /** @type {HTMLInputElement | null} */
  const startEl = overlay.querySelector("#calendar-create-start");
  /** @type {HTMLInputElement | null} */
  const endEl = overlay.querySelector("#calendar-create-end");
  /** @type {HTMLInputElement | null} */
  const allDayEl = overlay.querySelector("#event-is-all-day");
  const durationButtonsEl = overlay.querySelector(".calendar-duration-buttons");
  if (startEl) startEl.value = now.toISOString().slice(0, 16);
  const endTime = new Date(now.getTime() + 60 * 60 * 1000);
  if (endEl) endEl.value = endTime.toISOString().slice(0, 16);

  const toLocalISOString = (date) => {
    const offset = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - offset).toISOString().slice(0, 16);
  };

  let selectedDurationMinutes = 60;

  const updateEndTime = () => {
    if (!startEl || !endEl || selectedDurationMinutes === null) return;
    const startValue = startEl.value;
    if (!startValue) return;
    const startDate = new Date(startValue);
    if (Number.isNaN(startDate.getTime())) return;
    const endDate = new Date(startDate.getTime() + selectedDurationMinutes * 60000);
    endEl.value = toLocalISOString(endDate);
  };

  overlay.querySelectorAll(".duration-btn").forEach((btn) => {
    if (parseInt(btn.getAttribute("data-minutes") || "0", 10) === 60) {
      btn.classList.add("active");
    }
    btn.addEventListener("click", () => {
      const minutes = parseInt(btn.getAttribute("data-minutes") || "0", 10);
      selectedDurationMinutes = minutes;
      overlay.querySelectorAll(".duration-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      updateEndTime();
    });
  });

  startEl?.addEventListener("change", updateEndTime);
  startEl?.addEventListener("input", updateEndTime);

  const toggleAllDay = () => {
    if (!allDayEl || !startEl || !endEl || !durationButtonsEl) return;
    const isAllDay = allDayEl.checked;
    if (isAllDay) {
      const startDateValue = startEl.value;
      const endDateValue = endEl.value;
      startEl.type = "date";
      endEl.type = "date";
      if (startDateValue) startEl.value = startDateValue.slice(0, 10);
      if (endDateValue) endEl.value = endDateValue.slice(0, 10);
      durationButtonsEl.style.display = "none";
    } else {
      const startDateValue = startEl.value;
      const endDateValue = endEl.value;
      startEl.type = "datetime-local";
      endEl.type = "datetime-local";
      if (startDateValue) startEl.value = startDateValue + "T09:00";
      if (endDateValue) endEl.value = endDateValue + "T10:00";
      durationButtonsEl.style.display = "flex";
    }
  };

  allDayEl?.addEventListener("change", toggleAllDay);

  overlay.querySelector("#calendar-create-event-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const summary = /** @type {HTMLInputElement | null} */ (overlay.querySelector("#calendar-create-summary"))?.value || "";
    const startTime = /** @type {HTMLInputElement | null} */ (overlay.querySelector("#calendar-create-start"))?.value || "";
    const endTimeVal = /** @type {HTMLInputElement | null} */ (overlay.querySelector("#calendar-create-end"))?.value || "";
    const location = /** @type {HTMLInputElement | null} */ (overlay.querySelector("#calendar-create-location"))?.value || "";
    const description =
      /** @type {HTMLTextAreaElement | null} */ (overlay.querySelector("#calendar-create-description"))?.value || "";

    const isAllDay = overlay.querySelector("#event-is-all-day")?.checked || false;
    const eventPayload = {
      title: summary.trim(),
      start: new Date(startTime).toISOString(),
      end: new Date(endTimeVal).toISOString(),
      timezone: "Europe/Berlin",
      location: location?.trim() || null,
      description: description?.trim() || null,
      is_all_day: isAllDay,
    };

    try {
      await createCalendarEvent(eventPayload);
      window.dispatchEvent(new CustomEvent('calendar-refresh'));
      closeDialog();
    } catch {
      /* Fehler bereits behandelt */
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initCalendarFilters();
  initCalendarAiControls();

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
    if (syncFromDockStateRunning) return;
    syncFromDockStateRunning = true;
    try {
    const visible = isCalendarPanelVisible();
    if (calendarView) {
      calendarView.style.display = visible ? "flex" : "none";
    }
    if (visible && !prevVisible && calendarHost) {
      prevVisible = true;
      try {
        loadCalendarEvents();
        startCalendarPoll();
      } catch {
        /* ignore */
      }
    }
    if (!visible) {
      closeDetailPanel();
      hideAiPlanOverlay();
      stopCalendarPoll();
    }
    prevVisible = visible;
    syncNavActive();
    } finally {
      syncFromDockStateRunning = false;
    }
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
      if (e.target instanceof Element && e.target.closest("button, input, textarea, select, label")) return;
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

  const detailCloseBtn = document.getElementById("calendar-detail-close-btn");
  if (detailCloseBtn instanceof HTMLButtonElement) {
    // Exklusiv setzen: ersetzt potenziell alte/inkonsistente Listener.
    detailCloseBtn.onclick = handleDetailCloseClick;
  }

  window.addEventListener('calendar-refresh', () => {
    loadCalendarEvents();
  });
});
