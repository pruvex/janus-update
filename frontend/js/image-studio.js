document.addEventListener('DOMContentLoaded', () => {
  const openBtn = document.getElementById('open-image-studio-btn');
  const closeBtn = document.getElementById('close-image-studio-modal');
  const modal = document.getElementById('image-studio-modal');

  const providerSelect = document.getElementById('is-provider-select');
  const modelSelect = document.getElementById('is-model-select');
  const dynamicParamsContainer = document.getElementById('is-dynamic-params');
  const promptInput = document.getElementById('is-prompt');
  const costDisplay = document.getElementById('is-estimated-cost');
  const generateBtn = document.getElementById('is-generate-btn');
  const previewContainer = document.getElementById('is-preview-container');
  const generatedGallery = document.getElementById('is-gallery-generated');
  const uploadedGallery = document.getElementById('is-gallery-uploaded');
  const imageFilenameInput = document.getElementById('is-image-filename');
  
  // Inpainting Elements
  const maskCanvas = document.getElementById('is-mask-canvas');
  const maskControls = document.getElementById('mask-controls');
  const clearMaskBtn = document.getElementById('clear-mask-btn');
  const brushSizeInput = document.getElementById('brush-size');
  const maskModeCheckbox = document.getElementById('is-mask-mode');
  const previewWrapper = document.getElementById('is-preview-wrapper');
  
  // Edit Mode Elements
  const editModeCheckbox = document.getElementById('is-edit-mode');
  const applyPresetContainer = document.getElementById('apply-preset-to-edit-container');
  const applyPresetCheckbox = document.getElementById('is-apply-preset-to-edit');
  
  // Refine Mode Elements
  const applyPresetToRefineContainer = document.getElementById('apply-preset-to-refine-container');
  const applyPresetToRefineCheckbox = document.getElementById('is-apply-preset-to-refine');
  
  // Style Presets Elements
  const presetsModeCheckbox = document.getElementById('is-presets-mode');
  const presetsContainer = document.getElementById('is-presets-container');
  const styleSelect = document.getElementById('is-style-select');
  const variationSelect = document.getElementById('is-variation-select');
  const stylePreviewContainer = document.getElementById('is-style-preview-container');
  const stylePreviewImg = document.getElementById('current-style-image');
  const styleImagePlaceholder = document.getElementById('style-image-placeholder');
  
  // Quality Gate Elements
  const qualityGateSelect = document.getElementById('is-quality-gate-select');
  const maxCostWrapper = document.getElementById('is-max-cost-wrapper');
  const maxCostDisplay = document.getElementById('is-max-cost');
  
  // Quality Gate Configuration
  const QUALITY_GATE_CONFIG = {
    none:   { retries: 0 },
    low:    { retries: 1 },
    medium: { retries: 2 },
    high:   { retries: 3 }
  };
  
  // Geschätzte Kosten für GPT-4o Vision
  const ESTIMATED_VISION_COST = 0.01;

  // --- DIAGNOSE-VERSION: updateStylePreviewImage ---
  function updateStylePreviewImage() {
      console.log("--- DIAGNOSE: updateStylePreviewImage() WURDE AUFGERUFEN ---");

      const stylePreviewImg = document.getElementById('current-style-image');
      const placeholder = document.getElementById('style-image-placeholder');

      if (!stylePreviewImg || !placeholder) {
          console.error("DIAGNOSE-FEHLER: HTML-Element für Vorschau nicht gefunden!");
          return;
      }
      if (!loadedPresetData) {
          console.error("DIAGNOSE-FEHLER: Preset-Daten sind noch nicht geladen.");
          return;
      }

      const provider = providerSelect.value;
      const variation = variationSelect.value;

      // Wir loggen die exakten Werte, die die Funktion sieht
      console.log(`DIAGNOSE: Gelesener Provider-Wert -> "${provider}"`);
      console.log(`DIAGNOSE: Gelesener Variation-Wert -> "${variation}"`);

      if (!provider || !variation) {
          console.error("DIAGNOSE-STOP: Einer der Werte ist leer. Ladevorgang wird abgebrochen.");
          stylePreviewImg.style.display = 'none';
          placeholder.style.display = 'flex';
          placeholder.textContent = "Wähle ein Preset (Debug)";
          return;
      }

      const cleanVar = variation.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
      const filename = `${cleanVar}_${provider}.png`;
      const imageUrl = `http://localhost:8001/assets/previews/${filename}`;

      console.log(`DIAGNOSE: Berechneter Dateiname -> "${filename}"`);
      console.log(`DIAGNOSE: Finale URL -> "${imageUrl}"`);

      const imgTester = new Image();
      imgTester.onload = function() {
          console.log(`%cDIAGNOSE-ERFOLG: Bild "${filename}" geladen!`, 'color: lightgreen; font-weight: bold;');
          stylePreviewImg.src = imageUrl;
          stylePreviewImg.style.display = 'block';
          placeholder.style.display = 'none';
      };
      imgTester.onerror = function() {
          console.error(`%cDIAGNOSE-FEHLER: Bild "${filename}" konnte nicht geladen werden. Prüfe Pfad und Dateinamen!`, 'color: orange; font-weight: bold;');
          stylePreviewImg.style.display = 'none';
          placeholder.style.display = 'flex';
          placeholder.innerHTML = `<div style="text-align:center; font-size:0.8em; color:#666;">Bild fehlt:<br>${filename}</div>`;
      };
      
      imgTester.src = imageUrl;
  }

  // --- PRESETS V2.0 LOGIK START ---
  let loadedPresetData = null;
  
  // Globale Variablen für den Generierungskontext
  let lastContextIds = { response_id: null, image_id: null };
  let lastGeneratedPrompt = null;
  let lastGeneratedImageBase64 = null;
  
  // --- NEU: Zentrale Funktion zur Steuerung der Preset-Spalten ---
  function updatePresetVisibility() {
      const presetsActive = document.getElementById('is-presets-mode').checked;
      
      const editModeActive = document.getElementById('is-edit-mode').checked;
      const applyToEditActive = document.getElementById('is-apply-preset-to-edit')?.checked || false;
  
      const refineModeActive = document.getElementById('is-refine-mode').checked;
      const applyToRefineActive = document.getElementById('is-apply-preset-to-refine')?.checked || false;
      
      // Sichtbarkeit: Entweder Haupt-Preset-Modus AN, ODER Edit+Preset AN, ODER Refine+Preset AN
      const shouldBeVisible = presetsActive || 
                             (editModeActive && applyToEditActive) || 
                             (refineModeActive && applyToRefineActive);
      
      // 1. Mittlere Spalte (Dropdowns & Text)
      if (presetsContainer) {
          presetsContainer.style.display = shouldBeVisible ? 'flex' : 'none'; // 'flex' für Layout
      }

      // 2. Rechte Spalte (Bild-Vorschau) - DAS HAT GEFEHLT
      if (stylePreviewContainer) {
          stylePreviewContainer.style.display = shouldBeVisible ? 'flex' : 'none';
      }
      
      // Aufräumen wenn unsichtbar
      if (!shouldBeVisible) {
          if (styleSelect && styleSelect.options.length > 0) styleSelect.selectedIndex = 0;
          // Variation nicht nullen, sonst verlieren wir Status, aber UI ist eh weg
          if (stylePreviewImg) stylePreviewImg.style.display = 'none';
          if (styleImagePlaceholder) styleImagePlaceholder.style.display = 'flex';
      }
  }
  
  // Toggle visibility of the 'Apply Preset to Refine' checkbox
  function togglePresetForRefineUI() {
    const refineCheckbox = document.getElementById('is-refine-mode');
    if (!refineCheckbox || !applyPresetToRefineContainer) return;

    if (refineCheckbox.checked) {
      applyPresetToRefineContainer.style.display = 'block';
    } else {
      applyPresetToRefineContainer.style.display = 'none';
      if (applyPresetToRefineCheckbox) {
        applyPresetToRefineCheckbox.checked = false;
      }
    }
    updatePresetVisibility();
  }

  // Toggle visibility of the 'Apply Preset to Edit' checkbox
  function togglePresetForEditUI() {
    if (!editModeCheckbox || !applyPresetContainer) return;

    if (editModeCheckbox.checked) {
      applyPresetContainer.style.display = 'block';
    } else {
      applyPresetContainer.style.display = 'none';
      if (applyPresetCheckbox) {
        applyPresetCheckbox.checked = false; // Reset when hiding
      }
    }
    updatePresetVisibility();
  }

  async function fetchPresets() {
    try {
        // Pfad zum Backend-Endpoint
        const response = await fetch('http://localhost:8001/api/images/presets/list');
        
        if (!response.ok) throw new Error('Failed to load presets');
        
        loadedPresetData = await response.json();
        console.log("Presets loaded:", loadedPresetData);
        populateStyleSelect(); 
    } catch (error) {
        console.error("Error loading presets:", error);
    }
  }

  function populateStyleSelect() {
    styleSelect.innerHTML = '';
    
    if (!loadedPresetData) {
        const option = document.createElement('option');
        option.text = "Lade...";
        styleSelect.add(option);
        return;
    }

    for (const styleName in loadedPresetData) {
      const option = document.createElement('option');
      option.value = styleName;
      option.textContent = styleName;
      styleSelect.appendChild(option);
    }
    populateVariationSelect();
  }

  function populateVariationSelect() {
    const selectedStyle = styleSelect.value;
    variationSelect.innerHTML = '';

    if (loadedPresetData && loadedPresetData[selectedStyle]) {
        const variations = loadedPresetData[selectedStyle];
        Object.keys(variations).forEach(variationName => {
            const option = document.createElement('option');
            option.value = variationName;
            option.textContent = variationName;
            variationSelect.appendChild(option);
        });
    }
    
    // Aktualisiere die Text-Info
    updatePresetInfoBox();
    
    // Das Bild wird jetzt vom aufrufenden Event-Listener aktualisiert
    // (in styleSelect.addEventListener('change', ...))
  }

  function updatePresetInfoBox() {
    const style = styleSelect.value;
    const variation = variationSelect.value;
    const infoBox = document.getElementById('preset-info-display');
    
    if (!infoBox) return; 
    
    if (!loadedPresetData || !loadedPresetData[style] || !loadedPresetData[style][variation]) {
        infoBox.style.display = 'none';
        return;
    }

    const config = loadedPresetData[style][variation];
    const usageText = config.recommended_use || "Standard preset configuration.";

    infoBox.innerHTML = `
        <div style="margin-bottom: 10px;">
            <strong style="color: var(--accent-color); display:block; font-size: 0.85em; margin-bottom:4px; text-transform:uppercase;">🎯 ${config.name}</strong>
            <div style="font-size: 0.9em; color: #ddd; line-height: 1.4; margin-bottom: 6px;">${config.preset_intent}</div>
            <div style="font-size: 0.85em; color: #aaa; font-style: italic; border-left: 2px solid var(--accent-color); padding-left: 8px;">
                Empfohlen für: ${usageText}
            </div>
        </div>
        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 0.8em; color: #bbb;">
            <div>📸 ${config.camera}</div>
            <div>🔍 ${config.lens}</div>
            <div>🎞️ ${config.film_stock}</div>
            <div>💡 ${config.lighting}</div>
        </div>
    `;
    
    infoBox.style.display = 'block';
  }
  // --- PRESET WIEDERHERSTELLUNG (REIN DATA) ---
  function restorePresetSettings(style, variation) {
    if (!style || !variation) return;

    console.log("Stelle Preset-Werte wieder her (UI-Agnostisch):", style, variation);

    // WICHTIG: Wir fassen hier KEINE Checkboxen mehr an!
    // Das Aktivieren der richtigen Checkbox (Main, Edit oder Refine)
    // ist Aufgabe des Aufrufers (loadImageContext).

    // 1. Stil auswählen
    if (styleSelect) {
        styleSelect.value = style;
        // Variationen für diesen Stil laden
        populateVariationSelect();
    }

    // 2. Variation auswählen
    if (variationSelect) {
        variationSelect.value = variation;
        
        // Info-Box und Vorschau-Bild aktualisieren
        updatePresetInfoBox();
        updateStylePreviewImage();
    }
  }

  // --- PRESETS V2.0 LOGIK ENDE ---

  // Inpainting State
  let isDrawing = false;
  let ctx = null;
  let currentImageElement = null;
  let hiddenMaskCanvas = null;
  let hiddenCtx = null;

  let pricingData = null;
  let referenceImageUrl = null; 
  let currentImageFullUrl = null;
  
  // --- MASKING V8 ---
  let canvasScaleFactor = 1;
  let isInitDone = false;

  const isResolutionSelect = document.getElementById('is-resolution-select');
  const isResolutionControlGroup = document.getElementById('is-resolution-control-group');
  const openImageModal = window.openImageModal; 

    function initInpainting() {
        const img = previewContainer.querySelector('img');
        const wrapper = document.getElementById('is-preview-wrapper');
        
        if (!img || !wrapper) return;

        if (!img.complete || img.naturalWidth === 0) {
            img.onload = initInpainting;
            return;
        }

        const MAX_DISPLAY = 512;
        const ratio = img.naturalWidth / img.naturalHeight;
        
        let displayW, displayH;
        if (ratio > 1) {
            displayW = MAX_DISPLAY;
            displayH = MAX_DISPLAY / ratio;
        } else {
            displayH = MAX_DISPLAY;
            displayW = displayH * ratio;
        }

        if (isInitDone && Math.abs(parseFloat(wrapper.style.width) - displayW) < 1) return;

        console.log("Initializing Inpainting V8...");

        wrapper.style.width = `${displayW}px`;
        wrapper.style.height = `${displayH}px`;
        
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'fill';

        maskCanvas.width = img.naturalWidth;
        maskCanvas.height = img.naturalHeight;
        
        maskCanvas.style.width = '100%';
        maskCanvas.style.height = '100%';
        maskCanvas.style.top = '0px';
        maskCanvas.style.left = '0px';
        
        canvasScaleFactor = img.naturalWidth / displayW;
        
        ctx = maskCanvas.getContext('2d');
        ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
        
        updateBrushStyle();
        
        isInitDone = true;
        console.log(`Canvas V8 Ready: Native ${maskCanvas.width}x${maskCanvas.height}, Scale ${canvasScaleFactor.toFixed(2)}`);
    }
  
  function updateCanvasSize() {
    const img = previewContainer.querySelector('img');
    if (img && img.complete) {
      maskCanvas.width = img.width;
      maskCanvas.height = img.height;
      const imgRect = img.getBoundingClientRect();
      const containerRect = previewWrapper.getBoundingClientRect();
      maskCanvas.style.top = (imgRect.top - containerRect.top) + 'px';
      maskCanvas.style.left = (imgRect.left - containerRect.left) + 'px';
    }
  }
  
  function clearMaskCanvas() {
    if (ctx) {
      ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    }
    if (hiddenCtx && hiddenMaskCanvas) {
      hiddenCtx.clearRect(0, 0, hiddenMaskCanvas.width, hiddenMaskCanvas.height);
    }
  }

  // --- Inpainting Event Listeners ---
  maskModeCheckbox.addEventListener('change', (e) => {
    const wrapper = document.getElementById('is-preview-wrapper');
    const img = previewContainer.querySelector('img');

    if (e.target.checked) {
      if (!currentImageFullUrl) {
        alert("Bitte lade zuerst ein Bild hoch, um mit dem Maskieren zu beginnen.");
        e.target.checked = false;
        return;
      }
      
      document.getElementById('is-edit-mode').checked = false;
      document.getElementById('is-refine-mode').checked = false;
      document.getElementById('is-combine-mode').checked = false;
      
      maskCanvas.style.display = 'block';
      maskCanvas.classList.add('active');
      maskControls.style.display = 'flex';
      
      setTimeout(initInpainting, 50);
      updateCanvasSize();
      initInpainting();
    } else {
      maskCanvas.style.display = 'none';
      maskCanvas.classList.remove('active');
      maskControls.style.display = 'none';
      
      if (wrapper) {
        wrapper.style.width = '512px'; 
        wrapper.style.height = '512px'; 
      }
      if (img) {
        img.style.width = 'auto';
        img.style.height = 'auto';
        img.style.objectFit = 'contain';
      }
    }
  });

  clearMaskBtn.addEventListener('click', () => {
    clearMaskCanvas();
  });

  brushSizeInput.addEventListener('input', updateBrushStyle);

  function getCanvasCoordinates(e) {
      const rect = maskCanvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      return {
          x: x * canvasScaleFactor,
          y: y * canvasScaleFactor
      };
  }

  function updateBrushStyle() {
    if (!ctx) return;
    const baseSize = document.getElementById('brush-size').value;
    ctx.lineWidth = baseSize * canvasScaleFactor; 
    ctx.strokeStyle = '#ff0000'; 
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }
  
  document.getElementById('brush-size').addEventListener('input', updateBrushStyle);

  function getNativeCoords(e) {
    const rect = maskCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    return {
      x: x * canvasScaleFactor,
      y: y * canvasScaleFactor
    };
  }

  function startDrawing(e) {
    if (!maskModeCheckbox.checked) return;
    isDrawing = true;
    const p = getNativeCoords(e);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    draw(e);
  }

  function draw(e) {
    if (!isDrawing) return;
    const p = getNativeCoords(e);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  }

  function stopDrawing() {
    isDrawing = false;
    ctx.beginPath(); 
  }

  maskCanvas.addEventListener('mousedown', startDrawing);
  maskCanvas.addEventListener('mousemove', draw);
  maskCanvas.addEventListener('mouseup', stopDrawing);
  maskCanvas.addEventListener('mouseout', stopDrawing);
  
  // Touch events
  maskCanvas.addEventListener('touchstart', (e) => {
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
      clientX: touch.clientX,
      clientY: touch.clientY
    });
    maskCanvas.dispatchEvent(mouseEvent);
  });

  maskCanvas.addEventListener('touchmove', (e) => {
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
      clientX: touch.clientX,
      clientY: touch.clientY
    });
    maskCanvas.dispatchEvent(mouseEvent);
  });

  maskCanvas.addEventListener('touchend', () => {
    const mouseEvent = new MouseEvent('mouseup', {});
    maskCanvas.dispatchEvent(mouseEvent);
  });

  previewContainer.addEventListener('load', (e) => {
    if (e.target.tagName === 'IMG') {
      updateCanvasSize();
    }
  }, true);

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        const img = previewContainer.querySelector('img');
        if (img) {
          currentImageElement = img;
          if (img.complete) {
            updateCanvasSize();
          } else {
            img.onload = () => {
              updateCanvasSize();
            };
          }
        }
      }
    });
  });

  observer.observe(previewContainer, { childList: true, subtree: true });

  // --- Event Listeners UI ---
  openBtn.addEventListener('click', () => {
    modal.style.display = 'flex';
    if (!pricingData) {
      loadPricingData();
    }
    initInpainting();
  });

  closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  window.addEventListener('click', (event) => {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });

  providerSelect.addEventListener('change', () => {
    populateModelSelect();
    updateCost();
  });

  modelSelect.addEventListener('change', () => {
    const newModel = modelSelect.value;
    if (!newModel.startsWith('gpt-image-')) {
      lastContextIds = { response_id: null, image_id: null };
      document.getElementById('is-refine-mode').checked = false;
    }
    populateDynamicParams();
    updateCost();
  });

  // --- Exklusive Modi ---
  const exclusiveModeCheckboxes = ['is-refine-mode', 'is-edit-mode', 'is-mask-mode', 'is-combine-mode'];

  function updateExclusiveModes(activeModeId) {
    exclusiveModeCheckboxes.forEach(id => {
      if (id !== activeModeId) {
        document.getElementById(id).checked = false;
      }
    });
    if(activeModeId === 'is-combine-mode') {
         slotsWrapper.style.display = 'block';
         promptInput.placeholder = "Beschreibe, wie die Bilder kombiniert werden sollen...";
    } else {
        slotsWrapper.style.display = 'none';
        promptInput.placeholder = "Beschreibe dein Bild...";
    }
    
    // Handle refine mode specific UI updates
    if (activeModeId === 'is-refine-mode') {
        togglePresetForRefineUI();
    } else {
        // Bei anderen Modi sicherstellen, dass es weg ist
        const container = document.getElementById('apply-preset-to-refine-container');
        if (container) container.style.display = 'none';
    }
  }

  // Initialize event listeners for exclusive mode checkboxes
  exclusiveModeCheckboxes.forEach(id => {
    const checkbox = document.getElementById(id);
    if (!checkbox) return;
    
    // Special handling for refine mode checkbox
    if (id === 'is-refine-mode') {
      checkbox.addEventListener('change', (e) => {
        updateExclusiveModes(id);
        togglePresetForRefineUI();
        updatePresetVisibility();
      });
      return;
    }
    
    checkbox.addEventListener('change', (e) => {
      if (e.target.checked) {
        updateExclusiveModes(id);
      }
      
      // Handle refine mode specific logic
      if (id === 'is-refine-mode') {
        togglePresetForRefineUI();
      }
      
      // Update both UI states when any exclusive mode changes
      togglePresetForEditUI();
      updatePresetVisibility(); // Update preset visibility based on new state
    });
  });
  
  // Event listener for apply preset to refine checkbox
  if (applyPresetToRefineCheckbox) {
    applyPresetToRefineCheckbox.addEventListener('change', (e) => {
      updatePresetVisibility();
      if (e.target.checked) {
        // Sofort Presets laden (Variation & Bild)
        populateVariationSelect();
        updateStylePreviewImage();
      }
    });
  }

  generateBtn.addEventListener('click', generateImage);
  
  // --- Drag-and-Drop Preview ---
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
    
    // Check for image ID from gallery first (new approach)
    const imageId = event.dataTransfer.getData('application/janus-image-id');
    
    if (imageId) {
      console.log("Image dropped from gallery with ID:", imageId);
      previewContainer.innerHTML = '<div class="loader"></div>';
      
      try {
        // 1. Kontext laden
        const response = await fetch(`http://localhost:8001/api/context_by_id/${imageId}`);
        if (!response.ok) throw new Error('Konnte den Bildkontext nicht laden.');
        
        const context = await response.json();
        console.log("Kontext für Drop geladen:", context);
        
        // 2. Bild URL holen
        const galleryImg = document.querySelector(`.gallery-thumbnail[data-image-id="${imageId}"]`);
        if (!galleryImg) throw new Error('Bild in der Galerie nicht gefunden.');
        
        const imageUrl = galleryImg.src;
        updatePreviewImage(imageUrl, "Geladenes Bild");
        currentImageFullUrl = imageUrl; // WICHTIG: URL global setzen für Refine/Edit

        // Globalen Kontext aktualisieren (für Refine Mode wichtig)
        lastContextIds.response_id = context.response_id;
        lastContextIds.image_id = imageId; // oder context.image_id
        
        // 3. Modus-Entscheidung: Refine vs. Edit
        if (context.response_id) {
            // Es ist ein generiertes Bild -> REFINE Mode
            console.log("Generiertes Bild erkannt -> Schalte auf REFINE Mode");
            document.getElementById('is-refine-mode').checked = true;
            document.getElementById('is-edit-mode').checked = false;
            
            // Edit-spezifische Checkboxen zurücksetzen
            const applyPresetBox = document.getElementById('is-apply-preset-to-edit');
            if (applyPresetBox) applyPresetBox.checked = false;
            
            updateExclusiveModes('is-refine-mode');
        } else {
            // Es ist ein Upload -> EDIT Mode
            console.log("Upload erkannt -> Schalte auf EDIT Mode");
            setEditMode();
        }

        // 4. Presets Logik (Präzise Prüfung)
        // Wir prüfen strikt, ob echte Werte vorhanden sind (keine leeren Strings)
        const hasStyle = context.style_preset && context.style_preset !== "" && context.style_preset !== "null";
        const hasVar = context.variation_preset && context.variation_preset !== "" && context.variation_preset !== "null";

        if (hasStyle && hasVar) {
            console.log(`Presets gefunden: "${context.style_preset}" / "${context.variation_preset}" -> Aktiviere UI`);
            restorePresetSettings(context.style_preset, context.variation_preset);

            // NEU: Hake die richtige "Apply Preset" Checkbox an
            if (document.getElementById('is-refine-mode').checked) {
                if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = true;
            } else if (document.getElementById('is-edit-mode').checked) {
                if (applyPresetCheckbox) applyPresetCheckbox.checked = true;
            }

        } else {
            console.log("Keine Presets im Kontext -> Deaktiviere alle Preset-Optionen");
            
            // Alle relevanten Preset-Checkboxen ausschalten
            if (presetsModeCheckbox) presetsModeCheckbox.checked = false;
            if (applyPresetCheckbox) applyPresetCheckbox.checked = false;
            if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = false;
            
            // Dropdowns auf Standard zurücksetzen
            if (styleSelect) {
                styleSelect.selectedIndex = 0;
                populateVariationSelect(); 
            }
            
            // Info-Box leeren/verstecken
            const infoBox = document.getElementById('preset-info-display');
            if (infoBox) infoBox.style.display = 'none';
        }
        
        // WICHTIG: UI-Sichtbarkeit *IMMER* am Ende basierend auf dem finalen State aktualisieren
        updatePresetVisibility();
        
      } catch (error) {
        console.error('Fehler beim Laden des Bildes:', error);
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
      }
      return;
    }
    
    // Fallback: Check for file drop
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      if (!file.type.startsWith('image/')) {
        alert('Bitte laden Sie nur Bilddateien hoch.');
        return;
      }
      previewContainer.innerHTML = '<div class="loader"></div>';
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('http://localhost:8001/api/images/upload', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload fehlgeschlagen');
        }
        
        const imageData = await response.json();
        const newImageUrl = `http://localhost:8001${imageData.image_url}`;

        // Update the preview
        updatePreviewImage(newImageUrl, "Hochgeladenes Bild");
        
        // Add to gallery and update UI
        addImageToGallery(imageData, uploadedGallery);
        
        const filename = imageData.image_url.split('/').pop();
        imageFilenameInput.value = filename.split('.').slice(0, -1).join('.');

        // Set edit mode and update UI
        setEditMode();
        
      } catch (error) {
        console.error('Fehler beim Hochladen des Bildes:', error);
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
      }
      return; 
    }

    // Legacy fallback: Check for image URL from gallery (old approach)
    const imageUrl = event.dataTransfer.getData('text/plain');
    if (imageUrl) {
      // Set edit mode and update UI
      setEditMode();
      
      // Load image context
      try {
        await loadImageContext(imageUrl);
      } catch (error) {
        console.error('Fehler beim Laden des Bildkontexts:', error);
      }
    }
  });
  
  imageFilenameInput.addEventListener('blur', async () => {
    await renameImageFile();
  });
  
  imageFilenameInput.addEventListener('keydown', async (event) => {
    if (event.key === 'Enter') {
      event.preventDefault(); 
      imageFilenameInput.blur(); 
    }
  });
  
  async function renameImageFile() {
    if (!currentImageFullUrl) {
      console.warn("Kein Bild geladen, Dateiname kann nicht geändert werden.");
      return;
    }
    const oldFilenameWithExtension = currentImageFullUrl.match(/\/([^\/]+)$/)[1];
    const oldFilename = oldFilenameWithExtension.split('.')[0];
    const fileExtension = oldFilenameWithExtension.split('.').pop();
    const newFilename = imageFilenameInput.value.trim();
  
    if (newFilename === oldFilename || newFilename === "") {
      imageFilenameInput.value = oldFilename; 
      return;
    }
  
    const newFullFilenameWithExtension = `${newFilename}.${fileExtension}`;
    const oldLocalPath = currentImageFullUrl.replace('http://localhost:8001/user_images/', '');
  
    try {
      const response = await fetch('http://localhost:8001/api/images/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_path: oldLocalPath, new_filename: newFullFilenameWithExtension })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Fehler beim Umbenennen der Datei');
      }
      const newImageData = await response.json();
      const newImageUrl = `http://localhost:8001${newImageData.image_url}`;
      currentImageFullUrl = newImageUrl;
      if (previewContainer.querySelector('img')) {
          previewContainer.querySelector('img').src = newImageUrl;
      }
      const oldThumbnailSrc = currentImageFullUrl.replace(newFullFilenameWithExtension, oldFilenameWithExtension); 
      const allThumbnails = document.querySelectorAll('.gallery-thumbnail');
      allThumbnails.forEach(thumbnail => {
          if (thumbnail.src === oldThumbnailSrc) {
              thumbnail.src = newImageUrl;
              if (thumbnail.alt.includes(oldFilename)) {
                  thumbnail.alt = thumbnail.alt.replace(oldFilename, newFilename);
              }
          }
      });
  
    } catch (error) {
      console.error("Fehler beim Umbenennen der Datei:", error);
      alert(`Fehler beim Umbenennen der Datei: ${error.message}`);
      imageFilenameInput.value = oldFilename; 
    }
  }

  // --- Combine Slots Logic ---
  const combineCheckbox = document.getElementById('is-combine-mode');
  const slotsWrapper = document.getElementById('combine-slots-wrapper');
  const slots = document.querySelectorAll('.combine-slot');
  let combineSlotsData = [null, null, null, null, null];

  combineCheckbox.addEventListener('change', (e) => {
    if (e.target.checked) {
      slotsWrapper.style.display = 'block';
      document.getElementById('is-refine-mode').checked = false;
      document.getElementById('is-edit-mode').checked = false;
      promptInput.placeholder = "Beschreibe, wie die Bilder kombiniert werden sollen...";
    } else {
      slotsWrapper.style.display = 'none';
      promptInput.placeholder = "Beschreibe dein Bild...";
    }
  });

  slots.forEach(slot => {
    slot.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!slot.classList.contains('filled')) {
        slot.classList.add('drag-over');
      }
    });
    slot.addEventListener('dragleave', () => {
      slot.classList.remove('drag-over');
    });
    slot.addEventListener('drop', (e) => {
      e.preventDefault();
      slot.classList.remove('drag-over');
      const imageUrl = e.dataTransfer.getData('text/plain');
      if (!imageUrl) return;
      const index = parseInt(slot.dataset.index);
      combineSlotsData[index] = imageUrl;
      updateSlotsUI();
    });
    slot.addEventListener('click', () => {
      const index = parseInt(slot.dataset.index);
      if (combineSlotsData[index]) {
        combineSlotsData[index] = null;
        updateSlotsUI();
      }
    });
  });

  function updateSlotsUI() {
    slots.forEach((slot, index) => {
      const url = combineSlotsData[index];
      slot.innerHTML = ''; 
      slot.classList.remove('filled');
      if (url) {
        slot.classList.add('filled');
        const img = document.createElement('img');
        img.src = url;
        slot.appendChild(img);
        const removeDiv = document.createElement('div');
        removeDiv.classList.add('remove-slot-btn');
        removeDiv.innerHTML = '&times;'; 
        slot.appendChild(removeDiv);
      } else {
        slot.textContent = index + 1;
      }
    });
  }

    uploadedGallery.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadedGallery.classList.add('drag-over');
    });

    uploadedGallery.addEventListener('dragleave', () => {
        uploadedGallery.classList.remove('drag-over');
    });

    uploadedGallery.addEventListener('drop', async (event) => {
        event.preventDefault();
        uploadedGallery.classList.remove('drag-over');
        const files = event.dataTransfer.files;
        if (files && files.length > 0) {
            const hint = uploadedGallery.querySelector('.is-empty-hint');
            if (hint) hint.remove();
            for (const file of files) {
                if (!file.type.startsWith('image/')) {
                    continue;
                }
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await fetch('http://localhost:8001/api/images/upload', {
                        method: 'POST',
                        body: formData
                    });
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Upload failed');
                    }
                    const imageData = await response.json();
                    addImageToGallery(imageData, uploadedGallery);
                } catch (error) {
                    console.error('Error uploading file:', file.name, error);
                }
            }
        }
    });

    function addImageToGallery(imageData, galleryElement) {
        const hint = galleryElement.querySelector('.is-empty-hint');
        if (hint) hint.remove();
        const fullImageUrl = `http://localhost:8001${imageData.image_url}`;
        const thumbnailImg = document.createElement('img');
        thumbnailImg.src = fullImageUrl;
        thumbnailImg.alt = imageData.prompt || 'Uploaded image';
        thumbnailImg.classList.add('gallery-thumbnail');
        thumbnailImg.draggable = true;
        // Store the image ID as a data attribute
        thumbnailImg.dataset.imageId = imageData.id;
        
        thumbnailImg.addEventListener('click', () => {
            openImageModal(fullImageUrl);
        });
        
        // Update the dragstart event to use the image ID
        thumbnailImg.addEventListener('dragstart', (event) => {
            // Store the image ID in a custom data type
            event.dataTransfer.setData('application/janus-image-id', imageData.id);
            event.dataTransfer.effectAllowed = 'copy';
        });
        
        galleryElement.prepend(thumbnailImg);
    }
  
  function getMaskData() {
    if (!maskModeCheckbox.checked || !ctx) return null;
    const imgElement = previewContainer.querySelector('img');
    if (!imgElement) return null;
    
    const originalWidth = imgElement.naturalWidth || 1024;
    const originalHeight = imgElement.naturalHeight || 1024;
    
    const finalCanvas = document.createElement('canvas');
    finalCanvas.width = originalWidth;
    finalCanvas.height = originalHeight;
    const fCtx = finalCanvas.getContext('2d');
    
    fCtx.fillStyle = 'black';
    fCtx.fillRect(0, 0, originalWidth, originalHeight);
    fCtx.globalCompositeOperation = 'destination-out';
    fCtx.imageSmoothingEnabled = false; 
    
    fCtx.drawImage(
      maskCanvas, 
      0, 0, maskCanvas.width, maskCanvas.height, 
      0, 0, originalWidth, originalHeight        
    );
    
    fCtx.imageSmoothingEnabled = true;
    return finalCanvas.toDataURL('image/png');
  }

  // --- Logic ---
  async function loadPricingData() {
    try {
      const response = await fetch('http://localhost:8001/api/images/pricing');
      if (!response.ok) {
        throw new Error('Fehler beim Laden der Preisdaten');
      }
      pricingData = await response.json();
      console.log('Loaded pricingData:', pricingData);
      populateProviderSelect();    
    } catch (error) {
      console.error(error);
      costDisplay.textContent = 'Fehler';
    }
  }

  function populateProviderSelect() {
    providerSelect.innerHTML = '';
    if (!pricingData) return;

    const availableProviders = Object.keys(pricingData);
    if (availableProviders.length === 0) return;

    availableProviders.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider;
        providerSelect.appendChild(option);
    });

    if (!providerSelect.value || !pricingData[providerSelect.value]) {
        providerSelect.value = availableProviders[0];
    }
    populateModelSelect();
  }

  function populateModelSelect() {
    modelSelect.innerHTML = '';
    const selectedProvider = providerSelect.value;
    if (pricingData && pricingData[selectedProvider]) {
      const imageModels = Object.entries(pricingData[selectedProvider]).filter(([modelId, modelData]) => {
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

      if(!pricingData || !pricingData[selectedProvider] || !pricingData[selectedProvider][selectedModelId]) {
          updateCost();
          return;
      }

      const modelData = pricingData[selectedProvider][selectedModelId];
      
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
          
          // Add event listener for resolution changes
          sizeSelect.addEventListener('change', () => {
              updateCost();
          });
          
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
          } else {
            isResolutionControlGroup.style.display = 'none'; 
          }
          updateCost();

      } else {
          isResolutionControlGroup.style.display = 'none'; 
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

    if (!pricingData || !selectedProvider || !selectedModelId) {
      costDisplay.textContent = 'N/A';
      return;
    }

    try {
      const modelData = pricingData[selectedProvider]?.[selectedModelId];
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
        } else {
            finalCost = 'N/A';
        }
      } 
      else if (modelData.type === 'image' && modelData.aspect_ratios) {
          const ratioSelect = dynamicParamsContainer.querySelector('#is-param-aspect-ratio');
          const resolutionSelect = document.getElementById('is-resolution-select'); 

          const selectedResolution = resolutionSelect ? resolutionSelect.value : (modelData.default_resolution || "1K");
          
          if (modelData.cost_per_million_tokens_input && modelData.cost_per_million_tokens_output && modelData.tokens_per_resolution) {
              const outputTokensPerImage = modelData.tokens_per_resolution[selectedResolution] || modelData.tokens_per_resolution["1K"] || 1120; 
              const inputTokensPerImage = 560; 
              
              const inputCostPerImage = (inputTokensPerImage / 1000000) * modelData.cost_per_million_tokens_input;
              const outputCostPerImage = (outputTokensPerImage / 1000000) * modelData.cost_per_million_tokens_output;
              finalCost = inputCostPerImage + outputCostPerImage;
              
          } else if (modelData.cost_per_image) {
              finalCost = modelData.cost_per_image;
          } else {
              finalCost = 'N/A';
          }

      }
      else {
        isResolutionControlGroup.style.display = 'none'; 
        const params = {};
        dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
            params[sel.dataset.paramKey] = sel.value;
        });

        if (modelData.cost_per_image) {
            finalCost = modelData.cost_per_image;
        } else if (modelData.cost_per_token_input && modelData.cost_per_token_output) {
            finalCost = "Variiert";
        } else if (modelData.cost_per_query) {
             finalCost = modelData.cost_per_query;
        } else {
            const firstParamKey = Object.keys(modelData).find(key => typeof modelData[key] === 'object' && key !== 'pricing' && key !== 'capabilities');
            if (firstParamKey && params[firstParamKey]) {
                 finalCost = modelData[firstParamKey]?.[params[firstParamKey]];
            } else if (typeof modelData === 'number') {
                finalCost = modelData;
            } else {
                finalCost = 'N/A';
            }
        }
      }
      
      if (typeof finalCost === 'number') {
        const basePrice = finalCost.toFixed(4);
        costDisplay.textContent = `$${basePrice}`;
        
        const gateLevel = qualityGateSelect ? qualityGateSelect.value : 'none';

        if (gateLevel === 'none' || finalCost === 0) {
            if (maxCostWrapper) maxCostWrapper.style.display = 'none';
        } else {
            if (maxCostWrapper) maxCostWrapper.style.display = 'flex';
            
            const config = QUALITY_GATE_CONFIG[gateLevel];
            const totalRuns = 1 + config.retries;
            
            const maxRisk = (finalCost + ESTIMATED_VISION_COST) * totalRuns;
            
            if (maxCostDisplay) {
                maxCostDisplay.textContent = `$${maxRisk.toFixed(4)}`;
            }
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
    const actualResultWrapper = document.getElementById('is-actual-result-wrapper');
    const maxCostWrapper = document.getElementById('is-max-cost-wrapper');
    
    if (actualResultWrapper) actualResultWrapper.style.display = 'none';
    if (maxCostWrapper && document.getElementById('is-quality-gate-select').value !== 'none') {
        maxCostWrapper.style.display = 'flex'; 
    }
    
    previewContainer.innerHTML = '<div class="loader"></div>';
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generiere...';
    
    const refineActive = document.getElementById('is-refine-mode').checked;
    const editModeActive = document.getElementById('is-edit-mode').checked;
    const combineModeActive = document.getElementById('is-combine-mode').checked;
    
    const activeCombineImages = combineSlotsData.filter(url => url !== null);
    
    if (combineModeActive && activeCombineImages.length < 1) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte ziehe mindestens ein Bild in die nummerierten Felder.</p>';
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generieren';
      return;
    }
    
    if (editModeActive && !currentImageFullUrl) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte lade zuerst ein Bild hoch, um es zu bearbeiten.</p>';
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generieren';
      return;
    }
    
    // Define when to apply presets
    const applyRefinePreset = document.getElementById('is-apply-preset-to-refine')?.checked || false;
    const applyEditPreset = document.getElementById('is-apply-preset-to-edit')?.checked || false;
    
    const shouldSendPresets = presetsModeCheckbox.checked || 
                            (editModeActive && applyEditPreset) || 
                            (refineActive && applyRefinePreset);

    const payload = {
        prompt: promptInput.value,
        provider: providerSelect.value,
        model: modelSelect.value, 
        parameters: {},
        quality_gate_level: qualityGateSelect ? qualityGateSelect.value : 'none',
        previous_response_id: (refineActive && !combineModeActive) ? lastContextIds.response_id : null,
        previous_image_id: (refineActive && !combineModeActive) ? lastContextIds.image_id : null,
        apply_preset_to_edit: applyEditPreset,
        apply_preset_to_refine: applyRefinePreset,
        style_preset: shouldSendPresets ? styleSelect.value : null,
        variation_preset: shouldSendPresets ? variationSelect.value : null,
        
        // Debug information
        history: (refineActive && providerSelect.value === 'gemini') ? {
            prompt: lastGeneratedPrompt,
            image_base64: lastGeneratedImageBase64
        } : null,
        
        reference_image_url: (
            editModeActive || 
            maskModeCheckbox.checked || 
            (refineActive && !lastContextIds.response_id) ||
            (refineActive && providerSelect.value === 'openai' && !lastContextIds.response_id) 
        ) ? currentImageFullUrl : null,
        
        reference_image_urls: combineModeActive ? activeCombineImages : [],
        
        mask_image_data: (() => {
            if (!maskModeCheckbox.checked) return null;
            const finalCanvas = document.createElement('canvas');
            finalCanvas.width = maskCanvas.width;   
            finalCanvas.height = maskCanvas.height; 
            const fCtx = finalCanvas.getContext('2d');
            fCtx.fillStyle = 'black';
            fCtx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);
            fCtx.globalCompositeOperation = 'destination-out';
            fCtx.drawImage(maskCanvas, 0, 0); 
            return finalCanvas.toDataURL('image/png');
        })()
    };
    
    // Debug log for preset values
    console.log("PAYLOAD CHECK:", {
        style: payload.style_preset,
        variation: payload.variation_preset,
        apply_edit: payload.apply_preset_to_edit,
        editModeActive: editModeActive,
        presetsModeActive: presetsModeCheckbox.checked
    });
    
    console.log("Sending payload:", payload);

    const selectedModelId = modelSelect.value; 
    dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
        payload.parameters[sel.dataset.paramKey] = sel.value;
    });

    if (selectedModelId.startsWith('gemini-3') && isResolutionControlGroup.style.display !== 'none') {
        payload.parameters['resolution'] = isResolutionSelect.value;
    }

    try {
        const response = await fetch('http://localhost:8001/api/images/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ein Fehler ist aufgetreten');
        }

        const result = await response.json();
        console.log("Server Result:", result); 
        
        if (result.quality_gate_stats && result.quality_gate_stats.was_active) {
            const stats = result.quality_gate_stats;
            const actualWrapper = document.getElementById('is-actual-result-wrapper');
            const maxWrapper = document.getElementById('is-max-cost-wrapper');

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

                if (maxWrapper) maxWrapper.style.display = 'none'; 
                actualWrapper.style.display = 'flex';             
            }
        }
        
        const imageUrl = `http://localhost:8001${result.image_url}`;
        currentImageFullUrl = imageUrl; 
        
        if (result.previous_response_id || result.previous_image_id) {
          lastContextIds = {
            response_id: result.previous_response_id || null,
            image_id: result.previous_image_id || null
          };
        } else {
          lastContextIds = { response_id: null, image_id: null };
        }
        
        lastGeneratedPrompt = payload.prompt;
        
        fetch(imageUrl)
            .then(res => res.blob())
            .then(blob => {
                const reader = new FileReader();
                reader.onload = () => {
                    lastGeneratedImageBase64 = reader.result.split(',')[1]; 
                };
                reader.readAsDataURL(blob);
            });
          
        document.getElementById('is-refine-mode').checked = true;
        document.getElementById('is-combine-mode').checked = false;
        document.getElementById('is-edit-mode').checked = false;
        document.getElementById('is-mask-mode').checked = false;
        togglePresetForRefineUI(); // <--- FIX: Menü sichtbar machen

        const filenameMatch = imageUrl.match(/\/([^\/]+)$/);
        if (filenameMatch && filenameMatch[1]) {
            imageFilenameInput.value = filenameMatch[1].split('.')[0]; 
        } else {
            imageFilenameInput.value = "unbenannt";
        }
        
        previewContainer.innerHTML = ''; 
        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = payload.prompt;
        imgElement.style.maxWidth = '100%';
        imgElement.style.maxHeight = '100%';
        imgElement.style.objectFit = 'contain';
        imgElement.style.cursor = 'pointer'; 
        
        imgElement.addEventListener('click', () => {
            openImageModal(imageUrl); 
        });

        previewContainer.appendChild(imgElement);
        addImageToGallery(result, generatedGallery);

    } catch (error) {
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
        console.error(error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generieren';
    }
  }

  function updateCapabilityUI() {
    const provider = providerSelect.value;
    const maskCheckbox = document.getElementById('is-mask-mode');
    const maskContainer = maskCheckbox.parentElement; 

    if (provider === 'gemini') {
      if (maskCheckbox.checked) {
        maskCheckbox.checked = false;
        maskCheckbox.dispatchEvent(new Event('change'));
      }
      maskCheckbox.disabled = true;
      maskContainer.style.opacity = '0.5';
      maskContainer.title = "Inpainting is currently not supported by Gemini.";
    } else {
      maskCheckbox.disabled = false;
      maskContainer.style.opacity = '1';
      maskContainer.title = "";
    }
  }

  // Helper function to update preview image
  function updatePreviewImage(src, alt) {
    previewContainer.innerHTML = '';
    const imgElement = document.createElement('img');
    imgElement.src = src;
    imgElement.alt = alt || "Vorschau";
    imgElement.style.maxWidth = '100%';
    imgElement.style.maxHeight = '100%';
    imgElement.style.objectFit = 'contain';
    previewContainer.appendChild(imgElement);
  }
  
  // Helper function to set edit mode
  function setEditMode() {
    editModeCheckbox.checked = true;
    document.getElementById('is-refine-mode').checked = false;
    document.getElementById('is-mask-mode').checked = false;
    document.getElementById('is-combine-mode').checked = false;
    updateExclusiveModes('is-edit-mode');
    togglePresetForEditUI();
  }
  
  // Helper function to load image context
  async function loadImageContext(imageUrl) {
    try {
      const contextRes = await fetch(`http://localhost:8001/api/images/context?url=${encodeURIComponent(imageUrl)}`);
      if (!contextRes.ok) throw new Error('Konnte Bildkontext nicht laden');
      
      const contextData = await contextRes.json();
      lastContextIds.response_id = contextData.response_id;
      lastContextIds.image_id = contextData.image_id;
      
      console.log("Bild-Kontext geladen:", contextData);

      // --- PHASE 1: TOTAL RESET (Sicherheits-Löschung) ---
      // Wir löschen alle Haken, BEVOR wir den Modus wechseln.
      // Das verhindert, dass alte Zustände kurzzeitig sichtbar werden.
      if (presetsModeCheckbox) presetsModeCheckbox.checked = false;
      const refinePresetCb = document.getElementById('is-apply-preset-to-refine');
      if (refinePresetCb) refinePresetCb.checked = false;
      const editPresetCb = document.getElementById('is-apply-preset-to-edit');
      if (editPresetCb) editPresetCb.checked = false;
      
      // UI Update erzwingen, damit alles sauber ist
      updatePresetVisibility();

      // --- PHASE 2: MODUS SETZEN ---
      if (contextData.response_id) {
        // Refine mode
        document.getElementById('is-refine-mode').checked = true;
        document.getElementById('is-edit-mode').checked = false;
        
        // Menü sichtbar machen (Checkbox ist aber FALSE)
        togglePresetForRefineUI(); 
        updateExclusiveModes('is-refine-mode');
      } else {
        // Edit mode
        document.getElementById('is-edit-mode').checked = true;
        document.getElementById('is-refine-mode').checked = false;
        
        // Menü sichtbar machen (Checkbox ist aber FALSE)
        togglePresetForEditUI();
        updateExclusiveModes('is-edit-mode');
      }

      // --- PHASE 3: PRESETS LADEN (Falls vorhanden) ---
      const hasStyle = contextData.style_preset && contextData.style_preset !== "" && contextData.style_preset !== "null";
      const hasVar = contextData.variation_preset && contextData.variation_preset !== "" && contextData.variation_preset !== "null";

      if (hasStyle && hasVar) {
          console.log(`Presets gefunden: "${contextData.style_preset}" / "${contextData.variation_preset}" -> Aktiviere UI`);

          // A. Werte in Dropdowns setzen (Daten)
          // Timeout hilft, um sicherzustellen, dass die UI-Container bereit sind
          setTimeout(() => {
              restorePresetSettings(contextData.style_preset, contextData.variation_preset);
          }, 0);

          // B. Die passende Checkbox aktivieren (UI)
          if (contextData.response_id) {
              // Refine
              if (refinePresetCb) refinePresetCb.checked = true;
          } else {
              // Edit
              if (editPresetCb) editPresetCb.checked = true;
          }
      } else {
          console.log("Keine Presets im Kontext -> UI bleibt im Reset-Zustand.");
          // Dropdowns auf Standard zurücksetzen (optisch)
          if (styleSelect) styleSelect.selectedIndex = 0;
          const infoBox = document.getElementById('preset-info-display');
          if (infoBox) infoBox.style.display = 'none';
      }

      // --- PHASE 4: FINALES UI UPDATE ---
      // Jetzt, wo alle Haken korrekt sitzen, aktualisieren wir die Sichtbarkeit der großen Boxen.
      updatePresetVisibility();
      
    } catch (err) {
      console.error("Fehler beim Laden des Bildkontexts:", err);
      // Fallback
      document.getElementById('is-edit-mode').checked = true;
      updateExclusiveModes('is-edit-mode');
    }
    updateCost();
  }
  
  // --- EVENT LISTENER: Vorschaubild anklickbar machen ---
  if (stylePreviewImg) {
    stylePreviewImg.addEventListener('click', () => {
      // Hole die aktuelle URL des Bildes
      const imageUrl = stylePreviewImg.src;

      // Prüfe, ob eine gültige URL vorhanden ist (kein leerer String)
      if (imageUrl && imageUrl.includes('/assets/previews/')) {
        // Rufe die globale Funktion zum Öffnen des Modals auf
        if (typeof window.openImageModal === 'function') {
          window.openImageModal(imageUrl);
        } else {
          console.warn('openImageModal function is not defined');
        }
      }
    });
  }

  // --- EVENT LISTENERS (HIER WIRD ALLES VERKNÜPFT) ---
  
  // Update model select event listener
  modelSelect.addEventListener('change', () => {
    populateDynamicParams();
    updateCost();
  });
  
  // Toggle both presets and style preview containers
  if (presetsModeCheckbox) {
    presetsModeCheckbox.addEventListener('change', updatePresetVisibility);
  } else {
    presetsContainer.style.display = 'none';
    if (stylePreviewContainer) stylePreviewContainer.style.display = 'none';
  }
  
  // Provider-Wechsel
  providerSelect.addEventListener('change', () => {
    updateCapabilityUI();
    populateModelSelect();
    updateCost();
    updateStylePreviewImage(); // Bild tauschen
  });

  // Style change handler
  styleSelect.addEventListener('change', () => {
    // Don't clear context when in refine+preset mode
    const isRefiningWithPreset = document.getElementById('is-refine-mode').checked && 
                               document.getElementById('is-apply-preset-to-refine').checked;
                               
    if (!isRefiningWithPreset) {
        clearGenerationContext();
    }
    
    populateVariationSelect(); // Update variations for the new style
    updateStylePreviewImage(); // Update the style preview image
  });

  // Variation change handler
  variationSelect.addEventListener('change', () => {
    const refineActive = document.getElementById('is-refine-mode').checked;
    const applyToRefine = document.getElementById('is-apply-preset-to-refine')?.checked || false;
    
    // Only clear context if not in refine+preset mode
    if (!(refineActive && applyToRefine)) {
      clearGenerationContext();
    }
    
    updateStylePreviewImage();
  });
  
  // Clear generation context when presets are changed
  function clearGenerationContext() {
    // Clear previous generation IDs
    lastContextIds = { response_id: null, image_id: null };
    lastGeneratedPrompt = null;
    lastGeneratedImageBase64 = null;
    
    // Uncheck 'Refine' checkbox to indicate a fresh start
    const refineCheckbox = document.getElementById('is-refine-mode');
    if (refineCheckbox) refineCheckbox.checked = false;
    
    console.log("Kontext bereinigt: Bereit für frischen Start.");
  }

  // Style change handler
  styleSelect.addEventListener('change', () => {
    const refineActive = document.getElementById('is-refine-mode').checked;
    const applyToRefine = document.getElementById('is-apply-preset-to-refine')?.checked || false;
    
    // Only clear context if not in refine+preset mode
    if (!(refineActive && applyToRefine)) {
      clearGenerationContext();
    }
    
    populateVariationSelect();
    updateStylePreviewImage(); 
  });
  
  if (qualityGateSelect) {
    qualityGateSelect.addEventListener('change', updateCost);
  }
  
  // Add event listeners for preset-related checkboxes
  if (editModeCheckbox) {
    editModeCheckbox.addEventListener('change', () => {
      togglePresetForEditUI();
      updatePresetVisibility();
    });
  }
  
  // Add event listener for the 'Apply Preset to Edit' checkbox
  if (applyPresetCheckbox) {
    applyPresetCheckbox.addEventListener('change', (e) => {
      updatePresetVisibility();
      // FIX: Wenn aktiviert, sofort Infos und Bild laden!
      if (e.target.checked) {
        // FIX: Sicherstellen, dass Variationen zum Stil passen, bevor wir anzeigen
        populateVariationSelect();
        // (populateVariationSelect ruft updatePresetInfoBox automatisch auf)
        updateStylePreviewImage();
      }
    });
  }
  
  // --- FINAL INITIALIZATION ---

  async function initializeStudio() {
    // 1. Lade Preisdaten und baue die Provider/Model-Dropdowns
    await loadPricingData(); // Wir warten, bis das fertig ist

    // 2. Lade die Preset-Daten (was populateStyleSelect -> populateVariationSelect anstößt)
    await fetchPresets(); 
    
    // 3. JETZT, wo garantiert alles geladen und im DOM ist, rufen wir die Funktion einmal auf.
    console.log("DIAGNOSE: Initialisierung abgeschlossen. Lade erstes Vorschaubild.");
    updateStylePreviewImage();
  }

  // --- Initialisierung beim Start ---
  updateCapabilityUI(); 
  if (maskControls) maskControls.style.display = 'none';
  togglePresetForEditUI(); 
  togglePresetForRefineUI();
  updatePresetVisibility();

  // Starte die kontrollierte Lade-Kette
  initializeStudio();
});