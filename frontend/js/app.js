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
    const sidebarProviderSelect = document.getElementById('provider-select');
    const sidebarModelSelect = document.getElementById('model-select');

    if (sidebarProviderSelect && sidebarModelSelect) {
        // Update sidebar provider dropdown
        sidebarProviderSelect.value = appState.last_active.provider;

        // Populate sidebar model dropdown based on selected provider
        sidebarModelSelect.innerHTML = ''; // Clear existing options
        const selectedProviderModels = appState.user_selections[appState.last_active.provider] || [];
        selectedProviderModels.forEach(modelId => {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = modelId; // Display model ID for now
            sidebarModelSelect.appendChild(option);
        });
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
});

async function loadUserSelections() {
    const availableProviders = ["openai", "gemini"]; // Should come from backend eventually
    for (const provider of availableProviders) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
            const data = await response.json();
            appState.user_selections[provider] = data.selected_models;
        } catch (error) {
            appState.user_selections[provider] = []; // Default to empty if error
        }
    }
}

async function renderSettingsView() {
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

// Placeholder for MODEL_CATALOG - this should eventually come from the backend
const MODEL_CATALOG = {
    "openai": [
        { "id": "gpt-4o", "name": "GPT-4o", "price": "High", "description": "Latest flagship model" },
        { "id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "price": "Low", "description": "Fast and cost-effective" }
    ],
    "gemini": [
        { "id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "price": "Medium", "description": "Fast and versatile" },
        { "id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "price": "High", "description": "Advanced reasoning and multimodal" }
    ]
};

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
            <label for="${model.id}">${model.name} (${model.price}) - ${model.description}</label>
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