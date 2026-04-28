import { sanitizeReleaseNotes, sanitizeTemplateHtml } from "./dompurify-config.js";

// ================= WRAPPER FÜR FETCH (API KEY) =================
(() => {
    // API-Schlüssel einmal beim Start abrufen und für die Sitzung speichern.
    const apiKeyPromise = (async () => {
        try {
            const key = await window.electron?.getApiKey?.();
            if (!key) {
                console.error("API-Schlüssel konnte nicht abgerufen werden. API-Aufrufe werden wahrscheinlich fehlschlagen.");
            } else {
                console.log("API-Schlüssel erfolgreich für die Sitzung geladen.");
            }
            return key;
        } catch (e) {
            console.error("Fehler beim Abrufen des API-Schlüssels beim Start:", e);
            return null;
        }
    })();

    const originalFetch = window.fetch.bind(window);
    window.fetch = async (url, options = {}) => {
        // Wir erstellen eine Kopie der Optionen, um das Original nicht zu verändern.
        const newOptions = { ...options };

        // Sicherstellen, dass das headers-Objekt existiert.
        newOptions.headers = { ...(options?.headers || {}) };

        // Den API-Schlüssel nur hinzufügen, wenn der Aufruf an unser eigenes Backend geht.
        // WICHTIG: Bilder (/user_images/) und Sounds (/sounds/, /api/system/camera_sound) ausschließen, um CORS-Preflight-Fehler zu vermeiden!
        const urlStr = url.toString();
        const isBackend = urlStr.startsWith('http://127.0.0.1:8001') || urlStr.startsWith('http://localhost:8001');
        const isStaticAsset = urlStr.includes('/user_images/') || urlStr.includes('/sounds/') || urlStr.includes('/backend_assets/');
        const isApiCall = isBackend && !isStaticAsset;
        
        if (isApiCall) {
            const apiKey = await apiKeyPromise;
            if (apiKey) {
                newOptions.headers['X-Janus-Internal-Key'] = apiKey;
            }
        }

        // Die ursprüngliche fetch-Funktion mit den neuen Optionen aufrufen.
        return originalFetch(url, newOptions);
    };

    console.log("Globale fetch-Funktion wurde überschrieben, um den API-Schlüssel einzufügen.");
})();
// ===============================================================

// ================= SENTRY INTEGRATION (LOKALES MODUL) =================
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: "https://52d089968563a42a98ed367df7723736@o4510659131670528.ingest.de.sentry.io/4510660337533008",
  release: "janus-projekt@" + (import.meta.env.APP_VERSION || "0.0.0-dev"),
  integrations: [
    // --- NEU: DISTRIBUTED TRACING AKTIVIEREN ---
    Sentry.browserTracingIntegration({
      // Wir sagen Sentry, dass es bei Anfragen an unser eigenes Backend
      // den Trace-Header mitschicken soll, um Frontend und Backend zu verbinden.
      tracePropagationTargets: ["localhost", "127.0.0.1"],
    }),
    // -------------------------------------------
    Sentry.replayIntegration(),
  ],

  // --- NEU: FEEDBACK-DIALOG BEI FEHLERN ---
  beforeSend(event, hint) {
    // Wir prüfen, ob es sich um eine echte, unbehandelte Exception handelt.
    // Das verhindert, dass der Dialog bei kleinen Netzwerkfehlern aufploppt.
    if (event.exception && hint.originalException) {
      Sentry.showReportDialog({ 
          eventId: event.event_id,
          title: "Es ist ein Fehler aufgetreten",
          subtitle: "Unser Team wurde automatisch benachrichtigt.",
          subtitle2: "Wenn du uns helfen möchtest, beschreibe bitte kurz, was du gerade getan hast.",
          labelComments: "Was ist passiert?",
          labelClose: "Schließen",
          labelSubmit: "Feedback senden",
          successMessage: "Vielen Dank! Dein Feedback wurde übermittelt."
      });
    }
    return event;
  },
  // ----------------------------------------

  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

// ======================== ENDE DER INTEGRATION ========================

import interact from "interactjs";
import { API_BASE_URL } from "./config.js";
import "./personality-settings.js";
import { loadChats } from "./chat-manager.js";
import { initChatComposer, scrollChatToBottom, autoResize } from "./chat.js";
import {
  paneId,
  getActiveWindowId,
  WINDOW_IDS,
  getWindowState,
  subscribeWindowState,
  setWindowProvider,
  setWindowModel,
} from "./window-state.js";
import { openProjectModal, showProjectModalView, initProjectModalAfterListLoad } from "./projects.js";
import { openModal } from "./modal-api.js";

/** Scroll main chat (#chat-messages) to the end; delegates to chat.js (same role as scrollToBottom in autoResize docs). */
export function scrollToBottom(options) {
  scrollChatToBottom(options ?? {});
}

const appState = {
  currentView: "chat",
  currentProjectId: null,    // Track the currently selected project
  currentProjectName: null,  // Track the current project name
  user_selections: {},
  last_active: {
    provider: "openai",
    model: "gpt-3.5-turbo",
  },
  model_catalog: {}, // Will be loaded dynamically
};

function switchView(viewName, data = null) {
    const chatView = document.getElementById('chat-view');
    const projectDashboardView = document.getElementById('project-dashboard-view');
    const chatWindow = document.getElementById("chat-window-A");
    const chatWindowHost = document.getElementById("chat-window-host-A");
    const projectChatHost = document.getElementById('project-chat-host');

    // Hide all views
    if (chatView) chatView.style.display = 'none';
    if (projectDashboardView) projectDashboardView.style.display = 'none';

    if (viewName === 'chat') {
        if (chatView) {
            chatView.style.display = 'block';

            if (chatWindow && chatWindowHost && chatWindow.parentElement !== chatWindowHost) {
                chatWindowHost.appendChild(chatWindow);
                chatWindow.style.left = '0px';
                chatWindow.style.top = '0px';
                chatWindow.setAttribute('data-x', '0');
                chatWindow.setAttribute('data-y', '0');
            }

            // If a chatId is provided, load that specific chat
            if (data && data.chatId) {
                if (window.chatManager && typeof window.chatManager.loadChat === 'function') {
                    window.chatManager.loadChat(data.chatId, {
                      context: 'assistant',
                      windowId: getActiveWindowId(),
                    });
                } else {
                    console.error('chatManager.loadChat is not available');
                }
            } else {
                if (window.chatManager && typeof window.chatManager.loadChats === 'function') {
                    window.chatManager.loadChats(true, null);
                }
            }
        }
    } else if (viewName === 'project' && projectDashboardView) {
        projectDashboardView.style.display = 'block';

        if (chatWindow && projectChatHost && chatWindow.parentElement !== projectChatHost) {
            projectChatHost.appendChild(chatWindow);
            chatWindow.style.left = '0px';
            chatWindow.style.top = '0px';
            chatWindow.setAttribute('data-x', '0');
            chatWindow.setAttribute('data-y', '0');
        }

        // Call function to render project dashboard
        if (data && data.project) {
            // Update global state
            appState.currentProjectId = data.project.id;
            appState.currentProjectName = data.project.name;
            
            // Render the project dashboard
            if (window.renderProjectDashboard && typeof window.renderProjectDashboard === 'function') {
                window.renderProjectDashboard(data.project);
            } else {
                console.error('renderProjectDashboard function is not available');
            }
        }
    }
}

window.addEventListener('models-updated', async () => {
  console.info('[Auto-Aggregation] Modelle wurden angepasst, aktualisiere Dropdown.');
  try {
    await loadModelCatalog();
    await loadUserSelections();
    render();
  } catch (error) {
    console.error('Failed to refresh models after update event:', error);
  }
});

window.switchView = switchView;

let modelSelectionForm;
let backFromModelsBtn;
let modelList;

function formatCost(cost, suffix, isImageCost = false) { // NEU: isImageCost Parameter
  console.log("formatCost called with cost:", cost, "suffix:", suffix, "isImageCost:", isImageCost); // Debug Log
  if (cost === 0) {
    return `0.00${suffix}`;
  }

  // Für Token-Kosten: höhere Präzision
  if (!isImageCost) {
    // Sicherstellen, dass kleine Zahlen korrekt angezeigt werden, z.B. 0.0000005
    if (cost < 0.00001) {
        return `${cost.toFixed(8)}${suffix}`;
    }
    return `${cost.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 8 })}${suffix}`;
  } 
  // Für Bildkosten: 2 Nachkommastellen
  else {
    return `${cost.toFixed(2)}${suffix}`;
  }
}

function showLoginScreen() {
    console.log("Showing login screen");
    
    // Hide main app container if it exists
    const appContainer = document.querySelector('.app-container');
    if (appContainer) {
        appContainer.style.display = 'none';
    }

    // Check if login screen already exists
    let loginScreen = document.getElementById('login-screen');
    if (loginScreen) {
        loginScreen.style.display = 'flex';
        return;
    }

    // Create login screen
    loginScreen = document.createElement('div');
    loginScreen.id = 'login-screen';
    loginScreen.innerHTML = `
        <div class="login-container">
            <h1>Janus</h1>
            <p>Please configure your API keys to continue.</p>
            <div class="login-actions">
                <button id="open-settings-btn">Open Settings</button>
                <button id="retry-login-btn">Retry</button>
            </div>
            <p class="login-error" id="login-error-msg" style="display: none;"></p>
            <p class="login-hint">Please ensure your API keys are properly configured in the settings.</p>
        </div>
    `;
    document.body.appendChild(loginScreen);

    // Add styles for the login screen if they don't exist
    if (!document.getElementById('login-screen-styles')) {
        const style = document.createElement('style');
        style.id = 'login-screen-styles';
        style.textContent = `
            #login-screen {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(5px);
                display: flex;
                justify-content: center;
                align-items: center;
                text-align: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                color: #e0e0e0;
                z-index: 1000;
                padding: 20px;
                box-sizing: border-box;
            }
            .login-container {
                background: #2a2a2a;
                padding: 2.5rem;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 100%;
                border: 1px solid #404040;
            }
            .login-container h1 {
                margin: 0 0 1rem 0;
                font-size: 2rem;
                color: #ffffff;
            }
            .login-container p {
                margin: 0 0 1.5rem 0;
                line-height: 1.5;
            }
            .login-actions {
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin-bottom: 1.5rem;
            }
            #open-settings-btn,
            #retry-login-btn {
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 0.95rem;
            }
            #open-settings-btn {
                background: #007bff;
                color: white;
            }
            #open-settings-btn:hover {
                background: #0056b3;
                transform: translateY(-1px);
            }
            #retry-login-btn {
                background: #404040;
                color: #e0e0e0;
                border: 1px solid #555;
            }
            #retry-login-btn:hover {
                background: #505050;
                transform: translateY(-1px);
            }
            .login-error {
                margin: 1rem 0 0;
                color: #ff6b6b;
                font-size: 0.9rem;
                min-height: 1.5rem;
            }
            .login-hint {
                margin: 1.5rem 0 0 !important;
                font-size: 0.85rem;
                color: #a0a0a0;
            }
            @media (max-width: 600px) {
                .login-container {
                    padding: 1.5rem;
                }
                .login-actions {
                    flex-direction: column;
                }
                #open-settings-btn,
                #retry-login-btn {
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Add event listeners
    const retryBtn = document.getElementById('retry-login-btn');
    const settingsBtn = document.getElementById('open-settings-btn');
    const errorMsg = document.getElementById('login-error-msg');

    if (retryBtn) {
        retryBtn.addEventListener('click', async () => {
            errorMsg.style.display = 'none';
            const isAuthenticated = await attemptSilentLogin();
            if (!isAuthenticated) {
                errorMsg.textContent = 'Still unable to authenticate. Please check your API keys in settings.';
                errorMsg.style.display = 'block';
            }
        });
    }

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            console.log("Notfall-Button gedrückt: Erzwinge Einstellungen...");

            // 1. DAS MODAL ZWANGSWEISE AUSBLENDEN
            // Wir suchen das Modal-Element (das Eltern-Element des Buttons)
            const blockingModal = settingsBtn.closest('.modal-overlay') || settingsBtn.closest('div[style*="fixed"]');
            if (blockingModal) {
                blockingModal.style.display = 'none';
                blockingModal.remove(); // Sicher ist sicher: Weg damit aus dem DOM
            }
            
            // Versuchen wir auch, den "Login Screen" Container zu finden, falls er es ist
            const loginScreen = document.getElementById('login-screen');
            if (loginScreen) loginScreen.style.display = 'none';

            // 2. DIE NORMALE APP-OBERFLÄCHE EINBLENDEN
            const appContainer = document.querySelector('.app-container');
            if (appContainer) appContainer.style.display = 'flex';

            // 3. ZU DEN EINSTELLUNGEN WECHSELN
            // Wir nutzen die globale switchView Funktion, falls verfügbar
            if (typeof window.switchView === 'function') {
                window.switchView('settings-view');
            } else {
                // Manuelles Umschalten (Fallback)
                document.querySelectorAll('main.view').forEach(v => v.style.display = 'none');
                const settingsView = document.getElementById('settings-view');
                if (settingsView) settingsView.style.display = 'block';
            }

            // 4. API-KEY TAB AKTIVIEREN
            // Damit der User direkt im richtigen Feld landet
            setTimeout(() => {
                const apiKeyLink = document.querySelector('[data-target="api-key-section"]');
                if (apiKeyLink) apiKeyLink.click();
            }, 100);
        });
    }
}

function hideLoginScreen() {
    console.log("Hiding login screen");
    const loginScreen = document.getElementById('login-screen');
    if (loginScreen) {
        // Instead of removing, just hide it so we can show it again if needed
        loginScreen.style.display = 'none';
    }
    
    // Show the main app container
    const appContainer = document.querySelector('.app-container');
    if (appContainer) {
        appContainer.style.display = ''; // Revert to default display
    }
}


async function validateToken() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    console.warn("No authentication token found in localStorage for validation.");
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/users/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (response.ok) {
      console.log("Token validation successful.");
      return true;
    } else {
      console.warn(`Token validation failed with status: ${response.status}`);
      localStorage.removeItem('auth_token'); // Remove invalid token
      return false;
    }
  } catch (error) {
    console.error("Error during token validation:", error);
    return false;
  }
}

// NEU: Funktion zum Speichern des zuletzt verwendeten Modells und Providers im Backend
async function updateLastUsedModelInBackend() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    console.warn("Cannot update last used model: No auth token found.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/last-used-model`, {
      method: "PUT",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        provider: appState.last_active.provider,
        model: appState.last_active.model,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || "Failed to update last used model in backend.");
    }
    console.log("Last used model updated in backend:", appState.last_active.provider, appState.last_active.model);
  } catch (error) {
    console.error("Error updating last used model in backend:", error);
  }
}

/**
 * Füllt ein beliebiges Modell-Dropdown mit derselben Logik wie die Sidebar (Katalog + User-Selection + Filter).
 * @param {HTMLSelectElement} selectEl
 * @param {string} targetProvider
 */
function fillModelOptionsIntoSelect(selectEl, targetProvider) {
  if (!selectEl || !targetProvider) return;
  selectEl.innerHTML = "";
  let allowedModels = appState.user_selections[targetProvider] || [];

  // Wenn keine Modelle ausgewählt sind, zeige keine an (nicht alle als Fallback)
  if (allowedModels.length === 0) {
    console.warn(`[fillModelOptionsIntoSelect] No models selected for provider: ${targetProvider}`);
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "-- Keine Modelle ausgewählt --";
    selectEl.appendChild(option);
    return;
  }

  if (!appState.model_catalog[targetProvider]) {
    console.warn(`fillModelOptionsIntoSelect: No models for provider: ${targetProvider}`);
    return;
  }

  const filteredModels = appState.model_catalog[targetProvider].filter((model) => {
    const baseModelId =
      model.base_model_id ||
      (String(model.id || "").includes("@") ? String(model.id).split("@", 1)[0] : model.id);
    const allowedBaseModelIds = new Set(
      allowedModels
        .map((item) => (String(item || "").includes("@") ? String(item || "").split("@", 1)[0] : String(item || "")))
        .filter(Boolean),
    );
    const isAllowed =
      allowedModels.includes(model.id) ||
      (model.provider === "ollama" &&
        (allowedModels.includes(baseModelId) || allowedBaseModelIds.has(String(baseModelId || ""))));
    const isNotExcluded = !["gpt-image-1.5", "gpt-image-1-mini", "gpt-4o-mini"].includes(model.id);
    return isAllowed && isNotExcluded;
  });

  const modelsForDropdown = sortSidebarModelsForProvider(targetProvider, filteredModels);

  modelsForDropdown.forEach((model) => {
    const option = document.createElement("option");
    option.value = model.id;

    let costDisplay = "";
    if (model.type === "image") {
      if (model.provider === "gemini" && model.cost_per_million_output_tokens) {
        const costPerImage =
          (model.output_tokens_per_image_1024x1024 / 1000000) * model.cost_per_million_output_tokens;
        costDisplay = `${formatCost(costPerImage, "€/img", true)}`;
        if (model.cost_per_text_input_token) {
          costDisplay += ` + ${formatCost(model.cost_per_text_input_token * 1000000, "€/Mio. in")}`;
        }
      } else if (model.cost_per_image) {
        costDisplay = formatCost(model.cost_per_image, "€/img", true);
        if (model.cost_per_text_input_token) {
          costDisplay += ` + ${formatCost(model.cost_per_text_input_token * 1000000, "€/Mio. in")}`;
        }
      }
    } else if (model.cost_per_token_input) {
      costDisplay = `${formatCost(model.cost_per_token_input * 1000000, "€/Mio. in")} / ${formatCost(model.cost_per_token_output * 1000000, "€/Mio. out")}`;
    }

    const baseLabel = model.base_model_id || model.name || model.id;
    const nodeLabel = model.node_name ? ` (${model.node_name})` : "";
    option.textContent = `${baseLabel}${nodeLabel}${costDisplay ? ` (${costDisplay})` : ""}${model.desc ? " - " + model.desc : ""}`;
    selectEl.appendChild(option);
  });
}

function rebuildHeaderProviderOptions(headerSel) {
  const sb = document.getElementById("provider-select");
  if (!sb || !headerSel) return;
  const sbLabel = (sb.options[sb.selectedIndex]?.textContent || sb.value || "").trim();
  headerSel.innerHTML = "";
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = `↳ Wie Sidebar (${sbLabel || sb.value})`;
  headerSel.appendChild(opt0);
  Array.from(sb.options).forEach((o) => {
    const c = document.createElement("option");
    c.value = o.value;
    c.textContent = o.textContent;
    headerSel.appendChild(c);
  });
}

/**
 * Header-Dropdowns: Overrides aus window-state, sonst Sidebar spiegeln.
 * Nach jedem render() und bei Fenster-State-Events.
 */
function syncChatWindowHeaderLlm() {
  const sbp = document.getElementById("provider-select");
  const sbm = document.getElementById("model-select");
  if (!sbp || !sbm) return;

  for (const wid of WINDOW_IDS) {
    const w = getWindowState().windows[wid];
    const hp = document.getElementById(`chat-header-provider-${wid}`);
    const hm = document.getElementById(`chat-header-model-${wid}`);
    if (!hp || !hm) continue;

    rebuildHeaderProviderOptions(hp);
    hp.value = w.provider != null ? w.provider : "";

    const effProvider = w.provider ?? sbp.value;
    fillModelOptionsIntoSelect(hm, effProvider);

    const wantModel = w.modelId ?? sbm.value;
    if ([...hm.options].some((o) => o.value === wantModel)) {
      hm.value = wantModel;
    } else if (hm.options.length > 0) {
      hm.value = hm.options[0].value;
    }
  }
}

function setupChatHeaderLlmListeners() {
  if (document.body.dataset.janusChatHeaderLlmBound === "1") return;
  document.body.dataset.janusChatHeaderLlmBound = "1";

  for (const wid of WINDOW_IDS) {
    const hp = document.getElementById(`chat-header-provider-${wid}`);
    const hm = document.getElementById(`chat-header-model-${wid}`);
    if (!hp || !hm) continue;

    hp.addEventListener("change", () => {
      const v = hp.value === "" ? null : hp.value;
      setWindowProvider(wid, v);
      setWindowModel(wid, null);
      const sbp = document.getElementById("provider-select");
      const effP = v ?? sbp?.value;
      if (effP) {
        fillModelOptionsIntoSelect(hm, effP);
        const sbm = document.getElementById("model-select");
        const want = sbm?.value;
        if (want && [...hm.options].some((o) => o.value === want)) {
          hm.value = want;
        } else if (hm.options.length) {
          hm.value = hm.options[0].value;
        }
      }
      syncChatWindowHeaderLlm();
    });

    hm.addEventListener("change", () => {
      setWindowModel(wid, hm.value === "" ? null : hm.value);
    });
  }
}

function render() {
  console.log("Rendering app with appState.last_active.provider:", appState.last_active.provider); // Debug Log
  const chatView = document.getElementById("chat-view");
  const settingsView = document.getElementById("settings-view");

  const sidebarProviderSelect = document.getElementById("provider-select");
  const sidebarModelSelect = document.getElementById("model-select");

  if (sidebarProviderSelect && sidebarModelSelect) {
    // --- START DER FINALEN KORREKTUR ---

    // 0. Zustand aus dem Dropdown übernehmen, bevor wir es leeren. Sonst bleibt
    //    appState hinter der Nutzerwahl zurück (Modellwechsel aktualisierte bisher nur das DOM).
    //    Beim Öffnen der Einstellungen würde render() sonst z. B. wieder "Gemini Pro" setzen.
    if (sidebarModelSelect.options && sidebarModelSelect.options.length > 0) {
      const domProvider = sidebarProviderSelect.value;
      const domModel = sidebarModelSelect.value;
      if (domProvider && domModel) {
        appState.last_active.provider = domProvider;
        appState.last_active.model = domModel;
      }
    }

    // 1. Hole die korrekten Werte aus dem State, BEVOR wir das DOM manipulieren.
    const targetProvider = appState.last_active.provider;
    const targetModel = appState.last_active.model;

    // --- SENTRY DIAMANT-STANDARD: INITIALE TAGS ---
    if (window.Sentry) {
        Sentry.setTag("active_provider", targetProvider);
        if (targetModel) {
            Sentry.setTag("active_model", targetModel);
            console.log(`[Sentry] Initial tags set: provider=${targetProvider}, model=${targetModel}`);
        } else {
            console.log(`[Sentry] Initial tag set: provider=${targetProvider}`);
        }
    }
    // ----------------------------------------------

    // 2. Setze den Provider-Wert. Dies kann ein 'change'-Event auslösen, aber das ist uns jetzt egal.
    console.log(`--> [Render] Setting provider to: ${targetProvider}`);
    sidebarProviderSelect.value = targetProvider;

    // 3. Fülle die Modell-Liste basierend auf dem korrekten Provider (gleiche Logik wie Chat-Header).
    console.log(`--> [Render] Populating model list for provider: ${targetProvider}`);
    console.log("--- DROPDOWN-FILTER (Sidebar + Header teilen fillModelOptionsIntoSelect) ---");
    if (appState.model_catalog[targetProvider]) {
      fillModelOptionsIntoSelect(sidebarModelSelect, targetProvider);
    } else {
      console.warn(`No models found for provider: ${targetProvider}`);
    }

    // 4. Intelligentes Setzen des Modells
    // Wir prüfen erst, ob das gewünschte Modell überhaupt in der Liste existiert.
    const availableOptions = Array.from(sidebarModelSelect.options).map(o => o.value);
    console.log(`--> [Render] Verfügbare Modell-Optionen:`, availableOptions);
    console.log(`--> [Render] Ziel-Modell: ${targetModel}`);

    if (availableOptions.includes(targetModel)) {
      // Fall A: Alles gut, das Modell existiert.
      console.log(`--> [Render] Ziel-Modell '${targetModel}' gefunden, wird ausgewählt.`);
      sidebarModelSelect.value = targetModel;
    } else if (availableOptions.length > 0) {
      // Fall B: Das gespeicherte Modell existiert nicht mehr (z.B. gpt-4o-mini).
      // Selbstheilung: Wir wählen automatisch das erste verfügbare Modell.
      const fallbackModel = availableOptions[0];
      console.log(`--> [Render] Gespeichertes Modell '${targetModel}' nicht verfügbar. Wechsele zu Fallback: '${fallbackModel}'`);
      
      sidebarModelSelect.value = fallbackModel;
      
      // Wir aktualisieren auch gleich den State, damit beim nächsten Mal alles stimmt.
      appState.last_active.model = fallbackModel;
      updateLastUsedModelInBackend(); // Speichern im Hintergrund
      
      // Optional: Benachrichtigung an den Benutzer (kann entfernt werden, wenn nicht gewünscht)
      const notification = document.createElement('div');
      notification.className = 'notification is-warning is-light';
      notification.style.position = 'fixed';
      notification.style.top = '1rem';
      notification.style.right = '1rem';
      notification.style.zIndex = '1000';
      notification.innerHTML = `
        <button class="delete"></button>
        Modell '${targetModel}' ist nicht verfügbar. Verwende stattdessen '${fallbackModel}'.
      `;
      document.body.appendChild(notification);
      
      // Schließen-Button für die Benachrichtigung
      notification.querySelector('.delete').addEventListener('click', () => {
        notification.remove();
      });
      
      // Automatisches Ausblenden nach 5 Sekunden
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 5000);
    } else {
      // Fall C: Keine Modelle verfügbar
      console.error('--> [Render] Keine Modelle für den ausgewählten Provider verfügbar!');
      appState.last_active.model = null;
    }

    syncChatWindowHeaderLlm();

    // --- ENDE DER FINALEN KORREKTUR ---
  }

  if (appState.currentView === "chat") {
    chatView.style.display = "block";
    settingsView.style.display = "none";
  } else {
    chatView.style.display = "none";
    settingsView.style.display = "flex";
  }
}

// Function to handle silent login
/**
 * Attempts to authenticate the user either with an existing token or via silent login
 * @returns {Promise<boolean>} True if authentication was successful
 */
async function authenticate() {
    const token = localStorage.getItem('auth_token');
    
    // If we have a token, validate it first
    if (token) {
        try {
            const isValid = await validateToken();
            if (isValid) {
                console.log("Existing token is valid");
                return true;
            }
        } catch (error) {
            console.warn("Token validation failed:", error);
            // Continue with silent login if token validation fails
        }
    }
    
    // If no valid token, try silent login
    return await attemptSilentLogin();
}

/**
 * Attempts to perform silent login by getting a new token from the backend
 * @returns {Promise<boolean>} True if silent login was successful
 */
async function attemptSilentLogin() {
    try {
        console.log("Attempting silent login...");
        const response = await fetch(`${API_BASE_URL}/api/auth/token`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                console.log("No valid API keys found in keyring");
                return false;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.access_token) {
            localStorage.setItem('auth_token', data.access_token);
            console.log("Silent login successful");
            return true;
        }
        
        return false;
    } catch (error) {
        console.error("Silent login failed:", error);
        return false;
    }
}


// The single entry point of the application
document.addEventListener("DOMContentLoaded", async () => {
  console.log("--> [1] DOM fully loaded. Starting application initialization...");
  await initializeApp();
});

// The central initialization function that controls the entire startup process
async function initializeApp() {
  console.log("--> [1] Starting application initialization...");

  // Warten, bis das DOM wirklich da ist
  if (document.readyState === 'loading') {
      console.log("--> [0.5] Waiting for DOM to be fully loaded...");
      await new Promise(r => document.addEventListener('DOMContentLoaded', r));
  }

  let isAuthenticated = false;
  
  // --- RETRY LOGIK FÜR DEN START ---
  // Wir probieren es bis zu 20 Mal (20 Sekunden), damit das Backend Zeit hat zu starten.
  const maxRetries = 20;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`--> [1.1] Authentication attempt ${attempt}/${maxRetries}...`);
        
        // --- AUTH-FIX: Erst erneuern, dann validieren ---
        // 1. Zuerst versuchen wir immer, den Token zu erneuern.
        // Das fängt abgelaufene Tokens ab, bevor sie einen Fehler verursachen.
        console.log("--> [2a] Attempting silent login first...");
        try {
          await attemptSilentLogin();
          console.log("--> [2b] Silent login successful.");
        } catch (error) {
          console.warn("Silent login failed. This might be expected on first run.", error);
          // Wir machen trotzdem weiter, da der User eventuell noch keinen Account hat.
        }
        
        // 2. Jetzt, wo wir sicher einen frischen Token haben, können wir validieren
        console.log("--> [2c] Validating token...");
        const isTokenValid = await validateToken();
        if (isTokenValid) {
            console.log("--> [2d] Token validation successful.");
            isAuthenticated = true;
            break; // Erfolg! Schleife verlassen
        } else {
            console.log("--> [2e] No valid session found after silent login attempt.");
        }

      } catch (e) {
          console.warn(`Attempt ${attempt} failed with error:`, e);
      }

      // Wenn wir noch nicht drin sind und es nicht der letzte Versuch war: Warten.
      if (!isAuthenticated && attempt < maxRetries) {
          console.log("Backend not ready yet. Waiting 1s...");
          await new Promise(resolve => setTimeout(resolve, 1000));
      }
  }

  // FINALE PHASE: Wird nur ausgeführt, wenn einer der Versuche erfolgreich war
  if (isAuthenticated) {
    console.log("--> [3] Authentication successful. Loading application data...");
    
    // Lade ALLE notwendigen Daten.
    // Diese Funktionen sollten jetzt erfolgreich sein, da wir einen gültigen Token haben.
    try {
      console.log("--> [3.1] Loading model catalog...");
      await loadModelCatalog();
      
      console.log("--> [3.2] Loading user selections...");
      await loadUserSelections();
      
      console.log("--> [3.3] Loading last used model...");
      await loadLastUsedModel();
      
      console.log("--> [3.4] Loading projects...");
      await loadProjects();

      // RENDERE die UI und MACHE sie INTERAKTIV
      console.log("--> [3.5] Rendering UI and setting up event listeners...");
      render();
      setupEventListeners();

      // Lade die Chat-Liste als letzten Schritt
      console.log("--> [3.6] Loading chat list...");
      await loadChats();

      /* Fenster-Layout: keine persistierten Positionen — immer Standard (--dual-chat-host-*) */
      resetChatWindowLayout("A");
      resetChatWindowLayout("B");

      // --- NEU: VERSION IN SIDEBAR ANZEIGEN ---
      
      // Diagnose: Schau in die Browser-Konsole (F12)
      // Wenn hier "ReferenceError" kommt, hat Vite nichts ersetzt.
      // Wenn hier "1.0.5" steht, funktioniert es.
      try {
          console.log("Browser Check Version:", __APP_VERSION__);
      } catch (e) {
          console.log("Browser Check: Variable nicht definiert");
      }

      // Sichere Zuweisung
      let currentVersion = "Fehler";
      if (typeof __APP_VERSION__ !== 'undefined') {
          currentVersion = __APP_VERSION__;
      }

      const sidebarVersionEl = document.getElementById('sidebar-version');
      if (sidebarVersionEl) {
          sidebarVersionEl.textContent = `v${currentVersion}`;
      }
      
      const settingsVersionEl = document.getElementById('app-version-display');
      if (settingsVersionEl) {
          settingsVersionEl.textContent = `v${currentVersion}`;
      }

      // Show the app container and hide login screen
      const appContainer = document.querySelector('.app-container');
      if (appContainer) {
        appContainer.style.display = '';
      }
      hideLoginScreen();
      
      console.log("--> [4] Initialization complete. Janus is ready.");
    } catch (error) {
      console.error("--> [ERROR] Failed to initialize application after successful authentication:", error);
      showLoginScreen();
    }
  } else {
    // Fallback, wenn absolut nichts funktioniert hat
    console.error("--> [!] All authentication attempts failed. Showing login screen.");
    showLoginScreen();
  }
}

// A helper function to bundle all event listeners
subscribeWindowState(() => {
  syncChatWindowHeaderLlm();
});

function setupEventListeners() {
  console.log("Setting up UI event listeners...");
  setupChatHeaderLlmListeners();

  const appContainer = document.querySelector(".app-container");
  const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
  if (appContainer && toggleSidebarBtn) {
    const COLLAPSE_KEY = "janus_sidebar_collapsed";

    function applySidebarCollapsedUi(collapsed) {
      toggleSidebarBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
      toggleSidebarBtn.setAttribute(
        "aria-label",
        collapsed ? "Sidebar einblenden" : "Sidebar einklappen"
      );
      toggleSidebarBtn.title = collapsed ? "Sidebar einblenden" : "Sidebar einklappen";
    }

    function setSidebarCollapsed(collapsed) {
      if (collapsed) {
        appContainer.classList.add("sidebar-collapsed");
      } else {
        appContainer.classList.remove("sidebar-collapsed");
      }
      applySidebarCollapsedUi(collapsed);
      try {
        localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
      } catch (_) {
        /* ignore */
      }
    }

    toggleSidebarBtn.addEventListener("click", () => {
      const next = !appContainer.classList.contains("sidebar-collapsed");
      setSidebarCollapsed(next);
    });

    try {
      if (localStorage.getItem(COLLAPSE_KEY) === "1") {
        setSidebarCollapsed(true);
      } else {
        applySidebarCollapsedUi(false);
      }
    } catch (_) {
      applySidebarCollapsedUi(appContainer.classList.contains("sidebar-collapsed"));
    }
  }

  // Listener for model updates from settings
  document.addEventListener("models-updated", async () => {
    console.log("--> [Event] Models updated externally. Refreshing catalog...");
    
    // 1. Reload catalog (required for newly installed local models)
    await loadModelCatalog();

    // 2. Reload user selections from server
    await loadUserSelections();

    // 3. Re-render UI (updates dropdowns)
    render();
  });
  
  // Provider select dropdown
  const sidebarProviderSelect = document.getElementById("provider-select");
  if (sidebarProviderSelect) {
    sidebarProviderSelect.addEventListener("change", async () => {
      // --- START DER FINALEN KORREKTUR ---
      console.log("--> [Event] Provider changed!");

      // 1. Neuen Provider aus dem Dropdown lesen und im State speichern
      const newProvider = sidebarProviderSelect.value;
      appState.last_active.provider = newProvider;
      console.log(`--> [Event] New provider set in state: ${newProvider}`);
      
      // --- SENTRY DIAMANT-STANDARD: TAGS ---
      // Wir markieren den aktuellen Zustand für alle zukünftigen Fehler
      if (window.Sentry) {
          Sentry.setTag("active_provider", newProvider);
          console.log(`[Sentry] Tag gesetzt: active_provider=${newProvider}`);
          
          // Wenn wir bereits ein Modell haben, setzen wir es auch
          if (appState.last_active.model) {
              Sentry.setTag("active_model", appState.last_active.model);
              console.log(`[Sentry] Tag gesetzt: active_model=${appState.last_active.model}`);
          } else {
              // Ansonsten entfernen wir das Modell-Tag, um Inkonsistenzen zu vermeiden
              Sentry.setTag("active_model", undefined);
          }
      }
      // -------------------------------------

      // 2. Ein sinnvolles Standard-Modell für den neuen Provider finden und setzen
      // Das verhindert, dass ein ungültiges Modell (z.B. GPT in Gemini) ausgewählt bleibt.
      const firstAvailableModel = findFirstAvailableModel(newProvider);
      if (firstAvailableModel) {
        appState.last_active.model = firstAvailableModel.id;
        console.log(`--> [Event] New model set in state: ${firstAvailableModel.id}`);
      } else {
        appState.last_active.model = null; // Fallback, falls keine Modelle da sind
        console.warn(`--> [Event] No available models found for provider: ${newProvider}`);
      }

      // 3. Den Backend-Status aktualisieren (wichtig für den nächsten App-Start)
      await updateLastUsedModelInBackend();

      // 4. Die UI komplett neu zeichnen, um die Änderungen anzuzeigen
      console.log("--> [Event] Calling render() to update the UI...");
      render();

      // Sync window headers in 'Wie Sidebar' mode
      syncChatWindowHeaderLlm(); 
    });
  }

  const sidebarModelSelectForChange = document.getElementById("model-select");
  if (sidebarModelSelectForChange) {
    sidebarModelSelectForChange.addEventListener("change", async () => {
      const m = sidebarModelSelectForChange.value;
      appState.last_active.model = m;
      if (window.Sentry && m) {
        Sentry.setTag("active_model", m);
      }
      await updateLastUsedModelInBackend();
      // Sync window headers in 'Wie Sidebar' mode
      syncChatWindowHeaderLlm();
    });
  }
  
  // Settings button — nur Ansicht wechseln, kein render(): sonst wird #model-select
  // neu aufgebaut und kann das Chat-Modell überschreiben (siehe DOM-Sync in render()).
  const settingsBtn = document.getElementById("settings-btn");
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      console.log("Settings button clicked!");
      appState.currentView = "settings";
      const chatViewEl = document.getElementById("chat-view");
      const settingsViewEl = document.getElementById("settings-view");
      if (chatViewEl) chatViewEl.style.display = "none";
      if (settingsViewEl) settingsViewEl.style.display = "flex";
      document.dispatchEvent(new CustomEvent("show-settings"));
    });
  }

  // Back to chat button
  const backToChatBtn = document.getElementById("back-to-chat-btn");
  if (backToChatBtn) {
    backToChatBtn.addEventListener("click", () => {
      appState.currentView = "chat";
      render();
    });
  }
  
  // Initialize draggable and resizable elements
  initializeDraggableElements();

  // Ensure the legacy sidebar exposes the Knowledge Center trigger
  injectKnowledgeButton();

  const sidebarNavProjects = document.getElementById("sidebar-nav-projects");
  if (sidebarNavProjects) {
    sidebarNavProjects.addEventListener("click", (e) => {
      e.preventDefault();
      openProjectModal();
    });
  }

  document.addEventListener("project-modal-opened", () => {
    void loadProjects();
  });

  document.addEventListener("project-created", (e) => {
    const p = e.detail;
    if (p && p.id != null) {
      appState.currentProjectId = p.id;
    }
    void loadProjects();
  });

  /* #user-input-A|B: listeners; autoResize() in chat.js sets height, textarea scrollTop, then scrollChatToBottom */
  initChatComposer();
  WINDOW_IDS.forEach((wid) => {
    const userInput = document.getElementById(paneId("user-input", wid));
    if (!userInput) return;
    userInput.addEventListener("input", () => {
      requestAnimationFrame(() => autoResize.call(userInput));
    });
    userInput.addEventListener("paste", () => {
      setTimeout(() => autoResize.call(userInput), 20);
      requestAnimationFrame(() => autoResize.call(userInput));
    });
    userInput.addEventListener("focus", () => {
      requestAnimationFrame(() => autoResize.call(userInput));
    });
    requestAnimationFrame(() => autoResize.call(userInput));
  });

  console.log("Event listeners successfully set up.");
}

function injectKnowledgeButton() {
  const handler = () => {
    if (typeof window.openJanusKnowledge === "function") {
      window.openJanusKnowledge();
      return;
    }
    openModal({ type: "document" });
  };

  const existing = document.getElementById("btn-react-knowledge");
  if (existing) {
    existing.addEventListener("click", handler);
    console.log("Wissensdatenbank button wired (static markup).");
    return;
  }

  const sidebar =
    document.querySelector(".sidebar-menu") ||
    document.querySelector("#sidebar-nav") ||
    document.querySelector("#sidebar nav") ||
    document.querySelector("#sidebar");
  if (!sidebar) return;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.id = "btn-react-knowledge";
  btn.className = "sidebar-nav-item";
  btn.innerHTML =
    '<span class="sidebar-nav-icon icon-knowledge" aria-hidden="true"><svg class="janus-nav-icon-svg" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg></span><span class="sidebar-nav-label">Wissensdatenbank</span>';
  btn.addEventListener("click", handler);
  sidebar.appendChild(btn);
  console.log("Legacy sidebar now exposes the Wissensdatenbank button.");
}

/** Drag/Resize-Grenzen für #chat-window-A|B: im Chat #chat-view, in der Projektansicht #project-chat-host */
function getChatWindowBoundsEl(target) {
  if (target.id !== "chat-window-A" && target.id !== "chat-window-B") return null;
  const projectHost = target.closest("#project-chat-host");
  if (projectHost) return projectHost;
  return document.getElementById("chat-view");
}

/** Standardposition und -größe (--dual-chat-host-*) wie beim ersten Laden */
function resetChatWindowLayout(windowId) {
  const el = document.getElementById(`chat-window-${windowId}`);
  if (!el) return;

  const rootStyle = getComputedStyle(document.documentElement);
  const wRaw = rootStyle.getPropertyValue("--dual-chat-host-width").trim() || "600px";
  const hRaw = rootStyle.getPropertyValue("--dual-chat-host-height").trim() || "700px";
  const wNum = parseFloat(wRaw) || 600;

  el.style.width = wRaw;
  el.style.height = hRaw;

  if (el.closest("#chat-view")) {
    el.style.left = windowId === "A" ? "0px" : `${wNum + 1}px`;
    el.style.top = "0px";
  } else if (el.closest("#project-chat-host")) {
    el.style.left = "0px";
    el.style.top = "0px";
  }

  requestAnimationFrame(() => {
    el.setAttribute("data-x", String(el.offsetLeft));
    el.setAttribute("data-y", String(el.offsetTop));
  });
}

// Function to initialize all draggable and resizable elements
function initializeDraggableElements() {
  // Beide Haupt-Chatfenster (schwebend im #chat-view wie Legacy)
  interact("#chat-window-A, #chat-window-B")
    .draggable({
      allowFrom: '[id^="chat-header-"] .chat-header-drag-strip',
      inertia: true,
      listeners: {
        start(event) {
          const win = event.target.closest("#chat-window-A, #chat-window-B");
          if (win) {
            win.setAttribute("data-x", String(win.offsetLeft));
            win.setAttribute("data-y", String(win.offsetTop));
            return;
          }
          const target = event.target;
          const rect = target.getBoundingClientRect();
          target.setAttribute("data-x", rect.left);
          target.setAttribute("data-y", rect.top);
        },
        move: dragListener,
      },
    })
    .resizable({
      edges: { left: true, right: true, bottom: true, top: true },
      inertia: true,
      modifiers: [
        interact.modifiers.restrictSize({
          min: { width: 300, height: 200 },
        }),
      ],
      listeners: {
        start(event) {
          const win = event.target.closest("#chat-window-A, #chat-window-B");
          if (win) {
            win.setAttribute("data-x", String(win.offsetLeft));
            win.setAttribute("data-y", String(win.offsetTop));
          }
        },
        move: resizeListener,
      },
    });

  requestAnimationFrame(() => {
    ["chat-window-A", "chat-window-B"].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.setAttribute("data-x", String(el.offsetLeft));
      el.setAttribute("data-y", String(el.offsetTop));
    });
  });

  document.getElementById("chat-window-reset-btn-A")?.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    resetChatWindowLayout("A");
  });
  document.getElementById("chat-window-reset-btn-B")?.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    resetChatWindowLayout("B");
  });

  // Floating panel
  interact(".floating-panel")
    .draggable({
      allowFrom: ".panel-header",
      inertia: true,
      listeners: {
        start(event) {
          const target = event.target;
          target.setAttribute("data-x", target.offsetLeft);
          target.setAttribute("data-y", target.offsetTop);
        },
        move: dragFloatingListener,
      },
    })
    .resizable({
      edges: { left: true, right: true, bottom: true, top: true },
      inertia: true,
      modifiers: [
        interact.modifiers.restrictSize({
          min: { width: 320, height: 240 },
        }),
        interact.modifiers.restrictEdges({
          outer: "parent",
        }),
      ],
      listeners: {
        move: resizeFloatingListener,
      },
    });

  // Image modal
  interact("#image-modal .modal-content")
    .draggable({
      allowFrom: "#image-modal .modal-header",
      inertia: true,
      listeners: {
        start(event) {
          const target = event.target;
          const rect = target.getBoundingClientRect();
          target.setAttribute("data-x", rect.left);
          target.setAttribute("data-y", rect.top);
          window.justDragged = false;
        },
        move: dragListener,
        end(event) {
            window.justDragged = true;
        }
      },
    });
}

  function dragListener(event) {
    const target =
      event.target.closest("#chat-window-A, #chat-window-B") || event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

    if (target.closest("#image-modal .modal-content")) {
      const maxX = window.innerWidth - target.offsetWidth;
      const maxY = window.innerHeight - target.offsetHeight;
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    } else {
      const chatBounds = getChatWindowBoundsEl(target);
      if (chatBounds) {
        const maxX = Math.max(0, chatBounds.clientWidth - target.offsetWidth);
        const maxY = Math.max(0, chatBounds.clientHeight - target.offsetHeight);
        x = Math.max(0, Math.min(x, maxX));
        y = Math.max(0, Math.min(y, maxY));
      } else {
        const maxX = window.innerWidth - target.offsetWidth;
        const maxY = window.innerHeight - target.offsetHeight;
        x = Math.max(0, Math.min(x, maxX));
        y = Math.max(0, Math.min(y, maxY));
      }
    }

    target.style.left = `${x}px`;
    target.style.top = `${y}px`;

    target.setAttribute("data-x", x);
    target.setAttribute("data-y", y);
  }

  function resizeListener(event) {
    const target =
      event.target.closest("#chat-window-A, #chat-window-B") || event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.deltaRect.left;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.deltaRect.top;

    const host =
      getChatWindowBoundsEl(target) ||
      target.closest("#chat-window-host-A, #chat-window-host-B, #project-chat-host") ||
      document.getElementById("chat-view");

    let w = event.rect.width;
    let h = event.rect.height;

    if (host) {
      const maxW = Math.max(300, host.clientWidth - x);
      const maxH = Math.max(200, host.clientHeight - y);
      w = Math.min(w, maxW);
      h = Math.min(h, maxH);

      const maxX = Math.max(0, host.clientWidth - w);
      const maxY = Math.max(0, host.clientHeight - h);
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    }

    Object.assign(event.target.style, {
      width: `${w}px`,
      height: `${h}px`,
      left: `${x}px`,
      top: `${y}px`,
    });

    target.setAttribute("data-x", String(x));
    target.setAttribute("data-y", String(y));
  }

  function dragFloatingListener(event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

    const layout = document.getElementById("project-layout");
    if (layout) {
      const maxX = Math.max(0, layout.clientWidth - target.offsetWidth);
      const maxY = Math.max(0, layout.clientHeight - target.offsetHeight);
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    }

    target.style.left = `${x}px`;
    target.style.top = `${y}px`;

    target.setAttribute("data-x", x);
    target.setAttribute("data-y", y);
  }

  function resizeFloatingListener(event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.deltaRect.left;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.deltaRect.top;

    const layout = document.getElementById("project-layout");
    if (layout) {
      const maxX = Math.max(0, layout.clientWidth - event.rect.width);
      const maxY = Math.max(0, layout.clientHeight - event.rect.height);
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    }

    Object.assign(event.target.style, {
      width: `${event.rect.width}px`,
      height: `${event.rect.height}px`,
      left: `${x}px`,
      top: `${y}px`,
    });

    Object.assign(event.target.dataset, { x, y });
  }

  if (window.electron && typeof window.electron.on === 'function') {
    window.electron.on('project-list-updated', () => {
      console.log("Event 'project-list-updated' received. Reloading projects.");
      loadProjects();
    });
  }

  const backToProjectChatBtn = document.getElementById('back-to-chat-from-project');
  if (backToProjectChatBtn) {
    backToProjectChatBtn.addEventListener('click', () => {
      appState.currentProjectId = null;
      document.querySelectorAll('#project-list .project-item').forEach((item) => item.classList.remove('active'));
      switchView('chat');
    });
  }

  const newProjectChatBtn = document.getElementById('new-project-chat-btn');
  if (newProjectChatBtn) {
    newProjectChatBtn.addEventListener('click', () => {
      if (appState.currentProjectId) {
        createNewChatInProject(appState.currentProjectId);
      }
    });
  }

  // Initialize file input handling
  const browseFilesBtn = document.getElementById('browse-files-btn');
  const fileInput = document.getElementById('file-input');
  if (browseFilesBtn && fileInput) {
    browseFilesBtn.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0 && appState.currentProjectId) {
        handleFiles(e.target.files, appState.currentProjectId);
      }
    });
  }

async function loadProjects() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/projects`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const projects = await response.json();
    
    // --- SICHERHEITS-CHECK ---
    if (!Array.isArray(projects)) {
        console.warn("Projects data is not an array:", projects);
        return; // Abbrechen, bevor es knallt
    }
    // -------------------------

    const projectListDiv = document.getElementById('project-list');
    if (!projectListDiv) {
      console.warn("Project list container not found");
      return;
    }
    
    projectListDiv.innerHTML = ''; // Clear existing list
    const visibleProjects = projects.filter((project) => {
      const name = String(project.name ?? '').trim();
      const desc = String(project.description ?? '').trim();
      // Hide DB seed placeholder row (looks like a stray "Standard" label above chats)
      if (name === 'Standard' && desc === 'Default') {
        return false;
      }
      return true;
    });
    visibleProjects.forEach(project => {
      const projectDiv = document.createElement('div');
      projectDiv.classList.add('project-item'); // Add a class for styling
      projectDiv.textContent = project.name;
      projectDiv.dataset.projectId = project.id;

      if (appState.currentProjectId != null && Number(project.id) === Number(appState.currentProjectId)) {
        projectDiv.classList.add('active');
      }

      projectDiv.addEventListener('click', () => {
        console.log(`Projekt ${project.id} ausgewählt (Modal).`);
        appState.currentProjectId = project.id;
        projectListDiv.querySelectorAll('.project-item').forEach((item) => item.classList.remove('active'));
        projectDiv.classList.add('active');
        showProjectModalView('detail', project);
      });

      projectListDiv.appendChild(projectDiv);
    });

    initProjectModalAfterListLoad(visibleProjects, appState.currentProjectId);
  } catch (error) {
    console.error('Failed to load projects:', error);
  }
}

// Create a new chat in a specific project
async function createNewChatInProject(projectId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        title: `Chat ${new Date().toLocaleString()}`
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const newChat = await response.json();
    
    // Load the new chat
    if (window.chatManager && typeof window.chatManager.loadChat === 'function') {
      await window.chatManager.loadChat(newChat.id, {
        context: 'project',
        projectId,
        windowId: getActiveWindowId(),
      });
    }

    if (window.renderProjectDashboard && typeof window.renderProjectDashboard === 'function') {
      const currentProjectName = appState.currentProjectName || '';
      window.renderProjectDashboard({ id: projectId, name: currentProjectName });
    }
  } catch (error) {
    console.error('Error creating new chat in project:', error);
  }
}

// Handle file uploads for a project
async function handleFiles(files, projectId) {
  const formData = new FormData();
  
  // Add files to form data
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  
  // Add project ID to form data
  formData.append('project_id', projectId);

  try {
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/files`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Files uploaded successfully:', result);
    
    // Refresh file list
    if (window.projectDashboard && typeof window.projectDashboard.loadProjectFiles === 'function') {
      window.projectDashboard.loadProjectFiles(projectId);
    }
  } catch (error) {
    console.error('Error uploading files:', error);
  }
}


async function loadModelCatalog() {
  try {
    const [catalogResponse, localModelsResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/api/models/catalog`),
      fetch(`${API_BASE_URL}/api/local-llm/models`).catch(() => null),
    ]);
    if (!catalogResponse.ok) throw new Error(`HTTP Error ${catalogResponse.status}`);

    const data = await catalogResponse.json();
    const localModelsPayload = localModelsResponse && localModelsResponse.ok ? await localModelsResponse.json() : null;
    const localModels = Array.isArray(localModelsPayload?.models) ? localModelsPayload.models : [];
    const withoutOllama = Array.isArray(data) ? data.filter((model) => model.provider !== "ollama") : [];
    const mergedData = [...withoutOllama, ...localModels];
    
    // SAFETY CHECK: Is the data actually an array?
    if (!Array.isArray(mergedData)) {
      console.error("Model catalog data is not an array:", mergedData);
      appState.model_catalog = {};
      return;
    }

    const catalogByProvider = {};
    mergedData.forEach((model) => {
      if (!catalogByProvider[model.provider]) {
        catalogByProvider[model.provider] = [];
      }
      catalogByProvider[model.provider].push(model);
    });
    appState.model_catalog = catalogByProvider;
  } catch (error) {
    console.error("Failed to load model catalog:", error);
    // Set empty object to prevent crashes in dependent code
    appState.model_catalog = {}; 
  }
}

async function loadLastUsedModel() {
  try {
    // Get the authentication token from localStorage
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      console.warn("No authentication token found. User might not be logged in.");
      return; // Return here, as the request will fail anyway
    }

    const response = await fetch(`${API_BASE_URL}/api/last-used-model`, {
      method: "GET", 
      headers: { 
        "Authorization": `Bearer ${token}`
      },
    });

    if (!response.ok) {
        // Falls der Endpunkt einen Fehler wirft (z.B. 401 Unauthorized, 404 Not Found)
        throw new Error(`Failed to fetch last used model: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Nur aktualisieren, wenn gültige Daten zurückkommen
    if (data && data.provider && data.model) {
        appState.last_active.provider = data.provider;
        appState.last_active.model = data.model;
        console.log("Successfully loaded last used model:", appState.last_active);
    } else {
        console.warn("Received incomplete data for last used model:", data);
    }

  } catch (error) {
    // Bei einem Fehler werden einfach die Standardwerte beibehalten, die App stürzt nicht ab.
    console.warn("Could not load last used model, using defaults:", error.message);
  }
}

async function loadUserSelections() {
  try {
    // --- SICHERHEITS-CHECK ---
    if (!appState.model_catalog || typeof appState.model_catalog !== 'object') {
      console.warn("Model catalog is not properly initialized:", appState.model_catalog);
      appState.model_catalog = {}; // Ensure it's at least an object
    }
    // -------------------------

    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.warn("Cannot load user selections: No auth token found.");
      // Populate with empty selections to prevent errors
      const availableProviders = Object.keys(appState.model_catalog);
      for (const provider of availableProviders) {
          appState.user_selections[provider] = [];
      }
      return;
    }

    // Get all unique providers from the model catalog
    const availableProviders = Object.keys(appState.model_catalog);
    
    const selectionPromises = availableProviders.map(async (provider) => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`, {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        const data = await response.json();
        
        // --- SICHERHEITS-CHECK ---
        if (!data || !Array.isArray(data.selected_models)) {
          console.warn(`Invalid response format for provider ${provider}:`, data);
          appState.user_selections[provider] = [];
          return;
        }
        // -------------------------
        
        appState.user_selections[provider] = data.selected_models;
      } catch (error) {
        console.error(`Failed to load models for ${provider}:`, error);
        appState.user_selections[provider] = []; // Default to empty on error
      }
    });

    await Promise.all(selectionPromises);
  } catch (error) {
    console.error("Unexpected error in loadUserSelections:", error);
    // Ensure we have at least an empty object to prevent further errors
    if (!appState.user_selections || typeof appState.user_selections !== 'object') {
      appState.user_selections = {};
    }
  }
}

/**
 * OpenAI-Sidebar: nano → mini → … (Katalog-Reihenfolge = leichter zuerst).
 * Gemini-Katalog listet teils Pro vor Flash — hier Flash vor Pro, damit das Dropdown
 * dasselbe „kleinstes/schnellstes oben“-Muster hat.
 */
function geminiSidebarModelRank(m) {
  const id = String(m.id || "");
  const typ = m.type || "text";
  if (typ === "text") {
    if (/flash/i.test(id) && !/image/i.test(id)) return 100;
    if (/pro/i.test(id) && !/vision/i.test(id) && !/image/i.test(id)) return 101;
    return 150;
  }
  if (typ === "image") {
    if (/flash/i.test(id)) return 200;
    if (/pro/i.test(id)) return 201;
    return 250;
  }
  if (typ === "text_image") return 300;
  return 400;
}

function sortSidebarModelsForProvider(provider, models) {
  if (!Array.isArray(models)) return models;

  // OpenAI: Definierte Reihenfolge (kleinstes zuerst)
  if (provider === "openai") {
    const openaiRank = {
      "gpt-5.4-nano": 1,
      "gpt-5.4-mini": 2,
      "gpt-5.4": 3,
      "gpt-5.4-pro": 4,
      "gpt-5.5": 5,
      "gpt-5.5-pro": 6
    };
    return [...models].sort((a, b) => {
      const ra = openaiRank[a.id] || 999;
      const rb = openaiRank[b.id] || 999;
      return ra - rb;
    });
  }

  // Gemini: Bestehende Sortierung
  if (provider === "gemini") {
    return [...models].sort((a, b) => {
      const ra = geminiSidebarModelRank(a);
      const rb = geminiSidebarModelRank(b);
      if (ra !== rb) return ra - rb;
      return String(a.id).localeCompare(String(b.id));
    });
  }

  return models;
}

function findFirstAvailableModel(provider) {
  // Stellt sicher, dass der Provider im Katalog existiert, um Fehler zu vermeiden.
  if (!appState.model_catalog[provider]) {
    console.error(`Provider '${provider}' not found in model catalog.`);
    return null;
  }

  // Holt die vom User erlaubten Modelle. Kein Fallback auf alle Modelle.
  let allowedModels = appState.user_selections[provider] || [];
  if (allowedModels.length === 0) {
    console.warn(`[findFirstAvailableModel] No models selected for provider: ${provider}`);
    return null;
  }
  
  // Filtert die Modelle (z.B. um reine TTS-Modelle auszublenden).
  const availableModels = appState.model_catalog[provider].filter(
    model => {
             const baseModelId = model.base_model_id || (String(model.id || "").includes("@") ? String(model.id).split("@", 1)[0] : model.id);
             const allowedBaseModelIds = new Set(
               allowedModels
                 .map((item) => (String(item || "").includes("@") ? String(item).split("@", 1)[0] : String(item || "")))
                 .filter(Boolean)
             );
             const isAllowed =
               allowedModels.includes(model.id) ||
               (model.provider === "ollama" && (allowedModels.includes(baseModelId) || allowedBaseModelIds.has(String(baseModelId || ""))));
             return isAllowed &&
            !["gpt-image-1.5", "gpt-image-1-mini", "gpt-4o-mini"].includes(model.id)
    }
  );

  const ordered = sortSidebarModelsForProvider(provider, availableModels);
  // Gibt das erste gefundene Modell zurück oder null, wenn die Liste leer ist.
  return ordered.length > 0 ? ordered[0] : null;
}

// ============================================================
// NOTFALL-FIX FÜR NAVIGATION (Am Ende von app.js einfügen)
// ============================================================

// 1. Die Funktion, die garantiert die Einstellungen öffnet
function forceOpenSettings() {
    console.log(">>> NOTFALL-NAVIGATION: Öffne Einstellungen...");

    // A) Störende Modals/Overlays entfernen
    const loginScreen = document.getElementById('login-screen');
    if (loginScreen) loginScreen.style.display = 'none';
    
    document.querySelectorAll('.modal, .modal-overlay').forEach(el => {
        el.style.display = 'none';
    });

    // B) App-Container sichtbar machen
    const appContainer = document.querySelector('.app-container');
    if (appContainer) appContainer.style.display = 'flex';

    // C) Alle Haupt-Ansichten ausblenden
    document.querySelectorAll('main.view').forEach(view => {
        view.style.display = 'none';
    });

    // D) Nur die Settings-Ansicht einblenden
    const settingsView = document.getElementById('settings-view');
    if (settingsView) {
        settingsView.style.display = 'block';
        settingsView.style.visibility = 'visible'; // Sicherheitsnetz
    } else {
        console.error("CRITICAL: #settings-view nicht im HTML gefunden!");
        return; 
    }

    // E) In den Einstellungen zum API-Key Tab springen
    // Erst alle Unter-Sektionen ausblenden
    document.querySelectorAll('.settings-section').forEach(sec => sec.style.display = 'none');
    // Dann API Key Sektion zeigen
    const apiKeySection = document.getElementById('api-key-section');
    if (apiKeySection) apiKeySection.style.display = 'block';

    console.log(">>> Einstellungen sollten jetzt sichtbar sein.");

    // --- NEU: DIESEN BLOCK HINZUFÜGEN ---
    // Damit die App merkt, dass sie jetzt vielleicht Keys hat und Daten laden soll.
    console.log(">>> Triggering App Re-Initialization...");
    if (typeof window.initializeApp === 'function') {
        // Wir rufen die Haupt-Start-Funktion erneut auf.
        // Sie prüft den Token, lädt Modelle und Chats neu.
        window.initializeApp().catch(err => console.error("Re-Init failed:", err));
    }
    // -------------------------------------
}

// ============================================================
// AUTO-UPDATE UI MANAGER (NEUE VERSION)
// ============================================================
if (window.electron && typeof window.electron.on === 'function') {
    // Hilfsfunktion, um sicherzustellen, dass das Modal existiert und bereit ist
    function ensureUpdateModal() {
        if (document.getElementById('update-modal')) return document.getElementById('update-modal');

        const modal = document.createElement('div');
        modal.id = 'update-modal';
        modal.className = 'modal';
        // ... (Der restliche HTML-Code für das Modal bleibt identisch)
        modal.innerHTML = `
            <div class="modal-content" style="background: #1e1e2e; border-radius: 8px; padding: 1.5rem; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; color: #cdd6f4;">
                <h3 id="update-modal-title" style="margin-top: 0; color: #89b4fa;">Update-Information</h3>
                <div id="update-modal-body" style="margin: 1rem 0; line-height: 1.6; text-align: left;">
                    <p id="update-modal-text">Prüfe auf Updates...</p>
                    
                    <div id="progress-container" style="display: none; margin: 1rem 0;">
                        <progress id="update-progress-bar" value="0" max="100" style="width: 100%; height: 10px; border-radius: 5px; overflow: hidden;"></progress>
                        <div id="progress-text" style="font-size: 0.8em; color: #a6adc8; text-align: right; margin-top: 5px;">0%</div>
                    </div>
                    
                    <div id="changelog-container" style="display: none; margin-top: 1rem; padding: 1rem; background: rgba(0, 0, 0, 0.3); border-radius: 6px; max-height: 300px; overflow-y: auto;">
                        <h4 style="margin-top: 0; color: #a6adc8;">Änderungen in dieser Version:</h4>
                        <div id="changelog-content" style="font-size: 0.9rem; line-height: 1.5;">Lade Änderungsliste...</div>
                    </div>
                </div>
                <div id="update-modal-footer" style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
                    <button id="restart-app-btn" class="primary-button" style="display: none;">
                        Jetzt neu starten & installieren
                    </button>
                    <span id="download-progress-text" style="display: none; align-items: center; color: #a6adc8; font-size: 0.9rem;">
                        <span class="spinner" style="display: inline-block; width: 1rem; height: 1rem; border: 2px solid rgba(205, 214, 244, 0.3); border-radius: 50%; border-top-color: #89b4fa; animation: spin 1s ease-in-out infinite; margin-right: 0.5rem;"></span>
                        <span id="download-status">Update wird vorbereitet...</span>
                    </span>
                </div>
            </div>
            <style> @keyframes spin { to { transform: rotate(360deg); } } .primary-button { background: #89b4fa; color: #1e1e2e; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-weight: 500; } .primary-button:hover { opacity: 0.9; } </style>
        `;
        document.body.appendChild(modal);

        const restartBtn = document.getElementById('restart-app-btn');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                if (window.electron && typeof window.electron.send === 'function') {
                    window.electron.send('restart-app-for-update');
                }
            });
        }
        return modal;
    }

    // Event 1: Ein Update wurde gefunden
    window.electron.on('update-available', (data) => {
        console.log('EVENT: update-available', data);
        const modal = ensureUpdateModal();
        modal.style.display = 'flex';
        
        // UI zurücksetzen und vorbereiten
        document.getElementById('update-modal-title').textContent = `Update auf Version ${data.version} verfügbar!`;
        document.getElementById('update-modal-text').textContent = "Eine neue Version von Janus wird jetzt heruntergeladen.";
        
        // Ladebalken und Changelog anzeigen
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('changelog-container').style.display = 'block';
        document.getElementById('download-progress-text').style.display = 'flex';
        
        // Changelog füllen
        const changelogContent = document.getElementById('changelog-content');
        if (window.marked) {
            changelogContent.innerHTML = sanitizeReleaseNotes(window.marked.parse(data.releaseNotes || 'Keine Änderungsnotizen verfügbar.'));
        } else {
            changelogContent.textContent = data.releaseNotes || 'Keine Änderungsnotizen verfügbar.';
        }
    });

    // Event 2: Download-Fortschritt
    window.electron.on('download-progress', (progress) => {
        // Dieser Event kommt sehr oft, daher kein console.log
        const progressBar = document.getElementById('update-progress-bar');
        const progressText = document.getElementById('progress-text');

        if (progressBar && progressText) {
            const percent = Math.round(progress.percent);
            progressBar.value = percent;
            
            const downloadedMB = (progress.transferred / (1024 * 1024)).toFixed(1);
            const totalMB = (progress.total / (1024 * 1024)).toFixed(1);
            
            progressText.textContent = `${percent}% (${downloadedMB}MB / ${totalMB}MB)`;
        }
    });

    // Event 3: Download ist fertig
    window.electron.on('update-downloaded', () => {
        console.log('EVENT: update-downloaded');
        const modal = ensureUpdateModal(); // Sicherstellen, dass das Modal da ist
        modal.style.display = 'flex';

        // UI auf "Fertig" setzen
        document.getElementById('update-modal-title').textContent = 'Update bereit zur Installation!';
        document.getElementById('update-modal-text').textContent = 'Der Download ist abgeschlossen. Starten Sie die App neu, um das Update zu installieren.';
        
        // Fortschrittsanzeigen ausblenden
        document.getElementById('progress-container').style.display = 'none';
        document.getElementById('download-progress-text').style.display = 'none';
        
        // Neustart-Button anzeigen
        document.getElementById('restart-app-btn').style.display = 'block';
    });

    // Event 4: Fehler
    window.electron.on('update-error', (error) => {
        console.error('EVENT: update-error', error);
        const modal = ensureUpdateModal();
        modal.style.display = 'flex';
        
        // UI auf Fehler setzen
        document.getElementById('update-modal-title').textContent = 'Update-Fehler';
        document.getElementById('update-modal-body').innerHTML = sanitizeTemplateHtml(`
            <p>Beim Herunterladen des Updates ist ein Fehler aufgetreten:</p>
            <div style="background: rgba(243, 139, 168, 0.2); color: #f38ba8; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; font-size: 0.9rem;">
                ${error || 'Unbekannter Fehler'}
            </div>
            <p style="margin-top: 1rem;">Bitte überprüfen Sie Ihre Internetverbindung.</p>
        `);
        document.getElementById('update-modal-footer').innerHTML = sanitizeTemplateHtml(`
            <button onclick="document.getElementById('update-modal').style.display='none'" class="primary-button">Schließen</button>
        `);
    });
}

// 2. Event-Listener neu setzen (mit kurzer Verzögerung, um sicherzugehen, dass DOM da ist)
setTimeout(() => {
    // Button 1: Der im Start-Modal ("Open Settings")
    // Wir suchen nach ID oder Klasse, um ihn sicher zu treffen
    const modalBtn = document.getElementById('error-settings-btn') || 
                     document.querySelector('#login-screen button.primary-button');
    
    if (modalBtn) {
        // Wir klonen den Button, um alte, kaputte Event-Listener loszuwerden
        const newModalBtn = modalBtn.cloneNode(true);
        modalBtn.parentNode.replaceChild(newModalBtn, modalBtn);
        
        newModalBtn.addEventListener('click', (e) => {
            e.preventDefault();
            forceOpenSettings();
        });
        console.log("Fix für Modal-Button angewendet.");
    }

    // Button 2: Der in der Sidebar ("Einstellungen")
    const sidebarBtn = document.getElementById('settings-btn');
    if (sidebarBtn) {
        // Auch hier: Klonen um alte Listener zu löschen
        const newSidebarBtn = sidebarBtn.cloneNode(true);
        sidebarBtn.parentNode.replaceChild(newSidebarBtn, sidebarBtn);
        
        newSidebarBtn.addEventListener('click', (e) => {
            e.preventDefault();
            forceOpenSettings();
        });
        console.log("Fix für Sidebar-Button angewendet.");
    }
}, 500); // 500ms warten nach App-Start
// ============================================================

// ============================================================
// NOTFALL-FIX: ZURÜCK ZUM CHAT
// ============================================================
setTimeout(() => {
    const backBtn = document.getElementById('back-to-chat-btn');
    if (backBtn) {
        // Alten Listener entfernen (durch Klonen)
        const newBackBtn = backBtn.cloneNode(true);
        backBtn.parentNode.replaceChild(newBackBtn, backBtn);

        newBackBtn.addEventListener('click', (e) => {
            console.log(">>> NOTFALL: Zurück zum Chat...");
            e.preventDefault();

            // 1. Settings ausblenden
            const settingsView = document.getElementById('settings-view');
            if (settingsView) settingsView.style.display = 'none';

            // 2. Chat einblenden
            const chatView = document.getElementById('chat-view');
            if (chatView) chatView.style.display = 'block';
            
            // 3. App-Container sicherstellen
            const appContainer = document.querySelector('.app-container');
            if (appContainer) appContainer.style.display = 'flex';
            
            // 4. State aktualisieren (falls möglich)
            if (typeof appState !== 'undefined') {
                appState.currentView = 'chat';
            }
        });
        console.log("Fix für Zurück-Button angewendet.");
    }
}, 1000); // Etwas später ausführen als den anderen Fix
// ============================================================

// ============================================================
// BETA FEEDBACK MODAL LOGIC
// ============================================================
setTimeout(() => {
    const feedbackBtn = document.getElementById('btn-open-feedback');
    const feedbackModal = document.getElementById('modal-feedback');
    const closeFeedbackModal = document.getElementById('close-feedback-modal');
    const feedbackCancelBtn = document.getElementById('feedback-cancel-btn');
    const feedbackForm = document.getElementById('feedback-form');
    const feedbackSubmitBtn = document.getElementById('feedback-submit-btn');
    const feedbackStatus = document.getElementById('feedback-status');

    if (!feedbackBtn || !feedbackModal) {
        console.log("Feedback modal elements not found, skipping initialization");
        return;
    }

    // Open modal
    feedbackBtn.addEventListener('click', (e) => {
        e.preventDefault();
        feedbackModal.style.display = 'flex';
        feedbackStatus.style.display = 'none';
        feedbackForm.reset();
        // Reset checkbox to checked
        document.getElementById('feedback-include-logs').checked = true;
    });

    // Close modal helpers
    const closeFeedbackModalFn = () => {
        feedbackModal.style.display = 'none';
    };

    closeFeedbackModal.addEventListener('click', closeFeedbackModalFn);
    feedbackCancelBtn.addEventListener('click', closeFeedbackModalFn);

    // Close on outside click
    feedbackModal.addEventListener('click', (e) => {
        if (e.target === feedbackModal) {
            closeFeedbackModalFn();
        }
    });

    // Form submission
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const type = document.getElementById('feedback-type').value;
        const description = document.getElementById('feedback-description').value;
        const includeLogs = document.getElementById('feedback-include-logs').checked;

        // Validate minimum length
        if (description.length < 10) {
            feedbackStatus.style.display = 'block';
            feedbackStatus.style.background = 'rgba(243, 139, 168, 0.2)';
            feedbackStatus.style.color = '#f38ba8';
            feedbackStatus.textContent = 'Beschreibung muss mindestens 10 Zeichen lang sein.';
            return;
        }

        // Disable button and show loading state
        feedbackSubmitBtn.disabled = true;
        feedbackSubmitBtn.textContent = 'Wird gesendet...';
        feedbackStatus.style.display = 'none';

        try {
            const response = await fetch(`${API_BASE_URL}/api/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: type,
                    description: description,
                    include_logs: includeLogs,
                }),
            });

            const result = await response.json();

            if (result.success) {
                // Show success message
                feedbackStatus.style.display = 'block';
                feedbackStatus.style.background = 'rgba(139, 212, 136, 0.2)';
                feedbackStatus.style.color = '#8bc078';
                feedbackStatus.textContent = '✅ Feedback erfolgreich gesendet!';

                // Close modal after 2 seconds
                setTimeout(() => {
                    closeFeedbackModalFn();
                    feedbackForm.reset();
                    document.getElementById('feedback-include-logs').checked = true;
                }, 2000);
            } else {
                // Show error message
                feedbackStatus.style.display = 'block';
                feedbackStatus.style.background = 'rgba(243, 139, 168, 0.2)';
                feedbackStatus.style.color = '#f38ba8';
                feedbackStatus.textContent = `❌ Fehler: ${result.message || 'Unbekannter Fehler'}`;
            }
        } catch (error) {
            console.error('Feedback submission error:', error);
            feedbackStatus.style.display = 'block';
            feedbackStatus.style.background = 'rgba(243, 139, 168, 0.2)';
            feedbackStatus.style.color = '#f38ba8';
            feedbackStatus.textContent = '❌ Netzwerkfehler beim Senden des Feedbacks.';
        } finally {
            // Re-enable button
            feedbackSubmitBtn.disabled = false;
            feedbackSubmitBtn.textContent = 'Bericht senden';
        }
    });

    console.log("Feedback modal initialized successfully");
}, 500); // Execute after DOM is ready
// ============================================================
