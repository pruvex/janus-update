import interact from 'interactjs';
import { API_BASE_URL } from './config.js';
import './personality-settings.js';

const appState = {
  currentView: 'chat',
  user_selections: {},
  last_active: {
    provider: 'openai',
    model: 'gpt-3.5-turbo'
  },
  model_catalog: {} // Will be loaded dynamically
};

let modelSelectionForm;
let backFromModelsBtn;
let modelList;

function formatCost(cost, suffix) {
  if (cost === 0) {
    return `0.00${suffix}`;
  }
  // Use toLocaleString for better formatting of small numbers
  return `${cost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}${suffix}`;
}

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
    const provider = appState.last_active.provider;
    const allowedModels = appState.user_selections[provider] || [];
        
    if (appState.model_catalog[provider]) {
      const filteredModels = appState.model_catalog[provider].filter(model => 
        allowedModels.includes(model.id) && model.type !== 'image'
      );

      filteredModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.cost_per_image ? formatCost(model.cost_per_image, '€/img') : (model.cost_per_token_input ? formatCost(model.cost_per_token_input * 1000000, '€/Mio. in') + ' / ' + formatCost(model.cost_per_token_output * 1000000, '€/Mio. out') : '')})${model.desc ? ' - ' + model.desc : ''}`;
        sidebarModelSelect.appendChild(option);
      });
    } else {
      console.warn(`No models found for provider: ${provider}`);
    }

    sidebarModelSelect.value = appState.last_active.model;
  }

  if (appState.currentView === 'chat') {
    chatView.style.display = 'block';
    settingsView.style.display = 'none';
  } else {
    chatView.style.display = 'none';
    settingsView.style.display = 'flex';
    // renderSettingsView(); // <-- DIESEN AUFRUF ENTFERNEN
  }
}



document.addEventListener('DOMContentLoaded', async () => {
  const settingsBtn = document.getElementById('settings-btn');
  console.log('settingsBtn found:', settingsBtn);

  settingsBtn.addEventListener('click', () => {
    console.log('Settings button clicked!');
    appState.currentView = 'settings';
    render();
    // Dispatch a custom event to notify settings.js
    document.dispatchEvent(new CustomEvent('show-settings'));
  });
  const backToChatBtn = document.getElementById('back-to-chat-btn');
  const sidebarProviderSelect = document.getElementById('provider-select');

    

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

  // Initialize global variables for settings view elements
  modelSelectionForm = document.getElementById('model-selection-form');
  backFromModelsBtn = document.getElementById('back-from-models-btn');
  modelList = document.getElementById('model-list');

    

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
    });

  function dragListener (event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

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

    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
  }

  function resizeListener (event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.deltaRect.left;
    let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.deltaRect.top;

    Object.assign(event.target.style, {
      width: `${event.rect.width}px`,
      height: `${event.rect.height}px`,
      left: `${x}px`,
      top: `${y}px`
    });

    Object.assign(event.target.dataset, { x, y });
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
        console.warn(`Attempt ${i + 1} failed for ${provider} with error:`, error, '. Retrying...');
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
      }
    }
    if (!success) {
      console.error(`Failed to load models for ${provider} after ${MAX_RETRIES} retries.`);
      appState.user_selections[provider] = []; // Default to empty if all retries fail
    }
  }
}




