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
let nextThreadsPageToken = "";
let hasMoreThreads = false;
let loadingMoreThreads = false;
let infiniteScrollBound = false;
let composeMode = null;
let composeMeta = {
  inReplyTo: "",
  references: "",
  sourceMessageId: "",
};
const MAIL_ACCOUNTS_STORAGE_KEY = "janus_mail_accounts_v1";
const MAIL_ACTIVE_ACCOUNT_STORAGE_KEY = "janus_mail_active_account_v1";
const MAIL_KNOWN_ADDRESSES_STORAGE_KEY = "janus_mail_known_addresses_v1";
const MAIL_AI_ASSIST_GLOBAL_STORAGE_KEY = "janus_mail_ai_assist_global_v1";
const MAIL_AI_ASSIST_THREAD_STORAGE_KEY = "janus_mail_ai_assist_thread_v1";
let knownAccounts = [];
let activeAccountEmail = "";
let knownAddresses = [];
let undoTimer = null;
let pendingUndoAction = null;
let globalAiAssistEnabled = false;
let threadAiAssistMap = {};
let aiSummarySignature = "";
let aiAnalysisState = null;

function parseEmails(raw) {
  const text = String(raw || "");
  if (!text) return [];
  const matches = text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
  return matches.map((x) => x.trim().toLowerCase()).filter(Boolean);
}

function loadKnownAddresses() {
  try {
    const raw = localStorage.getItem(MAIL_KNOWN_ADDRESSES_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    knownAddresses = Array.isArray(parsed)
      ? parsed.filter((x) => typeof x === "string" && x.includes("@")).map((x) => x.trim().toLowerCase())
      : [];
  } catch {
    knownAddresses = [];
  }
}

function saveKnownAddresses() {
  try {
    localStorage.setItem(MAIL_KNOWN_ADDRESSES_STORAGE_KEY, JSON.stringify(knownAddresses.slice(0, 300)));
  } catch {
    // ignore storage errors
  }
}

function renderKnownAddressesDatalist() {
  const datalist = document.getElementById("mail-known-addresses");
  if (!(datalist instanceof HTMLDataListElement)) return;
  datalist.innerHTML = "";
  knownAddresses.slice(0, 200).forEach((email) => {
    const option = document.createElement("option");
    option.value = email;
    datalist.appendChild(option);
  });
}

function addKnownAddressesFromRaw(raw) {
  const emails = parseEmails(raw);
  if (!emails.length) return;
  let changed = false;
  emails.forEach((email) => {
    if (!knownAddresses.includes(email)) {
      knownAddresses.unshift(email);
      changed = true;
    }
  });
  if (!changed) return;
  knownAddresses = knownAddresses.slice(0, 300);
  saveKnownAddresses();
  renderKnownAddressesDatalist();
}

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

function loadAiAssistSettings() {
  try {
    globalAiAssistEnabled = localStorage.getItem(MAIL_AI_ASSIST_GLOBAL_STORAGE_KEY) === "1";
  } catch {
    globalAiAssistEnabled = false;
  }
  try {
    const raw = localStorage.getItem(MAIL_AI_ASSIST_THREAD_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    threadAiAssistMap = parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    threadAiAssistMap = {};
  }
}

function saveAiAssistSettings() {
  try {
    localStorage.setItem(MAIL_AI_ASSIST_GLOBAL_STORAGE_KEY, globalAiAssistEnabled ? "1" : "0");
    localStorage.setItem(MAIL_AI_ASSIST_THREAD_STORAGE_KEY, JSON.stringify(threadAiAssistMap));
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
  const archiveBtn = document.getElementById("mail-archive-btn");
  const restoreBtn = document.getElementById("mail-restore-btn");
  const trashBtn = document.getElementById("mail-trash-btn");
  const moveBtn = document.getElementById("mail-move-btn");
  const moveSel = document.getElementById("mail-move-folder");
  if (archiveBtn) archiveBtn.disabled = !enabled;
  if (restoreBtn) restoreBtn.disabled = !enabled;
  if (trashBtn) trashBtn.disabled = !enabled;
  if (moveBtn) moveBtn.disabled = !enabled;
  if (moveSel) moveSel.disabled = !enabled;
}

function clearUndoUi() {
  const row = document.getElementById("mail-undo-row");
  const text = document.getElementById("mail-undo-text");
  if (row) row.style.display = "none";
  if (text) text.textContent = "";
  pendingUndoAction = null;
  if (undoTimer) {
    window.clearTimeout(undoTimer);
    undoTimer = null;
  }
}

function showUndoUi({ messageId, sourceAction, text }) {
  const row = document.getElementById("mail-undo-row");
  const label = document.getElementById("mail-undo-text");
  if (!(row instanceof HTMLElement) || !(label instanceof HTMLElement)) return;
  pendingUndoAction = { messageId: String(messageId || ""), sourceAction: String(sourceAction || "") };
  label.textContent = text || "Aktion ausgeführt.";
  row.style.display = "";
  if (undoTimer) window.clearTimeout(undoTimer);
  undoTimer = window.setTimeout(() => clearUndoUi(), 8000);
}

function setComposeControlsEnabled(enabled) {
  const replyBtn = document.getElementById("mail-compose-reply-btn");
  const fwdBtn = document.getElementById("mail-compose-forward-btn");
  if (replyBtn) replyBtn.disabled = !enabled;
  if (fwdBtn) fwdBtn.disabled = !enabled;
}

function showComposeForm(show) {
  const form = document.getElementById("mail-compose-form");
  const cancelBtn = document.getElementById("mail-compose-cancel-btn");
  const previewPane = document.querySelector("#mail-modal .mail-preview-pane");
  if (form) form.style.display = show ? "flex" : "none";
  if (cancelBtn) cancelBtn.style.display = show ? "" : "none";
  if (previewPane) previewPane.classList.toggle("mail-preview-pane--composing", !!show);

  if (show) {
    const toEl = document.getElementById("mail-compose-to");
    const bodyEl = document.getElementById("mail-compose-body");
    const focusTarget = toEl instanceof HTMLInputElement && !toEl.value.trim() ? toEl : bodyEl;
    focusTarget?.focus();
    const contentEl = document.querySelector("#mail-modal .mail-preview-content");
    if (contentEl instanceof HTMLElement) contentEl.scrollTop = 0;
  }
}

function configureComposeModeUi(mode) {
  const forwardRow = document.getElementById("mail-forward-attachments-row");
  const forwardCheckbox = document.getElementById("mail-forward-include-attachments");
  const hintEl = document.getElementById("mail-compose-mode-hint");
  const isForward = mode === "forward";
  if (forwardRow) forwardRow.style.display = isForward ? "" : "none";
  if (forwardCheckbox instanceof HTMLInputElement) {
    if (!isForward) forwardCheckbox.checked = false;
    forwardCheckbox.onchange = () => {
      if (!(hintEl instanceof HTMLElement)) return;
      if (mode === "forward") {
        hintEl.textContent = forwardCheckbox.checked
          ? "Modus: Weiterleiten. Original-Anhaenge werden beim Senden mit uebernommen."
          : "Modus: Weiterleiten. Original-Anhaenge werden nicht automatisch mitgeschickt.";
      }
    };
  }
  if (hintEl instanceof HTMLElement) {
    if (mode === "reply") {
      hintEl.textContent = "Modus: Antworten. Threading aktiv (In-Reply-To/References wird gesetzt).";
    } else if (mode === "forward") {
      const includeOriginal = forwardCheckbox instanceof HTMLInputElement ? forwardCheckbox.checked : false;
      hintEl.textContent = includeOriginal
        ? "Modus: Weiterleiten. Original-Anhaenge werden beim Senden mit uebernommen."
        : "Modus: Weiterleiten. Original-Anhaenge werden nicht automatisch mitgeschickt.";
    } else if (mode === "new") {
      hintEl.textContent = "Modus: Neue E-Mail.";
    } else {
      hintEl.textContent = "";
    }
  }
}

function setComposeModeBadge(mode) {
  const badgeEl = document.getElementById("mail-compose-mode-badge");
  if (!(badgeEl instanceof HTMLElement)) return;
  badgeEl.classList.remove(
    "mail-compose-mode-badge--new",
    "mail-compose-mode-badge--reply",
    "mail-compose-mode-badge--forward",
  );
  if (mode === "reply") {
    badgeEl.textContent = "Antwort";
    badgeEl.classList.add("mail-compose-mode-badge--reply");
  } else if (mode === "forward") {
    badgeEl.textContent = "Weiterleiten";
    badgeEl.classList.add("mail-compose-mode-badge--forward");
  } else {
    badgeEl.textContent = "Neu";
    badgeEl.classList.add("mail-compose-mode-badge--new");
  }
}

function fillComposeForm({ to = "", subject = "", body = "", cc = "", bcc = "" } = {}) {
  const toEl = document.getElementById("mail-compose-to");
  const ccEl = document.getElementById("mail-compose-cc");
  const bccEl = document.getElementById("mail-compose-bcc");
  const subjectEl = document.getElementById("mail-compose-subject");
  const bodyEl = document.getElementById("mail-compose-body");
  if (toEl instanceof HTMLInputElement) toEl.value = to;
  if (ccEl instanceof HTMLInputElement) ccEl.value = cc;
  if (bccEl instanceof HTMLInputElement) bccEl.value = bcc;
  if (subjectEl instanceof HTMLInputElement) subjectEl.value = subject;
  if (bodyEl instanceof HTMLTextAreaElement) bodyEl.value = body;
}

function openCompose(mode) {
  composeMode = mode;
  composeMeta = { inReplyTo: "", references: "", sourceMessageId: "" };
  const current = currentSelectedDetail;
  if (mode === "new") {
    fillComposeForm({});
  } else if (mode === "reply") {
    const msgIdHeader = String(current?.message_id_header || "").trim();
    const refsHeader = String(current?.references_header || "").trim();
    composeMeta.inReplyTo = msgIdHeader;
    composeMeta.references = refsHeader
      ? `${refsHeader} ${msgIdHeader}`.trim()
      : msgIdHeader;
    fillComposeForm({
      to: String(current?.from_display || ""),
      subject: `Re: ${String(current?.subject || "(Kein Betreff)")}`,
      body: `\n\n---\n${String(current?.body_text || current?.snippet || "")}`,
    });
  } else if (mode === "forward") {
    composeMeta.sourceMessageId = String(current?.id || "").trim();
    fillComposeForm({
      subject: `Fwd: ${String(current?.subject || "(Kein Betreff)")}`,
      body: `\n\n--- Forwarded message ---\nFrom: ${String(current?.from_display || "")}\nDate: ${String(current?.date || "")}\n\n${String(current?.body_text || current?.snippet || "")}`,
    });
  }
  configureComposeModeUi(mode);
  setComposeModeBadge(mode);
  showComposeForm(true);
}

function closeCompose() {
  composeMode = null;
  composeMeta = { inReplyTo: "", references: "", sourceMessageId: "" };
  configureComposeModeUi(null);
  setComposeModeBadge(null);
  showComposeForm(false);
  const statusEl = document.getElementById("mail-compose-status");
  if (statusEl) statusEl.textContent = "Compose-Phase aktiv (Backend folgt).";
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

function getCurrentThreadAiEnabled() {
  if (!selectedThreadId) return false;
  return !!threadAiAssistMap[String(selectedThreadId)];
}

function getMessageSignature(detail) {
  const id = String(detail?.id || "");
  const date = String(detail?.date || "");
  const snippet = String(detail?.snippet || "").slice(0, 80);
  return `${id}|${date}|${snippet}`;
}

function simpleAiSummary(detail) {
  const text = String(detail?.body_text || detail?.snippet || "").replace(/\s+/g, " ").trim();
  if (!text) return "Keine verwertbaren Inhalte im Thread.";
  const firstSentence = text.split(/[.!?]\s/)[0] || text.slice(0, 220);
  return firstSentence.slice(0, 260);
}

function simpleReplyNeeded(detail) {
  const text = String(detail?.body_text || detail?.snippet || "").toLowerCase();
  if (text.includes("?") || /bitte|kannst du|deadline|termin/.test(text)) return "Ja";
  return "Eher nein";
}

function simplePriority(detail) {
  const from = String(detail?.from_display || "").toLowerCase();
  const subject = String(detail?.subject || "").toLowerCase();
  if (/rechnung|invoice|mahnung|deadline|dringend/.test(subject) || /chef|boss|bank/.test(from)) return "Hoch";
  if (/newsletter|promo|angebot/.test(subject)) return "Niedrig";
  return "Mittel";
}

function renderAiPanel(detail) {
  const statusEl = document.getElementById("mail-ai-assist-status");
  const globalToggle = document.getElementById("mail-ai-assist-global-toggle");
  const threadToggle = document.getElementById("mail-ai-thread-toggle");
  const summaryEl = document.getElementById("mail-ai-summary");
  const replyEl = document.getElementById("mail-ai-reply-needed");
  const prioEl = document.getElementById("mail-ai-priority");
  const staleEl = document.getElementById("mail-ai-stale");
  if (statusEl) statusEl.textContent = globalAiAssistEnabled ? "ON" : "OFF";
  if (globalToggle instanceof HTMLInputElement) globalToggle.checked = globalAiAssistEnabled;
  if (threadToggle instanceof HTMLInputElement) {
    threadToggle.disabled = !globalAiAssistEnabled || !detail;
    threadToggle.checked = !!(detail && getCurrentThreadAiEnabled());
  }
  if (!summaryEl || !replyEl || !prioEl || !staleEl) return;
  if (!detail) {
    summaryEl.textContent = "Keine Analyse vorhanden.";
    replyEl.textContent = "Reply: ?";
    prioEl.textContent = "Prio: ?";
    staleEl.style.display = "none";
    return;
  }
  if (!globalAiAssistEnabled || !getCurrentThreadAiEnabled()) {
    summaryEl.textContent = globalAiAssistEnabled
      ? "Thread-AI ist für diesen Thread deaktiviert."
      : "AI Mail Assist ist global OFF.";
    replyEl.textContent = "Reply: -";
    prioEl.textContent = "Prio: -";
    staleEl.style.display = "none";
    return;
  }
  const currentSig = getMessageSignature(detail);
  if (aiAnalysisState) {
    staleEl.style.display = aiAnalysisState.signature && aiAnalysisState.signature !== currentSig ? "" : "none";
    if (aiAnalysisState.degraded) {
      summaryEl.textContent = `AI nicht verfuegbar: ${aiAnalysisState.error_message || "Providerfehler"}`;
      replyEl.textContent = "Reply: ?";
      prioEl.textContent = "Prio: ?";
      aiSummarySignature = aiAnalysisState.signature || currentSig;
      return;
    }
    summaryEl.textContent = `Summary: ${aiAnalysisState.summary || "-"}`;
    replyEl.textContent = `Reply: ${aiAnalysisState.reply_needed || "-"}`;
    prioEl.textContent = `Prio: ${aiAnalysisState.priority || "-"}`;
    aiSummarySignature = aiAnalysisState.signature || currentSig;
  } else {
    staleEl.style.display = "none";
    summaryEl.textContent = "Noch keine AI-Analyse. Bitte 'AI aktualisieren' klicken.";
    replyEl.textContent = "Reply: ?";
    prioEl.textContent = "Prio: ?";
  }
}

function generateAiDraft(detail, tone) {
  const subject = String(detail?.subject || "(Kein Betreff)");
  const sender = String(detail?.from_display || "Ihnen");
  const base = tone === "kurz"
    ? "Danke für die Nachricht. Ich bestätige und melde mich mit den nächsten Schritten."
    : tone === "freundlich"
      ? "Vielen Dank für Ihre Nachricht. Ich habe alles gesehen und antworte Ihnen gern zeitnah mit den Details."
      : tone === "formal"
        ? "Vielen Dank für Ihre Nachricht. Ich bestätige den Eingang und werde Ihnen kurzfristig eine Rückmeldung übermitteln."
        : "Danke für die Nachricht. Ich habe den Punkt notiert und komme zeitnah mit einer Rückmeldung auf Sie zu.";
  return `Bezug: ${subject}\n\nHallo ${sender},\n\n${base}\n\nBeste Grüße`;
}

async function persistAiSettings(threadId = null, threadEnabled = null) {
  await fetch(`${API_BASE_URL}/api/mail/ai/settings`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      global_enabled: !!globalAiAssistEnabled,
      thread_id: threadId,
      thread_enabled: threadEnabled,
    }),
  });
}

async function requestAiAnalyze(messageId) {
  const response = await fetch(`${API_BASE_URL}/api/mail/ai/analyze`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ message_id: messageId }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function requestAiDraft(messageId, tone) {
  const response = await fetch(`${API_BASE_URL}/api/mail/ai/draft`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ message_id: messageId, tone }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.detail || `HTTP ${response.status}`);
  }
  return response.json();
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
  const attachmentsEl = document.getElementById("mail-preview-attachments");
  if (!subjectEl || !metaEl || !snippetEl || !attachmentsEl) return;
  if (!thread && !currentSelectedDetail) {
    subjectEl.textContent = "Keine Mail ausgewählt";
    metaEl.textContent = "Wähle eine Mail aus der Liste.";
    snippetEl.textContent = "";
    attachmentsEl.innerHTML = "";
    attachmentsEl.style.display = "none";
    setActionControlsEnabled(false);
    setComposeControlsEnabled(false);
    renderAiPanel(null);
    return;
  }
  if (currentSelectedDetail && thread && String(currentSelectedDetail.id) === String(thread.id)) {
    const fromDisplay = String(currentSelectedDetail.from_display || "Unbekannt");
    const toDisplay = String(currentSelectedDetail.to_display || "");
    const dateText = String(currentSelectedDetail.date || "");
    subjectEl.textContent = String(currentSelectedDetail.subject || "(Kein Betreff)");
    metaEl.textContent = `${fromDisplay}${toDisplay ? ` → ${toDisplay}` : ""} · ${dateText}`;
    snippetEl.textContent = String(currentSelectedDetail.body_text || currentSelectedDetail.snippet || "");
    renderAttachments(currentSelectedDetail.attachments || []);
    setActionControlsEnabled(true);
    setComposeControlsEnabled(true);
    renderAiPanel(currentSelectedDetail);
    return;
  }
  const fromDisplay = String(thread?.from_display || thread?.from || "Unbekannt");
  const dateText = String(thread?.date || "");
  subjectEl.textContent = String(thread?.subject || "(Kein Betreff)");
  metaEl.textContent = `${fromDisplay} · ${dateText}`;
  snippetEl.textContent = "Lade Nachricht...";
  attachmentsEl.innerHTML = "";
  attachmentsEl.style.display = "none";
  setActionControlsEnabled(false);
  setComposeControlsEnabled(false);
  renderAiPanel(null);
}

function formatBytes(size) {
  const n = Number(size || 0);
  if (!Number.isFinite(n) || n <= 0) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 102.4) / 10} KB`;
  return `${Math.round(n / 104857.6) / 10} MB`;
}

async function downloadAttachment(messageId, attachment) {
  const aid = String(attachment?.attachment_id || "").trim();
  if (!messageId || !aid) return;
  const filename = String(attachment?.filename || "attachment.bin");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(messageId)}/attachments/${encodeURIComponent(aid)}`, {
    method: "GET",
    headers: { Accept: "*/*" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderAttachments(attachments) {
  const attachmentsEl = document.getElementById("mail-preview-attachments");
  if (!(attachmentsEl instanceof HTMLElement)) return;
  attachmentsEl.innerHTML = "";
  const items = Array.isArray(attachments) ? attachments : [];
  if (!items.length || !selectedThreadId) {
    attachmentsEl.style.display = "none";
    return;
  }
  items.forEach((att) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mail-attachment-chip";
    const size = formatBytes(att?.size);
    btn.textContent = size ? `${String(att?.filename || "Anhang")} (${size})` : String(att?.filename || "Anhang");
    btn.addEventListener("click", async () => {
      try {
        setActionStatus(`Lade Anhang ${String(att?.filename || "")}...`);
        await downloadAttachment(selectedThreadId, att);
        setActionStatus(`Anhang geladen: ${String(att?.filename || "")}`);
      } catch (error) {
        setActionStatus(`Anhang konnte nicht geladen werden (${error instanceof Error ? error.message : "unbekannt"}).`);
      }
    });
    attachmentsEl.appendChild(btn);
  });
  attachmentsEl.style.display = "";
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
  aiAnalysisState = null;
  renderPreview(thread);
  try {
    const detail = await fetchMessageDetail(thread.id);
    if (String(selectedThreadId) !== String(thread.id)) return;
    currentSelectedDetail = detail;
    addKnownAddressesFromRaw(detail?.from_display || "");
    addKnownAddressesFromRaw(detail?.to_display || "");
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
  const affectedId = selectedThreadId;
  clearUndoUi();
  setActionStatus("Verschiebe in Papierkorb...");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(affectedId)}/trash`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  setActionStatus(payload.message || "In Papierkorb verschoben.");
  showUndoUi({
    messageId: affectedId,
    sourceAction: "trash",
    text: "In Papierkorb verschoben. Rueckgaengig moeglich (8s).",
  });
  selectedThreadId = null;
  currentSelectedDetail = null;
  await refreshInboxThreadsFromApi(String(document.getElementById("mail-search-input")?.value || "").trim());
}

async function moveSelectedMessage(targetFolder) {
  if (!selectedThreadId) return;
  const affectedId = selectedThreadId;
  clearUndoUi();
  setActionStatus("Verschiebe Mail...");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(affectedId)}/move`, {
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
  if (String(targetFolder) === "archive") {
    showUndoUi({
      messageId: affectedId,
      sourceAction: "archive",
      text: "Archiviert. Rueckgaengig moeglich (8s).",
    });
  }
  selectedThreadId = null;
  currentSelectedDetail = null;
  await refreshInboxThreadsFromApi(String(document.getElementById("mail-search-input")?.value || "").trim());
}

async function undoLastMailAction() {
  const ctx = pendingUndoAction;
  if (!ctx?.messageId) return;
  setActionStatus("Stelle Mail in Posteingang wieder her...");
  const response = await fetch(`${API_BASE_URL}/api/mail/messages/${encodeURIComponent(ctx.messageId)}/move`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ target_folder: "inbox" }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  clearUndoUi();
  setActionStatus("Rueckgaengig erfolgreich: Mail ist wieder im Posteingang.");
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
    addKnownAddressesFromRaw(fromDisplay);
    const dateText = formatCompactDate(thread);
    const attachmentBadge = thread.has_attachments
      ? `<span class="mail-thread-attachment" title="Hat Anhang" aria-label="Hat Anhang">📎</span>`
      : "";
    row.innerHTML = `
      <div class="mail-thread-top">
        <span class="mail-thread-from">${fromDisplay || "Unbekannt"}</span>
        <span class="mail-thread-date">${dateText}${attachmentBadge}</span>
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

function mergeThreads(existing, incoming) {
  const listA = Array.isArray(existing) ? existing : [];
  const listB = Array.isArray(incoming) ? incoming : [];
  const byId = new Map();
  listA.forEach((item) => {
    const id = String(item?.id || "");
    if (id) byId.set(id, item);
  });
  listB.forEach((item) => {
    const id = String(item?.id || "");
    if (!id) return;
    byId.set(id, item);
  });
  return Array.from(byId.values());
}

function formatCompactDate(thread) {
  const internalRaw = Number(thread?.internal_date_ms || 0);
  const rawDate = String(thread?.date || "");
  const d = internalRaw > 0 ? new Date(internalRaw) : new Date(rawDate);
  if (Number.isNaN(d.getTime())) return rawDate;
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

async function fetchInboxThreads(query = "", pageToken = "") {
  const url = new URL(`${API_BASE_URL}/api/mail/threads`);
  url.searchParams.set("max_results", "20");
  url.searchParams.set("folder", currentFolder);
  if (query.trim()) url.searchParams.set("q", query.trim());
  if (pageToken.trim()) url.searchParams.set("page_token", pageToken.trim());

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
    nextThreadsPageToken = String(payload?.next_page_token || "");
    hasMoreThreads = !!nextThreadsPageToken;
    loadingMoreThreads = false;
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
    hasMoreThreads = false;
    nextThreadsPageToken = "";
    loadingMoreThreads = false;
  }
}

async function loadMoreThreadsFromApi() {
  if (currentMailStatus !== "connected" || !hasMoreThreads || !nextThreadsPageToken || loadingMoreThreads) return;
  loadingMoreThreads = true;
  try {
    const payload = await fetchInboxThreads(lastServerQuery, nextThreadsPageToken);
    const incoming = Array.isArray(payload?.threads) ? payload.threads : [];
    currentThreads = mergeThreads(currentThreads, incoming);
    nextThreadsPageToken = String(payload?.next_page_token || "");
    hasMoreThreads = !!nextThreadsPageToken;
    renderInboxForState();
  } catch (error) {
    setActionStatus(`Weitere Mails konnten nicht geladen werden (${error instanceof Error ? error.message : "unbekannt"}).`);
  } finally {
    loadingMoreThreads = false;
    // Large viewports can still be at the bottom after append; keep filling until content exceeds viewport.
    handleThreadListInfiniteScroll().catch(() => {});
  }
}

async function handleThreadListInfiniteScroll() {
  const listEl = document.getElementById("mail-thread-list");
  const paneEl = document.querySelector("#mail-modal .mail-list-pane");
  if (!(listEl instanceof HTMLElement)) return;
  if (currentMailStatus !== "connected" || !hasMoreThreads || loadingMoreThreads) return;
  const thresholdPx = 120;
  const listRemaining = listEl.scrollHeight - listEl.scrollTop - listEl.clientHeight;
  let paneRemaining = Number.POSITIVE_INFINITY;
  if (paneEl instanceof HTMLElement) {
    paneRemaining = paneEl.scrollHeight - paneEl.scrollTop - paneEl.clientHeight;
  }
  if (listRemaining <= thresholdPx || paneRemaining <= thresholdPx) {
    await loadMoreThreadsFromApi();
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
      nextThreadsPageToken = "";
      hasMoreThreads = false;
      loadingMoreThreads = false;
      renderInboxForState();
    }
  } catch (error) {
    currentMailStatus = "sync_error";
    currentThreads = [];
    selectedThreadId = null;
    currentSelectedDetail = null;
    nextThreadsPageToken = "";
    hasMoreThreads = false;
    loadingMoreThreads = false;
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
  const archiveBtn = document.getElementById("mail-archive-btn");
  const restoreBtn = document.getElementById("mail-restore-btn");
  const trashBtn = document.getElementById("mail-trash-btn");
  const moveBtn = document.getElementById("mail-move-btn");
  const moveSel = document.getElementById("mail-move-folder");
  const undoBtn = document.getElementById("mail-undo-btn");
  const folderButtons = Array.from(document.querySelectorAll(".mail-folder-item[data-mail-folder]"));
  const switchAccountBtn = document.getElementById("mail-switch-account-btn");
  const accountSelect = document.getElementById("mail-account-select");
  const addAccountBtn = document.getElementById("mail-add-account-btn");
  const accountDialog = document.getElementById("mail-account-dialog");
  const accountDialogClose = document.getElementById("mail-account-dialog-close");
  const accountCancelBtn = document.getElementById("mail-account-cancel-btn");
  const accountConnectBtn = document.getElementById("mail-account-connect-btn");
  const accountEmailInput = document.getElementById("mail-account-email-input");
  const composeNewBtn = document.getElementById("mail-compose-new-btn");
  const composeReplyBtn = document.getElementById("mail-compose-reply-btn");
  const composeForwardBtn = document.getElementById("mail-compose-forward-btn");
  const composeCancelBtn = document.getElementById("mail-compose-cancel-btn");
  const composeSendBtn = document.getElementById("mail-compose-send-btn");
  const aiGlobalToggle = document.getElementById("mail-ai-assist-global-toggle");
  const aiThreadToggle = document.getElementById("mail-ai-thread-toggle");
  const aiRefreshBtn = document.getElementById("mail-ai-refresh-btn");
  const aiDraftBtn = document.getElementById("mail-ai-draft-btn");
  const aiToneEl = document.getElementById("mail-ai-tone");

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
  const listPaneEl = document.querySelector("#mail-modal .mail-list-pane");
  if (!infiniteScrollBound && listEl instanceof HTMLElement) {
    listEl.addEventListener("scroll", () => {
      handleThreadListInfiniteScroll().catch(() => {});
    });
    if (listPaneEl instanceof HTMLElement) {
      listPaneEl.addEventListener("scroll", () => {
        handleThreadListInfiniteScroll().catch(() => {});
      });
    }
    infiniteScrollBound = true;
  }
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
      nextThreadsPageToken = "";
      hasMoreThreads = false;
      loadingMoreThreads = false;
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
  archiveBtn?.addEventListener("click", async () => {
    try {
      await moveSelectedMessage("archive");
    } catch (error) {
      setActionStatus(`Aktion fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  restoreBtn?.addEventListener("click", async () => {
    try {
      await moveSelectedMessage("inbox");
    } catch (error) {
      setActionStatus(`Aktion fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
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
  aiGlobalToggle?.addEventListener("change", () => {
    globalAiAssistEnabled = !!(aiGlobalToggle instanceof HTMLInputElement && aiGlobalToggle.checked);
    saveAiAssistSettings();
    persistAiSettings().catch(() => {});
    renderAiPanel(currentSelectedDetail);
    setActionStatus(globalAiAssistEnabled ? "AI Mail Assist global aktiviert." : "AI Mail Assist global deaktiviert.");
  });
  aiThreadToggle?.addEventListener("change", () => {
    if (!selectedThreadId) return;
    const enabled = !!(aiThreadToggle instanceof HTMLInputElement && aiThreadToggle.checked);
    threadAiAssistMap[String(selectedThreadId)] = enabled;
    saveAiAssistSettings();
    persistAiSettings(String(selectedThreadId), enabled).catch(() => {});
    aiAnalysisState = null;
    renderAiPanel(currentSelectedDetail);
  });
  aiRefreshBtn?.addEventListener("click", async () => {
    if (!currentSelectedDetail) return;
    if (!globalAiAssistEnabled) {
      setActionStatus("AI-Analyse gesperrt: Bitte AI Mail Assist global aktivieren.");
      return;
    }
    if (!getCurrentThreadAiEnabled() && selectedThreadId) {
      threadAiAssistMap[String(selectedThreadId)] = true;
      saveAiAssistSettings();
      persistAiSettings(String(selectedThreadId), true).catch(() => {});
      renderAiPanel(currentSelectedDetail);
    }
    try {
      setActionStatus("AI analysiert Thread...");
      aiAnalysisState = await requestAiAnalyze(String(currentSelectedDetail.id));
      renderAiPanel(currentSelectedDetail);
      setActionStatus(aiAnalysisState?.degraded ? "AI-Analyse nicht verfuegbar." : "AI-Analyse aktualisiert.");
    } catch (error) {
      setActionStatus(`AI-Analyse fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  aiDraftBtn?.addEventListener("click", async () => {
    if (!currentSelectedDetail) return;
    if (!globalAiAssistEnabled) {
      setActionStatus("AI-Draft gesperrt: Bitte AI Mail Assist global aktivieren.");
      return;
    }
    if (!getCurrentThreadAiEnabled() && selectedThreadId) {
      threadAiAssistMap[String(selectedThreadId)] = true;
      saveAiAssistSettings();
      persistAiSettings(String(selectedThreadId), true).catch(() => {});
      renderAiPanel(currentSelectedDetail);
    }
    const tone = aiToneEl instanceof HTMLSelectElement ? String(aiToneEl.value || "neutral") : "neutral";
    try {
      setActionStatus("AI erstellt Draft...");
      const payload = await requestAiDraft(String(currentSelectedDetail.id), tone);
      if (payload?.degraded) {
        setActionStatus(`AI-Draft nicht verfuegbar (${payload.error_message || "Providerfehler"}).`);
        return;
      }
      openCompose("reply");
      const bodyEl = document.getElementById("mail-compose-body");
      if (bodyEl instanceof HTMLTextAreaElement) bodyEl.value = String(payload?.draft || "");
      const statusEl = document.getElementById("mail-compose-status");
      if (statusEl) statusEl.textContent = "AI-Draft erstellt. Bitte prüfen und dann senden.";
      setActionStatus("AI-Draft bereit.");
    } catch (error) {
      setActionStatus(`AI-Draft fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  undoBtn?.addEventListener("click", async () => {
    try {
      await undoLastMailAction();
    } catch (error) {
      clearUndoUi();
      setActionStatus(`Rueckgaengig fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`);
    }
  });
  composeNewBtn?.addEventListener("click", () => openCompose("new"));
  composeReplyBtn?.addEventListener("click", () => {
    if (!currentSelectedDetail) return;
    openCompose("reply");
  });
  composeForwardBtn?.addEventListener("click", () => {
    if (!currentSelectedDetail) return;
    openCompose("forward");
  });
  composeCancelBtn?.addEventListener("click", () => closeCompose());
  composeSendBtn?.addEventListener("click", async () => {
    const statusEl = document.getElementById("mail-compose-status");
    const toEl = document.getElementById("mail-compose-to");
    const ccEl = document.getElementById("mail-compose-cc");
    const bccEl = document.getElementById("mail-compose-bcc");
    const subjectEl = document.getElementById("mail-compose-subject");
    const bodyEl = document.getElementById("mail-compose-body");
    const attachmentsEl = document.getElementById("mail-compose-attachments");
    const forwardAttachEl = document.getElementById("mail-forward-include-attachments");
    const to = toEl instanceof HTMLInputElement ? String(toEl.value || "").trim() : "";
    const cc = ccEl instanceof HTMLInputElement ? String(ccEl.value || "").trim() : "";
    const bcc = bccEl instanceof HTMLInputElement ? String(bccEl.value || "").trim() : "";
    const subject = subjectEl instanceof HTMLInputElement ? String(subjectEl.value || "") : "";
    const body = bodyEl instanceof HTMLTextAreaElement ? String(bodyEl.value || "") : "";

    if (!to) {
      if (statusEl) statusEl.textContent = "Bitte Empfaenger in 'To' eintragen.";
      return;
    }
    if (statusEl) statusEl.textContent = "Sende E-Mail...";
    if (composeSendBtn instanceof HTMLButtonElement) composeSendBtn.disabled = true;
    try {
      const formData = new FormData();
      formData.append("to", to);
      formData.append("cc", cc);
      formData.append("bcc", bcc);
      formData.append("subject", subject);
      formData.append("body", body);
      formData.append("in_reply_to", String(composeMeta.inReplyTo || ""));
      formData.append("references", String(composeMeta.references || ""));
      formData.append("source_message_id", String(composeMeta.sourceMessageId || ""));
      const includeOriginal = composeMode === "forward" && forwardAttachEl instanceof HTMLInputElement && forwardAttachEl.checked;
      formData.append("include_original_attachments", includeOriginal ? "true" : "false");
      if (attachmentsEl instanceof HTMLInputElement && attachmentsEl.files) {
        Array.from(attachmentsEl.files).forEach((file) => formData.append("attachments", file));
      }
      const response = await fetch(`${API_BASE_URL}/api/mail/messages/send`, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: formData,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || `HTTP ${response.status}`);
      }
      if (statusEl) statusEl.textContent = "E-Mail gesendet.";
      addKnownAddressesFromRaw(to);
      addKnownAddressesFromRaw(cc);
      addKnownAddressesFromRaw(bcc);
      if (attachmentsEl instanceof HTMLInputElement) attachmentsEl.value = "";
      closeCompose();
      setActionStatus("E-Mail erfolgreich gesendet.");
      if (currentFolder === "sent") {
        await refreshInboxThreadsFromApi(String(searchInput?.value || "").trim());
      }
    } catch (error) {
      if (statusEl) statusEl.textContent = `Senden fehlgeschlagen (${error instanceof Error ? error.message : "unbekannt"}).`;
    } finally {
      if (composeSendBtn instanceof HTMLButtonElement) composeSendBtn.disabled = false;
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
  loadKnownAddresses();
  renderKnownAddressesDatalist();
  loadKnownAccounts();
  loadAiAssistSettings();
  renderAccountSelect();
  bindMailModalUi();
  syncMailFromState();
  renderInboxForState();
  renderPreview(null);
  renderAiPanel(null);
  syncSidebarActiveState();
  setActionStatus("Keine Aktion ausgeführt.");
  setActionControlsEnabled(false);
  setComposeControlsEnabled(false);
  showComposeForm(false);
  currentFilteredThreads = [];
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMailModal, { once: true });
  } else {
    initMailModal();
  }
}
