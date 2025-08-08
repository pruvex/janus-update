const appState = {
    currentView: 'chat'
};

function render() {
    const chatView = document.getElementById('chat-view');
    const settingsView = document.getElementById('settings-view');

    if (appState.currentView === 'chat') {
        chatView.style.display = 'block';
        settingsView.style.display = 'none';
    } else {
        chatView.style.display = 'none';
        settingsView.style.display = 'block';
        renderSettingsView();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const settingsBtn = document.getElementById('settings-btn');
    const backToChatBtn = document.getElementById('back-to-chat-btn');

    settingsBtn.addEventListener('click', () => {
        appState.currentView = 'settings';
        render();
    });

    backToChatBtn.addEventListener('click', () => {
        appState.currentView = 'chat';
        render();
    });

    render(); // Initial render
});

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
        console.error('Error loading API keys or rendering settings view:', error);
        alert(`Fehler beim Laden der API-Keys oder Rendern der Einstellungen: ${error.message}`);
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
            alert('Fehler beim Speichern des API-Keys.');
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
        console.error('Error fetching selected models:', error);
        alert(`Fehler beim Laden der Modell-Auswahl: ${error.message}`);
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
            console.error('Error saving model selection:', error);
            alert(`Fehler beim Speichern der Modell-Auswahl: ${error.message}`);
        }
    });
}