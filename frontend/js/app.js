import interact from 'interactjs';
import { API_BASE_URL } from './config.js';

const appState = {
    currentView: 'chat',
    user_selections: {},
    last_active: {
        provider: 'openai',
        model: 'gpt-3.5-turbo'
    },
    model_catalog: {} // Will be loaded dynamically
};

function formatCost(cost, suffix) {
    if (cost === 0) {
        return `0.00${suffix}`;
    }
    // Use toLocaleString for better formatting of small numbers
    return `${cost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}${suffix}`;
}

function render() {
    console.log('app.js: render() called');
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
        console.log(`app.js: render() - Set sidebarProviderSelect.value to ${appState.last_active.provider}`);

        // Populate sidebar model dropdown based on selected provider
        sidebarModelSelect.innerHTML = ''; // Clear existing options
        const provider = appState.last_active.provider;
        console.log('render: Current Provider:', provider);
        console.log('render: Model Catalog:', appState.model_catalog);
        const allowedModels = appState.user_selections[provider] || [];
        console.log('render: Allowed Models (from user_selections):', allowedModels);
        
        if (appState.model_catalog[provider]) {
            const filteredModels = appState.model_catalog[provider].filter(model => 
                allowedModels.includes(model.id) && model.type !== 'image'
            );
            console.log('render: Filtered Models (from MODEL_CATALOG):', filteredModels);

            filteredModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${model.cost_per_image ? formatCost(model.cost_per_image, '€/img') : (model.cost_per_token_input ? formatCost(model.cost_per_token_input * 1000000, '€/Mio. in') + ' / ' + formatCost(model.cost_per_token_output * 1000000, '€/Mio. out') : '')})${model.desc ? ' - ' + model.desc : ''}`;
                sidebarModelSelect.appendChild(option);
            });
        } else {
            console.warn(`No models found for provider: ${provider}`);
        }

        console.log('render: Final appState.last_active.model:', appState.last_active.model);
        sidebarModelSelect.value = appState.last_active.model;
        console.log(`app.js: render() - Set sidebarModelSelect.value to ${appState.last_active.model}`);
    }

    if (appState.currentView === 'chat') {
        chatView.style.display = 'block';
        settingsView.style.display = 'none';
    } else {
        chatView.style.display = 'none';
        settingsView.style.display = 'flex';
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

    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const appContainer = document.querySelector('.app-container');

    toggleSidebarBtn.addEventListener('click', () => {
        appContainer.classList.toggle('sidebar-collapsed');
        if (appContainer.classList.contains('sidebar-collapsed')) {
            toggleSidebarBtn.textContent = '▶';
        } else {
            toggleSidebarBtn.textContent = '◀';
        }
    });

    sidebarProviderSelect.addEventListener('change', () => {
        appState.last_active.provider = sidebarProviderSelect.value;
        const provider = appState.last_active.provider;
        const allowedModels = appState.user_selections[provider] || [];
        const filteredModels = appState.model_catalog[provider].filter(model => allowedModels.includes(model.id));
        if (filteredModels.length > 0) {
            appState.last_active.model = filteredModels[0].id;
        } else {
            appState.last_active.model = '';
        }
        render();
    });

    const sidebarModelSelect = document.getElementById('model-select');
    sidebarModelSelect.addEventListener('change', () => {
        appState.last_active.model = sidebarModelSelect.value;
        render();
    });

    await loadModelCatalog();
    await loadLastUsedModel();
    await loadUserSelections(); // Load selections before initial render
    render(); // Initial render

    // Attach API Key form submit listener once
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

    // Attach event listeners for model management buttons once
    // These buttons are dynamically created within renderSettingsView, so we need event delegation
    const modelManagementButtonsContainer = document.getElementById('model-management-buttons');
    modelManagementButtonsContainer.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            const provider = e.target.dataset.provider; // Assuming you add data-provider attribute to buttons
            renderModelManagementView(provider);
        }
    });

    // --- interact.js logic ---

    // NEW: Settings navigation logic
    const settingsNav = document.getElementById('settings-nav');
    const navLinks = document.querySelectorAll('.settings-nav-link');
    const contentSections = document.querySelectorAll('.settings-section');

    function setActiveSettingsSection(targetId) {
        navLinks.forEach(navLink => navLink.classList.remove('active-setting'));
        const activeLink = document.querySelector(`.settings-nav-link[data-target="${targetId}"]`);
        if (activeLink) {
            activeLink.classList.add('active-setting');
        }

        contentSections.forEach(section => {
            section.style.display = 'none';
        });

        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
    }

    settingsNav.addEventListener('click', (e) => {
        const link = e.target.closest('.settings-nav-link');
        if (!link) return;
        
        e.preventDefault();
        const targetId = link.dataset.target;
        setActiveSettingsSection(targetId);
    });

    // Initial call to set active section when settings view is first rendered
    // This will be called by renderSettingsView() and renderModelManagementView()

    interact('.chat-window')
      .draggable({
        allowFrom: '#chat-header',
        inertia: true,
        listeners: {
          start (event) {
            const target = event.target;
            target.setAttribute('data-x', target.offsetLeft);
            target.setAttribute('data-y', target.offsetTop);
            console.log(`Drag Start: initialX=${target.offsetLeft}, initialY=${target.offsetTop}`);
          },
          move: dragListener,
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
          move: resizeListener
        }
      })

    function dragListener (event) {
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

    function resizeListener (event) {
      const target = event.target
      let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.deltaRect.left
      let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.deltaRect.top

      Object.assign(event.target.style, {
        width: `${event.rect.width}px`,
        height: `${event.rect.height}px`,
        left: `${x}px`,
        top: `${y}px`
      })

      Object.assign(event.target.dataset, { x, y })
    }
});

async function loadModelCatalog() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/models/catalog`);
        const data = await response.json();
        // Transform the array into an object for easier lookup by provider
        const catalogByProvider = {};
        data.forEach(model => {
            if (!catalogByProvider[model.provider]) {
                catalogByProvider[model.provider] = [];
            }
            catalogByProvider[model.provider].push(model);
        });
        appState.model_catalog = catalogByProvider;
    } catch (error) {
        console.error('Failed to load model catalog:', error);
    }
}

async function loadLastUsedModel() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/last-used-model`);
        const data = await response.json();
        appState.last_active.provider = data.provider;
        appState.last_active.model = data.model;
    } catch (error) {
        console.error('Failed to load last used model:', error);
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
                    console.warn(`Attempt ${i + 1} failed for ${provider}: ${response.status} ${response.statusText}. Retrying...`);
                    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                    continue;
                }
                const data = await response.json();
                appState.user_selections[provider] = data.selected_models;
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

    // Set active navigation link and show API Key section
    setActiveSettingsSection('api-key-section');

    // Load API Keys
    const apiKeyList = document.getElementById('api-key-list');
    if (apiKeyList) { // Check if element exists
        apiKeyList.innerHTML = ''; // Clear existing list items
        try {
            const response = await fetch(`${API_BASE_URL}/api/keys`);
            const data = await response.json();

            for (const provider in data.api_keys) {
                const listItem = document.createElement('li');
                listItem.textContent = `Provider: ${provider}, Key: ****`;
                apiKeyList.appendChild(listItem);
            }
        } catch (error) {
        }
    }

    // Re-attach API Key form submit listener
    const apiKeyForm = document.getElementById('api-key-form');
    if (apiKeyForm && !apiKeyForm.dataset.listenerAttached) { // Check if element exists and listener not attached
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
        apiKeyForm.dataset.listenerAttached = 'true'; // Mark listener as attached
    }

    // Attach event listeners for model management buttons
    const modelManagementButtons = document.getElementById('model-management-buttons');
    if (modelManagementButtons) { // Check if element exists
        modelManagementButtons.innerHTML = ''; // Clear existing buttons
        try {
            const response = await fetch(`${API_BASE_URL}/api/keys`); // Re-fetch keys to get providers
            const data = await response.json();

            for (const provider in data.api_keys) {
                const manageModelsBtn = document.createElement('button');
                manageModelsBtn.textContent = `Modelle für ${provider} verwalten`;
                manageModelsBtn.dataset.provider = provider; // Add data-provider attribute
                // Event listener is now attached via delegation in DOMContentLoaded
                modelManagementButtons.appendChild(manageModelsBtn);
            }
        } catch (error) {
        }
    }
}



async function renderModelManagementView(provider) {
    // Set active navigation link and show Model Management section
    setActiveSettingsSection('model-management-section');

    // Update the title of the model management section
    document.querySelector('#model-management-section h3').textContent = `Modelle für ${provider} verwalten`;

    const modelList = document.getElementById('model-list');
    modelList.innerHTML = ''; // Clear existing list items

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
    appState.model_catalog[provider].forEach(model => {
        // Exclude 'gpt-image-1' from the selection list as it's a tool-called model
        if (model.id === 'gpt-image-1') {
            return;
        }
        const listItem = document.createElement('li');
        const isChecked = selectedModels.includes(model.id) ? 'checked' : '';
        listItem.innerHTML = `
            <input type="checkbox" id="${model.id}" value="${model.id}" ${isChecked}>
            <label for="${model.id}">${model.name} (${model.cost_per_image ? formatCost(model.cost_per_image, '€/img') : (model.cost_per_token_input ? formatCost(model.cost_per_token_input * 1000000, '€/Mio. in') + ' / ' + formatCost(model.cost_per_token_output * 1000000, '€/Mio. out') : '')})${model.desc ? ' - ' + model.desc : ''}</label>
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



