import '../css/settings.css';
import { API_BASE_URL } from './config.js';
import { initTTS } from './tts.js';

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

export async function updateActivePersonalityDisplay() {
  const activePersonalityDisplay = document.getElementById('active-personality-display');
  if (!activePersonalityDisplay) return;

  try {
    // Get active personality ID
    const activeResponse = await fetch(`${API_BASE_URL}/api/personalities/active`);
    const activeData = await activeResponse.json();
    const activePersonalityId = activeData.active_personality_id;

    // Get all personalities to find the name
    const allPersonalitiesResponse = await fetch(`${API_BASE_URL}/api/personalities`);
    const allPersonalities = await allPersonalitiesResponse.json();

    const activePersonality = allPersonalities.find(p => p.id === activePersonalityId);

    if (activePersonality) {
      activePersonalityDisplay.textContent = `(${activePersonality.name})`;
    } else {
      activePersonalityDisplay.textContent = '';
    }
  } catch (error) {
    console.error('Error updating active personality display:', error);
    activePersonalityDisplay.textContent = ''; // Clear on error
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
  updateActivePersonalityDisplay(); // Initial call to display active personality

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

  // --- RAG WISSENSBASIS-VERWALTUNG ---
  const ragFolderPathInput = document.getElementById('rag-folder-path-input');
  const ragIndexFolderBtn = document.getElementById('rag-index-folder-btn');
  const ragStatusMessage = document.getElementById('rag-status-message');
  const collectionSelect = document.getElementById('rag-collection-select');
  const newCollectionNameInput = document.getElementById('rag-new-collection-name-input');
  const progressContainer = document.getElementById('rag-progress-container');
  const progressText = document.getElementById('rag-progress-text');
  const progressBar = document.getElementById('rag-progress-bar');
  let pollingInterval = null;

  async function loadCollections() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/collections`);
      const data = await response.json();
      const currentSelection = collectionSelect.value;
      collectionSelect.innerHTML = '';
            
      const newOption = document.createElement('option');
      newOption.value = '__new__';
      newOption.textContent = 'Neue Bibliothek erstellen...';
      collectionSelect.appendChild(newOption);

      if (data.collections) {
        data.collections.forEach(name => {
          const option = document.createElement('option');
          option.value = name;
          option.textContent = name;
          collectionSelect.appendChild(option);
        });
      }
      // Stelle die vorherige Auswahl wieder her, falls möglich
      if (currentSelection && collectionSelect.querySelector(`option[value="${currentSelection}"]`)) {
        collectionSelect.value = currentSelection;
      }
      handleCollectionChange();
    } catch (error) { console.error('Fehler beim Laden der Wissens-Bibliotheken:', error); }
  }

  function handleCollectionChange() {
    newCollectionNameInput.style.display = collectionSelect.value === '__new__' ? 'block' : 'none';
  }

  collectionSelect.addEventListener('change', handleCollectionChange);

  function getSelectedCollectionName() {
    return collectionSelect.value === '__new__' ? newCollectionNameInput.value.trim() : collectionSelect.value;
  }

  async function updateProgress() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/indexing-status`);
      if (!response.ok) throw new Error(`Server-Fehler: ${response.status}`);
      const status = await response.json();

      if (status.in_progress) {
        progressContainer.style.display = 'block';
        if (status.total_files > 0) {
          progressBar.max = status.total_files;
          progressBar.value = status.processed_files;
          progressText.textContent = `[${status.processed_files}/${status.total_files}] Verarbeite: ${status.current_file || '...'}`;
        } else {
          progressText.textContent = 'Berechne Dateien...';
        }
      } else {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        progressContainer.style.display = 'none';
        ragStatusMessage.textContent = status.message || 'Prozess beendet.';
        ragStatusMessage.style.color = '#10b981';
        ragIndexFolderBtn.disabled = false;
        loadCollections();
      }
    } catch (error) {
      console.error('Fehler beim Abrufen des Indexierungsstatus:', error);
      ragStatusMessage.textContent = `Fehler beim Abruf des Status: ${error.message}`;
      ragStatusMessage.style.color = '#b91c1c';
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
      ragIndexFolderBtn.disabled = false;
    }
  }
    
  ragIndexFolderBtn.addEventListener('click', async () => {
    const path = ragFolderPathInput.value.trim();
    const collectionName = getSelectedCollectionName();
    if (!path || !collectionName) {
      alert('Bitte geben Sie einen Ordnerpfad UND einen gültigen Bibliotheksnamen an.');
      return;
    }
    if (pollingInterval) clearInterval(pollingInterval);

    ragIndexFolderBtn.disabled = true;
    ragStatusMessage.textContent = 'Indexierung wird gestartet...';
    ragStatusMessage.style.color = '#3b82f6';
    progressContainer.style.display = 'block';
    progressText.textContent = 'Initialisiere...';
    progressBar.value = 0;

    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/index-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, collection_name: collectionName })
      });
      const result = await response.json();
      if (response.ok) {
        ragStatusMessage.textContent = result.message;
        setTimeout(() => {
          updateProgress();
          pollingInterval = setInterval(updateProgress, 2000);
        }, 1000);
      } else {
        throw new Error(result.detail || 'Fehler beim Starten.');
      }
    } catch (error) {
      ragStatusMessage.textContent = `Fehler: ${error.message}`;
      ragStatusMessage.style.color = '#b91c1c';
      ragIndexFolderBtn.disabled = false;
      progressContainer.style.display = 'none';
    }
  });

  // Sorge dafür, dass die Sammlungen geladen werden, wenn der Tab geklickt wird
  const ragNavLink = document.querySelector('.settings-nav-link[data-target="rag-management-section"]');
  if(ragNavLink) {
    ragNavLink.addEventListener('click', loadCollections);
  }

  // --- TTS SETTINGS ---
  const ttsVoiceSelect = document.getElementById('tts-voice-select');
  const ttsSpeedInput = document.getElementById('tts-speed-input');
  const ttsSpeedValue = document.getElementById('tts-speed-value');
  const ttsTestBtn = document.getElementById('tts-test-btn');
    const ttsStatusMessage = document.getElementById('tts-status-message');
    const ttsPresetSelect = document.getElementById('tts-preset-select'); // NEU
    const usePiperTtsCheckbox = document.getElementById('use-piper-tts');
  
    async function saveTtsSettings() {
      const settings = {
        voice: ttsVoiceSelect.value,
        speed: parseFloat(ttsSpeedInput.value),
        preset: ttsPresetSelect.value,
        use_piper_tts: usePiperTtsCheckbox.checked
      };
  
      try {
        const response = await fetch(`${API_BASE_URL}/api/tts/settings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(settings)
        });
        if (!response.ok) {
          throw new Error('Failed to save TTS settings');
        }
        const result = await response.json();
        ttsStatusMessage.textContent = 'TTS-Einstellungen gespeichert.';
        ttsStatusMessage.style.color = '#10b981';
        initTTS(); // Re-initialize TTS to apply changes immediately
      } catch (error) {
        console.error('Error saving TTS settings:', error);
        ttsStatusMessage.textContent = 'Fehler beim Speichern der TTS-Einstellungen.';
        ttsStatusMessage.style.color = '#b91c1c';
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
        console.error('Error loading TTS settings:', error);
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
        voices = voices.filter(voice => voice.provider === 'piper');
      }

      const currentVoice = ttsVoiceSelect.value;

      ttsVoiceSelect.innerHTML = '';
      voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice.id;
        option.textContent = `${voice.name} (${voice.lang.toUpperCase()})`;
        ttsVoiceSelect.appendChild(option);
      });

      // Restore selection if possible
      if (voices.find(v => v.id === currentVoice)) {
        ttsVoiceSelect.value = currentVoice;
      } else if (usePiperTts) {
        const defaultPiperVoice = 'piper_de_DE-thorsten-high';
        if (ttsVoiceSelect.querySelector(`option[value="${defaultPiperVoice}"]`)) {
          ttsVoiceSelect.value = defaultPiperVoice;
        }
      }
      
      // Populate TTS Presets
      const presets = ["assistenz", "diktat", "narration"];
      ttsPresetSelect.innerHTML = '';
      presets.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset;
        option.textContent = preset.charAt(0).toUpperCase() + preset.slice(1); // Capitalize first letter
        ttsPresetSelect.appendChild(option);
      });
      
      ttsStatusMessage.textContent = `${voices.length} Stimme(n) geladen.`;
      ttsStatusMessage.style.color = '#10b981';

    } catch (error) {
      console.error('Error loading TTS voices:', error);
      ttsStatusMessage.textContent = 'Fehler beim Laden der Stimmen.';
      ttsStatusMessage.style.color = '#b91c1c';
    }
  }



  // Voice selection
  ttsVoiceSelect.addEventListener('change', saveTtsSettings);

  // Speed adjustment
  ttsSpeedInput.addEventListener('input', () => {
    ttsSpeedValue.textContent = parseFloat(ttsSpeedInput.value).toFixed(1);
    saveTtsSettings();
  });

  // Preset selection
  ttsPresetSelect.addEventListener('change', saveTtsSettings);

  // Piper TTS preference
  usePiperTtsCheckbox.addEventListener('change', async () => {
    await saveTtsSettings();
    await loadTTSVoices();

    // After reloading, check if the current selection is valid
    const selectedOption = ttsVoiceSelect.querySelector(`option[value="${ttsVoiceSelect.value}"]`);
    if (!selectedOption) {
        console.log('Invalid voice selection after filter change. Setting default Piper voice.');
        const defaultPiperVoice = 'piper_de_DE-thorsten-high';
        if (ttsVoiceSelect.querySelector(`option[value="${defaultPiperVoice}"]`)) {
            ttsVoiceSelect.value = defaultPiperVoice;
            await saveTtsSettings(); // Save the new default selection
        }
    }
  });

  // Test button
  ttsTestBtn.addEventListener('click', async () => {
    const voice = ttsVoiceSelect.value;
    const speed = parseFloat(ttsSpeedInput.value);
    const preset = ttsPresetSelect.value; // NEU
    const testText = 'Hallo, das ist eine Testausgabe der Text-zu-Sprache-Funktion.';
    
    if (!voice) {
      ttsStatusMessage.textContent = 'Bitte wählen Sie eine Stimme aus.';
      ttsStatusMessage.style.color = '#b91c1c';
      return;
    }
    
    ttsTestBtn.disabled = true;
    ttsStatusMessage.textContent = 'Generiere Audioausgabe...';
    ttsStatusMessage.style.color = '#3b82f6';
    
    try {
      const params = new URLSearchParams({
        text: testText,
        lang: 'de',
        voice_id: voice, // NEU: voice_id statt voice
        speed: speed.toString(),
        fmt: 'mp3',
        preset: preset // NEU
      });
      
      const response = await fetch(`${API_BASE_URL}/api/tts/synthesize?${params.toString()}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Synthesis failed');
      }
      
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audio.play();
      
      audio.addEventListener('ended', () => {
        URL.revokeObjectURL(audioUrl);
      });
      
      ttsStatusMessage.textContent = 'Testausgabe erfolgreich!';
      ttsStatusMessage.style.color = '#10b981';
    } catch (error) {
      console.error('TTS test error:', error);
      ttsStatusMessage.textContent = `Fehler: ${error.message}`;
      ttsStatusMessage.style.color = '#b91c1c';
    } finally {
      ttsTestBtn.disabled = false;
    }
  });

  // Load TTS voices when TTS tab is clicked
  const ttsNavLink = document.querySelector('.settings-nav-link[data-target="tts-section"]');
  if (ttsNavLink) {
    ttsNavLink.addEventListener('click', loadTTSVoices);
  }
});
