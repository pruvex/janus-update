import { API_BASE_URL } from "./config.js";
import { getActiveChatIdForWindow, paneId, WINDOW_IDS } from "./window-state.js";

const REFRESH_TIMERS = new Map();
const REFRESH_DELAY_MS = 500;

// ═══════════════════════════════════════════════════════════════════════════════
// 💎 CU-2: Auth-Hilfsfunktionen (EMERGENCY FIX für 401 Unauthorized)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Holt den Auth-Token aus localStorage.
 * @returns {string|null} Der Token oder null
 */
function getAuthToken() {
  return localStorage.getItem('auth_token');
}

/**
 * Erstellt Standard-Headers für authentifizierte API-Calls.
 * @returns {Object} Headers mit Authorization und Content-Type
 */
function getAuthHeaders() {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    "Authorization": token ? `Bearer ${token}` : "",
  };
}

// Phase 2: Warning & Decision Layer State
const PREVIOUS_STATES = new Map(); // Track status transitions per window
const WARNING_SHOWN = new Set(); // Prevent duplicate warnings
let modelSwitchInterceptorInstalled = false;
const PENDING_MODEL_SWITCH = new Map(); // Store pending model switch decisions

function getEffectiveProviderModel(windowId) {
  const headerProvider = document.getElementById(`chat-header-provider-${windowId}`)?.value;
  const headerModel = document.getElementById(`chat-header-model-${windowId}`)?.value;
  const sidebarProvider = document.getElementById("provider-select")?.value;
  const sidebarModel = document.getElementById("model-select")?.value;
  return {
    provider: headerProvider || sidebarProvider || "unknown",
    model: headerModel || sidebarModel || "unknown",
  };
}

function collectVisibleMessages(windowId) {
  const container = document.getElementById(paneId("chat-messages", windowId));
  if (!container) return [];
  return Array.from(container.querySelectorAll(".message")).map((el) => {
    const role = el.classList.contains("user") ? "user" : "assistant";
    const bubble = el.querySelector(".bubble");
    const content = (bubble?.innerText || "").trim();
    return { role, content };
  }).filter((message) => message.content && message.content !== "...");
}

function ensureMeterElement(windowId) {
  const header = document.getElementById(`chat-header-${windowId}`);
  if (!header) return null;
  let meter = document.getElementById(`context-meter-${windowId}`);
  if (meter) return meter;
  meter = document.createElement("div");
  meter.id = `context-meter-${windowId}`;
  meter.className = "context-meter context-meter--green";
  meter.dataset.status = "green";
  meter.innerHTML = `
    <span class="context-meter-dot" aria-hidden="true"></span>
    <span class="context-meter-label">Kontext</span>
    <span class="context-meter-value">0%</span>
    <span class="context-meter-warning" aria-live="polite"></span>
  `;
  // 💎 CU-3: Klick auf Ampel startet Compression Flow (außer bei green)
  meter.addEventListener("click", () => {
    const status = meter.dataset.status;
    if (status && status !== "green") {
      const { model } = getEffectiveProviderModel(windowId);
      if (model && model !== "unknown") {
        logContextEvent("context_meter_clicked", { window_id: windowId, status, model });
        showCompressionLoadingModal(model);
        fetchCompressionProposal(model).then((proposal) => {
          removeCompressionLoadingModal();
          if (proposal && proposal.can_compress) {
            showCompressionReviewModal(proposal, model);
          } else {
            showCompressionErrorModal(proposal?.message || "Keine Kompression möglich.");
          }
        });
      }
    }
  });
  header.appendChild(meter);
  return meter;
}

function formatTokens(value) {
  const num = Number(value || 0);
  return new Intl.NumberFormat("de-DE").format(num);
}

/**
 * D10 Telemetrie: Loggt Context Awareness Events
 * @param {string} eventType - z.B. 'context_warning_shown', 'context_model_switch_risk'
 * @param {object} payload - Event-Daten
 */
async function logContextEvent(eventType, payload = {}) {
  try {
    const traceId = window.__JANUS_TRACE_ID__ || `ctx-${Date.now()}`;
    await fetch(`${API_BASE_URL}/api/context/log`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        event_type: eventType,
        trace_id: traceId,
        payload: {
          timestamp: new Date().toISOString(),
          source: "context_awareness",
          ...payload,
        },
      }),
    });
  } catch (error) {
    // Silent fail - Telemetrie darf Chat nicht blockieren
    console.warn("[CONTEXT-AWARENESS] Telemetry failed:", error);
  }
}

function updateMeter(windowId, state) {
  const meter = ensureMeterElement(windowId);
  if (!meter || !state) return;

  const prevState = PREVIOUS_STATES.get(windowId);
  const status = state.status || "green";

  // Phase 2: Detect yellow → orange transition for in-chat warning
  if (prevState && prevState.status === "yellow" && status === "orange") {
    showInChatWarning(windowId, state);
  }

  // Update meter UI
  meter.dataset.status = status;
  meter.className = `context-meter context-meter--${status}`;
  const valueEl = meter.querySelector(".context-meter-value");
  const warningEl = meter.querySelector(".context-meter-warning");
  const percent = Number(state.usage_percent || 0).toFixed(1).replace(".0", "");
  if (valueEl) valueEl.textContent = `${percent}%`;
  meter.title = `${formatTokens(state.total_tokens)} / ${formatTokens(state.effective_input_limit)} Tokens · ${formatTokens(state.remaining_tokens)} verbleibend · Modell: ${state.model}`;
  if (warningEl) {
    warningEl.textContent = state.warning || "";
  }

  // Store current state for next comparison
  PREVIOUS_STATES.set(windowId, { status, percent: state.usage_percent, timestamp: Date.now() });
}

/**
 * Phase 2: Zeige dezenten In-Chat Toast wenn Status von yellow auf orange springt
 */
function showInChatWarning(windowId, state) {
  const warningKey = `${windowId}-orange-warning`;
  if (WARNING_SHOWN.has(warningKey)) return; // Nur einmal pro Session

  const container = document.getElementById(paneId("chat-messages", windowId));
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "context-toast context-toast--orange";
  toast.innerHTML = `
    <span class="context-toast-icon">⚠️</span>
    <span class="context-toast-text">Kontext wird voll (${state.usage_percent.toFixed(0)}%). Ältere Nachrichten könnten zusammengefasst werden.</span>
    <button class="context-toast-close" aria-label="Schließen">×</button>
  `;

  toast.querySelector(".context-toast-close")?.addEventListener("click", () => {
    toast.remove();
  });

  // Auto-remove after 10 seconds
  setTimeout(() => toast.remove(), 10000);

  container.appendChild(toast);
  WARNING_SHOWN.add(warningKey);

  // D10 Telemetrie
  logContextEvent("context_warning_shown", {
    warning_type: "in_chat_orange_transition",
    window_id: windowId,
    model: state.model,
    usage_percent: state.usage_percent,
    status: state.status,
  });
}

export async function refreshContextMeter(windowId) {
  const { provider, model } = getEffectiveProviderModel(windowId);
  if (!model || model === "unknown") return;
  const chatId = getActiveChatIdForWindow(windowId);
  const messages = collectVisibleMessages(windowId);
  try {
    const response = await fetch(`${API_BASE_URL}/api/context/state`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: chatId,
        provider,
        model,
        messages,
        include_persisted_messages: messages.length === 0,
      }),
    });
    if (!response.ok) return;
    const data = await response.json();
    updateMeter(windowId, data);
  } catch (error) {
    console.warn("[CONTEXT-AWARENESS] refresh failed", error);
  }
}

export function scheduleContextRefresh(windowId) {
  const targetWindowId = windowId || "A";
  clearTimeout(REFRESH_TIMERS.get(targetWindowId));
  REFRESH_TIMERS.set(targetWindowId, setTimeout(() => {
    refreshContextMeter(targetWindowId);
  }, REFRESH_DELAY_MS));
}

export function setupContextAwareness() {
  try {
    WINDOW_IDS.forEach((windowId) => {
      ensureMeterElement(windowId);
      scheduleContextRefresh(windowId);
      const input = document.getElementById(paneId("user-input", windowId));
      if (input && input.dataset.contextAwarenessBound !== "1") {
        input.dataset.contextAwarenessBound = "1";
        input.addEventListener("input", () => scheduleContextRefresh(windowId));
      }
    });

    // Phase 2: Installiere Modellwechsel-Interceptor (einmalig)
    if (!modelSwitchInterceptorInstalled) {
      installModelSwitchInterceptor();
      modelSwitchInterceptorInstalled = true;
    }

    // 💎 CU-2: Initialisiere Listener für Compression-Details-Buttons
    initCompressionDetailsListeners();
  } catch (error) {
    // EMERGENCY FIX: Boot-Fehler dürfen nicht die ganze App stoppen
    console.error("[CONTEXT-AWARENESS] Boot error in setupContextAwareness:", error);
  }
}

/**
 * Phase 2: Installiert Interceptor für model-select und provider-select
 * Prüft Context-Status VOR dem Wechsel und zeigt Warnung bei Bedarf.
 */
function installModelSwitchInterceptor() {
  const modelSelect = document.getElementById("model-select");
  const providerSelect = document.getElementById("provider-select");

  if (modelSelect) {
    // Speichere vorherigen Wert für Cancel-Reset
    PENDING_MODEL_SWITCH.set("previousModel", modelSelect.value);

    modelSelect.addEventListener("change", async (e) => {
      const targetModel = e.target.value;
      const provider = providerSelect?.value || "unknown";

      // Speichere vorherigen Wert für mögliches Zurücksetzen
      const previousValue = PENDING_MODEL_SWITCH.get("previousModel") || modelSelect.value;
      PENDING_MODEL_SWITCH.set("previousModel", previousValue);

      // Prüfe Context für Ziel-Modell
      const shouldBlock = await checkModelSwitchRisk(targetModel, provider);
      if (shouldBlock) {
        e.preventDefault();
        e.stopImmediatePropagation();
        // Warte auf Modal-Entscheidung
        return;
      }
      // Update gespeicherten Wert bei erfolgreichem Wechsel
      PENDING_MODEL_SWITCH.set("previousModel", targetModel);
    }, true); // Use capture phase to intercept before other handlers
  }

  if (providerSelect) {
    providerSelect.addEventListener("change", async (e) => {
      const targetProvider = e.target.value;
      // Finde erstes verfügbares Modell für neuen Provider
      const firstModel = findFirstModelForProvider(targetProvider);
      if (firstModel) {
        const shouldBlock = await checkModelSwitchRisk(firstModel, targetProvider);
        if (shouldBlock) {
          e.preventDefault();
          e.stopImmediatePropagation();
        }
      }
    }, true);
  }
}

/**
 * Prüft Risiko für Modellwechsel. Zeigt Modal bei kritischem Status.
 * @returns {Promise<boolean>} true = blockiere Wechsel (Modal angezeigt), false = OK
 */
async function checkModelSwitchRisk(targetModel, targetProvider) {
  const messages = [];
  // Sammle Messages von allen Fenstern für konservative Schätzung
  WINDOW_IDS.forEach((wid) => {
    messages.push(...collectVisibleMessages(wid));
  });

  try {
    const response = await fetch(`${API_BASE_URL}/api/context/state`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: null, // Kein spezifischer Chat
        provider: targetProvider,
        model: targetModel,
        messages,
        include_persisted_messages: messages.length === 0,
      }),
    });

    if (!response.ok) return false; // Bei Fehler: nicht blockieren

    const state = await response.json();
    const criticalStatuses = ["orange", "red", "overflow"];

    if (criticalStatuses.includes(state.status)) {
      showModelSwitchWarningModal(targetModel, state);
      return true; // Blockiere Original-Event
    }
  } catch (error) {
    console.warn("[CONTEXT-AWARENESS] Model switch risk check failed:", error);
  }
  return false;
}

/**
 * Zeigt Warn-Modal für Modellwechsel mit kritischem Context
 */
function showModelSwitchWarningModal(targetModel, state) {
  const modalId = "context-switch-warning-modal";

  // #UIDeduplication: Entferne existierendes Modal
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = modalId;
  modal.className = "context-modal context-modal--warning";
  modal.innerHTML = `
    <div class="context-modal-backdrop"></div>
    <div class="context-modal-content">
      <h3 class="context-modal-title">⚠️ Kontext-Warnung</h3>
      <p class="context-modal-body">
        Das gewählte Modell <strong>${targetModel}</strong> nähert sich seinem Kontext-Limit.<br>
        Aktuelle Auslastung mit deinem Chat: <strong>${state.usage_percent.toFixed(1)}%</strong>
      </p>
      <div class="context-modal-actions">
        <button class="context-modal-btn context-modal-btn--primary" data-action="proceed">
          Trotzdem wechseln
        </button>
        <button class="context-modal-btn context-modal-btn--secondary" data-action="cancel">
          Abbrechen
        </button>
        <button class="context-modal-btn context-modal-btn--tertiary" data-action="compress">
          Kompression vorschlagen
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Event Listeners für Buttons
  modal.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const action = e.target.dataset.action;
      handleModelSwitchDecision(action, targetModel, modal);
    });
  });

  // D10 Telemetrie
  logContextEvent("context_model_switch_risk", {
    target_model: targetModel,
    target_provider: state.provider,
    usage_percent: state.usage_percent,
    status: state.status,
    total_tokens: state.total_tokens,
    effective_input_limit: state.effective_input_limit,
  });
}

/**
 * Verarbeitet Entscheidung im Warn-Modal
 */
function handleModelSwitchDecision(action, targetModel, modal) {
  modal.remove();

  const modelSelect = document.getElementById("model-select");
  const providerSelect = document.getElementById("provider-select");

  switch (action) {
    case "proceed":
      // Nutzer will trotzdem wechseln
      logContextEvent("context_model_switch_proceeded", { target_model: targetModel });
      // 💎 CU-3: Update Backend und State vor dem Event
      if (modelSelect) {
        modelSelect.value = targetModel;
        // Update appState für updateLastUsedModelInBackend
        if (window.appState && window.appState.last_active) {
          window.appState.last_active.model = targetModel;
          if (providerSelect) {
            window.appState.last_active.provider = providerSelect.value;
          }
        }
        // Speichere im Backend (global function from app.js)
        if (typeof window.updateLastUsedModelInBackend === "function") {
          window.updateLastUsedModelInBackend().catch(err => {
            console.warn("[CONTEXT-AWARENESS] updateLastUsedModelInBackend failed:", err);
          });
        }
        // Trigger change event manually
        modelSelect.dispatchEvent(new Event("change", { bubbles: true }));
      }
      break;

    case "cancel":
      // Reset Dropdown auf vorherigen Wert
      logContextEvent("context_model_switch_cancelled", { target_model: targetModel });
      if (modelSelect && PENDING_MODEL_SWITCH.has("previousModel")) {
        modelSelect.value = PENDING_MODEL_SWITCH.get("previousModel");
      }
      break;

    case "compress":
      // Phase 3: Starte Proposal Flow
      logContextEvent("context_compression_started", { target_model: targetModel, source: "model_switch_modal" });
      showCompressionLoadingModal(targetModel);
      fetchCompressionProposal(targetModel).then((proposal) => {
        removeCompressionLoadingModal();
        if (proposal && proposal.can_compress) {
          showCompressionReviewModal(proposal, targetModel);
        } else {
          showCompressionErrorModal(proposal?.message || "Keine Kompression möglich.");
        }
      });
      break;
  }

  PENDING_MODEL_SWITCH.delete("previousModel");
}

/**
 * Hilfsfunktion: Findet erstes verfügbares Modell für Provider
 */
function findFirstModelForProvider(provider) {
  const modelSelect = document.getElementById("model-select");
  if (!modelSelect) return null;

  const options = Array.from(modelSelect.options);
  return options.find((opt) => {
    // Annahme: Option value enthält Provider-Präfix oder wir prüfen data-Attribute
    const optProvider = opt.dataset?.provider || provider;
    return optProvider === provider;
  })?.value || options[0]?.value;
}

// ============================================
// Phase 3: Compression Proposal UI
// ============================================

/**
 * Zeigt Lade-Modal während Proposal-Generierung
 */
function showCompressionLoadingModal(targetModel) {
  const modalId = "context-compression-loading-modal";
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = modalId;
  modal.className = "context-modal";
  modal.innerHTML = `
    <div class="context-modal-backdrop"></div>
    <div class="context-modal-content">
      <h3 class="context-modal-title">🔄 Analysiere Kontext...</h3>
      <p class="context-modal-body">
        Untersuche Nachrichten für <strong>${targetModel}</strong>...<br>
        <span class="context-loading-dots">•••</span>
      </p>
      <div class="context-modal-actions">
        <button class="context-modal-btn context-modal-btn--secondary" data-action="cancel-loading">
          Abbrechen
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Cancel-Button entfernt nur das Modal
  modal.querySelector('[data-action="cancel-loading"]')?.addEventListener("click", () => {
    modal.remove();
  });
}

/**
 * Entfernt das Lade-Modal
 */
function removeCompressionLoadingModal() {
  const modal = document.getElementById("context-compression-loading-modal");
  if (modal) modal.remove();
}

/**
 * Fetcht Compression Proposal vom Backend
 */
async function fetchCompressionProposal(targetModel) {
  try {
    // 💎 FIX: Sammle nur Messages vom aktiven Fenster (A), nicht von allen Fenstern
    // Bug: Vorher wurden Messages aus allen Fenstern gesammelt, aber nur chat_id von Fenster A gesendet
    const chatId = getActiveChatIdForWindow("A"); // Primäres Fenster
    const messages = collectVisibleMessages("A");

    const response = await fetch(`${API_BASE_URL}/api/context/compression/propose`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: chatId,
        messages: messages.length > 0 ? messages : undefined,
        include_persisted_messages: messages.length === 0,
        target_model: targetModel,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Proposal-Generierung fehlgeschlagen");
    }

    return await response.json();
  } catch (error) {
    console.error("[CONTEXT-AWARENESS] Compression proposal failed:", error);
    return { can_compress: false, message: error.message };
  }
}

/**
 * Zeigt Review-Modal mit Proposal-Details
 */
function showCompressionReviewModal(proposal, targetModel) {
  const modalId = "context-compression-review-modal";
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const savingsVisual = proposal.savings_euro_estimate > 0
    ? `<div class="context-savings-visual">
         💰 Geschätzte Ersparnis: ~${proposal.savings_euro_estimate.toFixed(3)}€
       </div>`
    : "";

  const modal = document.createElement("div");
  modal.id = modalId;
  modal.className = "context-modal";
  modal.innerHTML = `
    <div class="context-modal-backdrop"></div>
    <div class="context-modal-content context-modal-content--large">
      <h3 class="context-modal-title">📋 Kompressions-Vorschlag</h3>

      <div class="context-proposal-stats">
        <div class="context-stat">
          <span class="context-stat-value">${proposal.candidates.length}</span>
          <span class="context-stat-label">Nachrichten</span>
        </div>
        <div class="context-stat">
          <span class="context-stat-value">${proposal.estimated_tokens_saved.toLocaleString("de-DE")}</span>
          <span class="context-stat-label">Tokens gespart</span>
        </div>
        <div class="context-stat">
          <span class="context-stat-value">${proposal.savings_percent.toFixed(1)}%</span>
          <span class="context-stat-label">Einsparung</span>
        </div>
      </div>

      ${savingsVisual}

      <div class="context-proposal-summary">
        <h4>Zusammenfassung:</h4>
        <pre class="context-summary-text">${escapeHtml(proposal.summary_preview)}</pre>
      </div>

      <div class="context-proposal-candidates">
        <h4>Betroffene Nachrichten (Vorschau):</h4>
        <ul class="context-candidate-list">
          ${proposal.candidates.slice(0, 5).map(c => `
            <li class="context-candidate-item">
              <span class="context-candidate-role">${c.role}</span>
              <span class="context-candidate-preview">${escapeHtml(c.content_preview.substring(0, 60))}...</span>
              <span class="context-candidate-tokens">~${c.estimated_tokens} tokens</span>
            </li>
          `).join("")}
          ${proposal.candidates.length > 5 ? `<li class="context-candidate-more">...und ${proposal.candidates.length - 5} weitere</li>` : ""}
        </ul>
      </div>

      <div class="context-modal-actions">
        <button class="context-modal-btn context-modal-btn--primary" data-action="apply-compression">
          ✅ Bestätigen & Komprimieren (Phase 4)
        </button>
        <button class="context-modal-btn context-modal-btn--secondary" data-action="cancel-compression">
          Abbrechen
        </button>
      </div>

      <p class="context-modal-hint">
        💡 Die letzten ${proposal.protected_count} Nachrichten bleiben unverändert (aktiver Kontext).
      </p>

      <!-- 💎 CU-3: PDF Backup Option -->
      <div class="compression-pdf-option">
        <label class="compression-pdf-label">
          <input type="checkbox" id="create-pdf-backup" checked>
          <span class="compression-pdf-text">
            📄 Backup der Original-Nachrichten als PDF speichern (JanusPDFs)
          </span>
        </label>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Event Listeners
  const applyBtn = modal.querySelector('[data-action="apply-compression"]');
  if (applyBtn) {
    applyBtn.textContent = "✅ Bestätigen & Komprimieren";
    applyBtn.addEventListener("click", async () => {
      applyBtn.disabled = true;
      applyBtn.textContent = "⏳ Komprimiere...";

      const chatId = getActiveChatIdForWindow("A");
      if (!chatId) {
        alert("Kein aktiver Chat gefunden.");
        applyBtn.disabled = false;
        applyBtn.textContent = "✅ Bestätigen & Komprimieren";
        return;
      }

      // 💎 CU-3: PDF-Backup Option auslesen
      const pdfCheckbox = document.getElementById("create-pdf-backup");
      const createPdfBackup = pdfCheckbox ? pdfCheckbox.checked : true;

      const result = await applyCompression(
        chatId,
        proposal.candidates.map(c => c.index),
        proposal.summary_preview,
        proposal.estimated_tokens_saved,
        createPdfBackup
      );

      modal.remove();

      if (result.success) {
        logContextEvent("context_compression_applied", {
          compression_id: result.compression_id,
          messages_archived: result.messages_archived,
          target_model: targetModel,
        });

        // 💎 SILENT COMPRESSION: Refresh nur Pane A, nicht Pane B
        // Verhindert automatisches Öffnen von Pane B nach Kompression
        await refreshChatMessages("A");

        // Zeige Erfolgs-Toast
        showCompressionSuccessToast(result);
      } else {
        logContextEvent("context_compression_apply_failed", {
          error: result.message,
          target_model: targetModel,
        });
        alert(`Kompression fehlgeschlagen: ${result.message}`);
      }
    });
  }

  modal.querySelector('[data-action="cancel-compression"]')?.addEventListener("click", () => {
    modal.remove();
    logContextEvent("context_compression_cancelled", { target_model: targetModel });
  });
}

/**
 * Zeigt Fehler-Modal wenn Proposal fehlschlägt
 */
function showCompressionErrorModal(message) {
  const modalId = "context-compression-error-modal";
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = modalId;
  modal.className = "context-modal";
  modal.innerHTML = `
    <div class="context-modal-backdrop"></div>
    <div class="context-modal-content">
      <h3 class="context-modal-title">⚠️ Kompression nicht möglich</h3>
      <p class="context-modal-body">${escapeHtml(message)}</p>
      <div class="context-modal-actions">
        <button class="context-modal-btn context-modal-btn--secondary" data-action="close">
          Schließen
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  modal.querySelector('[data-action="close"]')?.addEventListener("click", () => {
    modal.remove();
  });
}

/**
 * Hilfsfunktion: Escaped HTML für sichere Anzeige
 */
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ============================================
// Phase 4: Apply & Restore Functions
// ============================================

/**
 * Wendet die Kompression auf den Chat an
 */
async function applyCompression(chatId, candidateIndices, summaryText, tokensSaved, createPdfBackup = true) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/context/compression/apply`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: chatId,
        candidate_indices: candidateIndices,
        summary_text: summaryText,
        tokens_saved: tokensSaved,
        create_pdf_backup: createPdfBackup,  // 💎 CU-3: PDF Backup Option
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return { success: false, message: error.detail || "Kompression fehlgeschlagen" };
    }

    return await response.json();
  } catch (error) {
    console.error("[CONTEXT-AWARENESS] Apply compression failed:", error);
    return { success: false, message: error.message };
  }
}

/**
 * Stellt eine komprimierte Nachrichtengruppe wieder her
 */
export async function restoreCompression(compressionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/context/compression/${compressionId}/restore`, {
      method: "POST",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return { success: false, message: error.detail || "Wiederherstellung fehlgeschlagen" };
    }

    const result = await response.json();

    if (result.success) {
      logContextEvent("context_compression_restored", {
        compression_id: compressionId,
        messages_restored: result.messages_restored,
      });

      // 💎 SILENT COMPRESSION: Refresh nur Pane A, nicht Pane B
      // Verhindert automatisches Öffnen von Pane B nach Wiederherstellung
      await refreshChatMessages("A");
    }

    return result;
  } catch (error) {
    console.error("[CONTEXT-AWARENESS] Restore compression failed:", error);
    return { success: false, message: error.message };
  }
}

/**
 * Refresht die Nachrichten eines Chat-Fensters nach Compression/Restore
 */
async function refreshChatMessages(windowId) {
  const chatId = getActiveChatIdForWindow(windowId);
  if (!chatId) return;

  // 💎 CU-2: Trigger reload via chatManager (korrekter Pfad)
  if (window.chatManager && typeof window.chatManager.loadChat === "function") {
    await window.chatManager.loadChat(parseInt(chatId), {
      context: 'compression_refresh',
      windowId: windowId,
    });
    console.log("[CONTEXT-AWARENESS] Chat reloaded for window", windowId);
  } else {
    // Fallback: Reload page
    console.warn("[CONTEXT-AWARENESS] chatManager.loadChat not available, reloading page");
    window.location.reload();
  }

  // Refresh context meter (force immediate update)
  scheduleContextRefresh(windowId);
}

/**
 * Zeigt Erfolgs-Toast nach Kompression
 */
function showCompressionSuccessToast(result) {
  const container = document.getElementById(paneId("chat-messages", "A"));
  if (!container) return;

  const toast = document.createElement("div");
  // 💎 CU-3: PDF Backup Info im Toast anzeigen
  const pdfInfo = result.pdf_backup_created
    ? `<span class="context-toast-pdf-info">📄 PDF in JanusPDFs gespeichert</span>`
    : "";

  toast.className = "context-toast context-toast--success";
  toast.innerHTML = `
    <span class="context-toast-icon">✅</span>
    <span class="context-toast-text">
      ${result.messages_archived} Nachrichten komprimiert.
      ${pdfInfo}
      <button class="context-toast-action" data-compression-id="${result.compression_id}">
        Rückgängig
      </button>
    </span>
    <button class="context-toast-close" aria-label="Schließen">×</button>
  `;

  // Restore-Button Handler
  toast.querySelector(".context-toast-action")?.addEventListener("click", async (e) => {
    const compressionId = e.target.dataset.compressionId;
    const restoreResult = await restoreCompression(compressionId);
    if (restoreResult.success) {
      toast.remove();
      alert(`${restoreResult.messages_restored} Nachrichten wiederhergestellt.`);
    } else {
      alert(`Fehler: ${restoreResult.message}`);
    }
  });

  toast.querySelector(".context-toast-close")?.addEventListener("click", () => {
    toast.remove();
  });

  // Auto-remove after 15 seconds
  setTimeout(() => toast.remove(), 15000);

  container.appendChild(toast);
}

/**
 * Renders a compression summary block in the chat
 * Call this from message rendering code to show "Details" button
 */
export function renderCompressionSummary(metadata) {
  if (!metadata || !metadata.is_compression_summary) return null;

  const compressionId = metadata.compression_id;

  return {
    isCompressionSummary: true,
    compressionId: compressionId,
    render: () => `
      <div class="compression-summary-block">
        <div class="compression-summary-header">
          <span class="compression-summary-icon">📦</span>
          <span class="compression-summary-title">Kontext-Kompression</span>
        </div>
        <div class="compression-summary-content">
          <button class="compression-details-btn" data-compression-id="${compressionId}">
            📋 Details anzeigen
          </button>
          <button class="compression-restore-btn" data-compression-id="${compressionId}">
            ↩️ Wiederherstellen
          </button>
        </div>
      </div>
    `,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// 💎 CU-2: Interaktive Kompressions-Details (Global Event Listener)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Initialisiert globalen Event-Listener für Compression-Detail-Buttons.
 * Wird einmal beim App-Start aufgerufen.
 */
export function initCompressionDetailsListeners() {
  // Delegate clicks on compression detail buttons
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".show-compression-details");
    if (!btn) return;

    const compressionId = btn.dataset.compressionId;
    if (!compressionId) {
      console.warn("[CONTEXT-AWARENESS] No compression ID found on button");
      return;
    }

    e.preventDefault();
    e.stopPropagation();

    await showCompressionDetailsModal(compressionId);
  });
}

/**
 * Zeigt das Compression-Details-Modal mit Summary und archivierten Nachrichten.
 */
async function showCompressionDetailsModal(compressionId) {
  // Erstelle Modal falls nicht vorhanden
  const modalId = "compression-details-modal";
  let modal = document.getElementById(modalId);
  if (modal) modal.remove();

  modal = document.createElement("div");
  modal.id = modalId;
  modal.className = "context-modal compression-details-modal";
  modal.innerHTML = `
    <div class="context-modal-backdrop"></div>
    <div class="context-modal-content compression-details-content">
      <div class="compression-details-header">
        <h3 class="compression-details-title">📦 Kompressions-Details</h3>
        <button class="compression-details-close" aria-label="Schließen">×</button>
      </div>
      <div class="compression-details-body">
        <div class="compression-loading">⏳ Lade Details...</div>
      </div>
      <div class="compression-details-footer">
        <button class="context-modal-btn context-modal-btn--secondary compression-details-close-btn">
          Schließen
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Close handlers
  const closeModal = () => modal.remove();
  modal.querySelector(".compression-details-close")?.addEventListener("click", closeModal);
  modal.querySelector(".compression-details-close-btn")?.addEventListener("click", closeModal);
  modal.querySelector(".context-modal-backdrop")?.addEventListener("click", closeModal);

  // ESC key handler
  const escHandler = (e) => {
    if (e.key === "Escape") {
      closeModal();
      document.removeEventListener("keydown", escHandler);
    }
  };
  document.addEventListener("keydown", escHandler);

  // Load details
  try {
    const response = await fetch(`${API_BASE_URL}/api/context/compression/${compressionId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    renderCompressionDetails(modal, data);
  } catch (error) {
    console.error("[CONTEXT-AWARENESS] Failed to load compression details:", error);
    modal.querySelector(".compression-details-body").innerHTML = `
      <div class="compression-error">
        <p>❌ Fehler beim Laden der Details.</p>
        <p class="compression-error-details">${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

/**
 * Rendert die Compression-Details in das Modal.
 */
function renderCompressionDetails(modal, data) {
  const body = modal.querySelector(".compression-details-body");
  if (!body) return;

  const archivedCount = data.archived_messages?.length || 0;
  const savedPercent = data.compression_ratio
    ? Math.round(data.compression_ratio * 100)
    : 0;

  let archivedHtml = "";
  if (archivedCount > 0) {
    archivedHtml = `
      <details class="compression-archives-accordion">
        <summary class="compression-archives-summary">
          📋 Archivierte Nachrichten (${archivedCount})
        </summary>
        <div class="compression-archives-list">
          ${data.archived_messages
            .map(
              (msg, idx) => `
            <div class="compression-archive-item">
              <div class="compression-archive-header">
                <span class="compression-archive-role ${msg.role}">${msg.role}</span>
                <span class="compression-archive-index">#${idx + 1}</span>
              </div>
              <div class="compression-archive-content">
                ${escapeHtml(msg.content?.substring(0, 500) || "(kein Inhalt)")}
                ${msg.content?.length > 500 ? "..." : ""}
              </div>
            </div>
          `
            )
            .join("")}
        </div>
      </details>
    `;
  }

  body.innerHTML = `
    <div class="compression-details-summary">
      <div class="compression-meta">
        <div class="compression-meta-item">
          <span class="compression-meta-label">Tokens gespart:</span>
          <span class="compression-meta-value">${data.tokens_saved?.toLocaleString() || 0}</span>
        </div>
        <div class="compression-meta-item">
          <span class="compression-meta-label">Kompressionsrate:</span>
          <span class="compression-meta-value">~${savedPercent}%</span>
        </div>
        <div class="compression-meta-item">
          <span class="compression-meta-label">Nachrichten:</span>
          <span class="compression-meta-value">${data.original_message_count || archivedCount}</span>
        </div>
        ${data.is_restored ? '<span class="compression-restored-badge">🔄 Bereits wiederhergestellt</span>' : ""}
      </div>

      <div class="compression-summary-box">
        <h4 class="compression-summary-box-title">📝 Zusammenfassung</h4>
        <div class="compression-summary-text">
          ${escapeHtml(data.summary_text || "(keine Zusammenfassung verfügbar)")}
        </div>
      </div>

      ${archivedHtml}
    </div>
  `;
}
