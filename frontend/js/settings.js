import "../css/settings.css";
import { API_BASE_URL } from "./config.js";
import { initTTS } from "./tts.js";

const appState = {
  // Minimal appState for settings
  model_catalog: {},
  user_selections: {},
};

// --- DOM Elements ---
const settingsNav = document.getElementById("settings-nav");
const navLinks = document.querySelectorAll(".settings-nav-link");
const contentSections = document.querySelectorAll(".settings-section");
const apiKeyForm = document.getElementById("api-key-form");
const providerInput = document.getElementById("provider-input");
const apiKeyInput = document.getElementById("api-key-input");
const apiKeyList = document.getElementById("api-key-list");
const modelManagementButtons = document.getElementById("model-management-buttons");
const modelSelectionForm = document.getElementById("model-selection-form");
const modelList = document.getElementById("model-list");
const backFromModelsBtn = document.getElementById("back-from-models-btn");
const workspacesList = document.getElementById("workspaces-list");
const addWorkspaceBtn = document.getElementById("add-workspace-btn");
const memoryListContainer = document.getElementById("memory-list-container");

// Memory Modal Elements
const memoryModal = document.getElementById("memory-modal");
const memoryForm = document.getElementById("memory-form");
const closeMemoryModalBtn = document.getElementById("close-memory-modal");
const addMemoryBtn = document.getElementById("add-memory-btn");
const memoryPrioritySelect = document.getElementById("memory-priority");

// --- Functions ---

function setActiveSettingsSection(targetId) {
  navLinks.forEach((navLink) => navLink.classList.remove("active-setting"));
  const activeLink = document.querySelector(`.settings-nav-link[data-target="${targetId}"]`);
  if (activeLink) {
    activeLink.classList.add("active-setting");
  }

  contentSections.forEach((section) => {
    section.style.display = "none";
  });

  const targetSection = document.getElementById(targetId);
  if (targetSection) {
    targetSection.style.display = "block";
  }
}

async function loadApiKeys() {
  apiKeyList.innerHTML = "";
  try {
    const response = await fetch(`${API_BASE_URL}/api/keys`);
    const data = await response.json();
    for (const provider in data.api_keys) {
      const listItem = document.createElement("li");
      listItem.textContent = `Provider: ${provider}, Key: ****`;
      apiKeyList.appendChild(listItem);
    }
  } catch (error) {
    console.error("Error loading API keys:", error);
  }
}

async function renderSettingsView() {
  setActiveSettingsSection("api-key-section");
  await loadApiKeys();

  modelManagementButtons.innerHTML = "";
  try {
    const response = await fetch(`${API_BASE_URL}/api/keys`);
    const data = await response.json();
    for (const provider in data.api_keys) {
      const manageModelsBtn = document.createElement("button");
      manageModelsBtn.textContent = `Modelle für ${provider} verwalten`;
      manageModelsBtn.dataset.provider = provider;
      modelManagementButtons.appendChild(manageModelsBtn);
    }
  } catch (error) {
    console.error("Error loading providers for model management buttons:", error);
  }
}

async function renderModelManagementView(provider) {
  setActiveSettingsSection("model-management-section");
  document.querySelector("#model-management-section h3").textContent =
    `Modelle für ${provider} verwalten`;
  modelList.innerHTML = "";

  let selectedModels = [];
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
    const data = await response.json();
    selectedModels = data.selected_models;
  } catch (error) {
    console.error("Error fetching selected models:", error);
  }

  const excludedModels = [
    "gpt-image-1.5",
    "gpt-image-1-mini",
    "gpt-4o-mini-tts",
    "gpt-image-1",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
    "gemini-pro-vision"
  ];
  appState.model_catalog[provider].forEach((model) => {
    if (excludedModels.includes(model.id)) return;
    const listItem = document.createElement("li");
    const isChecked = selectedModels.includes(model.id) ? "checked" : "";
    listItem.innerHTML = `<input type="checkbox" id="${model.id}" value="${model.id}" ${isChecked}> <label for="${model.id}">${model.name}</label>`;
    modelList.appendChild(listItem);
  });

  modelSelectionForm.dataset.provider = provider;
}

async function renderWorkspacesView() {
  setActiveSettingsSection("workspaces-section");
  workspacesList.innerHTML = "";
  try {
    const response = await fetch(`${API_BASE_URL}/api/workspaces`);
    const data = await response.json();
    const workspaces = data.workspaces || [];
    if (workspaces.length === 0) {
      workspacesList.innerHTML = "<li>Keine Arbeitsverzeichnisse konfiguriert.</li>";
    } else {
      workspaces.forEach((path) => {
        const listItem = document.createElement("li");
        listItem.textContent = path;
        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Entfernen";
        removeBtn.classList.add("remove-workspace-btn"); // Add a class for styling and event delegation
        removeBtn.dataset.path = path; // Store the path in a data attribute
        listItem.appendChild(removeBtn);
        workspacesList.appendChild(listItem);
      });
    }
  } catch (error) {
    console.error("Error loading workspaces:", error);
  }
}

async function renderMemoryView() {
  setActiveSettingsSection("memory-section");
  memoryListContainer.innerHTML = '<div class="spinner"></div> Lade Diamond Memory...';

  try {
    const response = await fetch(`${API_BASE_URL}/api/memory`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const memories = await response.json();

    if (!memories || memories.length === 0) {
      memoryListContainer.innerHTML = "<p>Keine Einträge gefunden. Füge deinen ersten Fakt hinzu!</p>";
      return;
    }

    memoryListContainer.innerHTML = "";
    
    memories.forEach((memory) => {
      const memoryCard = document.createElement("div");
      
      // Styling & Labeling Logik
      let priorityClass = "priority-general";
      let icon = "📄";
      let label = "General";
      
      const priority = memory.core_priority !== undefined ? memory.core_priority : 0;
      
      if (priority === 2) {
          priorityClass = "priority-core-identity";
          icon = "💎";
          label = "Core Identity";
      } else if (priority === 1) {
          priorityClass = "priority-core-detail";
          icon = "🔹";
          label = "Core Detail";
      }

      // --- NEU: Zuerst das JSON-Objekt aus dem Snippet parsen ---
      let factObject;
      try {
          factObject = JSON.parse(memory.snippet);
      } catch (e) {
          // Fallback für alte, nicht-JSON-formatierte Einträge
          factObject = { fact: memory.snippet, category: memory.category };
      }
      // --- ENDE NEU ---

      memoryCard.className = `memory-card ${priorityClass}`;
      memoryCard.dataset.id = memory.id;

      // --- KORREKTUR: Daten für das Modal aus dem geparsten Objekt speichern ---
      // Speichert das ganze Objekt als String, um es im Modal wieder zu laden
      memoryCard.dataset.factObject = JSON.stringify(factObject); 
      // --- ENDE KORREKTUR ---

      memoryCard.innerHTML = `
        <div class="memory-header" style="display:flex; justify-content:space-between; font-size:0.8em; margin-bottom:8px; opacity:0.9;">
            <span class="mem-type" style="font-weight:bold;">${icon} ${label}</span>
            <span class="mem-cat" style="background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px;">${factObject.category || "Unkategorisiert"}</span>
        </div>
        <div class="memory-content" style="margin-bottom:15px; line-height:1.5;">
          <span class="memory-snippet">${factObject.fact}</span> <!-- KORREKTUR: Nur das 'fact'-Feld anzeigen -->
        </div>
        <div class="memory-actions">
          <button class="edit-memory-btn secondary-button">Bearbeiten</button>
          <button class="delete-memory-btn secondary-button" style="border-color:#b91c1c; color:#fca5a5;">Löschen</button>
        </div>
      `;
      memoryListContainer.appendChild(memoryCard);
    });

    // Event Listeners für die neuen Buttons
    document.querySelectorAll(".edit-memory-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => openMemoryModal(e.target.closest(".memory-card")));
    });
    
    document.querySelectorAll(".delete-memory-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => deleteMemoryEntry(e.target.closest(".memory-card")));
    });

  } catch (error) {
    console.error("Error loading memory:", error);
    memoryListContainer.innerHTML = `<p class="error-message">Fehler: ${error.message}</p>`;
  }
}

// --- Memory Modal Logic ---

function openMemoryModal(card = null) {
  const title = document.getElementById("memory-modal-title");
  const idInput = document.getElementById("memory-id");
  const snippetInput = document.getElementById("memory-snippet");
  const catInput = document.getElementById("memory-category");
  const prioInput = document.getElementById("memory-priority");

  if (card) {
    // Edit Mode
    const factObject = JSON.parse(card.dataset.factObject);
    title.textContent = "Fakt bearbeiten";
    idInput.value = card.dataset.id;
    snippetInput.value = factObject.fact; // Aus dem Objekt lesen
    catInput.value = factObject.category; // Aus dem Objekt lesen
    
    let priority = 0;
    if (factObject.type === "CORE_IDENTITY") priority = 2;
    else if (factObject.type === "CORE_DETAIL") priority = 1;
    prioInput.value = priority;
  } else {
    // Add Mode
    title.textContent = "Neuen Fakt hinzufügen";
    idInput.value = "";
    snippetInput.value = "";
    catInput.value = "Allgemein";
    prioInput.value = "0";
  }
  
  memoryModal.style.display = "block";
}

function updatePriorityDescription(priority, element) {
    const descriptions = {
        "2": "Definiert fundamentale Eigenschaften der Identität. Diese Fakten werden IMMER im Kontext berücksichtigt.",
        "1": "Wichtige Details zu deiner Person. Diese Fakten werden bei thematischer Relevanz automatisch abgerufen.",
        "0": "Allgemeine Informationen. Diese Fakten können bei Bedarf aus dem aktiven Speicher entfernt werden."
    };
    
    if (element) {
        element.textContent = descriptions[priority] || "";
    }
}

function closeMemoryModal() {
    memoryModal.style.display = "none";
}

// Event Listeners für das Memory-Modal
if (addMemoryBtn) addMemoryBtn.addEventListener("click", () => openMemoryModal(null));
if (closeMemoryModalBtn) closeMemoryModalBtn.addEventListener("click", closeMemoryModal);
if (memoryPrioritySelect) {
    memoryPrioritySelect.addEventListener("change", (e) => {
        updatePriorityDescription(e.target.value, document.getElementById("priority-desc"));
    });
}

// Schließen des Modals, wenn außerhalb geklickt wird
window.addEventListener("click", (event) => {
    if (event.target === memoryModal) {
        closeMemoryModal();
    }
});

// Form Submit Handler
if (memoryForm) {
    memoryForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const id = document.getElementById("memory-id").value;
        const snippet = document.getElementById("memory-snippet").value.trim();
        const category = document.getElementById("memory-category").value.trim() || "Allgemein";
        const priority = parseInt(document.getElementById("memory-priority").value) || 0;
        
        if (!snippet) {
            alert("Bitte gib einen Fakt ein.");
            return;
        }

        const payload = {
            snippet: snippet,
            category: category,
            core_priority: priority,
            is_core_fact: priority > 0
        };

        const url = id ? `${API_BASE_URL}/api/memory/${id}` : `${API_BASE_URL}/api/memory`;
        const method = id ? "PUT" : "POST";

        try {
            const response = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Speichern fehlgeschlagen");
            }
            
            closeMemoryModal();
            await renderMemoryView(); // Refresh list

        } catch (error) {
            console.error("Error saving memory:", error);
            alert(`Fehler: ${error.message}`);
        }
    });
}

// Abbrechen-Button
const cancelMemoryBtn = document.getElementById("memory-cancel-btn");
if (cancelMemoryBtn) {
    cancelMemoryBtn.addEventListener("click", closeMemoryModal);
}

// --- START: Address Book Functions ---
const contactListContainer = document.getElementById("contact-list-container");
const contactModal = document.getElementById("contact-modal");
const contactForm = document.getElementById("contact-form");
const contactModalTitle = document.getElementById("contact-modal-title");
const closeContactModalBtn = contactModal.querySelector(".close-button");
const addContactBtn = document.getElementById("add-contact-btn");

async function renderAddressBookView() {
  setActiveSettingsSection("address-book-section");
  contactListContainer.innerHTML = "<p>Lade Kontakte...</p>";

  try {
    const response = await fetch(`${API_BASE_URL}/api/contacts`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const contacts = await response.json();
    renderContactList(contacts);
  } catch (error) {
    console.error("Error loading contacts:", error);
    contactListContainer.innerHTML = `<p>Fehler beim Laden der Kontakte: ${error.message}</p>`;
  }
}

function renderContactList(contacts) {
  contactListContainer.innerHTML = "";
  if (contacts.length === 0) {
    contactListContainer.innerHTML = "<p>Keine Kontakte gefunden.</p>";
    return;
  }

  contacts.forEach((contact) => {
    const contactCard = document.createElement("div");
    contactCard.className = "contact-card";
    contactCard.dataset.id = contact.id;

    // Create website link if it exists
    const websiteLink = contact.website
      ? `<p class="website"><a href="${contact.website}" target="_blank" rel="noopener noreferrer">${contact.website}</a></p>`
      : "";

    // Populate card with more details
    contactCard.innerHTML = `
      <div class="contact-details">
        <strong>${contact.name}</strong>
        <small class="category">${contact.category || "Unkategorisiert"}</small>
        <p class="email">${contact.email || ""}</p>
        <p class="phone">${contact.phone || ""}</p>
        <p class="address">${contact.address || ""}</p>
        ${websiteLink}
        <p class="notes">${contact.notes || ""}</p>
      </div>
      <div class="contact-actions">
        <button class="edit-contact-btn">Bearbeiten</button>
        <button class="delete-contact-btn">Löschen</button>
      </div>
    `;
    contactListContainer.appendChild(contactCard);
  });

  // Add event listeners for the new buttons
  contactListContainer.querySelectorAll(".edit-contact-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const card = e.target.closest(".contact-card");
      const contactId = card.dataset.id;
      try {
        const response = await fetch(`${API_BASE_URL}/api/contacts/${contactId}`);
        if (!response.ok) throw new Error("Kontakt nicht gefunden");
        const contact = await response.json();
        showContactModal(contact);
      } catch (error) {
        console.error("Error fetching contact details:", error);
      }
    });
  });

  contactListContainer.querySelectorAll(".delete-contact-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const card = e.target.closest(".contact-card");
      const contactId = card.dataset.id;
      if (
        confirm(
          `Möchtest du den Kontakt "${card.querySelector("strong").textContent}" wirklich löschen?`
        )
      ) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/contacts/${contactId}`, {
            method: "DELETE",
          });
          if (!response.ok) throw new Error("Fehler beim Löschen");
          renderAddressBookView(); // Refresh list
        } catch (error) {
          console.error("Error deleting contact:", error);
        }
      }
    });
  });
}

function showContactModal(contact = null) {
  contactForm.reset();
  const contactIdInput = document.getElementById("contact-id");
  if (contact) {
    contactModalTitle.textContent = "Kontakt bearbeiten";
    contactIdInput.value = contact.id;
    document.getElementById("contact-name").value = contact.name || "";
    document.getElementById("contact-category").value = contact.category || "";
    document.getElementById("contact-email").value = contact.email || "";
    document.getElementById("contact-phone").value = contact.phone || "";
    document.getElementById("contact-address").value = contact.address || "";
    document.getElementById("contact-website").value = contact.website || "";
    document.getElementById("contact-notes").value = contact.notes || "";
  } else {
    contactModalTitle.textContent = "Neuer Kontakt";
    contactIdInput.value = "";
  }
  contactModal.style.display = "block";
}

function hideContactModal() {
  contactModal.style.display = "none";
}

// Event Listeners for Modal
addContactBtn.addEventListener("click", () => showContactModal());
closeContactModalBtn.addEventListener("click", hideContactModal);
window.addEventListener("click", (event) => {
  if (event.target == contactModal) {
    hideContactModal();
  }
});

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("contact-id").value;
  const contactData = {
    name: document.getElementById("contact-name").value,
    category: document.getElementById("contact-category").value,
    email: document.getElementById("contact-email").value,
    phone: document.getElementById("contact-phone").value,
    address: document.getElementById("contact-address").value,
    website: document.getElementById("contact-website").value,
    notes: document.getElementById("contact-notes").value,
  };

  const url = id ? `${API_BASE_URL}/api/contacts/${id}` : `${API_BASE_URL}/api/contacts`;
  const method = id ? "PUT" : "POST";

  try {
    const response = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(contactData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Speichern fehlgeschlagen");
    }
    hideContactModal();
    renderAddressBookView();
  } catch (error) {
    console.error("Error saving contact:", error);
    alert(`Fehler: ${error.message}`);
  }
});

// --- END: Address Book Functions ---

async function editMemoryEntry(memoryCard) {
  const memoryId = memoryCard.dataset.id;
  const snippetSpan = memoryCard.querySelector(".memory-snippet");
  const categorySpan = memoryCard.querySelector(".memory-category");
  const editBtn = memoryCard.querySelector(".edit-memory-btn");
  const deleteBtn = memoryCard.querySelector(".delete-memory-btn");

  const originalSnippet = snippetSpan.textContent;
  const originalCategory = categorySpan.dataset.category;

  // Make snippet editable
  snippetSpan.innerHTML = `<textarea class="edit-snippet-textarea">${originalSnippet}</textarea>`;

  // Make category editable with a dropdown
  const categories = [
    "Personal",
    "Preference",
    "Goal",
    "Value",
    "Experience",
    "Professional",
    "General Fact",
  ];
  categorySpan.innerHTML = `
    <select class="edit-category-select">
      ${categories.map((cat) => `<option value="${cat}" ${cat === originalCategory ? "selected" : ""}>${cat}</option>`).join("")}
    </select>
  `;

  // Change buttons to Save/Cancel
  editBtn.textContent = "Speichern";
  editBtn.classList.remove("edit-memory-btn");
  editBtn.classList.add("save-memory-btn");
  deleteBtn.textContent = "Abbrechen";
  deleteBtn.classList.remove("delete-memory-btn");
  deleteBtn.classList.add("cancel-edit-btn");

  // New event listeners for Save/Cancel
  editBtn.onclick = async () => {
    const updatedSnippet = memoryCard.querySelector(".edit-snippet-textarea").value;
    const updatedCategory = memoryCard.querySelector(".edit-category-select").value;

    try {
      const response = await fetch(`${API_BASE_URL}/api/memory/${memoryId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ snippet: updatedSnippet, category: updatedCategory }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      renderMemoryView(); // Re-render to show updated data
    } catch (error) {
      console.error("Error updating memory entry:", error);
      alert(`Fehler beim Aktualisieren des Eintrags: ${error.message}`);
    }
  };

  deleteBtn.onclick = () => {
    // Revert to original state if cancelled
    snippetSpan.textContent = originalSnippet;
    categorySpan.textContent = originalCategory;
    categorySpan.className = `memory-category category-${originalCategory.toLowerCase().replace(/\s/g, "-")}`;
    categorySpan.dataset.category = originalCategory;

    editBtn.textContent = "Bearbeiten";
    editBtn.classList.remove("save-memory-btn");
    editBtn.classList.add("edit-memory-btn");
    deleteBtn.textContent = "Löschen";
    deleteBtn.classList.remove("cancel-edit-btn");
    deleteBtn.classList.add("delete-memory-btn");

    // Re-attach original event listeners
    editBtn.onclick = null; // Clear previous listener
    deleteBtn.onclick = null; // Clear previous listener
    editBtn.addEventListener("click", (e) => editMemoryEntry(e.target.closest(".memory-card")));
    deleteBtn.addEventListener("click", (e) => deleteMemoryEntry(e.target.closest(".memory-card")));
  };
}

async function deleteMemoryEntry(memoryCard) {
  const memoryId = memoryCard.dataset.id;
  const snippet = memoryCard.querySelector(".memory-snippet").textContent;

  if (confirm(`Möchtest du den Fakt "${snippet}" wirklich löschen?`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/memory/${memoryId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      memoryCard.remove(); // Remove from UI
      alert("Fakt erfolgreich gelöscht!");
    } catch (error) {
      console.error("Error deleting memory entry:", error);
      alert(`Fehler beim Löschen des Eintrags: ${error.message}`);
    }
  }
}

export async function updateActivePersonalityDisplay() {
  const activePersonalityDisplay = document.getElementById("active-personality-display");
  if (!activePersonalityDisplay) return;

  try {
    // Get active personality ID
    const activeResponse = await fetch(`${API_BASE_URL}/api/personalities/active`);
    const activeData = await activeResponse.json();
    const activePersonalityId = activeData.active_personality_id;

    // Get all personalities to find the name
    const allPersonalitiesResponse = await fetch(`${API_BASE_URL}/api/personalities`);
    const allPersonalities = await allPersonalitiesResponse.json();

    const activePersonality = allPersonalities.find((p) => p.id === activePersonalityId);

    if (activePersonality) {
      activePersonalityDisplay.textContent = `(${activePersonality.name})`;
    } else {
      activePersonalityDisplay.textContent = "";
    }
  } catch (error) {
    console.error("Error updating active personality display:", error);
    activePersonalityDisplay.textContent = ""; // Clear on error
  }
}

// --- Event Listeners ---

document.addEventListener("DOMContentLoaded", async () => {
  // Display app version
  const versionDisplay = document.getElementById('app-version-display');
  if (versionDisplay) {
    versionDisplay.textContent = `Version ${import.meta.env.APP_VERSION || '0.1.0-beta.1'}`;
  }

  // Load initial data
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/catalog`);
    const data = await response.json();
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

  // Listen for custom event to show settings
  document.addEventListener("show-settings", () => {
    renderSettingsView();
  });

  // Initial render
  renderSettingsView();
  updateActivePersonalityDisplay(); // Initial call to display active personality

  // Navigation
  settingsNav.addEventListener("click", (e) => {
    const link = e.target.closest(".settings-nav-link");
    if (!link) return;
    e.preventDefault();
    const targetId = link.dataset.target;
    setActiveSettingsSection(targetId);
    if (targetId === "workspaces-section") {
      renderWorkspacesView();
    } else if (targetId === "memory-section") {
      // NEU
      renderMemoryView();
    } else if (targetId === "address-book-section") {
      renderAddressBookView();
    }
  });

  // API Key Form
  apiKeyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const provider = providerInput.value;
    const api_key = apiKeyInput.value;
    
    // Visuelles Feedback
    const submitBtn = apiKeyForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Speichere...";
    submitBtn.disabled = true;

    try {
        await fetch(`${API_BASE_URL}/api/keys`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider, api_key }),
        });
        
        apiKeyInput.value = "";
        
        // --- FIX: HARTER NEUSTART ---
        // Zwingt die App, neu zu laden. Dadurch werden 'initializeApp' 
        // und 'loadChats' erneut ausgeführt, diesmal MIT gültigem Token.
        console.log("API Key gespeichert. Führe Neustart durch...");
        window.location.reload(); 
        // ----------------------------

    } catch (error) {
        console.error("Fehler beim Speichern des Keys:", error);
        alert("Fehler beim Speichern: " + error.message);
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
  });

  // Model Management
  modelManagementButtons.addEventListener("click", (e) => {
    if (e.target.tagName === "BUTTON") {
      const provider = e.target.dataset.provider;
      renderModelManagementView(provider);
    }
  });

  modelSelectionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const provider = modelSelectionForm.dataset.provider;
    const checkboxes = modelList.querySelectorAll('input[type="checkbox"]:checked');
    const newSelection = Array.from(checkboxes).map((cb) => cb.value);
    
    await fetch(`${API_BASE_URL}/api/models/selection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: provider, models: newSelection }),
    });

    // Send update signal to the main app
    console.log("Modelle gespeichert, sende Update-Signal...");
    document.dispatchEvent(new CustomEvent("models-updated"));
    
    renderSettingsView();
  });

  backFromModelsBtn.addEventListener("click", () => {
    renderSettingsView();
  });

  // Workspaces
  addWorkspaceBtn.addEventListener("click", async () => {
    const path = await window.electron.openDirectoryDialog();
    if (path) {
      await fetch(`${API_BASE_URL}/api/workspaces/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      renderWorkspacesView();
    }
  });

  workspacesList.addEventListener("click", async (e) => {
    if (e.target.classList.contains("remove-workspace-btn")) {
      const pathToRemove = e.target.dataset.path;
      await fetch(`${API_BASE_URL}/api/workspaces/remove`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ path: pathToRemove }),
      });
      renderWorkspacesView();
    }
  });

  // --- RAG WISSENSBASIS-VERWALTUNG ---
  const ragFolderPathInput = document.getElementById("rag-folder-path-input");
  const ragIndexFolderBtn = document.getElementById("rag-index-folder-btn");
  const ragStatusMessage = document.getElementById("rag-status-message");
  const collectionSelect = document.getElementById("rag-collection-select");
  const newCollectionNameInput = document.getElementById("rag-new-collection-name-input");
  const progressContainer = document.getElementById("rag-progress-container");
  const progressText = document.getElementById("rag-progress-text");
  const progressBar = document.getElementById("rag-progress-bar");
  let pollingInterval = null;

  async function loadCollections() {
    const ragCollectionList = document.getElementById("rag-collection-list");
    const collectionSelect = document.getElementById("rag-collection-select");

    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/collections`);
      const data = await response.json();

      // Get current selection before clearing
      const currentSelection = collectionSelect ? collectionSelect.value : null;

      // Clear both the list and the dropdown
      if (ragCollectionList) ragCollectionList.innerHTML = "";
      if (collectionSelect) {
        collectionSelect.innerHTML = "";
        const newOption = document.createElement("option");
        newOption.value = "__new__";
        newOption.textContent = "Neue Bibliothek erstellen...";
        collectionSelect.appendChild(newOption);
      }

      if (data.collections) {
        data.collections.forEach((name) => {
          // Populate the list for display
          if (ragCollectionList) {
            const listItem = document.createElement("li");
            listItem.className = "collection-list-item";

            const collectionNameSpan = document.createElement("span");
            collectionNameSpan.textContent = name;
            listItem.appendChild(collectionNameSpan);

            const analyzeBtn = document.createElement("button");
            analyzeBtn.innerHTML = "✨";
            analyzeBtn.className = "analyze-style-btn";
            analyzeBtn.title = "Stil-Profil für diese Collection generieren";
            analyzeBtn.dataset.collectionName = name;
            listItem.appendChild(analyzeBtn);

            ragCollectionList.appendChild(listItem);
          }

          // Populate the dropdown for indexing
          if (collectionSelect) {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            collectionSelect.appendChild(option);
          }
        });
      }

      // Restore selection in dropdown
      if (
        collectionSelect &&
        currentSelection &&
        collectionSelect.querySelector(`option[value="${currentSelection}"]`)
      ) {
        collectionSelect.value = currentSelection;
      }
      handleCollectionChange();
    } catch (error) {
      console.error("Fehler beim Laden der Wissens-Bibliotheken:", error);
      if (ragCollectionList)
        ragCollectionList.innerHTML = "<li>Fehler beim Laden der Bibliotheken.</li>";
    }
  }

  function handleCollectionChange() {
    newCollectionNameInput.style.display = collectionSelect.value === "__new__" ? "block" : "none";
  }

  collectionSelect.addEventListener("change", handleCollectionChange);

  function getSelectedCollectionName() {
    return collectionSelect.value === "__new__"
      ? newCollectionNameInput.value.trim()
      : collectionSelect.value;
  }

  async function updateProgress() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/indexing-status`);
      if (!response.ok) throw new Error(`Server-Fehler: ${response.status}`);
      const status = await response.json();

      if (status.in_progress) {
        progressContainer.style.display = "block";
        if (status.total_files > 0) {
          progressBar.max = status.total_files;
          progressBar.value = status.processed_files;
          progressText.textContent = `[${status.processed_files}/${status.total_files}] Verarbeite: ${status.current_file || "..."}`;
        } else {
          progressText.textContent = "Berechne Dateien...";
        }
      } else {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        progressContainer.style.display = "none";
        ragStatusMessage.textContent = status.message || "Prozess beendet.";
        ragStatusMessage.style.color = "#10b981";
        ragIndexFolderBtn.disabled = false;
        loadCollections();
      }
    } catch (error) {
      console.error("Fehler beim Abrufen des Indexierungsstatus:", error);
      ragStatusMessage.textContent = `Fehler beim Abruf des Status: ${error.message}`;
      ragStatusMessage.style.color = "#b91c1c";
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
      ragIndexFolderBtn.disabled = false;
    }
  }

  ragIndexFolderBtn.addEventListener("click", async () => {
    const path = ragFolderPathInput.value.trim();
    const collectionName = getSelectedCollectionName();
    if (!path || !collectionName) {
      alert("Bitte geben Sie einen Ordnerpfad UND einen gültigen Bibliotheksnamen an.");
      return;
    }
    if (pollingInterval) clearInterval(pollingInterval);

    ragIndexFolderBtn.disabled = true;
    ragStatusMessage.textContent = "Indexierung wird gestartet...";
    ragStatusMessage.style.color = "#3b82f6";
    progressContainer.style.display = "block";
    progressText.textContent = "Initialisiere...";
    progressBar.value = 0;

    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/index-folder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, collection_name: collectionName }),
      });
      const result = await response.json();
      if (response.ok) {
        ragStatusMessage.textContent = result.message;
        setTimeout(() => {
          updateProgress();
          pollingInterval = setInterval(updateProgress, 2000);
        }, 1000);
      } else {
        throw new Error(result.detail || "Fehler beim Starten.");
      }
    } catch (error) {
      ragStatusMessage.textContent = `Fehler: ${error.message}`;
      ragStatusMessage.style.color = "#b91c1c";
      ragIndexFolderBtn.disabled = false;
      progressContainer.style.display = "none";
    }
  });

  // Sorge dafür, dass die Sammlungen geladen werden, wenn der Tab geklickt wird
  const ragNavLink = document.querySelector(
    '.settings-nav-link[data-target="rag-management-section"]'
  );
  if (ragNavLink) {
    ragNavLink.addEventListener("click", loadCollections);
  }

  const ragCollectionList = document.getElementById("rag-collection-list");
  if (ragCollectionList) {
    ragCollectionList.addEventListener("click", async (e) => {
      if (e.target.classList.contains("analyze-style-btn")) {
        const collectionName = e.target.dataset.collectionName;
        const button = e.target;

        // Show loading indicator
        button.disabled = true;
        button.innerHTML = '<div class="spinner"></div>';

        try {
          const response = await fetch(
            `${API_BASE_URL}/api/rag/collections/${collectionName}/analyze-style`,
            {
              method: "POST",
            }
          );

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const profile = await response.json();
          showStyleProfileModal(collectionName, profile);
        } catch (error) {
          console.error("Error analyzing style:", error);
          alert(`Fehler bei der Stilanalyse für ${collectionName}: ${error.message}`);
        } finally {
          // Restore button
          button.disabled = false;
          button.innerHTML = "✨";
        }
      }
    });
  }

  // --- TTS SETTINGS ---
  const ttsVoiceSelect = document.getElementById("tts-voice-select");
  const ttsSpeedInput = document.getElementById("tts-speed-input");
  const ttsSpeedValue = document.getElementById("tts-speed-value");
  const ttsTestBtn = document.getElementById("tts-test-btn");
  const ttsStatusMessage = document.getElementById("tts-status-message");
  const ttsPresetSelect = document.getElementById("tts-preset-select"); // NEU
  const usePiperTtsCheckbox = document.getElementById("use-piper-tts");

  async function saveTtsSettings() {
    const settings = {
      voice: ttsVoiceSelect.value,
      speed: parseFloat(ttsSpeedInput.value),
      preset: ttsPresetSelect.value,
      use_piper_tts: usePiperTtsCheckbox.checked,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/api/tts/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (!response.ok) {
        throw new Error("Failed to save TTS settings");
      }
      const result = await response.json();
      ttsStatusMessage.textContent = "TTS-Einstellungen gespeichert.";
      ttsStatusMessage.style.color = "#10b981";
      initTTS(); // Re-initialize TTS to apply changes immediately
    } catch (error) {
      console.error("Error saving TTS settings:", error);
      ttsStatusMessage.textContent = "Fehler beim Speichern der TTS-Einstellungen.";
      ttsStatusMessage.style.color = "#b91c1c";
    }
  }

  async function loadTtsSettings() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts/settings`);
      const settings = await response.json();

      if (settings.voice && ttsVoiceSelect.querySelector(`option[value="${settings.voice}"]`)) {
        ttsVoiceSelect.value = settings.voice;
      }
      if (settings.speed) {
        ttsSpeedInput.value = settings.speed;
        ttsSpeedValue.textContent = settings.speed.toFixed(1);
      }
      if (settings.preset) {
        ttsPresetSelect.value = settings.preset;
      }
      if (settings.use_piper_tts) {
        usePiperTtsCheckbox.checked = settings.use_piper_tts;
      }
    } catch (error) {
      console.error("Error loading TTS settings:", error);
    }
  }

  async function loadTTSVoices() {
    try {
      // First, load the saved settings to know if we need to filter for Piper
      await loadTtsSettings();

      const response = await fetch(`${API_BASE_URL}/api/tts/voices`);
      const data = await response.json();
      let voices = data.voices || [];

      const usePiperTts = usePiperTtsCheckbox.checked;

      if (usePiperTts) {
        voices = voices.filter((voice) => voice.provider === "piper");
      }

      const currentVoice = ttsVoiceSelect.value;

      ttsVoiceSelect.innerHTML = "";
      voices.forEach((voice) => {
        const option = document.createElement("option");
        option.value = voice.id;
        option.textContent = `${voice.name} (${voice.lang.toUpperCase()})`;
        ttsVoiceSelect.appendChild(option);
      });

      // Restore selection if possible
      if (voices.find((v) => v.id === currentVoice)) {
        ttsVoiceSelect.value = currentVoice;
      } else if (usePiperTts) {
        const defaultPiperVoice = "piper_de_DE-thorsten-high";
        if (ttsVoiceSelect.querySelector(`option[value="${defaultPiperVoice}"]`)) {
          ttsVoiceSelect.value = defaultPiperVoice;
        }
      }

      // Populate TTS Presets
      const presets = ["assistenz", "diktat", "narration"];
      ttsPresetSelect.innerHTML = "";
      presets.forEach((preset) => {
        const option = document.createElement("option");
        option.value = preset;
        option.textContent = preset.charAt(0).toUpperCase() + preset.slice(1); // Capitalize first letter
        ttsPresetSelect.appendChild(option);
      });

      ttsStatusMessage.textContent = `${voices.length} Stimme(n) geladen.`;
      ttsStatusMessage.style.color = "#10b981";
    } catch (error) {
      console.error("Error loading TTS voices:", error);
      ttsStatusMessage.textContent = "Fehler beim Laden der Stimmen.";
      ttsStatusMessage.style.color = "#b91c1c";
    }
  }

  // Voice selection
  ttsVoiceSelect.addEventListener("change", saveTtsSettings);

  // Speed adjustment
  ttsSpeedInput.addEventListener("input", () => {
    ttsSpeedValue.textContent = parseFloat(ttsSpeedInput.value).toFixed(1);
    saveTtsSettings();
  });

  // Preset selection
  ttsPresetSelect.addEventListener("change", saveTtsSettings);

  // Piper TTS preference
  usePiperTtsCheckbox.addEventListener("change", async () => {
    await saveTtsSettings();
    await loadTTSVoices();

    // After reloading, check if the current selection is valid
    const selectedOption = ttsVoiceSelect.querySelector(`option[value="${ttsVoiceSelect.value}"]`);
    if (!selectedOption) {
      console.log("Invalid voice selection after filter change. Setting default Piper voice.");
      const defaultPiperVoice = "piper_de_DE-thorsten-high";
      if (ttsVoiceSelect.querySelector(`option[value="${defaultPiperVoice}"]`)) {
        ttsVoiceSelect.value = defaultPiperVoice;
        await saveTtsSettings(); // Save the new default selection
      }
    }
  });

  // Test button
  ttsTestBtn.addEventListener("click", async () => {
    const voice = ttsVoiceSelect.value;
    const speed = parseFloat(ttsSpeedInput.value);
    const preset = ttsPresetSelect.value; // NEU
    const testText = "Hallo, das ist eine Testausgabe der Text-zu-Sprache-Funktion.";

    if (!voice) {
      ttsStatusMessage.textContent = "Bitte wählen Sie eine Stimme aus.";
      ttsStatusMessage.style.color = "#b91c1c";
      return;
    }

    ttsTestBtn.disabled = true;
    ttsStatusMessage.textContent = "Generiere Audioausgabe...";
    ttsStatusMessage.style.color = "#3b82f6";

    try {
      const params = new URLSearchParams({
        text: testText,
        lang: "de",
        voice_id: voice, // NEU: voice_id statt voice
        speed: speed.toString(),
        fmt: "mp3",
        preset: preset, // NEU
      });

      const response = await fetch(`${API_BASE_URL}/api/tts/synthesize?${params.toString()}`, {
        method: "POST",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Synthesis failed");
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audio.play();

      audio.addEventListener("ended", () => {
        URL.revokeObjectURL(audioUrl);
      });

      ttsStatusMessage.textContent = "Testausgabe erfolgreich!";
      ttsStatusMessage.style.color = "#10b981";
    } catch (error) {
      console.error("TTS test error:", error);
      ttsStatusMessage.textContent = `Fehler: ${error.message}`;
      ttsStatusMessage.style.color = "#b91c1c";
    } finally {
      ttsTestBtn.disabled = false;
    }
  });

  // Load TTS voices when TTS tab is clicked
  const ttsNavLink = document.querySelector('.settings-nav-link[data-target="tts-section"]');
  if (ttsNavLink) {
    ttsNavLink.addEventListener("click", loadTTSVoices);
  }

  function showStyleProfileModal(collectionName, profile) {
    const modal = document.getElementById("style-profile-modal");
    const modalTitle = document.getElementById("style-profile-modal-title");
    const textarea = document.getElementById("style-profile-textarea");
    const saveBtn = document.getElementById("style-profile-save-btn");
    const cancelBtn = document.getElementById("style-profile-cancel-btn");
    const closeBtn = modal.querySelector(".close-button");
    const errorDiv = document.getElementById("style-profile-modal-error");

    modalTitle.textContent = `Stil-Profil für ${collectionName}`;
    textarea.value = JSON.stringify(profile, null, 2);
    errorDiv.textContent = "";
    modal.style.display = "block";

    const saveHandler = async () => {
      const updatedProfileStr = textarea.value;
      let updatedProfile;

      try {
        updatedProfile = JSON.parse(updatedProfileStr);
      } catch (error) {
        errorDiv.textContent = "Fehler: Das eingegebene JSON ist ungültig.";
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/styles/profiles`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            profile_key: collectionName,
            profile_data: updatedProfile,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Speichern fehlgeschlagen");
        }

        alert("Profil erfolgreich gespeichert!");
        modal.style.display = "none";
        // Remove event listeners to avoid duplicates
        saveBtn.removeEventListener("click", saveHandler);
        cancelBtn.removeEventListener("click", cancelHandler);
        closeBtn.removeEventListener("click", cancelHandler);
      } catch (error) {
        errorDiv.textContent = `Fehler: ${error.message}`;
      }
    };

    const cancelHandler = () => {
      modal.style.display = "none";
      // Remove event listeners to avoid duplicates
      saveBtn.removeEventListener("click", saveHandler);
      cancelBtn.removeEventListener("click", cancelHandler);
      closeBtn.removeEventListener("click", cancelHandler);
    };

    saveBtn.addEventListener("click", saveHandler);
    cancelBtn.addEventListener("click", cancelHandler);
    closeBtn.addEventListener("click", cancelHandler);
  }
});
