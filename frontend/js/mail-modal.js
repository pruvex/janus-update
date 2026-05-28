import { API_BASE_URL } from "./config.js";
import {
  dockClose,
  dockMinimize,
  getDockModuleState,
  subscribeWindowState,
} from "./window-state.js";
import { bringToFront } from "./modal-api.js";
import { mapMailStatusToUi } from "./mail-status-ui.js";
import { filterMailThreads } from "./mail-inbox-ui.js";

const MODULE_ID = "mail";

let currentMailStatus = "disconnected";
let currentThreads = [];
let selectedThreadId = null;
let currentSelectedDetail = null;
let lastServerQuery = "";
let searchDebounceTimer = null;
let currentFolder = "inbox";
let currentFilteredThreads = [];
const MAIL_ACCOUNTS_STORAGE_KEY = "janus_mail_accounts_v1";
const MAIL_ACTIVE_ACCOUNT_STORAGE_KEY = "janus_mail_active_account_v1";
let knownAccounts = [];
let activeAccountEmail = "";

function loadKnownAccounts() {
  try {
    const raw = localStorage.getItem(MAIL_ACCOUNTS_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    knownAccounts = Array.isArray(parsed) ? parsed.filter((x) => typeof x === "string" && x.includes("@")) : [];
  } catch {
    knownAccounts = [];
  }
  try {
    const active = String(localStorage.getItem(MAIL_ACTIVE_ACCOUNT_STORAGE_KEY) || "").trim().toLowerCase();
    if (active.includes("@")) activeAccountEmail = active;
  } catch {
    // ignore storage errors
  }
}

function saveKnownAccounts() {
  try {
    localStorage.setItem(MAIL_ACCOUNTS_STORAGE_KEY, JSON.stringify(knownAccounts));
  } catch {
    // ignore storage errors
  }
}

function saveActiveAccount(email) {
  try {
    const normalized = String(email || "").trim().toLowerCase();
    if (normalized && normalized.includes("@")) {
      localStorage.setItem(MAIL_ACTIVE_ACCOUNT_STORAGE_KEY, normalized);
    } else {
      localStorage.removeItem(MAIL_ACTIVE_ACCOUNT_STORAGE_KEY);
    }
  } catch {
    // ignore storage errors
  }
}

function ensureAccountInList(email) {
  const normalized = String(email || "").trim().toLowerCase();
  if (!normalized || !normalized.includes("@")) return;
  if (!knownAccounts.includes(normalized)) {
    knownAccounts.unshift(normalized);
    saveKnownAccounts();
  }
}

function renderAccountSelect() {
  const select = document.getElementById("mail-account-select");
  if (!(select instanceof HTMLSelectElement)) return;
  select.innerHTML = "";

  if (!knownAccounts.length) {
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Keine gespeicherten Konten";
    select.appendChild(empty);
    select.disabled = true;
    return;
  }

  knownAccounts.forEach((acc) => {
    const option = document.createElement("option");
    option.value = acc;
    option.textContent = acc;
    select.appendChild(option);
  });
  select.disabled = false;

  if (activeAccountEmail && knownAccounts.includes(activeAccountEmail)) {
    select.value = activeAccountEmail;
  } else {
    select.value = knownAccounts[0];
  }
}

function setActionStatus(text) {
  const el = document.getElementById("mail-action-status");
  if (el) el.textContent = text;
}

function setActionControlsEnabled(enabled) {
  const trashBtn = document.getElementById("mail-trash-btn");
  const moveBtn = document.getElementById("mail-move-btn");
  const moveSel = document.getElementById("mail-move-folder");
  if (trashBtn) trashBtn.disabled = !enabled;
  if (moveBtn) moveBtn.disabled = !enabled;
  if (moveSel) moveSel.disabled = !enabled;
}

function isPanelVisible() {
  const state = getDockModuleState(MODULE_ID);
  return !!(state?.isOpen && !state?.minimized);
}

function renderStatus({ badge, message, lastChecked }) {
  const badgeEl = document.getElementById("mail-connection-badge");
  const messageEl = document.getElementById("mail-status-message");
  const checkedEl = document.getElementById("mail-last-checked");
  if (badgeEl) badgeEl.textContent = badge;
  if (messageEl) messageEl.textContent = message;
  if (checkedEl) checkedEl.textContent = lastChecked ? `Zuletzt geprüft: ${lastChecked}` : "";
}

function renderLoading() {
  renderStatus({
    badge: "Prüfe...",
    message: "Lade Verbindungsstatus...",
    lastChecked: "",
  });
}

function renderPreview(thread) {
  const subjectEl = document.getElementById("mail-preview-subject");
  const metaEl = document.getElementById("mail-preview-meta");
  const snippetEl = document.getElementById("mail-preview-snippet");
  if (!subjectEl || !metaEl || !snippetEl) return;
  if (!thread && !currentSelectedDetail) {
    subjectEl.textContent = "Keine Mail ausgewählt";
    metaEl.textContent = "Wähle eine Mail aus der Liste.";
    snippetEl.textContent = "";
    setActionControlsEnabled(false);
    return;
  }
  if (currentSelectedDetail && thread && String(currentSelectedDetail.id) === String(thread.id)) {
    const fromDisplay = String(currentSelectedDetail.from_display || "Unbekannt");
    const toDisplay = String(currentSelectedDetail.to_display || "");
    const dateText = String(currentSelectedDetail.date || "");
    subjectEl.textContent = String(currentSelectedDetail.subject || "(Kein Betreff)");
    metaEl.textContent = `${fromDisplay}${toDisplay ? ` → ${toDisplay}` : ""} · ${dateText}`;
    snippetEl.textContent = String(currentSelectedDetail.body_text || currentSelectedDetail.snippet || "");
    setActionControlsEnabled(true);
    return;
  }
  const fromDisplay = String(thread?.from_display || thread?.from || "Unbekannt");
  const dateText = String(thread?.date || "");
  subjectEl.textContent = String(thread?.subject || "(Kein Betreff)");
  metaEl.textContent = `${fromDisplay} · ${dateText}`;
  snippetEl.textContent = "Lade Nachricht...";
  setActionControlsEnabled(false);
}

async function fetchMessageDetail(messageId) {
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(messageId)}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function loadSelectedMessageDetail(thread) {
  if (!thread?.id) return;
  currentSelectedDetail = null;
  renderPreview(thread);
  try {
    const detail = await fetchMessageDetail(thread.id);
    if (String(selectedThreadId) !== String(thread.id)) return;
    currentSelectedDetail = detail;
    renderPreview(thread);
    setActionStatus("Nachricht geladen.");
  } catch (_error) {
    if (String(selectedThreadId) !== String(thread.id)) return;
    currentSelectedDetail = null;
    const snippetEl = document.getElementById("mail-preview-snippet");
    if (snippetEl) snippetEl.textContent = "Nachrichtentext konnte nicht geladen werden.";
    setActionStatus("Detail konnte nicht geladen werden.");
    setActionControlsEnabled(false);
  }
}

async function trashSelectedMessage() {
  if (!selectedThreadId) return;
  setActionStatus("Verschiebe in Papierkorb...");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(selectedThreadId)}/trash`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  setActionStatus(payload.message || "In Papierkorb verschoben.");
  selectedThreadId = null;
  currentSelectedDetail = null;
  await refreshInboxThreadsFromApi(String(document.getElementById("mail-search-input")?.value || "").trim());
}

async function moveSelectedMessage(targetFolder) {
  if (!selectedThreadId) return;
  setActionStatus("Verschiebe Mail...");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(selectedThreadId)}/move`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ target_folder: targetFolder }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  setActionStatus(payload.message || "Mail verschoben.");
  selectedThreadId = null;
  currentSelectedDetail = null;
  await refreshInboxThreadsFromApi(String(document.getElementById("mail-search-input")?.value || "").trim());
}

function renderThreadList(threads) {
  const listEl = document.getElementById("mail-thread-list");
  if (!listEl) return;
  listEl.innerHTML = "";
  listEl.setAttribute("role", "listbox");

  threads.forEach((thread) => {
    const row = document.createElement("div");
    row.className = "mail-thread-row";
    row.setAttribute("role", "option");
    row.tabIndex = -1;
    row.dataset.mailId = String(thread.id || "");
    if (selectedThreadId && String(thread.id) === String(selectedThreadId)) {
      row.classList.add("mail-thread-row--active");
      row.setAttribute("aria-selected", "true");
    } else {
      row.setAttribute("aria-selected", "false");
    }
    if (thread.unread) row.classList.add("mail-thread-row--unread");
    const fromDisplay = String(thread.from_display || thread.from || "");
    const dateText = formatCompactDate(thread.date);
    row.innerHTML = `
      <div class="mail-thread-top">
        <span class="mail-thread-from">${fromDisplay || "Unbekannt"}</span>
        <span class="mail-thread-date">${dateText}</span>
      </div>
      <div class="mail-thread-subject">${String(thread.subject || "(Kein Betreff)")}</div>
    `;
    row.addEventListener("click", () => {
      selectedThreadId = thread.id;
      currentSelectedDetail = null;
      renderInboxForState();
      loadSelectedMessageDetail(thread);
    });
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        selectedThreadId = thread.id;
        currentSelectedDetail = null;
        renderInboxForState();
        loadSelectedMessageDetail(thread);
      }
    });
    listEl.appendChild(row);
  });
}

function formatCompactDate(rawDate) {
  if (!rawDate) return "";
  const d = new Date(rawDate);
  if (Number.isNaN(d.getTime())) return String(rawDate);
  const now = new Date();
  const isToday =
    d.getFullYear() === now.getFullYear()
    && d.getMonth() === now.getMonth()
    && d.getDate() === now.getDate();
  const y = new Date(now);
  y.setDate(now.getDate() - 1);
  const isYesterday =
    d.getFullYear() === y.getFullYear()
    && d.getMonth() === y.getMonth()
    && d.getDate() === y.getDate();
  if (isToday) return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  if (isYesterday) return "Gestern";
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
}

function focusActiveMailRow() {
  const listEl = document.getElementById("mail-thread-list");
  if (!listEl) return;
  const active = listEl.querySelector(".mail-thread-row--active");
  if (active instanceof HTMLElement) active.focus();
}

function moveSelectionBy(delta) {
  if (!currentFilteredThreads.length) return;
  const idx = currentFilteredThreads.findIndex((t) => String(t.id) === String(selectedThreadId));
  const safeIdx = idx < 0 ? 0 : idx;
  const nextIdx = Math.max(0, Math.min(currentFilteredThreads.length - 1, safeIdx + delta));
  const next = currentFilteredThreads[nextIdx];
  if (!next) return;
  selectedThreadId = next.id;
  currentSelectedDetail = null;
  renderInboxForState();
  loadSelectedMessageDetail(next);
  focusActiveMailRow();
}

function renderInboxForState() {
  const listEl = document.getElementById("mail-thread-list");
  const emptyEl = document.getElementById("mail-inbox-empty");
  const searchEl = document.getElementById("mail-search-input");
  if (!listEl || !emptyEl || !searchEl) return;

  if (currentMailStatus !== "connected") {
    listEl.style.display = "none";
    emptyEl.style.display = "";
    emptyEl.textContent = "Verbinde Gmail, um Mails zu sehen.";
    renderPreview(null);
    return;
  }

  const filtered = filterMailThreads(currentThreads, searchEl.value);
  currentFilteredThreads = filtered;
  if (!filtered.length) {
    listEl.style.display = "none";
    emptyEl.style.display = "";
    emptyEl.textContent = "Keine Mails passend zur Suche.";
    renderPreview(null);
    return;
  }

  if (!selectedThreadId || !filtered.some((t) => String(t.id) === String(selectedThreadId))) {
    selectedThreadId = filtered[0].id;
  }
  const active = filtered.find((t) => String(t.id) === String(selectedThreadId)) || filtered[0];

  emptyEl.style.display = "none";
  listEl.style.display = "";
  renderThreadList(filtered);
  renderPreview(active);
}

async function fetchInboxThreads(query = "") {
  const url = new URL(`${API_BASE_URL}/api/mail/threads`);
  url.searchParams.set("max_results", "20");
  url.searchParams.set("folder", currentFolder);
  if (query.trim()) url.searchParams.set("q", query.trim());

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = String(payload?.detail || "").trim();
    } catch {
      detail = "";
    }
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function refreshInboxThreadsFromApi(query = "") {
  if (currentMailStatus !== "connected") return;
  const emptyEl = document.getElementById("mail-inbox-empty");
  if (emptyEl) {
    emptyEl.style.display = "";
    emptyEl.textContent = "Lade Mails...";
  }

  try {
    const payload = await fetchInboxThreads(query);
    currentThreads = Array.isArray(payload?.threads) ? payload.threads : [];
    if (!selectedThreadId && currentThreads.length) selectedThreadId = currentThreads[0].id;
    currentSelectedDetail = null;
    lastServerQuery = query.trim();
    renderInboxForState();
    const active = currentThreads.find((t) => String(t.id) === String(selectedThreadId));
    if (active) loadSelectedMessageDetail(active);
  } catch (error) {
    const listEl = document.getElementById("mail-thread-list");
    if (listEl) listEl.style.display = "none";
    renderPreview(null);
    if (emptyEl) {
      emptyEl.style.display = "";
      emptyEl.textContent = `Mails konnten nicht geladen werden (${error instanceof Error ? error.message : "unbekannter Fehler"}).`;
    }
  }
}

function toLocalTimeLabel(isoLike) {
  if (!isoLike) return "";
  const d = new Date(isoLike);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("de-DE");
}

async function fetchMailStatus() {
  const response = await fetch(`${API_BASE_URL}/api/mail/sync/status`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function refreshMailStatus() {
  if (!isPanelVisible()) return;
  renderLoading();
  try {
    const payload = await fetchMailStatus();
    currentMailStatus = String(payload?.status || "disconnected");
    const ui = mapMailStatusToUi(payload);
    activeAccountEmail = String(payload?.account_hint || "").trim().toLowerCase();
    if (activeAccountEmail) {
      ensureAccountInList(activeAccountEmail);
      saveActiveAccount(activeAccountEmail);
    }
    renderAccountSelect();
    renderStatus({
      badge: ui.badge,
      message: ui.message,
      lastChecked: toLocalTimeLabel(payload?.last_checked),
    });
    if (currentMailStatus === "connected") {
      await refreshInboxThreadsFromApi("");
    } else {
      currentThreads = [];
      selectedThreadId = null;
      currentSelectedDetail = null;
      renderInboxForState();
    }
  } catch (error) {
    currentMailStatus = "sync_error";
    currentThreads = [];
    selectedThreadId = null;
    currentSelectedDetail = null;
    renderStatus({
      badge: "Fehler",
      message: `Status konnte nicht geladen werden (${error instanceof Error ? error.message : "unbekannter Fehler"}).`,
      lastChecked: "",
    });
    renderInboxForState();
  }
}

function bindMailModalUi() {
  const closeBtn = document.getElementById("mail-close-btn");
  const minimizeBtn = document.getElementById("mail-minimize-btn");
  const resetBtn = document.getElementById("mail-reset-btn");
  const refreshBtn = document.getElementById("mail-refresh-status-btn");
  const modal = document.getElementById("mail-modal");
  const header = modal?.querySelector(".dock-panel-header");
  const searchInput = document.getElementById("mail-search-input");
  const trashBtn = document.getElementById("mail-trash-btn");
  const moveBtn = document.getElementById("mail-move-btn");
  const moveSel = document.getElementById("mail-move-folder");
  const folderButtons = Array.from(document.querySelectorAll(".mail-folder-item[data-mail-folder]"));
  const switchAccountBtn = document.getElementById("mail-switch-account-btn");
  const accountSelect = document.getElementById("mail-account-select");
  const addAccountBtn = document.getElementById("mail-add-account-btn");
  const accountDialog = document.getElementById("mail-account-dialog");
  const accountDialogClose = document.getElementById("mail-account-dialog-close");
  const accountCancelBtn = document.getElementById("mail-account-cancel-btn");
  const accountConnectBtn = document.getElementById("mail-account-connect-btn");
  const accountEmailInput = document.getElementById("mail-account-email-input");

  closeBtn?.addEventListener("click", () => dockClose(MODULE_ID));
  minimizeBtn?.addEventListener("click", () => dockMinimize(MODULE_ID, true));
  resetBtn?.addEventListener("click", () => refreshMailStatus());
  refreshBtn?.addEventListener("click", () => refreshMailStatus());
  searchInput?.addEventListener("input", () => {
    renderInboxForState();
    if (currentMailStatus !== "connected") return;
    const query = String(searchInput.value || "").trim();
    if (query === lastServerQuery) return;
    if (searchDebounceTimer) window.clearTimeout(searchDebounceTimer);
    searchDebounceTimer = window.setTimeout(() => refreshInboxThreadsFromApi(query), 300);
  });
  searchInput?.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveSelectionBy(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveSelectionBy(-1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const active = currentFilteredThreads.find((t) => String(t.id) === String(selectedThreadId));
      if (active) loadSelectedMessageDetail(active);
    }
  });
  const listEl = document.getElementById("mail-thread-list");
  listEl?.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveSelectionBy(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveSelectionBy(-1);
    }
  });
  folderButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const folder = String(btn.dataset.mailFolder || "inbox");
      if (folder === currentFolder) return;
      currentFolder = folder;
      selectedThreadId = null;
      currentSelectedDetail = null;
      lastServerQuery = "";
      folderButtons.forEach((node) => {
        node.classList.toggle("mail-folder-item--active", node === btn);
      });
      if (currentMailStatus === "connected") {
        refreshInboxThreadsFromApi(String(searchInput?.value || "").trim());
      } else {
        renderInboxForState();
      }
    });
  });
  trashBtn?.addEventListener("click", async () => {
    try {
      await trashSelectedMessage();
    } catch (error) {
      setActionStatus(`Aktion fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  moveBtn?.addEventListener("click", async () => {
    try {
      const target = String(moveSel?.value || "inbox");
      await moveSelectedMessage(target);
    } catch (error) {
      setActionStatus(`Aktion fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  switchAccountBtn?.addEventListener("click", async () => {
    try {
      setActionStatus("Trenne Gmail-Konto...");
      const response = await fetch(`${API_BASE_URL}/api/mail/disconnect`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setActionStatus("Konto getrennt. Bitte jetzt mit dem gewünschten Google-Konto neu verbinden.");
      activeAccountEmail = "";
      saveActiveAccount("");
      await refreshMailStatus();
    } catch (error) {
      setActionStatus(`Kontowechsel fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  accountSelect?.addEventListener("change", async () => {
    if (!(accountSelect instanceof HTMLSelectElement)) return;
    const email = String(accountSelect.value || "").trim().toLowerCase();
    if (!email || !email.includes("@")) {
      setActionStatus("Bitte zuerst ein gespeichertes Konto auswählen.");
      return;
    }
    if (email === activeAccountEmail) return;
    try {
      setActionStatus(`Aktiviere ${email}...`);
      let response = await fetch(`${API_BASE_URL}/api/mail/accounts/activate`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!response.ok && response.status === 404) {
        // Recovery path only when account is missing in backend token store.
        setActionStatus(`Konto nicht im Backend gefunden. Verbinde ${email} neu...`);
        response = await fetch(`${API_BASE_URL}/api/mail/accounts/connect`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || `HTTP ${response.status}`);
      }
      activeAccountEmail = email;
      saveActiveAccount(activeAccountEmail);
      ensureAccountInList(email);
      renderAccountSelect();
      // Activation already succeeded; switch UI state immediately and load inbox.
      currentMailStatus = "connected";
      renderStatus({
        badge: "Verbunden",
        message: `Aktives Konto: ${email}`,
        lastChecked: toLocalTimeLabel(new Date().toISOString()),
      });
      await refreshInboxThreadsFromApi(String(searchInput?.value || "").trim());
      setActionStatus(`Konto ${email} ist jetzt aktiv.`);
    } catch (error) {
      setActionStatus(`Konto konnte nicht aktiviert werden (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  function openAccountDialog() {
    if (!accountDialog) return;
    accountDialog.style.display = "";
    if (accountEmailInput instanceof HTMLInputElement) {
      accountEmailInput.value = "";
      accountEmailInput.focus();
    }
  }
  function closeAccountDialog() {
    if (!accountDialog) return;
    accountDialog.style.display = "none";
  }
  addAccountBtn?.addEventListener("click", openAccountDialog);
  accountDialogClose?.addEventListener("click", closeAccountDialog);
  accountCancelBtn?.addEventListener("click", closeAccountDialog);
  accountConnectBtn?.addEventListener("click", async () => {
    const email = String(accountEmailInput instanceof HTMLInputElement ? accountEmailInput.value : "").trim().toLowerCase();
    if (!email || !email.includes("@")) {
      setActionStatus("Bitte gültige E-Mail-Adresse eingeben.");
      return;
    }
    try {
      setActionStatus(`Verbinde ${email}...`);
      const response = await fetch(`${API_BASE_URL}/api/mail/accounts/connect`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || `HTTP ${response.status}`);
      }
      ensureAccountInList(email);
      activeAccountEmail = email;
      saveActiveAccount(activeAccountEmail);
      renderAccountSelect();
      closeAccountDialog();
      currentMailStatus = "connected";
      renderStatus({
        badge: "Verbunden",
        message: `Aktives Konto: ${email}`,
        lastChecked: toLocalTimeLabel(new Date().toISOString()),
      });
      await refreshInboxThreadsFromApi(String(searchInput?.value || "").trim());
      setActionStatus(`Konto ${email} verbunden.`);
    } catch (error) {
      setActionStatus(`Konto konnte nicht verbunden werden (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  header?.addEventListener("pointerdown", () => bringToFront(MODULE_ID));
}

function placeMailPanelNearChatB() {
  const modal = document.getElementById("mail-modal");
  if (!modal) return;
  const calendar = document.getElementById("calendar-modal");
  if (calendar) {
    // Prefer explicit calendar geometry first (works even when calendar is hidden).
    const cw = String(calendar.style.width || "").trim();
    const ch = String(calendar.style.height || "").trim();
    const cl = String(calendar.style.left || "").trim();
    const ct = String(calendar.style.top || "").trim();
    if (cw) modal.style.width = cw;
    if (ch) modal.style.height = ch;
    if (cl) modal.style.left = cl;
    if (ct) modal.style.top = ct;

    // Fallback to rendered box when available.
    const rect = calendar.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      modal.style.width = `${Math.round(rect.width)}px`;
      modal.style.height = `${Math.round(rect.height)}px`;
      modal.style.left = `${Math.round(rect.left)}px`;
      modal.style.top = `${Math.round(rect.top)}px`;
      return;
    }
  }
  // Final fallback: match calendar defaults.
  modal.style.width = "clamp(1280px, 97vw, 1480px)";
  modal.style.height = "min(780px, 90vh)";
  modal.style.left = "0px";
  modal.style.top = "0px";
}

function syncSidebarActiveState() {
  const navBtn = document.getElementById("sidebar-nav-mail");
  if (!navBtn) return;
  navBtn.classList.toggle("sidebar-nav-item--active", isPanelVisible());
}

function syncMailFromState() {
  let lastVisible = false;
  subscribeWindowState(() => {
    const visible = isPanelVisible();
    if (visible && !lastVisible) {
      placeMailPanelNearChatB();
      refreshMailStatus();
    }
    syncSidebarActiveState();
    lastVisible = visible;
  });
}

function initMailModal() {
  loadKnownAccounts();
  renderAccountSelect();
  bindMailModalUi();
  syncMailFromState();
  renderInboxForState();
  renderPreview(null);
  syncSidebarActiveState();
  setActionStatus("Keine Aktion ausgeführt.");
  setActionControlsEnabled(false);
  currentFilteredThreads = [];
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMailModal, { once: true });
  } else {
    initMailModal();
  }
}
