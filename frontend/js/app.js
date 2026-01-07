// ================= SENTRY INTEGRATION (LOKALES MODUL) =================
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: "https://52d089968563a42a98ed367df7723736@o4510659131670528.ingest.de.sentry.io/4510660337533008",
  
  // --- AUTOMATISCHE VERSIONIERUNG ---
  // Vite ersetzt 'import.meta.env.APP_VERSION' beim Build automatisch 
  // mit der Version aus deiner package.json
  release: "janus-projekt@" + (import.meta.env.APP_VERSION || "0.0.0-dev"),
  // ----------------------------------

  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

// ======================== ENDE DER INTEGRATION ========================

import interact from "interactjs";
import { API_BASE_URL } from "./config.js";
import "./personality-settings.js";
import { loadChats } from "./chat-manager.js";

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
    const chatWindow = document.getElementById('chat-window');
    const chatWindowHost = document.getElementById('chat-window-host');
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
                    window.chatManager.loadChat(data.chatId, { context: 'assistant' });
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
        "x-api-key": token,
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
        "x-api-key": token
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

function render() {
  console.log("Rendering app with appState.last_active.provider:", appState.last_active.provider); // Debug Log
  const chatView = document.getElementById("chat-view");
  const settingsView = document.getElementById("settings-view");

  const sidebarProviderSelect = document.getElementById("provider-select");
  const sidebarModelSelect = document.getElementById("model-select");

  if (sidebarProviderSelect && sidebarModelSelect) {
    // --- START DER FINALEN KORREKTUR ---

    // 1. Hole die korrekten Werte aus dem State, BEVOR wir das DOM manipulieren.
    const targetProvider = appState.last_active.provider;
    const targetModel = appState.last_active.model;

    // 2. Setze den Provider-Wert. Dies kann ein 'change'-Event auslösen, aber das ist uns jetzt egal.
    console.log(`--> [Render] Setting provider to: ${targetProvider}`);
    sidebarProviderSelect.value = targetProvider;

    // 3. Fülle die Modell-Liste basierend auf dem korrekten Provider.
    console.log(`--> [Render] Populating model list for provider: ${targetProvider}`);
    sidebarModelSelect.innerHTML = ""; // Leere die alte Liste
    let allowedModels = appState.user_selections[targetProvider] || [];
    
    // Fallback für neue Benutzer
    if (allowedModels.length === 0 && appState.model_catalog[targetProvider]) {
      console.warn(`Keine Modelle für Provider '${targetProvider}' ausgewählt. Zeige alle als Fallback an.`);
      allowedModels = appState.model_catalog[targetProvider].map(model => model.id);
    }
    
    if (appState.model_catalog[targetProvider]) {
      // DIAGNOSTIC LOGS - START
      console.log("--- DROPDOWN-FILTER-DIAGNOSE ---");
      console.log("Ausgewählter Provider:", targetProvider);
      console.log("Verfügbare Modelle für diesen Provider:", appState.model_catalog[targetProvider]);
      console.log("Vom User erlaubte Modell-IDs:", allowedModels);

      const filteredModels = appState.model_catalog[targetProvider].filter(
        (model) => {
          const isAllowed = allowedModels.includes(model.id);
          const isNotExcluded = !["gpt-image-1.5", "gpt-image-1-mini", "gpt-4o-mini-tts"].includes(model.id);
          console.log(`Modell: ${model.id} - Erlaubt: ${isAllowed}, Nicht ausgeschlossen: ${isNotExcluded}`);
          return isAllowed && isNotExcluded;
        }
      );

      console.log("Ergebnis des Filters (anzuzeigende Modelle):", filteredModels);
      console.log("---------------------------------");
      // DIAGNOSTIC LOGS - END
      
      // Fülle die Dropdown-Liste mit den gefilterten Modellen
      filteredModels.forEach((model) => {
        const option = document.createElement("option");
        option.value = model.id;
        
        // Berechne die Kostenanzeige
        let costDisplay = "";
        if (model.type === "image") {
          // Für Gemini Bildmodelle mit Token-basierter Preisgestaltung
          if (model.provider === "gemini" && model.cost_per_million_output_tokens) {
            const costPerImage = (model.output_tokens_per_image_1024x1024 / 1000000) * model.cost_per_million_output_tokens;
            costDisplay = `${formatCost(costPerImage, "€/img", true)}`;
            if (model.cost_per_text_input_token) {
              costDisplay += ` + ${formatCost(model.cost_per_text_input_token * 1000000, "€/Mio. in")}`;
            }
          }
          // Fallback für andere Bildmodelle (z.B. DALL-E 3) mit fixem cost_per_image
          else if (model.cost_per_image) {
            costDisplay = formatCost(model.cost_per_image, "€/img", true);
            if (model.cost_per_text_input_token) {
              costDisplay += ` + ${formatCost(model.cost_per_text_input_token * 1000000, "€/Mio. in")}`;
            }
          }
        } else if (model.cost_per_token_input) {
          costDisplay = `${formatCost(model.cost_per_token_input * 1000000, "€/Mio. in")} / ${formatCost(model.cost_per_token_output * 1000000, "€/Mio. out")}`;
        }
        
        option.textContent = `${model.name} (${costDisplay})${model.desc ? " - " + model.desc : ""}`;
        sidebarModelSelect.appendChild(option);
      });
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
            const isValid = await validateToken(token);
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

  let isAuthenticated = false;

  // --- START DER FINALEN KORREKTUR ---
  try {
    // Validate the existing token
    console.log("--> [1.1] Validating existing token...");
    const isTokenValid = await validateToken();

    if (isTokenValid) {
      console.log("--> [2a] Existing token is valid.");
      isAuthenticated = true;
    } else {
      // If token is invalid, throw an error to trigger the silent login fallback
      throw new Error("Existing token is invalid or missing.");
    }
  } catch (validationError) {
    console.warn("--> [2b] Token validation failed, attempting silent login:", validationError.message);
    
    // FALLBACK: Attempt silent login
    try {
      console.log("--> [2c] Attempting silent login...");
      const isSilentLoginSuccess = await attemptSilentLogin();
      if (isSilentLoginSuccess) {
        isAuthenticated = true;
        console.log("--> [2d] Silent login successful.");
      } else {
        throw new Error("Silent login failed.");
      }
    } catch (silentLoginError) {
      console.error("--> [!] Both token validation and silent login failed:", silentLoginError.message);
      isAuthenticated = false;
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
function setupEventListeners() {
  console.log("Setting up UI event listeners...");

  // Listener for model updates from settings
  document.addEventListener("models-updated", async () => {
    console.log("--> [Event] Models updated externally. Refreshing catalog...");
    
    // 1. Reload user selections from server
    await loadUserSelections();
    
    // 2. (Optional) Reload catalog if API keys might have changed
    // await loadModelCatalog();

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
    });
  }
  
  // Settings button
  const settingsBtn = document.getElementById("settings-btn");
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      console.log("Settings button clicked!");
      appState.currentView = "settings";
      render();
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
  
  console.log("Event listeners successfully set up.");
}

// Function to initialize all draggable and resizable elements
function initializeDraggableElements() {
  // Chat window
  interact(".chat-window")
    .draggable({
      allowFrom: "#chat-header",
      inertia: true,
      listeners: {
        start(event) {
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
        move: resizeListener,
      },
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
    const target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

    if (target.closest('#image-modal .modal-content')) {
      const maxX = window.innerWidth - target.offsetWidth;
      const maxY = window.innerHeight - target.offsetHeight;
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    } else {
      const maxX = window.innerWidth - target.offsetWidth;
      const maxY = window.innerHeight - target.offsetHeight;
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    }

    target.style.left = `${x}px`;
    target.style.top = `${y}px`;

    target.setAttribute("data-x", x);
    target.setAttribute("data-y", y);
  }

  function resizeListener(event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.deltaRect.left;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.deltaRect.top;

    const host = target.closest('#chat-window-host, #project-chat-host') || document.getElementById('chat-view');
    if (host) {
      const maxX = Math.max(0, host.clientWidth - event.rect.width);
      const maxY = Math.max(0, host.clientHeight - event.rect.height);
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
      document.querySelectorAll('.project-item').forEach(item => item.classList.remove('active'));
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
    projects.forEach(project => {
      const projectDiv = document.createElement('div');
      projectDiv.classList.add('project-item'); // Add a class for styling
      projectDiv.textContent = project.name;
      projectDiv.dataset.projectId = project.id;
      
      // Add click handler for project selection
      projectDiv.addEventListener('click', () => {
        console.log(`Projekt ${project.id} ausgewählt.`);
        
        // Set the active project globally
        appState.currentProjectId = project.id;
        
        // Update UI feedback
        document.querySelectorAll('.project-item').forEach(item => item.classList.remove('active'));
        projectDiv.classList.add('active');
        
        // Switch to project view
        switchView('project', { project: project });
      });
      
      projectListDiv.appendChild(projectDiv);
    });
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
      await window.chatManager.loadChat(newChat.id, { context: 'project', projectId });
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
    const response = await fetch(`${API_BASE_URL}/api/models/catalog`);
    if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
    
    const data = await response.json();
    
    // SAFETY CHECK: Is the data actually an array?
    if (!Array.isArray(data)) {
      console.error("Model catalog data is not an array:", data);
      appState.model_catalog = {};
      return;
    }

    const catalogByProvider = {};
    data.forEach((model) => {
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
        "x-api-key": token
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
            "x-api-key": token,
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

function findFirstAvailableModel(provider) {
  // Stellt sicher, dass der Provider im Katalog existiert, um Fehler zu vermeiden.
  if (!appState.model_catalog[provider]) {
    console.error(`Provider '${provider}' not found in model catalog.`);
    return null;
  }

  // Holt die vom User erlaubten Modelle oder nimmt alle als Fallback.
  let allowedModels = appState.user_selections[provider] || [];
  if (allowedModels.length === 0) {
      allowedModels = appState.model_catalog[provider].map(m => m.id);
  }
  
  // Filtert die Modelle (z.B. um reine TTS-Modelle auszublenden).
  const availableModels = appState.model_catalog[provider].filter(
    model => allowedModels.includes(model.id) && 
             !["gpt-image-1.5", "gpt-image-1-mini", "gpt-4o-mini-tts"].includes(model.id)
  );

  // Gibt das erste gefundene Modell zurück oder null, wenn die Liste leer ist.
  return availableModels.length > 0 ? availableModels[0] : null;
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
