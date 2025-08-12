import interact from 'interactjs';

const appState = {
    currentView: 'chat',
    user_selections: {},
    last_active: {
        provider: 'openai',
        model: 'gpt-3.5-turbo'
    }
};

function render() {
    const chatView = document.getElementById('chat-view');
    const settingsView = document.getElementById('settings-view');
    console.log('render: currentView =', appState.currentView);
    console.log('render: chatView =', chatView, 'settingsView =', settingsView);

    const sidebarProviderSelect = document.getElementById('provider-select');
    const sidebarModelSelect = document.getElementById('model-select');

    if (sidebarProviderSelect && sidebarModelSelect) {
        console.log('render: appState.user_selections:', appState.user_selections);
        // Update sidebar provider dropdown
        sidebarProviderSelect.value = appState.last_active.provider;

        // Populate sidebar model dropdown based on selected provider
        sidebarModelSelect.innerHTML = ''; // Clear existing options
        const provider = appState.last_active.provider;
        console.log('render: Current Provider:', provider);
        const allowedModels = appState.user_selections[provider] || [];
        console.log('render: Allowed Models (from user_selections):', allowedModels);
        const filteredModels = MODEL_CATALOG[provider].filter(model => allowedModels.includes(model.id));
        console.log('render: Filtered Models (from MODEL_CATALOG):', filteredModels);

        filteredModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = `${model.name} (${model.price}) - ${model.desc}`;
            sidebarModelSelect.appendChild(option);
        });
        // Ensure the selected model is still valid after filtering
        if (filteredModels.length > 0 && !allowedModels.includes(appState.last_active.model)) {
            appState.last_active.model = filteredModels[0].id;
        } else if (filteredModels.length === 0) {
            appState.last_active.model = ''; // No models available
        }
        console.log('render: Final appState.last_active.model:', appState.last_active.model);
        sidebarModelSelect.value = appState.last_active.model;
    }

    if (appState.currentView === 'chat') {
        chatView.style.display = 'block';
        settingsView.style.display = 'none';
    } else {
        chatView.style.display = 'none';
        settingsView.style.display = 'block';
        renderSettingsView();
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const settingsBtn = document.getElementById('settings-btn');
    console.log('settingsBtn found:', settingsBtn);

    settingsBtn.addEventListener('click', () => {
        console.log('Settings button clicked!');
        appState.currentView = 'settings';
        render();
    });
    const backToChatBtn = document.getElementById('back-to-chat-btn');
    const sidebarProviderSelect = document.getElementById('provider-select');

    settingsBtn.addEventListener('click', () => {
        appState.currentView = 'settings';
        render();
    });

    backToChatBtn.addEventListener('click', () => {
        appState.currentView = 'chat';
        render();
    });

    sidebarProviderSelect.addEventListener('change', () => {
        appState.last_active.provider = sidebarProviderSelect.value;
        render();
    });

    const sidebarModelSelect = document.getElementById('model-select');
    sidebarModelSelect.addEventListener('change', () => {
        appState.last_active.model = sidebarModelSelect.value;
    });

    await loadUserSelections(); // Load selections before initial render
    render(); // Initial render

    // --- interact.js logic ---
    interact('.chat-window')
      .draggable({
        allowFrom: '#chat-header',
        inertia: true,
        listeners: {
          start (event) {
            const target = event.target;
            // Initialize data-x and data-y with the current position relative to its offsetParent
            target.setAttribute('data-x', target.offsetLeft);
            target.setAttribute('data-y', target.offsetTop);
            console.log(`Drag Start: initialX=${target.offsetLeft}, initialY=${target.offsetTop}`);
          },
          move: dragMoveListener,
        }
      })
      .resizable({
        edges: { left: true, right: true, bottom: true, top: true },
        inertia: true,
        // NEU: Fügt die Größenbeschränkung hinzu
        modifiers: [
          interact.modifiers.restrictSize({
            min: { width: 300, height: 200 }
          })
        ],
        listeners: {
          move (event) {
            let { x, y } = event.target.dataset

            x = (parseFloat(x) || 0) + event.deltaRect.left
            y = (parseFloat(y) || 0) + event.deltaRect.top

            Object.assign(event.target.style, {
              width: `${event.rect.width}px`,
              height: `${event.rect.height}px`,
              left: `${x}px`,
              top: `${y}px`
            })

            Object.assign(event.target.dataset, { x, y })
          }
        }
      })

    function dragMoveListener (event) {
      const target = event.target
      let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx
      let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy

      // Get window and sidebar dimensions
      const sidebarWidth = 250; // From styles.css
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;

      // Get chat window dimensions
      const chatWindowWidth = target.offsetWidth;
      const chatWindowHeight = target.offsetHeight;

      // Get chatView dimensions (parent of chat-window)
      const chatView = document.getElementById('chat-view');
      const chatViewRect = chatView.getBoundingClientRect();

      // Clamp x position
      x = Math.max(0, Math.min(x, chatViewRect.width - chatWindowWidth));

      // Clamp y position
      y = Math.max(0, Math.min(y, chatViewRect.height - chatWindowHeight));

      target.style.left = `${x}px`;
      target.style.top = `${y}px`;

      target.setAttribute('data-x', x)
      target.setAttribute('data-y', y)
    }
});

async function loadUserSelections() {
    const availableProviders = ["openai", "gemini"];
    const MAX_RETRIES = 5;
    const RETRY_DELAY_MS = 1000; // 1 second delay

    for (const provider of availableProviders) {
        let success = false;
        for (let i = 0; i < MAX_RETRIES; i++) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
                if (!response.ok) {
                    console.warn(`Attempt ${i + 1} failed for ${provider}: ${response.status} ${response.statusText}. Retrying...`);
                    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                    continue;
                }
                const data = await response.json();
                appState.user_selections[provider] = data.selected_models;
                console.log(`loadUserSelections: Provider: ${provider}, Selected Models:`, data.selected_models);
                success = true;
                break; // Exit retry loop on success
            } catch (error) {
                console.warn(`Attempt ${i + 1} failed for ${provider} with error:`, error, `. Retrying...`);
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
            }
        }
        if (!success) {
            console.error(`Failed to load models for ${provider} after ${MAX_RETRIES} retries.`);
            appState.user_selections[provider] = []; // Default to empty if all retries fail
        }
    }
}

async function renderSettingsView() {
    await loadUserSelections(); // Ensure user_selections is up-to-date
    const settingsView = document.getElementById('settings-view');
    settingsView.innerHTML = `
        <div class="settings-content">
            <h2>Einstellungen</h2>
            <form id="api-key-form">
                <select id="provider-input">
                    <option value="openai">OpenAI</option>
                    <option value="gemini">Gemini</option>
                </select>
                <input type="password" id="api-key-input" placeholder="API Key">
                <button type="submit">Speichern</button>
            </form>
            <h3>Gespeicherte API Keys</h3>
            <ul id="api-key-list"></ul>
            <h3>Modellverwaltung</h3>
            <div id="model-management-buttons"></div>
            <button id="back-to-chat-btn">Zurück zum Chat</button>
        </div>
    `;

    // Re-attach event listeners for dynamically created elements
    document.getElementById('back-to-chat-btn').addEventListener('click', () => {
        appState.currentView = 'chat';
        render();
    });

    // Load API Keys and add model management buttons
    const apiKeyList = document.getElementById('api-key-list');
    const modelManagementButtons = document.getElementById('model-management-buttons');

    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`);
        const data = await response.json();

        for (const provider in data.api_keys) {
            const listItem = document.createElement('li');
            listItem.textContent = `Provider: ${provider}, Key: ****`;
            apiKeyList.appendChild(listItem);

            const manageModelsBtn = document.createElement('button');
            manageModelsBtn.textContent = `Modelle für ${provider} verwalten`;
            manageModelsBtn.addEventListener('click', () => renderModelManagementView(provider));
            modelManagementButtons.appendChild(manageModelsBtn);
        }
    } catch (error) {
    }

    // Re-attach API Key form submit listener (from settings.js)
    const apiKeyForm = document.getElementById('api-key-form');
    const providerInput = document.getElementById('provider-input');
    const apiKeyInput = document.getElementById('api-key-input');

    apiKeyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = providerInput.value;
        const api_key = apiKeyInput.value;

        try {
            await fetch(`${API_BASE_URL}/api/keys`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ provider, api_key }),
            });
            apiKeyInput.value = '';
            renderSettingsView(); // Reload settings view to show new key
        } catch (error) {
        }
    });
}



async function renderModelManagementView(provider) {
    const settingsView = document.getElementById('settings-view');
    settingsView.innerHTML = `
        <div class="settings-content">
            <h2>Modelle für ${provider} verwalten</h2>
            <form id="model-selection-form">
                <ul id="model-list"></ul>
                <button type="submit">Auswahl speichern</button>
                <button type="button" id="back-from-models-btn">Zurück</button>
            </form>
        </div>
    `;

    const modelList = document.getElementById('model-list');
    const backFromModelsBtn = document.getElementById('back-from-models-btn');
    const modelSelectionForm = document.getElementById('model-selection-form');

    backFromModelsBtn.addEventListener('click', () => {
        renderSettingsView();
    });

    // Fetch selected models from backend
    let selectedModels = [];
    try {
        const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
        const data = await response.json();
        selectedModels = data.selected_models;
    } catch (error) {
    }

    // Populate model list
    MODEL_CATALOG[provider].forEach(model => {
        const listItem = document.createElement('li');
        const isChecked = selectedModels.includes(model.id) ? 'checked' : '';
        listItem.innerHTML = `
            <input type="checkbox" id="${model.id}" value="${model.id}" ${isChecked}>
            <label for="${model.id}">${model.name} (${model.price}) - ${model.desc}</label>
        `;
        modelList.appendChild(listItem);
    });

    // Handle form submission
    modelSelectionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const checkboxes = modelList.querySelectorAll('input[type="checkbox"]:checked');
        const newSelection = Array.from(checkboxes).map(cb => cb.value);

        try {
            await fetch(`${API_BASE_URL}/api/models/selection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ provider: provider, models: newSelection }),
            });
            renderSettingsView(); // Go back to main settings view
        } catch (error) {
        }
    });
}