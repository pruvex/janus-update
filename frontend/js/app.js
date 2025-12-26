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

// NEU: Funktion zum Speichern des zuletzt verwendeten Modells und Providers im Backend
async function updateLastUsedModelInBackend() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/last-used-model`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
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
    // Update sidebar provider dropdown
    sidebarProviderSelect.value = appState.last_active.provider;

    // Populate sidebar model dropdown based on selected provider
    sidebarModelSelect.innerHTML = ""; // Clear existing options
    const provider = appState.last_active.provider;
    const allowedModels = appState.user_selections[provider] || [];

    if (appState.model_catalog[provider]) {
                const filteredModels = appState.model_catalog[provider].filter(
                  (model) => allowedModels.includes(model.id)
                );
      filteredModels.forEach((model) => {
        const option = document.createElement("option");
        option.value = model.id;
        console.log("Debugging cost display for model:", model.id, "cost_per_image:", model.cost_per_image, "cost_per_text_input_token:", model.cost_per_text_input_token); // NEU
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
                                }        option.textContent = `${model.name} (${costDisplay})${model.desc ? " - " + model.desc : ""}`;
        sidebarModelSelect.appendChild(option);
      });
    } else {
      console.warn(`No models found for provider: ${provider}`);
    }

    sidebarModelSelect.value = appState.last_active.model;
  }

  if (appState.currentView === "chat") {
    chatView.style.display = "block";
    settingsView.style.display = "none";
  } else {
    chatView.style.display = "none";
    settingsView.style.display = "flex";
    // renderSettingsView(); // <-- DIESEN AUFRUF ENTFERNEN
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const settingsBtn = document.getElementById("settings-btn");
  console.log("settingsBtn found:", settingsBtn);

  settingsBtn.addEventListener("click", () => {
    console.log("Settings button clicked!");
    appState.currentView = "settings";
    render();
    // Dispatch a custom event to notify settings.js
    document.dispatchEvent(new CustomEvent("show-settings"));
  });
  const backToChatBtn = document.getElementById("back-to-chat-btn");
  const sidebarProviderSelect = document.getElementById("provider-select");

  backToChatBtn.addEventListener("click", () => {
    appState.currentView = "chat";
    render();
  });

  const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
  const appContainer = document.querySelector(".app-container");

  toggleSidebarBtn.addEventListener("click", () => {
    appContainer.classList.toggle("sidebar-collapsed");
    if (appContainer.classList.contains("sidebar-collapsed")) {
      toggleSidebarBtn.textContent = "▶";
    } else {
      toggleSidebarBtn.textContent = "◀";
    }
  });

  sidebarProviderSelect.addEventListener("change", async () => {
    appState.last_active.provider = sidebarProviderSelect.value;
    const provider = appState.last_active.provider;
    const allowedModels = appState.user_selections[provider] || [];
    const filteredModels = appState.model_catalog[provider].filter((model) =>
      allowedModels.includes(model.id)
    );
    if (filteredModels.length > 0) {
      appState.last_active.model = filteredModels[0].id;
    } else {
      appState.last_active.model = "";
    }
    await updateLastUsedModelInBackend();
    render();
  });

  const sidebarModelSelect = document.getElementById("model-select");
  sidebarModelSelect.addEventListener("change", async () => {
    appState.last_active.model = sidebarModelSelect.value;
    await updateLastUsedModelInBackend();
    render();
  });

  await loadModelCatalog();
  await loadLastUsedModel();
  await loadUserSelections(); // Load selections before initial render
  render(); // Initial render

  // Load projects
  await loadProjects();

  // Initialize global variables for settings view elements
  modelSelectionForm = document.getElementById("model-selection-form");
  backFromModelsBtn = document.getElementById("back-from-models-btn");
  modelList = document.getElementById("model-list");

  // Initial call to set active section when settings view is first rendered
  // This will be called by renderSettingsView() and renderModelManagementView()

  interact(".chat-window")
    .draggable({
      allowFrom: "#chat-header",
      inertia: true,
      listeners: {
        start(event) {
          const target = event.target;
          const rect = target.getBoundingClientRect();
          // Setze die Startposition relativ zum Viewport, um konsistent zu sein
          target.setAttribute("data-x", rect.left);
          target.setAttribute("data-y", rect.top);
        },
        move: dragListener,
      },
    })
    .resizable({
      edges: { left: true, right: true, bottom: true, top: true },
      inertia: true,
      // NEU: Fügt die Größenbeschränkung hinzu
      modifiers: [
        interact.modifiers.restrictSize({
          min: { width: 300, height: 200 },
        }),
      ],
      listeners: {
        move: resizeListener,
      },
    });

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

  // NEU: Drag-and-Drop für das Image Modal
  interact("#image-modal .modal-content")
    .draggable({
      allowFrom: "#image-modal .modal-header", // Header als Drag-Handle
      inertia: true,
      listeners: {
        start(event) {
          const target = event.target;
          const rect = target.getBoundingClientRect();
          target.setAttribute("data-x", rect.left);
          target.setAttribute("data-y", rect.top);
          window.justDragged = false; // Zurücksetzen am Start des Drags
        },
        move: dragListener,
        end(event) {
            window.justDragged = true; // Markiere, dass ein Drag beendet wurde
        }
      },
    }); // Keine resizable Konfiguration für das Bild-Modal

  function dragListener(event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

    // Wiederherstellung der separaten Logik zur Fehlerbehebung
    if (target.closest('#image-modal .modal-content')) {
      // Spezifische Logik für das Bild-Modal
      const maxX = window.innerWidth - target.offsetWidth;
      const maxY = window.innerHeight - target.offsetHeight;
      x = Math.max(0, Math.min(x, maxX));
      y = Math.max(0, Math.min(y, maxY));
    } else {
      // Logik für alle anderen draggable Elemente (z.B. Chat-Fenster)
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

  // Listener for project list updates from the main process
  if (window.electron && typeof window.electron.on === 'function') {
    window.electron.on('project-list-updated', () => {
      console.log("Event 'project-list-updated' received. Reloading projects.");
      loadProjects();
    });
  }

    // Back to chat from project dashboard
  const backToProjectChatBtn = document.getElementById('back-to-chat-from-project');
  if (backToProjectChatBtn) {
    backToProjectChatBtn.addEventListener('click', () => {
      appState.currentProjectId = null;
      document.querySelectorAll('.project-item').forEach(item => item.classList.remove('active'));
      switchView('chat');
    });
  }

  // New chat in project
  const newProjectChatBtn = document.getElementById('new-project-chat-btn');
  if (newProjectChatBtn) {
    newProjectChatBtn.addEventListener('click', () => {
      if (appState.currentProjectId) {
        // Create a new chat in the current project
        createNewChatInProject(appState.currentProjectId);
      }
    });
  }

  // File upload button
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
});

async function loadProjects() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/projects`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const projects = await response.json();
    const projectListDiv = document.getElementById('project-list');
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
    const data = await response.json();
    // Transform the array into an object for easier lookup by provider
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
  }
}

async function loadLastUsedModel() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/last-used-model`);
    const data = await response.json();
    appState.last_active.provider = data.provider;
    appState.last_active.model = data.model;
    console.log("loadLastUsedModel - data:", data); // Debug Log
    console.log("appState.last_active.provider after loadLastUsedModel:", appState.last_active.provider); // Debug Log
  } catch (error) {
    console.error("Failed to load last used model:", error);
  }
}

async function loadUserSelections() {
  // Get all unique providers from the model catalog
  const availableProviders = Object.keys(appState.model_catalog);
  const MAX_RETRIES = 5;
  const RETRY_DELAY_MS = 1000; // 1 second delay

  for (const provider of availableProviders) {
    let success = false;
    for (let i = 0; i < MAX_RETRIES; i++) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
        if (!response.ok) {
          console.warn(
            `Attempt ${i + 1} failed for ${provider}: ${response.status} ${response.statusText}. Retrying...`
          );
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
          continue;
        }
        const data = await response.json();
        appState.user_selections[provider] = data.selected_models;
        success = true;
        break; // Exit retry loop on success
      } catch (error) {
        console.warn(`Attempt ${i + 1} failed for ${provider} with error:`, error, ". Retrying...");
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
      }
    }
    if (!success) {
      console.error(`Failed to load models for ${provider} after ${MAX_RETRIES} retries.`);
      appState.user_selections[provider] = []; // Default to empty if all retries fail
    }
  }
}
