import { getDockBarHeightPx } from './dock.js';
import {
  dockClose,
  dockMinimize,
  dockOpen,
  getDockModuleState,
  subscribeWindowState,
} from './window-state.js';
import { openModal, closeModal, bringToFront } from './modal-api.js';
import { appState } from './modules/image-studio/state.js';
import { getBackendBaseUrl, extractFilenameFromUrl } from './modules/image-studio/utils.js';
import { fetchPricingData, generateImageApi } from './modules/image-studio/api.js';
import { initExportModule, openExportModal } from './modules/image-studio/export.js';
import { 
    initPresetsModule, 
    updatePresetVisibility, 
    restorePresetSettings, 
    updateStylePreviewImage,
    togglePresetForEditUI,
    togglePresetForRefineUI,
    getSelectedPresetValues
} from './modules/image-studio/presets.js';
import { initInpaintingModule, toggleInpaintingUI, getMaskData, initCanvasSize } from './modules/image-studio/inpainting.js';

document.addEventListener('DOMContentLoaded', () => {
  let isInternalChange = false; // Sicherheits-Riegel gegen Endlosschleifen
  // --- Audio ---
  const shutterSound = new Audio();
  shutterSound.volume = 0.5;
  shutterSound.preload = 'auto';

  async function ensureShutterSoundLoaded() {
    if (appState.shutterSoundObjectUrl) return true;
    const backendBase = getBackendBaseUrl();
    const candidates = [
      `${backendBase}/api/system/camera_sound`,
      `${backendBase}/sounds/camera-shutter-199580.mp3`,
    ];
    for (const url of candidates) {
      try {
        const resp = await fetch(url, { cache: 'no-store' });
        if (!resp.ok) continue;
        const contentType = (resp.headers.get('content-type') || '').toLowerCase();
        const blob = await resp.blob();
        const blobType = (blob.type || '').toLowerCase();
        if (!contentType.startsWith('audio/') && !blobType.startsWith('audio/')) continue;
        if (appState.shutterSoundObjectUrl) URL.revokeObjectURL(appState.shutterSoundObjectUrl);
        appState.shutterSoundObjectUrl = URL.createObjectURL(blob);
        shutterSound.src = appState.shutterSoundObjectUrl;
        shutterSound.load();
        return true;
      } catch (e) { /* ignore */ }
    }
    return false;
  }

  async function playShutterSoundOnce() {
    try {
      if (!(await ensureShutterSoundLoaded())) return;
      shutterSound.currentTime = 0;
      await shutterSound.play().catch(() => {});
    } catch (e) {
      console.warn("Kamera-Sound konnte nicht abgespielt werden:", e);
    }
  }

  // --- TUTORIAL MODAL LOGIK START ---
  const tutorialModal = document.getElementById('is-tutorial-modal');
  const openTutorialBtn = document.getElementById('open-tutorial-btn');
  const closeTutorialBtn = document.getElementById('close-tutorial-modal');

  if (openTutorialBtn && tutorialModal) {
      openTutorialBtn.addEventListener('click', () => { tutorialModal.style.display = 'flex'; });
  }
  if (closeTutorialBtn && tutorialModal) {
      closeTutorialBtn.addEventListener('click', () => { tutorialModal.style.display = 'none'; });
  }
  window.addEventListener('click', (event) => {
      if (event.target === tutorialModal) tutorialModal.style.display = 'none';
  });
  // --- TUTORIAL MODAL LOGIK ENDE ---

  const openBtn = document.getElementById('open-image-studio-btn');
  const closeBtn = document.getElementById('close-image-studio-modal');
  const minimizeBtn = document.getElementById('image-studio-minimize-btn');
  const modal = document.getElementById('image-studio-modal');

  function syncImageStudioDockReserve() {
    if (!modal) return;
    modal.style.setProperty('--image-studio-dock-reserve', `${getDockBarHeightPx()}px`);
  }

  function syncImageStudioFromDockState() {
    const m = getDockModuleState('image-studio');
    const visible = !!m?.isOpen && !m?.minimized;
    if (modal) {
      modal.classList.toggle('image-studio-modal--visible', visible);
      if (visible) {
        modal.style.removeProperty('display');
        syncImageStudioDockReserve();
      } else {
        modal.style.display = 'none';
      }
    }
    openBtn?.classList.toggle('sidebar-nav-item--active', visible);
  }

  subscribeWindowState(() => syncImageStudioFromDockState());
  syncImageStudioFromDockState();

  const providerSelect = document.getElementById('is-provider-select');
  const modelSelect = document.getElementById('is-model-select');
  const dynamicParamsContainer = document.getElementById('is-dynamic-params');
  const isResolutionSelect = document.getElementById('is-resolution-select');
  const isResolutionControlGroup = document.getElementById('is-resolution-control-group');
  const promptInput = document.getElementById('is-prompt');
  const costDisplay = document.getElementById('is-estimated-cost');
  const generateBtn = document.getElementById('is-generate-btn');
  const previewContainer = document.getElementById('is-preview-container');
  const generatedGallery = document.getElementById('is-gallery-generated');
  const uploadedGallery = document.getElementById('is-gallery-uploaded');
  const allImagesGallery = document.getElementById('is-gallery-all');
  const imageFilenameInput = document.getElementById('is-image-filename');
  

  
  // Mode checkboxes
  const editModeCheckbox = document.getElementById('is-edit-mode');
  const refineModeCheckbox = document.getElementById('is-refine-mode');
  const maskModeCheckbox = document.getElementById('is-mask-mode');
  const presetsModeCheckbox = document.getElementById('is-presets-mode');
  
  // Preset application checkboxes
  const applyPresetContainer = document.getElementById('apply-preset-to-edit-container');
  const applyPresetCheckbox = document.getElementById('is-apply-preset-to-edit');
  const applyPresetToRefineContainer = document.getElementById('apply-preset-to-refine-container');
  const applyPresetToRefineCheckbox = document.getElementById('is-apply-preset-to-refine');
  
  // Quality Gate Elements
  const qualityGateSelect = document.getElementById('is-quality-gate-select');
  const maxCostWrapper = document.getElementById('is-max-cost-wrapper');
  const maxCostDisplay = document.getElementById('is-max-cost');
  
  const QUALITY_GATE_CONFIG = {
    none:   { retries: 0 },
    low:    { retries: 1 },
    medium: { retries: 2 },
    high:   { retries: 3 }
  };
  const ESTIMATED_VISION_COST = 0.01;
  let currentImageElement = null;

  // --- FUNKTIONEN (UI, LOGIK, ETC.) ---



  async function loadPricingData() {
    try {
      appState.pricingData = await fetchPricingData();
      populateProviderSelect();    
    } catch (error) {
      console.error(error);
      costDisplay.textContent = 'Fehler';
    }
  }

  async function loadAllLocalImages() {
    if (!allImagesGallery) return;
    allImagesGallery.innerHTML = '<div class="is-empty-hint">Lade Historie...</div>';
    try {
        const response = await fetch(`${getBackendBaseUrl()}/api/images/list_all`);
        if (!response.ok) throw new Error(`Status: ${response.status}`);
        const images = await response.json();
        if (images.length === 0) {
            allImagesGallery.innerHTML = '<div class="is-empty-hint">Keine Historie gefunden.</div>';
            return;
        }
        allImagesGallery.innerHTML = '';
        if (uploadedGallery) uploadedGallery.innerHTML = '';
        if (generatedGallery && generatedGallery.children.length === 0) {
             generatedGallery.innerHTML = '<div class="is-empty-hint">Noch keine Bilder in dieser Sitzung generiert</div>';
        }
        images.reverse().forEach(imageData => {
            const url = imageData.image_url || '';
            const isUpload = url.includes('/uploads/') || url.includes('\\uploads\\') || !imageData.provider;
            if (isUpload) {
                if (uploadedGallery) addImageToGallery(imageData, uploadedGallery);
            } else {
                if (allImagesGallery) addImageToGallery(imageData, allImagesGallery);
            }
        });
    } catch (error) {
        console.error("[DEBUG] FEHLER in loadAllLocalImages:", error);
        allImagesGallery.innerHTML = `<div class="is-empty-hint" style="color: red;">Fehler: ${error.message}</div>`;
    }
  }

  function populateProviderSelect() {
    providerSelect.innerHTML = '';
    if (!appState.pricingData) return;
    const availableProviders = Object.keys(appState.pricingData);
    if (availableProviders.length === 0) return;
    availableProviders.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider;
        providerSelect.appendChild(option);
    });
    if (!providerSelect.value || !appState.pricingData[providerSelect.value]) providerSelect.value = availableProviders[0];
    providerSelect.dispatchEvent(new Event('change'));
  }

  function populateModelSelect() {
    modelSelect.innerHTML = '';
    const selectedProvider = providerSelect.value;
    if (appState.pricingData && appState.pricingData[selectedProvider]) {
      const imageModels = Object.entries(appState.pricingData[selectedProvider]).filter(([modelId, modelData]) => {
          return typeof modelData === 'object' && modelData.type === 'image' && modelData.capabilities && modelData.capabilities.includes('image_generation');
      });
      imageModels.forEach(([modelId, modelData]) => {
        const option = document.createElement('option');
        option.value = modelId;
        option.textContent = modelData.name; 
        modelSelect.appendChild(option);
      });
    }
    populateDynamicParams();
  }
  
  function populateDynamicParams() {
      dynamicParamsContainer.innerHTML = '';
      const selectedProvider = providerSelect.value;
      const selectedModelId = modelSelect.value; 
      isResolutionControlGroup.style.display = 'none';

      if(!appState.pricingData || !appState.pricingData[selectedProvider] || !appState.pricingData[selectedProvider][selectedModelId]) {
          updateCost();
          return;
      }

      const modelData = appState.pricingData[selectedProvider][selectedModelId];
      
      if (modelData.type === 'image' && modelData.pricing) {
          const qualityDiv = document.createElement('div');
          qualityDiv.classList.add('control-group');
          qualityDiv.innerHTML = `<label for="is-param-quality">Qualität</label><select id="is-param-quality" data-param-key="quality"></select>`;
          dynamicParamsContainer.appendChild(qualityDiv);
          const qualitySelect = qualityDiv.querySelector('select');
          const availableQualities = Object.keys(modelData.pricing);
          availableQualities.forEach(q => {
              const option = document.createElement('option');
              option.value = q;
              option.textContent = q.charAt(0).toUpperCase() + q.slice(1);
              qualitySelect.appendChild(option);
          });
          qualitySelect.value = modelData.default_quality || availableQualities[0];

          const sizeDiv = document.createElement('div');
          sizeDiv.classList.add('control-group');
          sizeDiv.innerHTML = `<label for="is-param-size">Auflösung</label><select id="is-param-size" data-param-key="size"></select>`;
          dynamicParamsContainer.appendChild(sizeDiv);
          const sizeSelect = sizeDiv.querySelector('select');

          const populateSizeOptions = () => {
              sizeSelect.innerHTML = ''; 
              const currentQuality = qualitySelect.value;
              const availableSizes = modelData.pricing[currentQuality] ? Object.keys(modelData.pricing[currentQuality]) : [];
              availableSizes.forEach(s => {
                  const option = document.createElement('option');
                  option.value = s;
                  option.textContent = s;
                  sizeSelect.appendChild(option);
              });
              sizeSelect.value = modelData.default_size || availableSizes[0];
              updateCost(); 
          };
          qualitySelect.addEventListener('change', populateSizeOptions);
          sizeSelect.addEventListener('change', () => updateCost());
          populateSizeOptions(); 
      } 
      else if (modelData.type === 'image' && modelData.aspect_ratios) {
          const ratioDiv = document.createElement('div');
          ratioDiv.classList.add('control-group');
          ratioDiv.innerHTML = `<label for="is-param-aspect-ratio">Seitenverhältnis</label><select id="is-param-aspect-ratio" data-param-key="aspect_ratio"></select>`;
          dynamicParamsContainer.appendChild(ratioDiv);
          const ratioSelect = ratioDiv.querySelector('select');
          modelData.aspect_ratios.forEach(ratio => {
              const option = document.createElement('option');
              option.value = ratio;
              option.textContent = ratio;
              ratioSelect.appendChild(option);
          });
          ratioSelect.value = modelData.default_aspect_ratio || "1:1";
          ratioSelect.addEventListener('change', updateCost);
          
          if (selectedModelId.startsWith('gemini-3')) { 
            isResolutionControlGroup.style.display = 'block';
            isResolutionSelect.innerHTML = ''; 
            isResolutionSelect.dataset.paramKey = 'image_size'; 
            const availableResolutions = modelData.resolutions || ["1K", "2K"]; 
            availableResolutions.forEach(res => {
                const option = document.createElement('option');
                option.value = res;
                option.textContent = res;
                isResolutionSelect.appendChild(option);
            });
            isResolutionSelect.value = modelData.default_resolution || availableResolutions[0];
            isResolutionSelect.addEventListener('change', updateCost); 
          }
          updateCost();
      } else {
          const parameterKeys = Object.keys(modelData).filter(key => typeof modelData[key] === 'object' && key !== 'pricing' && key !== 'capabilities');
          parameterKeys.forEach(paramKey => {
              const div = document.createElement('div');
              div.classList.add('control-group');
              div.innerHTML = `<label for="is-param-${paramKey}">${paramKey.charAt(0).toUpperCase() + paramKey.slice(1)}</label><select id="is-param-${paramKey}" data-param-key="${paramKey}"></select>`;
              dynamicParamsContainer.appendChild(div);
              const select = div.querySelector('select');
              const paramData = modelData[paramKey]; 
              for(const optionValue in paramData) {
                  const option = document.createElement('option');
                  option.value = optionValue;
                  option.textContent = optionValue;
                  select.appendChild(option);
              }
              select.addEventListener('change', updateCost);
              if(select.value === '') select.value = Object.keys(paramData)[0]; 
          });
          updateCost();
      }
  }

  function updateCost() {
    costDisplay.textContent = 'Berechne...';
    const selectedProvider = providerSelect.value;
    const selectedModelId = modelSelect.value; 

    if (!appState.pricingData || !selectedProvider || !selectedModelId) {
      costDisplay.textContent = 'N/A';
      return;
    }

    try {
      const modelData = appState.pricingData[selectedProvider]?.[selectedModelId];
      if (!modelData) {
        costDisplay.textContent = 'N/A';
        return;
      }

      let finalCost = 'N/A';
      if (modelData.type === 'image' && modelData.pricing) {
        isResolutionControlGroup.style.display = 'none'; 
        const qualitySelect = dynamicParamsContainer.querySelector('#is-param-quality');
        const sizeSelect = dynamicParamsContainer.querySelector('#is-param-size');
        const quality = qualitySelect ? qualitySelect.value : null;
        const size = sizeSelect ? sizeSelect.value : null;
        if (quality && size && modelData.pricing[quality] && modelData.pricing[quality][size]) {
            finalCost = modelData.pricing[quality][size];
        }
      } else if (modelData.type === 'image' && modelData.aspect_ratios) {
          const resolutionSelect = document.getElementById('is-resolution-select'); 
          const selectedResolution = resolutionSelect ? resolutionSelect.value : (modelData.default_resolution || "1K");
          if (modelData.cost_per_million_tokens_input && modelData.cost_per_million_tokens_output && modelData.tokens_per_resolution) {
              const outputTokensPerImage = modelData.tokens_per_resolution[selectedResolution] || 1120; 
              const inputTokensPerImage = 560; 
              const inputCostPerImage = (inputTokensPerImage / 1000000) * modelData.cost_per_million_tokens_input;
              const outputCostPerImage = (outputTokensPerImage / 1000000) * modelData.cost_per_million_tokens_output;
              finalCost = inputCostPerImage + outputCostPerImage;
          } else if (modelData.cost_per_image) {
              finalCost = modelData.cost_per_image;
          }
      } else {
          const params = {};
          dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
              params[sel.dataset.paramKey] = sel.value;
          });
          if (modelData.cost_per_image) finalCost = modelData.cost_per_image;
          else if (modelData.cost_per_token_input) finalCost = "Variiert";
          else if (modelData.cost_per_query) finalCost = modelData.cost_per_query;
          else {
              const firstParamKey = Object.keys(modelData).find(key => typeof modelData[key] === 'object' && key !== 'pricing' && key !== 'capabilities');
              if (firstParamKey && params[firstParamKey]) finalCost = modelData[firstParamKey]?.[params[firstParamKey]];
              else if (typeof modelData === 'number') finalCost = modelData;
          }
      }
      
      if (typeof finalCost === 'number') {
        costDisplay.textContent = `$${finalCost.toFixed(4)}`;
        const gateLevel = qualityGateSelect ? qualityGateSelect.value : 'none';
        if (gateLevel === 'none' || finalCost === 0) {
            if (maxCostWrapper) maxCostWrapper.style.display = 'none';
        } else {
            if (maxCostWrapper) maxCostWrapper.style.display = 'flex';
            const config = QUALITY_GATE_CONFIG[gateLevel];
            const totalRuns = 1 + config.retries;
            const maxRisk = (finalCost + ESTIMATED_VISION_COST) * totalRuns;
            if (maxCostDisplay) maxCostDisplay.textContent = `$${maxRisk.toFixed(4)}`;
        }
      } else {
        costDisplay.textContent = 'N/A';
        if (maxCostWrapper) maxCostWrapper.style.display = 'none';
      }
    } catch (e) {
      console.error("Fehler bei der Kostenkalkulation:", e);
      costDisplay.textContent = 'Fehler';
    }
  }

  async function generateImage() {
    try {
      await playShutterSoundOnce();
      shutterSound.pause();
      shutterSound.currentTime = 0;
    } catch (e) { /* ignore */ }

    const actualResultWrapper = document.getElementById('is-actual-result-wrapper');
    if (actualResultWrapper) actualResultWrapper.style.display = 'none';
    if (maxCostWrapper && qualityGateSelect.value !== 'none') {
        maxCostWrapper.style.display = 'flex'; 
    }
    
    previewContainer.innerHTML = '<div class="loader"></div>';
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generiere...';
    
    const refineActive = document.getElementById('is-refine-mode').checked;
    const editModeActive = editModeCheckbox.checked;
    const combineModeActive = document.getElementById('is-combine-mode').checked;
    const activeCombineImages = appState.combineSlotsData.filter(url => url !== null);
    
    if (combineModeActive && activeCombineImages.length < 1) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte ziehe mindestens ein Bild in die Felder.</p>';
      generateBtn.disabled = false;
      return;
    }
    
    if (editModeActive && !appState.currentImageFullUrl) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte lade zuerst ein Bild hoch.</p>';
      generateBtn.disabled = false;
      return;
    }
    
    const applyRefinePreset = applyPresetToRefineCheckbox?.checked || false;
    const applyEditPreset = applyPresetCheckbox?.checked || false;
    
    // Prüfen, ob Presets aktiv sind
    const presetsModeActive = document.getElementById('is-presets-mode')?.checked || false;
    const shouldSendPresets = presetsModeActive || (editModeActive && applyEditPreset) || (refineActive && applyRefinePreset);

    // Werte über die Export-Funktion des Moduls holen
    const presetValues = getSelectedPresetValues();

    // Nur schicken, wenn nicht leer und nicht der String "null"
    const finalStyle = (shouldSendPresets && presetValues.style && presetValues.style !== "null") ? presetValues.style : null;
    const finalVar = (shouldSendPresets && presetValues.variation && presetValues.variation !== "null") ? presetValues.variation : null;

    const payload = {
        prompt: promptInput.value,
        provider: providerSelect.value,
        model: modelSelect.value, 
        parameters: {},
        quality_gate_level: qualityGateSelect ? qualityGateSelect.value : 'none',
        // Sicherstellen, dass IDs echte Werte sind
        // KORREKTUR: IDs explizit in String umwandeln mit String()
        previous_response_id: (refineActive && appState.lastContextIds.response_id) 
            ? String(appState.lastContextIds.response_id) 
            : null,
        previous_image_id: (refineActive && appState.lastContextIds.image_id) 
            ? String(appState.lastContextIds.image_id) 
            : null,
        
        apply_preset_to_edit: applyEditPreset,
        apply_preset_to_refine: applyRefinePreset,
        
        // Gesäuberte Werte nutzen
        style_preset: finalStyle,
        variation_preset: finalVar,
        history: (refineActive && providerSelect.value === 'gemini') ? {
            prompt: appState.lastGeneratedPrompt,
            image_base64: appState.lastGeneratedImageBase64
        } : null,
        reference_image_url: (editModeActive || maskModeCheckbox.checked || refineActive) ? appState.currentImageFullUrl : null,
        reference_image_urls: combineModeActive ? activeCombineImages : [],
        mask_image_data: (maskModeCheckbox.checked) ? getMaskData() : null
    };
    
    dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
        payload.parameters[sel.dataset.paramKey] = sel.value;
    });

    if (modelSelect.value.startsWith('gemini-3') && isResolutionControlGroup.style.display !== 'none') {
        payload.parameters['resolution'] = isResolutionSelect.value;
    }

    try {
        const result = await generateImageApi(payload);
        
        if (result.quality_gate_stats && result.quality_gate_stats.was_active) {
            const stats = result.quality_gate_stats;
            const actualWrapper = document.getElementById('is-actual-result-wrapper');
            if (actualWrapper) {
                const costEl = document.getElementById('is-actual-cost');
                const attemptsEl = document.getElementById('is-actual-attempts');
                const scoreEl = document.getElementById('is-actual-score');
                if (costEl) costEl.textContent = `$${stats.total_cost.toFixed(4)}`;
                if (attemptsEl) attemptsEl.textContent = `${stats.attempts}`;
                if (scoreEl) {
                    scoreEl.textContent = `${stats.final_score}%`;
                    scoreEl.style.color = stats.final_score >= 80 ? '#4caf50' : (stats.final_score >= 60 ? '#ffc107' : '#f44336');
                }
                if (maxCostWrapper) maxCostWrapper.style.display = 'none'; 
                actualWrapper.style.display = 'flex';             
            }
        }
        
        const imageUrl = `${getBackendBaseUrl()}${result.image_url}`;
        appState.currentImageFullUrl = imageUrl; 
        
        playShutterSoundOnce();
        
        appState.lastContextIds = {
            response_id: result.previous_response_id || null,
            image_id: result.previous_image_id || null
        };
        appState.lastGeneratedPrompt = payload.prompt;
        
        fetch(imageUrl).then(res => res.blob()).then(blob => {
            const reader = new FileReader();
            reader.onload = () => { appState.lastGeneratedImageBase64 = reader.result.split(',')[1]; };
            reader.readAsDataURL(blob);
        });
          
        document.getElementById('is-refine-mode').checked = true;
        document.getElementById('is-combine-mode').checked = false;
        document.getElementById('is-edit-mode').checked = false;
        if (applyPresetCheckbox) applyPresetCheckbox.checked = false;
        if (maskModeCheckbox) maskModeCheckbox.checked = false;
        togglePresetForRefineUI();

        if (shouldSendPresets) {
            if (presetsModeCheckbox) presetsModeCheckbox.checked = false;
            if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = true;
            updatePresetVisibility();
        }

        const filenameMatch = imageUrl.match(/\/([^\/]+)$/);
        imageFilenameInput.value = filenameMatch ? filenameMatch[1].split('.')[0] : "unbenannt";
        
        previewContainer.innerHTML = ''; 
        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = payload.prompt;
        imgElement.style.maxWidth = '100%';
        imgElement.style.maxHeight = '100%';
        imgElement.style.objectFit = 'contain';
        imgElement.addEventListener('click', () => {
            if (window.openImageModal) window.openImageModal(imageUrl);
        });
        previewContainer.appendChild(imgElement);
        addImageToGallery(result, generatedGallery);
        
        const pollId = result.id;
        let pollAttempts = 0;
        const maxPollAttempts = 20;
        const initialDelay = 2000;
        const pollInterval = 2000;

        const pollForNewName = async () => {
            pollAttempts++;
            if (pollAttempts > maxPollAttempts) {
                console.warn(`Namens-Polling für Bild-ID ${pollId} nach ${maxPollAttempts} Versuchen aufgegeben.`);
                return;
            }
            try {
                const ctxRes = await fetch(`${getBackendBaseUrl()}/api/context_by_id/${pollId}`);
                if (ctxRes.ok) {
                    const ctxData = await ctxRes.json();
                    const currentUrlPath = ctxData.image_url;
                    if (currentUrlPath && currentUrlPath.includes('__')) {
                        console.log(`Auto-Update für ID ${pollId}: Neuer Name erkannt -> ${currentUrlPath}`);
                        const newFullUrl = `${getBackendBaseUrl()}${currentUrlPath}`;
                        appState.currentImageFullUrl = newFullUrl;
                        if (imgElement.src.includes(result.image_url)) {
                            imgElement.src = newFullUrl;
                        }
                        const newFilename = currentUrlPath.split('/').pop().split('.').slice(0, -1).join('.');
                        if (imageFilenameInput) {
                            imageFilenameInput.value = newFilename;
                            imageFilenameInput.style.transition = "background-color 0.5s";
                            imageFilenameInput.style.backgroundColor = "rgba(76, 175, 80, 0.2)";
                            setTimeout(() => { imageFilenameInput.style.backgroundColor = ""; }, 500);
                        }
                        const thumb = document.querySelector(`.gallery-thumbnail[data-image-id="${pollId}"]`);
                        if (thumb) {
                            thumb.src = newFullUrl;
                        }
                        return; 
                    }
                }
            } catch (e) {
                console.warn(`Fehler beim Namens-Polling (Versuch ${pollAttempts}):`, e);
            }
            setTimeout(pollForNewName, pollInterval);
        };
        setTimeout(pollForNewName, initialDelay);
    } catch (error) {
        // Fehler-Nachricht extrahieren
        const msg = error.message || "Unbekannter Fehler";
        previewContainer.innerHTML = `<div style="color: #ff5252; padding: 20px; text-align: center; background: rgba(255,0,0,0.1); border-radius: 8px;">
            <strong>Generierungsfehler</strong><br>
            <small style="opacity: 0.8;">${msg}</small>
        </div>`;
        console.error("Detaillierter Fehler:", error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generieren';
    }
  }

  function updateCapabilityUI() {
    const provider = providerSelect.value;
    const maskContainer = maskModeCheckbox.parentElement; 
    if (provider === 'gemini') {
      if (maskModeCheckbox.checked) {
        maskModeCheckbox.checked = false;
        maskModeCheckbox.dispatchEvent(new Event('change'));
      }
      maskModeCheckbox.disabled = true;
      maskContainer.style.opacity = '0.5';
      maskContainer.title = "Not supported by Gemini.";
    } else {
      maskModeCheckbox.disabled = false;
      maskContainer.style.opacity = '1';
      maskContainer.title = "";
    }
  }

  function updatePreviewImage(src, alt) {
    previewContainer.innerHTML = '';
    const imgElement = document.createElement('img');
    imgElement.src = src;
    imgElement.alt = alt || "Vorschau";
    imgElement.style.maxWidth = '100%';
    imgElement.style.maxHeight = '100%';
    imgElement.style.objectFit = 'contain';
    previewContainer.appendChild(imgElement);
    setTimeout(() => initCanvasSize(), 100); // Kurz warten, bis Bild gerendert ist
  }
  
  function setEditMode() {
    editModeCheckbox.checked = true;
    document.getElementById('is-refine-mode').checked = false;
    document.getElementById('is-mask-mode').checked = false;
    document.getElementById('is-combine-mode').checked = false;
    updateExclusiveModes('is-edit-mode');
    togglePresetForEditUI();
  }
  
  async function loadImageContext(imageUrl) {
    try {
      const contextRes = await fetch(`${getBackendBaseUrl()}/api/images/context?url=${encodeURIComponent(imageUrl)}`);
      if (!contextRes.ok) throw new Error('Kontext-Fehler');
      
      const contextData = await contextRes.json();
      
      // SICHERHEIT: Ist es ein Upload?
      const isUpload = imageUrl.includes('/uploads/') || imageUrl.includes('\\uploads\\');
      const resId = (!isUpload && contextData.response_id && contextData.response_id !== "null") ? contextData.response_id : null;
      const imgId = (contextData.image_id && contextData.image_id !== "null") ? contextData.image_id : null;
      
      appState.lastContextIds.response_id = resId;
      appState.lastContextIds.image_id = imgId;
      
      try {
        const filename = extractFilenameFromUrl(imageUrl);
        if (imageFilenameInput) imageFilenameInput.value = filename;
      } catch (e) { console.warn(e); }
      
      // Preset Checkboxen resetten
      if (presetsModeCheckbox) presetsModeCheckbox.checked = false;
      if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = false;
      if (applyPresetCheckbox) applyPresetCheckbox.checked = false;
      
      // Modus setzen (ruft jetzt den loop-freien updateExclusiveModes auf)
      if (resId) {
        updateExclusiveModes('is-refine-mode'); 
      } else {
        updateExclusiveModes('is-edit-mode');
      }

      // Diamond Standard: Presets wiederherstellen
      const hasStyle = contextData.style_preset && contextData.style_preset !== "null" && contextData.style_preset !== "";
      const hasVar = contextData.variation_preset && contextData.variation_preset !== "null" && contextData.variation_preset !== "";

      if (hasStyle && hasVar) {
          restorePresetSettings(contextData.style_preset, contextData.variation_preset);
          if (resId) {
              if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = true;
          } else {
              if (applyPresetCheckbox) applyPresetCheckbox.checked = true;
          }
          updatePresetVisibility(); // Sichtbarkeit nochmal explizit prüfen
      } else {
          const infoBox = document.getElementById('preset-info-display');
          if (infoBox) infoBox.style.display = 'none';
      }
    } catch (err) {
      console.error("Fehler beim Laden des Bild-Kontexts:", err);
      updateExclusiveModes('is-edit-mode');
    }
    updateCost();
  }

  function toggleSelection(wrapperElement, imageId) {
    if (appState.selectedImageIds.has(imageId)) {
        // Abwählen
        appState.selectedImageIds.delete(imageId);
        wrapperElement.classList.remove('selected');
    } else {
        // Auswählen
        appState.selectedImageIds.add(imageId);
        wrapperElement.classList.add('selected');
    }
    console.log("Ausgewählte Bilder:", Array.from(appState.selectedImageIds));
}

function addImageToGallery(imageData, galleryElement) {
        const existingImg = galleryElement.querySelector(`img[data-image-id="${imageData.id}"]`);
        if (existingImg) {
            existingImg.closest('.gallery-item-wrapper')?.style.setProperty('box-shadow', '0 0 10px #4caf50', 'important');
            setTimeout(() => {
                const wrapper = existingImg.closest('.gallery-item-wrapper');
                if (wrapper) wrapper.style.boxShadow = '';
            }, 500);
            return;
        }

        const hint = galleryElement.querySelector('.is-empty-hint');
        if (hint) hint.remove();

        const fullImageUrl = `${getBackendBaseUrl()}${imageData.image_url}`;
        const wrapper = document.createElement('div');
        wrapper.classList.add('gallery-item-wrapper');
        wrapper.dataset.imageId = imageData.id;
        const thumbnailImg = document.createElement('img');
        thumbnailImg.src = fullImageUrl;
        thumbnailImg.alt = imageData.prompt || 'Uploaded image';
        thumbnailImg.classList.add('gallery-thumbnail');
        thumbnailImg.draggable = true;
        thumbnailImg.dataset.imageId = imageData.id;
        const checkbox = document.createElement('div');
        checkbox.classList.add('gallery-checkbox');
        
        thumbnailImg.addEventListener('click', () => {
            if (window.openImageModal) window.openImageModal(thumbnailImg.src);
        });
        checkbox.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSelection(wrapper, imageData.id);
        });
        thumbnailImg.addEventListener('dragstart', (event) => {
            event.dataTransfer.setData('application/janus-image-id', imageData.id);
            event.dataTransfer.effectAllowed = 'copy';
        });

        wrapper.appendChild(thumbnailImg);
        wrapper.appendChild(checkbox);
        galleryElement.prepend(wrapper);
  }

  async function deleteImage(imageId, elementToRemove) {
      if (!imageId) return;
      try {
          const token = localStorage.getItem('auth_token');
          if (!token) throw new Error("Authentifizierungs-Token nicht gefunden.");
          const response = await fetch(`${getBackendBaseUrl()}/api/images/${imageId}`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
              const idStr = String(imageId);
              const allWrappers = document.querySelectorAll(`.gallery-item-wrapper[data-image-id="${idStr}"]`);
              allWrappers.forEach(wrapper => wrapper.remove());
              appState.selectedImageIds.delete(parseInt(imageId));
          } else {
              const errorData = await response.json();
              throw new Error(errorData.detail || "Unbekannter Fehler beim Löschen.");
          }
      } catch (error) {
          console.error("Fehler beim Löschen des Bildes:", error);
          alert(`Löschen fehlgeschlagen: ${error.message}`);
          throw error;
      }
  }

function showDeleteConfirm(isBatch, imageId) {
    const deleteModal = document.getElementById('is-delete-confirm-modal');
    const titleEl = document.getElementById('delete-dialog-title');
    const textEl = document.getElementById('delete-dialog-text');
    const confirmBtn = document.getElementById('delete-confirm-btn');

    if (!deleteModal) return;

    // IDs sammeln
    let idsToDelete = [];
    if (isBatch) {
        idsToDelete = Array.from(appState.selectedImageIds);
    } else if (imageId) {
        idsToDelete = [imageId];
    }

    if (idsToDelete.length === 0) {
        console.warn("Löschen aufgerufen, aber keine Bilder ausgewählt.");
        return;
    }

    // UI Texte setzen
    if (idsToDelete.length > 1) {
        titleEl.textContent = `${idsToDelete.length} Bilder löschen?`;
        textEl.textContent = `Möchtest du wirklich alle ${idsToDelete.length} ausgewählten Bilder unwiderruflich löschen?`;
    } else {
        titleEl.textContent = "Bild löschen?";
        textEl.textContent = "Möchtest du dieses Bild wirklich unwiderruflich löschen?";
    }

    deleteModal.style.display = 'flex';

    // Event Listener neu binden
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.addEventListener('click', async () => {
        try {
            newConfirmBtn.disabled = true;
            let successCount = 0;

            for (const id of idsToDelete) {
                newConfirmBtn.textContent = `Lösche ${successCount + 1}/${idsToDelete.length}...`;
                try {
                    // WICHTIG: Wir übergeben die ID explizit (String/Zahl egal durch Konvertierung im deleteImage)
                    await deleteImage(id);
                    successCount++;
                } catch (e) {
                    console.error(`Fehler beim Löschen von Bild ${id}:`, e);
                }
            }

            console.log(`${successCount} Bilder erfolgreich gelöscht.`);
            
            // Auswahl leeren
            appState.selectedImageIds.clear();
            document.querySelectorAll('.gallery-item-wrapper.selected').forEach(el => el.classList.remove('selected'));
            
        } catch (err) {
            console.error("Kritischer Fehler im Batch-Delete:", err);
            alert("Ein unerwarteter Fehler ist aufgetreten.");
        } finally {
            deleteModal.style.display = 'none';
            newConfirmBtn.disabled = false;
            newConfirmBtn.textContent = "Ja, löschen";
        }
    });
  }

  // --- Initialisierung und Event-Listener ---

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => {
      openModal({ type: 'image-studio' });

      if (!appState.pricingData) loadPricingData();
      loadAllLocalImages();
      updatePresetVisibility();

      // Canvas anpassen, NACHDEM das Modal sichtbar ist
      setTimeout(() => initCanvasSize(), 100);
    });
  }

  minimizeBtn?.addEventListener('click', () => {
    dockMinimize('image-studio', true);
  });

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      closeModal('image-studio');
    });
  }

  window.addEventListener('click', (event) => {
    if (event.target === modal) {
      closeModal('image-studio');
    }
  });

  // NEU: Focus-to-Front bei Klick auf Panel
  modal?.addEventListener('mousedown', () => { bringToFront('image-studio'); });

  window.addEventListener('resize', () => {
    if (modal?.classList.contains('image-studio-modal--visible')) {
      syncImageStudioDockReserve();
    }
  });

  if (providerSelect) {
    providerSelect.addEventListener('change', () => {
      populateModelSelect();
      updateCost();
      updateCapabilityUI();
      updateStylePreviewImage();
    });
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', () => {
      // Wir löschen hier NICHTS mehr. 
      // Der Modus (Refine/Edit) bleibt erhalten, egal welches Modell gewählt wird.
      populateDynamicParams();
      updateCost();
    });
  }

  const exclusiveModeCheckboxes = ['is-refine-mode', 'is-edit-mode', 'is-mask-mode', 'is-combine-mode'];

function handleModeChange(e) {
    if (isInternalChange) {
        return;
    }

    const activeId = e.target.checked ? e.target.id : null;
    updateExclusiveModes(activeId);
}

  exclusiveModeCheckboxes.forEach(id => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.addEventListener('change', handleModeChange);
  });

function updateExclusiveModes(activeModeId) {
    isInternalChange = true;
    try {
        exclusiveModeCheckboxes.forEach(id => {
            const cb = document.getElementById(id);
            if (cb) cb.checked = (id === activeModeId);
        });
        
        const slotsWrapper = document.getElementById('combine-slots-wrapper');
        if (slotsWrapper) slotsWrapper.style.display = (activeModeId === 'is-combine-mode') ? 'block' : 'none';
        
        toggleInpaintingUI(activeModeId === 'is-mask-mode');

        if (promptInput) {
            if (activeModeId === 'is-combine-mode') promptInput.placeholder = "Beschreibe, wie die Bilder kombiniert werden sollen...";
            else if (activeModeId === 'is-mask-mode') promptInput.placeholder = "Beschreibe, was in den maskierten Bereich soll...";
            else promptInput.placeholder = "Beschreibe dein Bild...";
        }
        
        togglePresetForEditUI();
        togglePresetForRefineUI();
        updatePresetVisibility();
    } finally {
        isInternalChange = false;
    }
}
  
  if (applyPresetToRefineCheckbox) {
    applyPresetToRefineCheckbox.addEventListener('change', () => { updatePresetVisibility(); });
  }
  if (applyPresetCheckbox) {
    applyPresetCheckbox.addEventListener('change', () => { updatePresetVisibility(); updateStylePreviewImage(); });
  }
  if (presetsModeCheckbox) {
    presetsModeCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            exclusiveModeCheckboxes.forEach(id => {
                const cb = document.getElementById(id);
                if (cb && cb.checked) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change'));
                }
            });
            updateStylePreviewImage();
        }
        updatePresetVisibility();
    });
  }

  if (generateBtn) generateBtn.addEventListener('click', generateImage);
  
  // --- COMBINE SLOTS LOGIK ---
  const combineSlots = document.querySelectorAll('.combine-slot');

  combineSlots.forEach((slot, index) => {
      // Dragover: Erlaubt das Droppen und zeigt visuellen Effekt
      slot.addEventListener('dragover', (e) => {
          e.preventDefault();
          slot.classList.add('drag-over');
      });

      slot.addEventListener('dragleave', () => {
          slot.classList.remove('drag-over');
      });

      // Drop: Verarbeitet das Bild
      slot.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          slot.classList.remove('drag-over');

          const imageId = e.dataTransfer.getData('application/janus-image-id');
          const files = e.dataTransfer.files;
          const droppedUrl = e.dataTransfer.getData('text/plain');

          let finalUrl = null;

          // FALL 1: Internes Bild aus der Galerie
          if (imageId) {
              try {
                  const resp = await fetch(`${getBackendBaseUrl()}/api/context_by_id/${imageId}`);
                  if (resp.ok) {
                      const data = await resp.json();
                      finalUrl = `${getBackendBaseUrl()}${data.image_url}`;
                  }
              } catch (err) { console.error("Slot Drop Error:", err); }
          }
          // FALL 2: Lokale Datei
          else if (files && files.length > 0) {
              const file = files[0];
              if (file.type.startsWith('image/')) {
                  const formData = new FormData();
                  formData.append('file', file);
                  try {
                      const resp = await fetch(`${getBackendBaseUrl()}/api/images/upload`, { method: 'POST', body: formData });
                      if (resp.ok) {
                          const data = await resp.json();
                          finalUrl = `${getBackendBaseUrl()}${data.image_url}`;
                          // Galerie nach Upload sicher aktualisieren
                          await loadAllLocalImages();
                      }
                  } catch (err) { console.error("Slot Upload Error:", err); }
              }
          }
          // FALL 3: URL aus dem Web
          else if (droppedUrl) {
              finalUrl = droppedUrl;
          }

          // UI & STATE UPDATE
          if (finalUrl) {
              // Vorschaubild im Slot anzeigen
              slot.innerHTML = `<img src="${finalUrl}" style="width:100%; height:100%; object-fit:cover; border-radius:4px;">`;
              // Im appState speichern (index ist 0-4)
              appState.combineSlotsData[index] = finalUrl;
              console.log(`Slot ${index + 1} befüllt mit:`, finalUrl);
          }
      });

      // Klick auf befüllten Slot: Slot leeren
      slot.addEventListener('click', () => {
          slot.innerHTML = (index + 1).toString(); // Nummer wieder anzeigen
          appState.combineSlotsData[index] = null;
          console.log(`Slot ${index + 1} geleert.`);
      });
  });

// --- DRAG & DROP FÜR HOCHGELADENE BILDER GALERIE ---
  if (uploadedGallery) {
      uploadedGallery.addEventListener('dragover', (e) => {
          e.preventDefault();
          uploadedGallery.classList.add('drag-over-gallery');
      });
      
      uploadedGallery.addEventListener('dragleave', () => {
          uploadedGallery.classList.remove('drag-over-gallery');
      });
      
      uploadedGallery.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          uploadedGallery.classList.remove('drag-over-gallery');
          
          const files = e.dataTransfer.files;

          if (files && files.length > 0) {
              for (const file of files) {
                  if (file.type.startsWith('image/')) {
                      // Zeige einen temporären Loader in der Galerie an
                      const loaderDiv = document.createElement('div');
                      loaderDiv.className = 'gallery-item-wrapper loader-placeholder';
                      uploadedGallery.prepend(loaderDiv);
                      
                      try {
                          const formData = new FormData();
                          formData.append('file', file);
                          
                          const response = await fetch(`${getBackendBaseUrl()}/api/images/upload`, {
                              method: 'POST',
                              body: formData
                          });

                          loaderDiv.remove(); // Loader entfernen, egal ob erfolgreich oder nicht

                          if (response.ok) {
                              const imageData = await response.json();
                              // Bild zur Galerie hinzufügen
                              addImageToGallery(imageData, uploadedGallery);
                          } else {
                              console.error(`Upload von ${file.name} fehlgeschlagen.`);
                          }
                      } catch (error) {
                          console.error(`Fehler beim Upload von ${file.name}:`, error);
                          loaderDiv.remove();
                      }
                  }
              }
          } else {
              alert("Bitte ziehen Sie nur Dateien von Ihrem Computer in diesen Bereich.");
          }
      });
  }
  async function initializeStudio() {
    await loadPricingData();
    // Initialize the presets module
    initPresetsModule();
    initExportModule();
    initInpaintingModule();
  }

  // --- Drag & Drop für Preview Container ---
  if (previewContainer) {
      previewContainer.addEventListener('dragover', (event) => {
        event.preventDefault(); 
        previewContainer.classList.add('drag-over'); 
      });
      
      previewContainer.addEventListener('dragleave', () => {
        previewContainer.classList.remove('drag-over'); 
      });
      
      previewContainer.addEventListener('drop', async (event) => {
        event.preventDefault();
        event.stopPropagation();
        previewContainer.classList.remove('drag-over');
        
        const imageId = event.dataTransfer.getData('application/janus-image-id');
        const files = event.dataTransfer.files;
        const droppedUrl = event.dataTransfer.getData('text/plain');

        // FALL 1: Internes Bild aus der Galerie
        if (imageId) {
          console.log("Image dropped from gallery with ID:", imageId);
          previewContainer.innerHTML = '<div class="loader"></div>';
          try {
            const response = await fetch(`${getBackendBaseUrl()}/api/context_by_id/${imageId}`);
            if (!response.ok) throw new Error('Konnte Bildkontext nicht laden.');
            const context = await response.json();
            const url = `${getBackendBaseUrl()}${context.image_url}`;
            
            updatePreviewImage(url);
            appState.currentImageFullUrl = url;
            
            const filename = context.image_url.split('/').pop().split('.').slice(0, -1).join('.');
            if (imageFilenameInput) imageFilenameInput.value = filename;

            loadImageContext(url);
          } catch (error) {
            console.error('Fehler beim Laden des Bildes:', error);
            previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
          }
          return;
        }

        // FALL 2: Lokale Bilddatei vom Computer
        if (files && files.length > 0) {
          const file = files[0];
          if (!file.type.startsWith('image/')) {
            alert('Bitte nur Bilddateien hochladen.');
            return;
          }
          previewContainer.innerHTML = '<div class="loader"></div>';
          try {
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch(`${getBackendBaseUrl()}/api/images/upload`, { method: 'POST', body: formData });
            if (!response.ok) throw new Error('Upload fehlgeschlagen');
            
            const imageData = await response.json();
            const url = `${getBackendBaseUrl()}${imageData.image_url}`;
            
            updatePreviewImage(url);
            appState.currentImageFullUrl = url;
            
            if (uploadedGallery && !uploadedGallery.querySelector(`img[data-image-id="${imageData.id}"]`)) {
                addImageToGallery(imageData, uploadedGallery);
            }
            
            const filename = imageData.image_url.split('/').pop().split('.').slice(0, -1).join('.');
            if (imageFilenameInput) imageFilenameInput.value = filename;
            
            setEditMode();
          } catch (error) {
            console.error('Fehler beim Upload:', error);
            previewContainer.innerHTML = `<p style="color: red;">Upload Fehler: ${error.message}</p>`;
          }
          return;
        }

        // FALL 3: Bild-URL aus dem Browser
        if (droppedUrl) {
          setEditMode();
          try {
            await loadImageContext(droppedUrl);
          } catch (error) {
            console.error('Fehler beim Laden des URL-Bildkontexts:', error);
          }
        }
      });
  }

  // --- GALLERY CONTEXT MENU LOGIC ---
  const contextMenu = document.getElementById('is-gallery-context-menu');
  let currentContextMenuTarget = null; // Speichert das geklickte Bild
  const contextMenuOverlay = document.getElementById('is-context-menu-overlay');

  function hideContextMenu() {
      if (contextMenu) contextMenu.style.display = 'none';
      if (contextMenuOverlay) contextMenuOverlay.style.display = 'none';
      currentContextMenuTarget = null;
  }

  document.addEventListener('contextmenu', (event) => {
      const clickedElement = event.target;
      if (clickedElement.matches('.gallery-thumbnail')) {
          event.preventDefault();
          currentContextMenuTarget = clickedElement;
          const clickedId = parseInt(clickedElement.dataset.imageId);

          const exportItem = document.getElementById('ctx-export-item');
          const deleteItem = document.getElementById('ctx-delete-item');
          const isPartOfSelection = appState.selectedImageIds.has(clickedId) && appState.selectedImageIds.size > 1;
          
          if (isPartOfSelection) {
              const count = appState.selectedImageIds.size;
              exportItem.textContent = `${count} Bilder exportieren...`;
              deleteItem.textContent = `${count} Bilder löschen...`;
          } else {
              exportItem.textContent = 'Speichern unter...';
              deleteItem.textContent = 'Löschen...';
          }

          const menuWidth = contextMenu.offsetWidth;
          const menuHeight = contextMenu.offsetHeight;
          const menuX = (window.innerWidth / 2) - (menuWidth / 2);
          const menuY = (window.innerHeight / 2) - (menuHeight / 2);

          contextMenu.style.top = `${menuY}px`;
          contextMenu.style.left = `${menuX}px`;
          contextMenu.style.display = 'block';
          
          if (contextMenuOverlay) {
              contextMenuOverlay.style.display = 'block';
          }
      } else {
          hideContextMenu();
      }
  });

  document.addEventListener('click', () => {
      hideContextMenu();
  });

  if (contextMenu) {
      contextMenu.addEventListener('click', async (event) => {
          const action = event.target.dataset.action;
          if (!action || !currentContextMenuTarget) return;

          const imageId = currentContextMenuTarget.dataset.imageId;
          const clickedId = parseInt(imageId);
          const isBatchAction = appState.selectedImageIds.size > 1 && appState.selectedImageIds.has(clickedId);

          try {
              switch (action) {
                  case 'save-as':
                      if (isBatchAction) {
                          const firstId = appState.selectedImageIds.values().next().value;
                          openExportModal(firstId, true);
                      } else {
                          openExportModal(imageId, false);
                      }
                      break;
                  case 'delete':
                      showDeleteConfirm(isBatchAction, imageId, currentContextMenuTarget);
                      break;
              }
          } catch (error) {
              console.error('Fehler bei der Kontextmenü-Aktion:', error);
              alert(`Ein Fehler ist aufgetreten: ${error.message}`);
          }
          hideContextMenu();
      });
  }
  
  const cancelDeleteBtn = document.getElementById('delete-cancel-btn');
  if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', () => {
          document.getElementById('is-delete-confirm-modal').style.display = 'none';
      });
  }

  // --- END: GALLERY CONTEXT MENU LOGIC ---

// Initialisierungs-Aufrufe
  updateCapabilityUI(); 
  // Die Preset-UI wird jetzt durch updateExclusiveModes gesteuert, das beim Start läuft
  initializeStudio();
});