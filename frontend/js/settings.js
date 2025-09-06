import '../css/settings.css';
import { API_BASE_URL } from './config.js';

const appState = { // Minimal appState for settings
    model_catalog: {},
    user_selections: {}
};

// --- DOM Elements ---
const settingsNav = document.getElementById('settings-nav');
const navLinks = document.querySelectorAll('.settings-nav-link');
const contentSections = document.querySelectorAll('.settings-section');
const apiKeyForm = document.getElementById('api-key-form');
const providerInput = document.getElementById('provider-input');
const apiKeyInput = document.getElementById('api-key-input');
const apiKeyList = document.getElementById('api-key-list');
const modelManagementButtons = document.getElementById('model-management-buttons');
const modelSelectionForm = document.getElementById('model-selection-form');
const modelList = document.getElementById('model-list');
const backFromModelsBtn = document.getElementById('back-from-models-btn');
const workspacesList = document.getElementById('workspaces-list');
const addWorkspaceBtn = document.getElementById('add-workspace-btn');

// --- Functions ---

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

async function loadApiKeys() {
    apiKeyList.innerHTML = '';
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`);
        const data = await response.json();
        for (const provider in data.api_keys) {
            const listItem = document.createElement('li');
            listItem.textContent = `Provider: ${provider}, Key: ****`;
            apiKeyList.appendChild(listItem);
        }
    } catch (error) {
        console.error('Error loading API keys:', error);
    }
}

async function renderSettingsView() {
    setActiveSettingsSection('api-key-section');
    await loadApiKeys();

    modelManagementButtons.innerHTML = '';
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`);
        const data = await response.json();
        for (const provider in data.api_keys) {
            const manageModelsBtn = document.createElement('button');
            manageModelsBtn.textContent = `Modelle für ${provider} verwalten`;
            manageModelsBtn.dataset.provider = provider;
            modelManagementButtons.appendChild(manageModelsBtn);
        }
    } catch (error) {
        console.error('Error loading providers for model management buttons:', error);
    }
}

async function renderModelManagementView(provider) {
    setActiveSettingsSection('model-management-section');
    document.querySelector('#model-management-section h3').textContent = `Modelle für ${provider} verwalten`;
    modelList.innerHTML = '';

    let selectedModels = [];
    try {
        const response = await fetch(`${API_BASE_URL}/api/models/selection/${provider}`);
        const data = await response.json();
        selectedModels = data.selected_models;
    } catch (error) {
        console.error('Error fetching selected models:', error);
    }

    appState.model_catalog[provider].forEach(model => {
        if (model.id === 'gpt-image-1') return;
        const listItem = document.createElement('li');
        const isChecked = selectedModels.includes(model.id) ? 'checked' : '';
        listItem.innerHTML = `<input type="checkbox" id="${model.id}" value="${model.id}" ${isChecked}> <label for="${model.id}">${model.name}</label>`;
        modelList.appendChild(listItem);
    });

    modelSelectionForm.dataset.provider = provider;
}

async function renderWorkspacesView() {
    setActiveSettingsSection('workspaces-section');
    workspacesList.innerHTML = '';
    try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces`);
        const data = await response.json();
        const workspaces = data.workspaces || [];
        if (workspaces.length === 0) {
            workspacesList.innerHTML = '<li>Keine Arbeitsverzeichnisse konfiguriert.</li>';
        } else {
            workspaces.forEach(path => {
                const listItem = document.createElement('li');
                listItem.textContent = path;
                const removeBtn = document.createElement('button');
                removeBtn.textContent = 'Entfernen';
                removeBtn.classList.add('remove-workspace-btn'); // Add a class for styling and event delegation
                removeBtn.dataset.path = path; // Store the path in a data attribute
                listItem.appendChild(removeBtn);
                workspacesList.appendChild(listItem);
            });
        }
    } catch (error) {
        console.error('Error loading workspaces:', error);
    }
}

// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', async () => {
    // Load initial data
    try {
        const response = await fetch(`${API_BASE_URL}/api/models/catalog`);
        const data = await response.json();
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

    // Listen for custom event to show settings
    document.addEventListener('show-settings', () => {
        renderSettingsView();
    });

    // Initial render
    renderSettingsView();

    // Navigation
    settingsNav.addEventListener('click', (e) => {
        const link = e.target.closest('.settings-nav-link');
        if (!link) return;
        e.preventDefault();
        const targetId = link.dataset.target;
        setActiveSettingsSection(targetId);
        if (targetId === 'workspaces-section') {
            renderWorkspacesView();
        }
    });

    // API Key Form
    apiKeyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = providerInput.value;
        const api_key = apiKeyInput.value;
        await fetch(`${API_BASE_URL}/api/keys`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, api_key }),
        });
        apiKeyInput.value = '';
        renderSettingsView();
    });

    // Model Management
    modelManagementButtons.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            const provider = e.target.dataset.provider;
            renderModelManagementView(provider);
        }
    });

    modelSelectionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = modelSelectionForm.dataset.provider;
        const checkboxes = modelList.querySelectorAll('input[type="checkbox"]:checked');
        const newSelection = Array.from(checkboxes).map(cb => cb.value);
        await fetch(`${API_BASE_URL}/api/models/selection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: provider, models: newSelection }),
        });
        renderSettingsView();
    });

    backFromModelsBtn.addEventListener('click', () => {
        renderSettingsView();
    });

    // Workspaces
    addWorkspaceBtn.addEventListener('click', async () => {
        const path = await window.electron.openDirectoryDialog();
        if (path) {
            await fetch(`${API_BASE_URL}/api/workspaces/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path }),
            });
            renderWorkspacesView();
        }
    });

    workspacesList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('remove-workspace-btn')) {
            const pathToRemove = e.target.dataset.path;
            await fetch(`${API_BASE_URL}/api/workspaces/remove`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: pathToRemove }),
            });
            renderWorkspacesView();
        }
    });
});