/**
 * Janus Tages-Panel — Sidebar-Toggle + rechter Chat-Rail.
 *
 * Architektur-Hinweis (Universal Modal / MCL):
 * Dieses Panel ist BEWUSST kein Floating-Dock-Modul (`registerDockModule` / `openModal`).
 * Es ist eingebetteter „Chrome“ am Chat-Arbeitsbereich (Diamond-Dossier: Zero Friction, kein zweites Popup).
 * Vollkalender bleibt MCL‑Modal (`dockOpen('calendar')`). Siehe modal-api.js + UNIVERSAL_MODAL_SYSTEM_DIAMOND_DOSSIER.
 */

import { API_BASE_URL } from "./config.js";
import {
  computePlanningStatsForDay,
  eventTone,
  formatHourAmount,
} from "./calendar-day-stats.js";
import { getWindowState } from "./window-state.js";

/** Kein statischer Import von calendar-modal: wenn dieses Modul beim Laden scheitert, darf × / Panel‑Chrome trotzdem funktionieren. */
function loadCalendarModalModule() {
  return import("./calendar-modal.js");
}

export const CALENDAR_DAY_WIDGET_STORAGE_KEY = "janus_calendar_day_widget_visible";

let refreshInFlight = null;
let /** @type {ReturnType<typeof setTimeout> | null} */ refreshDebounce = null;

function readStoredVisible() {
  try {
    const v = localStorage.getItem(CALENDAR_DAY_WIDGET_STORAGE_KEY);
    if (v === null) return false;
    return v === "1" || v === "true";
  } catch {
    return false;
  }
}

function persistVisible(visible) {
  try {
    localStorage.setItem(CALENDAR_DAY_WIDGET_STORAGE_KEY, visible ? "1" : "0");
  } catch {
    /* ignore */
  }
}

function sourceGoogleEnabled() {
  const el = document.getElementById("calendar-source-google");
  return !el || el.checked;
}

function todayQueryString() {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setHours(23, 59, 59, 999);
  const sp = new URLSearchParams();
  sp.set("start", start.toISOString());
  sp.set("end", end.toISOString());
  return `?${sp.toString()}`;
}

async function apiFetchCalendar(method, endpoint) {
  const token = localStorage.getItem("auth_token");
  /** @type {Record<string, string>} */
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  /** @type {RequestInit} */
  const options = { method, headers };
  let response = await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, options);
  if (response.status === 401) {
    if (typeof window.attemptSilentLogin === "function") await window.attemptSilentLogin();
    const newToken = localStorage.getItem("auth_token");
    if (newToken) headers.Authorization = `Bearer ${newToken}`;
    response = await fetch(`${API_BASE_URL}/api/calendar${endpoint}`, { ...options, headers });
  }
  if (!response.ok) {
    const t = await response.text().catch(() => "");
    throw new Error(`Kalender API ${response.status}: ${t.slice(0, 120)}`);
  }
  return response.json();
}

/** @param {Record<string, unknown>} ev */
function normEvent(ev) {
  const raw = ev || {};
  return {
    id: String(raw.id ?? ""),
    title: String(raw.title ?? raw.summary ?? "(Kein Titel)"),
    start: raw.start,
    end: raw.end,
    description: raw.description ?? null,
    location: raw.location ?? null,
    is_all_day: !!raw.is_all_day,
    html_link: raw.html_link != null ? String(raw.html_link) : null,
    hangout_link: raw.hangout_link != null ? String(raw.hangout_link) : null,
  };
}

/** @param {unknown} text */
function extractConferenceUrl(text) {
  if (text == null || text === "") return null;
  const s = String(text);
  const patterns = [
    /https:\/\/meet\.google\.com\/[a-z0-9\-?&=_]+/i,
    /https:\/\/[^\s)"']*zoom\.us\/(?:j\/|my\?)[^\s)"']+/i,
    /https:\/\/teams\.microsoft\.com\/[^\s)"']+/i,
  ];
  for (const re of patterns) {
    const m = s.match(re);
    if (m) return m[0].replace(/[,;.]$/, "");
  }
  return null;
}

/** @param {ReturnType<typeof normEvent>} ev */
function resolveJoinTarget(ev) {
  if (ev.hangout_link) return "video";
  const fromHang = extractConferenceUrl(ev.location) || extractConferenceUrl(ev.description);
  if (fromHang) return "video";
  if (ev.html_link) return "calendar";
  return null;
}

/** @param {ReturnType<typeof normEvent>} ev */
function resolveJoinUrl(ev) {
  if (ev.hangout_link) return ev.hangout_link;
  const extracted = extractConferenceUrl(ev.location) || extractConferenceUrl(ev.description);
  if (extracted) return extracted;
  if (ev.html_link) return ev.html_link;
  return null;
}

/** Zweite Zeile unter dem Titel („Zoom Meeting“ / Ort). */
/** @param {ReturnType<typeof normEvent>} ev */
/** @param {string | null} joinUrl */
function joinSubline(ev, joinUrl) {
  if (ev.location && String(ev.location).trim()) {
    const loc = String(ev.location).trim();
    if (!joinUrl || !loc.includes("http")) return loc.slice(0, 120);
  }
  if (!joinUrl) return "";
  const u = joinUrl.toLowerCase();
  if (u.includes("meet.google.com")) return "Google Meet";
  if (u.includes("zoom.us")) return "Zoom Meeting";
  if (u.includes("teams.microsoft.com")) return "Microsoft Teams";
  return "Online-Termin";
}

function escapeAttr(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;");
}

/** @param {unknown} iso */
function formatTimeShort(iso) {
  try {
    return new Date(String(iso)).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

/** @param {unknown} isoStart */
function formatCountdown(isoStart) {
  try {
    const t = new Date(String(isoStart)).getTime() - Date.now();
    if (!Number.isFinite(t)) return "";
    if (t <= 0 && t > -3600000) return "Jetzt";
    if (t <= 0) return "";
    const m = Math.round(t / 60000);
    if (m < 60) return `in ${m} Min`;
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return rm ? `in ${h} Std ${rm} Min` : `in ${h} Std`;
  } catch {
    return "";
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

/** @param {ReturnType<typeof normEvent>} ev @param {number} ms */
function eventSpansInstant(ev, ms) {
  const s = new Date(String(ev.start)).getTime();
  const e = new Date(String(ev.end)).getTime();
  if (!Number.isFinite(s) || !Number.isFinite(e)) return false;
  return ms >= s && ms < e;
}

function escapeShouldLeaveDayPanelOpen() {
  if (document.getElementById("calendar-create-dialog-overlay")) return true;
  const consent = document.getElementById("consent-modal");
  if (consent && !consent.classList.contains("hidden")) return true;
  const mods = getWindowState()?.dock?.modules || {};
  return Object.values(mods).some((m) => m && m.exists && m.isOpen && !m.minimized);
}

/** Rail wirklich sichtbar/klickbar (nicht nur `hidden`-Attribut — sonst schließt × ohne Effekt). */
function dayPanelIsOpen() {
  const rail = document.getElementById("calendar-day-widget-rail");
  if (!rail) return false;
  const cs = getComputedStyle(rail);
  if (cs.display === "none" || cs.visibility === "hidden") return false;
  const op = parseFloat(cs.opacity || "1");
  return !Number.isFinite(op) || op > 0;
}

/** @param {ReturnType<typeof normEvent>[]} allNorm */
function renderDayWidgetBody(allNorm) {
  const mount = document.getElementById("calendar-day-widget-body");
  if (!mount) return;

  if (!sourceGoogleEnabled()) {
    mount.innerHTML =
      `<p class="calendar-day-widget-muted">Google‑Kalender ist in den Kalenderfiltern deaktiviert.</p>`;
    return;
  }

  const stats = computePlanningStatsForDay(allNorm, new Date());
  const today = stats.todayEvents;
  const now = Date.now();

  /** @type {ReturnType<typeof normEvent> | undefined} */
  let next =
    [...allNorm]
      .filter((ev) => {
        const end = new Date(String(ev.end)).getTime();
        return Number.isFinite(end) && end >= now;
      })
      .sort((a, b) => new Date(String(a.start)) - new Date(String(b.start)))[0];

  const lp = stats.loadPercent;
  let html = `
      <section class="calendar-day-widget-section calendar-day-widget-stats-block" aria-label="Heute Kennzahlen">
        <div class="calendar-day-widget-kicker">Heute</div>
        <div class="calendar-day-widget-stats-grid">
          <div><strong>${stats.eventCount}</strong><span>Termine</span></div>
          <div><strong>${escapeHtml(formatHourAmount(stats.focusMinutes))}</strong><span>Fokuszeit</span></div>
          <div><strong>${lp}%</strong><span>Auslastung</span></div>
        </div>
        <div class="calendar-day-widget-load-meter" aria-hidden="true"><span style="width:${lp}%"></span></div>
      </section>`;

  if (next) {
    const tone = eventTone(next);
    const cd = next.is_all_day ? "" : formatCountdown(next.start);
    const timeRange = next.is_all_day ? "Ganztägig" : `${formatTimeShort(next.start)} – ${formatTimeShort(next.end)}`;
    const joinUrl = resolveJoinUrl(next);
    const target = resolveJoinTarget(next);
    const sub = joinSubline(next, joinUrl);

    let actionsHtml = "";
    const playIcon = `<svg class="calendar-day-widget-join-play" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>`;
    if (joinUrl && target === "video") {
      actionsHtml = `
        <div class="calendar-day-widget-next-actions">
          <button type="button" class="calendar-day-widget-join-btn" data-join-url="${escapeAttr(joinUrl)}">
            ${playIcon}
            <span>Beitreten</span>
          </button>
        </div>`;
    } else if (joinUrl && target === "calendar") {
      actionsHtml = `
        <div class="calendar-day-widget-next-actions">
          <button type="button" class="calendar-day-widget-join-btn calendar-day-widget-join-btn--secondary" data-join-url="${escapeAttr(joinUrl)}">Im Kalender öffnen</button>
        </div>`;
    }

    html += `
      <section class="calendar-day-widget-section calendar-day-widget-section--next" aria-label="Nächster Termin">
        <div class="calendar-day-widget-kicker">Nächster Termin</div>
        <div class="calendar-day-widget-next-card${cd ? " calendar-day-widget-next-card--haspill" : ""}">
          ${cd ? `<span class="calendar-day-widget-next-pill">${escapeHtml(cd)}</span>` : ""}
          <div class="calendar-day-widget-next-top">
            <span class="calendar-day-widget-next-dot calendar-day-widget-next-dot--${tone}" aria-hidden="true"></span>
            <div class="calendar-day-widget-next-copy">
              <div class="calendar-day-widget-next-range">${escapeHtml(timeRange)}</div>
              <div class="calendar-day-widget-next-heading">${escapeHtml(next.title)}</div>
              ${sub ? `<div class="calendar-day-widget-next-sub">${escapeHtml(sub)}</div>` : ""}
            </div>
          </div>
          ${actionsHtml}
        </div>
      </section>`;
  }

  if (today.length) {
    const nowLabel = formatTimeShort(new Date(now).toISOString());
    html += `
      <section class="calendar-day-widget-section calendar-day-widget-section--list" aria-label="Tagesplan">
        <div class="calendar-day-widget-kicker">Tagesplan (${today.length})</div>
        <div class="calendar-day-widget-now-marker" role="status">
          <span class="calendar-day-widget-now-dot" aria-hidden="true"></span>
          <span class="calendar-day-widget-now-label">Jetzt</span>
          <span class="calendar-day-widget-now-time">${escapeHtml(nowLabel)}</span>
        </div>
        <ul class="calendar-day-widget-timeline">
          ${today
            .slice(0, 12)
            .map(
              (ev) => `
            <li class="calendar-day-widget-slot${eventSpansInstant(ev, now) ? " calendar-day-widget-slot--active" : ""}">
              <span class="calendar-day-widget-slot-time">${ev.is_all_day ? "ganztägig" : escapeHtml(formatTimeShort(ev.start))}</span>
              <span class="calendar-day-widget-slot-title">${escapeHtml(ev.title)}</span>
            </li>`
            )
            .join("")}
        </ul>
        ${today.length > 12 ? `<p class="calendar-day-widget-muted">+ ${today.length - 12} weitere …</p>` : ""}
      </section>`;
  } else if (!next) {
    html += `<p class="calendar-day-widget-muted calendar-day-widget-empty-day">Keine Termine für heute.</p>`;
  }

  mount.innerHTML = html;
}

async function refreshDayPanelData() {
  if (!dayPanelIsOpen()) return;

  if (!sourceGoogleEnabled()) {
    renderDayWidgetBody([]);
    return;
  }

  refreshInFlight = (async () => {
    const data = await apiFetchCalendar("GET", `/events${todayQueryString()}`);
    const raw = Array.isArray(data.events) ? data.events : [];
    const allNorm = raw.map(normEvent).filter((e) => e.id);
    renderDayWidgetBody(allNorm);
  })();

  try {
    await refreshInFlight;
  } catch (e) {
    console.warn("calendar-day-widget:", e);
    const mount = document.getElementById("calendar-day-widget-body");
    if (mount)
      mount.innerHTML = `<p class="calendar-day-widget-muted calendar-day-widget--error">Termine konnten nicht geladen werden. Kalender öffnen und erneut versuchen.</p>`;
  } finally {
    refreshInFlight = null;
  }
}

function scheduleRefresh() {
  if (refreshDebounce) clearTimeout(refreshDebounce);
  refreshDebounce = setTimeout(() => {
    refreshDebounce = null;
    void refreshDayPanelData();
  }, 280);
}

function syncChrome(visible, { btn, rail, chatView }) {
  btn?.setAttribute("aria-pressed", visible ? "true" : "false");
  btn?.classList.toggle("sidebar-nav-item--active", visible);
  chatView?.classList.toggle("calendar-day-widget-visible", visible);

  if (rail) {
    if (visible) {
      rail.removeAttribute("hidden");
      rail.setAttribute("aria-hidden", "false");
      scheduleRefresh();
    } else {
      rail.setAttribute("hidden", "");
      rail.setAttribute("aria-hidden", "true");
    }
  }
}

function setDayPanelVisible(visible, els) {
  persistVisible(visible);
  syncChrome(visible, els);
}

/** @returns {boolean} neuer sichtbarer Zustand */
export function toggleDayPanel() {
  const rail = document.getElementById("calendar-day-widget-rail");
  if (!rail) return false;
  const visible = dayPanelIsOpen();
  const next = !visible;
  setDayPanelVisible(next, collectEls());
  return next;
}

function collectEls() {
  return {
    btn: document.getElementById("sidebar-nav-day-panel"),
    rail: document.getElementById("calendar-day-widget-rail"),
    chatView: document.getElementById("chat-view"),
  };
}

function ensureJoinClickDelegation() {
  const body = document.getElementById("calendar-day-widget-body");
  if (!body || body.dataset.cdwJoinBound === "1") return;
  body.dataset.cdwJoinBound = "1";
  body.addEventListener("click", (e) => {
    const t =
      e.target && typeof e.target.closest === "function"
        ? e.target.closest("[data-join-url]")
        : null;
    if (!(t instanceof HTMLElement)) return;
    const u = t.getAttribute("data-join-url");
    if (!u) return;
    e.preventDefault();
    try {
      window.open(u, "_blank", "noopener,noreferrer");
    } catch {
      /* ignore */
    }
  });
}

function pointerHitDismissZone(ev, el) {
  if (!(el instanceof HTMLElement)) return false;
  const r = el.getBoundingClientRect();
  return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
}

/** Sofort beim Laden — nicht erst nach weiterem Init (Imports anderer Module können sonst dieses Script nie ausführen). */
function attachDayPanelDismissGloballyOnce() {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  if (document.documentElement.dataset.janusCdwDismissGlob === "1") return;
  document.documentElement.dataset.janusCdwDismissGlob = "1";

  window.janusCloseDayPanel = (ev) => {
    ev?.preventDefault?.();
    ev?.stopPropagation?.();
    if (!dayPanelIsOpen()) return;
    setDayPanelVisible(false, collectEls());
  };

  function dismissFromCloseControl(e, source) {
    if (!dayPanelIsOpen()) return;
    const closeBtn = document.getElementById("calendar-day-widget-close");
    if (!closeBtn || !(closeBtn instanceof HTMLElement)) return;
    const raw = e.target;
    const el = raw instanceof Element ? raw : raw?.parentElement;
    const directOnClose = !!(el && closeBtn.contains(el));
    if (!directOnClose && !pointerHitDismissZone(e, closeBtn)) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    setDayPanelVisible(false, collectEls());
    if (typeof localStorage !== "undefined" && localStorage.getItem("janus_debug_day_panel") === "1") {
      console.info("[calendar-day-widget] geschlossen:", source);
    }
  }

  document.addEventListener(
    "pointerdown",
    (e) => {
      if (e.button !== 0) return;
      dismissFromCloseControl(e, "pointerdown");
    },
    true
  );

  document.addEventListener(
    "click",
    (e) => {
      const raw = e.target;
      const el = raw instanceof Element ? raw : raw?.parentElement;
      const t = el && typeof el.closest === "function" ? el.closest("#calendar-day-widget-close") : null;
      if (!t) return;
      dismissFromCloseControl(e, "click");
    },
    true
  );

  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key !== "Escape") return;
      if (!dayPanelIsOpen()) return;
      if (escapeShouldLeaveDayPanelOpen()) return;
      e.preventDefault();
      setDayPanelVisible(false, collectEls());
    },
    true
  );
}

attachDayPanelDismissGloballyOnce();

function initCalendarDayWidget() {
  ensureJoinClickDelegation();

  document.getElementById("cdw-quick-create")?.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const mod = await loadCalendarModalModule();
      mod.openCalendarQuickCreateDialog();
    } catch (err) {
      console.warn("[calendar-day-widget] Schnellerstellung:", err);
    }
  });

  document.getElementById("cdw-quick-calendar")?.addEventListener("click", (e) => {
    e.preventDefault();
    if (typeof window.dockOpen === "function") window.dockOpen("calendar");
  });

  document.getElementById("cdw-quick-focus")?.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const mod = await loadCalendarModalModule();
      await mod.triggerCalendarAiQuickFromRail("focus_block");
    } catch (err) {
      console.warn("[calendar-day-widget] Fokuszeit:", err);
    }
  });

  const aiInput = document.getElementById("calendar-day-widget-ai-input");
  const aiOut = document.getElementById("calendar-day-widget-ai-out");
  const submitAi = () => {
    const v = aiInput && "value" in aiInput ? String(aiInput.value || "").trim() : "";
    if (!v) return;
    if (aiOut) {
      aiOut.hidden = false;
      aiOut.textContent = "Kalender wird geöffnet …";
    }
    void loadCalendarModalModule()
      .then((mod) => mod.runCalendarAiPlanFromQuickEntry(v))
      .then((plan) => {
        if (!aiOut) return;
        if (plan) aiOut.textContent = "Vorschau im Kalender — dort bestätigen oder abbrechen.";
        else {
          aiOut.textContent = "";
          aiOut.hidden = true;
        }
      })
      .catch((err) => {
        console.warn("[calendar-day-widget] KI‑Plan:", err);
        if (aiOut) {
          aiOut.textContent = "";
          aiOut.hidden = true;
        }
      });
  };

  document.getElementById("calendar-day-widget-ai-send")?.addEventListener("click", (e) => {
    e.preventDefault();
    submitAi();
  });

  aiInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submitAi();
    }
  });

  document.getElementById("calendar-day-widget-open-calendar")?.addEventListener("click", () => {
    if (typeof window.dockOpen === "function") window.dockOpen("calendar");
  });

  const els = collectEls();
  const { btn, rail } = els;
  if (!rail) return;

  const initial = readStoredVisible();
  setDayPanelVisible(initial, els);

  if (btn) {
    btn.addEventListener("click", () => {
      const next = !dayPanelIsOpen();
      setDayPanelVisible(next, collectEls());
    });
  }

  window.addEventListener(
    "calendar-refresh",
    () => {
      if (dayPanelIsOpen()) scheduleRefresh();
    },
    false
  );

  document.getElementById("calendar-source-google")?.addEventListener("change", () => {
    if (dayPanelIsOpen()) scheduleRefresh();
  });
}

document.addEventListener("DOMContentLoaded", initCalendarDayWidget);
