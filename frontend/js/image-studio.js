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
  const imageFilenameInput = document.getElementById('is-image-filename'); // NEU: Für Dateiname
  
  // Inpainting Elements
  const maskCanvas = document.getElementById('is-mask-canvas');
  const maskControls = document.getElementById('mask-controls');
  const clearMaskBtn = document.getElementById('clear-mask-btn');
  const brushSizeInput = document.getElementById('brush-size');
  const maskModeCheckbox = document.getElementById('is-mask-mode');
  const previewWrapper = document.getElementById('is-preview-wrapper');
  
  // Inpainting State
  let isDrawing = false;
  let ctx = null;
  let currentImageElement = null;
  let hiddenMaskCanvas = null;
  let hiddenCtx = null;

  let pricingData = null;
  let referenceImageUrl = null; // Für Drag-and-Drop Referenzbild
  let currentImageFullUrl = null; // Speichere die aktuelle volle URL des angezeigten Bildes
  let lastContextIds = { response_id: null, image_id: null }; // Für Multi-turn Refinement
  let lastGeneratedPrompt = null; // Speichert den letzten generierten Prompt
  let lastGeneratedImageBase64 = null; // Speichert das letzte generierte Bild als Base64
  
  // --- MASKING V8 (Native Resolution + Visual Scaling) ---
  let canvasScaleFactor = 1;
  let isInitDone = false;

  const isResolutionSelect = document.getElementById('is-resolution-select');
  const isResolutionControlGroup = document.getElementById('is-resolution-control-group');
  // Da openImageModal jetzt global im window-Objekt verfügbar gemacht wurde:
  const openImageModal = window.openImageModal; // Referenz auf die globale Funktion


    // Funktion zum Initialisieren des Masking-Canvas
    // (Wird aufgerufen, wenn Checkbox aktiv ist oder Bild geladen wird)
    function initInpainting() {
        const img = previewContainer.querySelector('img');
        const wrapper = document.getElementById('is-preview-wrapper');
        
        if (!img || !wrapper) return;

        // Warten auf Bild
        if (!img.complete || img.naturalWidth === 0) {
            img.onload = initInpainting;
            return;
        }

        // --- 1. Layout Fixieren (Shrink-to-Fit) ---
        // Wir berechnen die Anzeigegröße (max 512px)
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

        // Loop-Schutz: Wenn Größe schon stimmt, abbrechen
        if (isInitDone && Math.abs(parseFloat(wrapper.style.width) - displayW) < 1) return;

        console.log("Initializing Inpainting V8...");

        // Wrapper exakt auf Bildgröße zwingen (keine schwarzen Balken!)
        wrapper.style.width = `${displayW}px`;
        wrapper.style.height = `${displayH}px`;
        
        // Bild füllt Wrapper
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'fill';

        // --- 2. Canvas Setup (Originalauflösung!) ---
        // Der Canvas hat intern die echten Bild-Pixel (z.B. 1024x1024)
        maskCanvas.width = img.naturalWidth;
        maskCanvas.height = img.naturalHeight;
        
        // Per CSS skalieren wir ihn deckungsgleich zum Bild
        maskCanvas.style.width = '100%';
        maskCanvas.style.height = '100%';
        maskCanvas.style.top = '0px';
        maskCanvas.style.left = '0px';
        
        // Faktor für Maus-Events berechnen
        canvasScaleFactor = img.naturalWidth / displayW;
        
        // Context Reset
        ctx = maskCanvas.getContext('2d');
        ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
        
        // Pinsel initialisieren (skaliert!)
        updateBrushStyle();
        
        isInitDone = true;
        console.log(`Canvas V8 Ready: Native ${maskCanvas.width}x${maskCanvas.height}, Scale ${canvasScaleFactor.toFixed(2)}`);
    }
  
  function updateCanvasSize() {
    const img = previewContainer.querySelector('img');
    if (img && img.complete) {
      maskCanvas.width = img.width;
      maskCanvas.height = img.height;
      // Position the canvas over the image
      const imgRect = img.getBoundingClientRect();
      const containerRect = previewWrapper.getBoundingClientRect();
      maskCanvas.style.top = (imgRect.top - containerRect.top) + 'px';
      maskCanvas.style.left = (imgRect.left - containerRect.left) + 'px';
    }
  }
  
  function clearMaskCanvas() {
    // Clear visible canvas
    if (ctx) {
      ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    }
    
    // Clear hidden canvas
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
      
      // Uncheck other modes
      document.getElementById('is-edit-mode').checked = false;
      document.getElementById('is-refine-mode').checked = false;
      document.getElementById('is-combine-mode').checked = false;
      
      // Show mask controls and canvas
      maskCanvas.style.display = 'block';
      maskCanvas.classList.add('active');
      maskControls.style.display = 'flex';
      
      // Initialize inpainting with a small delay to ensure layout is ready
      setTimeout(initInpainting, 50);
      updateCanvasSize();
      initInpainting();
    } else {
      // If mask mode is unchecked, reset everything
      maskCanvas.style.display = 'none';
      maskCanvas.classList.remove('active');
      maskControls.style.display = 'none';
      
      // Reset layout to default
      if (wrapper) {
        wrapper.style.width = '512px'; // Default width
        wrapper.style.height = '512px'; // Default height
      }
      if (img) {
        img.style.width = 'auto';
        img.style.height = 'auto';
        img.style.objectFit = 'contain';
      }
    }
  });

  // Clear mask button
  clearMaskBtn.addEventListener('click', () => {
    clearMaskCanvas();
  });

  // Update brush style when brush size changes
  brushSizeInput.addEventListener('input', updateBrushStyle);

  function getCanvasCoordinates(e) {
      const rect = maskCanvas.getBoundingClientRect();
      // Mausposition im Element (0 bis displayWidth)
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Umrechnung auf interne Auflösung (0 bis naturalWidth)
      return {
          x: x * canvasScaleFactor,
          y: y * canvasScaleFactor
      };
  }

  // Pinselgröße an die Auflösung anpassen
  function updateBrushStyle() {
    if (!ctx) return;
    const baseSize = document.getElementById('brush-size').value;
    // WICHTIG: Pinselgröße mit Skalierungsfaktor multiplizieren
    // Damit ist "30" auf einem riesigen Bild auch riesig.
    ctx.lineWidth = baseSize * canvasScaleFactor; 
    ctx.strokeStyle = '#ff0000'; // Rot
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }
  
  // Event Listener für Slider
  document.getElementById('brush-size').addEventListener('input', updateBrushStyle);

  // Maus-Koordinaten umrechnen
  function getNativeCoords(e) {
    const rect = maskCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    // Skalieren auf native Auflösung
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
    
    // Neuen Pfad für flüssiges Zeichnen starten
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  }

  function stopDrawing() {
    isDrawing = false;
    ctx.beginPath(); // Reset path
  }

  // Add event listeners for drawing
  maskCanvas.addEventListener('mousedown', startDrawing);
  maskCanvas.addEventListener('mousemove', draw);
  maskCanvas.addEventListener('mouseup', stopDrawing);
  maskCanvas.addEventListener('mouseout', stopDrawing);
  
  // Update mask checkbox event listener
  maskModeCheckbox.addEventListener('change', (e) => {
    const wrapper = document.getElementById('is-preview-wrapper');
    const img = previewContainer.querySelector('img');

    if (e.target.checked) {
      if (!currentImageFullUrl) {
        alert("Bitte erst ein Bild laden/generieren!");
        e.target.checked = false;
        return;
      }
      // Deaktiviere andere Modi
      document.getElementById('is-combine-mode').checked = false;
      
      maskCanvas.style.display = 'block';
      // WICHTIG: Pointer-Events aktivieren!
      maskCanvas.classList.add('active'); 
      
      maskControls.style.display = 'flex';
      
      // Verzögertes Init, damit Layout steht
      setTimeout(initInpainting, 50); 
    } else {
      maskCanvas.style.display = 'none';
      // WICHTIG: Pointer-Events deaktivieren!
      maskCanvas.classList.remove('active');
      
      maskControls.style.display = 'none';
      
      // RESET LAYOUT (Wichtig!)
      // Wir setzen die Inline-Styles zurück, damit CSS wieder greift (512x512 fix)
      if (wrapper) {
        wrapper.style.width = ''; 
        wrapper.style.height = '';
      }
      if (img) {
        img.style.width = '';
        img.style.height = '';
        img.style.objectFit = ''; // Zurück zu CSS 'contain'
      }
    }
  });

  // Also handle touch events for mobile
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

  // Update canvas size when image is loaded
  previewContainer.addEventListener('load', (e) => {
    if (e.target.tagName === 'IMG') {
      updateCanvasSize();
    }
  }, true);

  // Add observer to handle dynamic image loading
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        const img = previewContainer.querySelector('img');
        if (img) {
          currentImageElement = img;
          // If image is already loaded, update canvas size
          if (img.complete) {
            updateCanvasSize();
          } else {
            // If not, wait for it to load
            img.onload = () => {
              updateCanvasSize();
            };
          }
        }
      }
    });
  });

  // Start observing the preview container for changes
  observer.observe(previewContainer, { childList: true, subtree: true });

  // --- Event Listeners ---
  openBtn.addEventListener('click', () => {
    modal.style.display = 'flex';
    if (!pricingData) {
      loadPricingData();
    }
    // Initialize inpainting when opening the modal
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
    // Only reset context if switching to a non-OpenAI model
    if (!newModel.startsWith('gpt-image-')) {
      lastContextIds = { response_id: null, image_id: null };
      document.getElementById('is-refine-mode').checked = false;
    }
    // Keep lastContextIds for OpenAI model switches to enable cross-model refinement
    populateDynamicParams();
    updateCost();
  });

  // Toggle between refine and edit modes (mutually exclusive)
  document.getElementById('is-refine-mode').addEventListener('change', (e) => {
    if (e.target.checked) {
      // If refine mode is checked, uncheck edit mode
      document.getElementById('is-edit-mode').checked = false;
    }
  });

  document.getElementById('is-edit-mode').addEventListener('change', (e) => {
    if (e.target.checked) {
      // If edit mode is checked, uncheck refine mode
      document.getElementById('is-refine-mode').checked = false;
    }
  });
  
    // dynamicParamsContainer.addEventListener('change', (event) => {
  
    //     if(event.target.tagName === 'SELECT') {
  
    //         updateCost();
  
    //     }
  
    // }); // Dies wird jetzt innerhalb von populateDynamicParams() spezifisch behandelt
  
  
  
  
  
    generateBtn.addEventListener('click', generateImage);
  
  
  
  // --- Drag-and-Drop Funktionalität für das Vorschaufenster ---
  
  previewContainer.addEventListener('dragover', (event) => {
  
    event.preventDefault(); // Ermöglicht das Ablegen
  
    previewContainer.classList.add('drag-over'); // Optional: visueller Hinweis
  
  });
  
  
  
  previewContainer.addEventListener('dragleave', () => {
  
    previewContainer.classList.remove('drag-over'); // Optional: visueller Hinweis entfernen
  
  });
  
  
  
  previewContainer.addEventListener('drop', async (event) => {
    event.preventDefault();
    previewContainer.classList.remove('drag-over');
    
    // Handle file uploads from desktop
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

        // --- Display in preview ---
        previewContainer.innerHTML = '';
        const imgElement = document.createElement('img');
        imgElement.src = newImageUrl;
        imgElement.alt = "Hochgeladenes Bild";
        imgElement.style.maxWidth = '100%';
        imgElement.style.maxHeight = '100%';
        imgElement.style.objectFit = 'contain';
        previewContainer.appendChild(imgElement);
        currentImageFullUrl = newImageUrl;
        
        // --- Add to uploaded gallery ---
        addImageToGallery(imageData, uploadedGallery);
        
        // --- Update filename input ---
        const filename = imageData.image_url.split('/').pop();
        imageFilenameInput.value = filename.split('.').slice(0, -1).join('.');

        // --- NEU: Editiermodus standardmäßig aktivieren ---
        document.getElementById('is-edit-mode').checked = true;
        // Andere exklusive Modi deaktivieren
        document.getElementById('is-refine-mode').checked = false;
        document.getElementById('is-mask-mode').checked = false;
        document.getElementById('is-combine-mode').checked = false;

      } catch (error) {
        console.error('Fehler beim Hochladen des Bildes:', error);
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
      }
      return; // End execution for file drop
    }
    
    // Handle drag from internal galleries
    const imageUrl = event.dataTransfer.getData('text/plain');
    if (imageUrl) {
      console.log('Image dropped from gallery:', imageUrl);
      
      previewContainer.innerHTML = '';
      const droppedImgElement = document.createElement('img');
      droppedImgElement.src = imageUrl;
      droppedImgElement.alt = "Vorschau des ausgewählten Bildes";
      droppedImgElement.style.maxWidth = '100%';
      droppedImgElement.style.maxHeight = '100%';
      droppedImgElement.style.objectFit = 'contain';
      previewContainer.appendChild(droppedImgElement);
      
      currentImageFullUrl = imageUrl;
      
      const filenameMatch = imageUrl.match(/\/([^\/]+)$/);
      if (filenameMatch && filenameMatch[1]) {
        imageFilenameInput.value = filenameMatch[1].split('.')[0];
      } else {
        imageFilenameInput.value = "unbenannt";
      }
      
      promptInput.placeholder = `Prompt (Referenzbild geladen)`;
      
      // Reset modes before fetching context
      document.getElementById('is-edit-mode').checked = false;
      document.getElementById('is-refine-mode').checked = false;
      document.getElementById('is-mask-mode').checked = false;
      document.getElementById('is-combine-mode').checked = false;

      try {
        const contextRes = await fetch(`http://localhost:8001/api/images/context?url=${encodeURIComponent(imageUrl)}`);
        if (contextRes.ok) {
          const contextData = await contextRes.json();
          lastContextIds.response_id = contextData.response_id;
          lastContextIds.image_id = contextData.image_id;
          console.log("Context for dropped image:", lastContextIds);
          
          // CORE LOGIC: Set mode based on context
          if (contextData.response_id) {
            // It's a generated image, so enable refine mode
            document.getElementById('is-refine-mode').checked = true;
          } else {
            // It's an uploaded image without generation context, so enable edit mode
            document.getElementById('is-edit-mode').checked = true;
          }
        } else {
          // If context fetch fails, default to edit mode
          document.getElementById('is-edit-mode').checked = true;
        }
      } catch (err) {
        console.error("Error loading image context:", err);
        // On error, also default to edit mode
        document.getElementById('is-edit-mode').checked = true;
      }

      updateCost();
    }
  });
  
  
  
  // --- Event Listener für Dateinamen-Änderung ---
  
  imageFilenameInput.addEventListener('blur', async () => {
  
    await renameImageFile();
  
  });
  
  
  
  imageFilenameInput.addEventListener('keydown', async (event) => {
  
    if (event.key === 'Enter') {
  
      event.preventDefault(); // Verhindert das Absenden eines Formulars
  
      imageFilenameInput.blur(); // Löst den blur-Event aus, der renameImageFile aufruft
  
    }
  
  });
  
  
  
  // --- Funktion zum Umbenennen der Bilddatei ---
  
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
  
      // Keine Änderung oder leerer Name, nichts tun
  
      imageFilenameInput.value = oldFilename; // Setze den alten Namen zurück, falls leer
  
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

      console.log(`Datei erfolgreich umbenannt zu ${newImageUrl}`);
  
      // Aktualisiere die interne Full URL, um zukünftige Umbenennungen korrekt zu behandeln
      currentImageFullUrl = newImageUrl;
      // Aktualisiere die Bildquelle im Preview Container
      if (previewContainer.querySelector('img')) {
          previewContainer.querySelector('img').src = newImageUrl;
      }
  
      // Finde und aktualisiere das entsprechende Thumbnail in der Galerie
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
  
      imageFilenameInput.value = oldFilename; // Setze den Namen auf den alten Wert zurück
  
    }
  
  }

  // --- Combine Slots Logic ---
  const combineCheckbox = document.getElementById('is-combine-mode');
  const slotsWrapper = document.getElementById('combine-slots-wrapper');
  const slots = document.querySelectorAll('.combine-slot');
  let combineSlotsData = [null, null, null, null, null];

  // Toggle Visibility
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

  // Slot Drag & Drop Handlers
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
    
    // Click to remove
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
      slot.innerHTML = ''; // Clear contents
      slot.classList.remove('filled');

      if (url) {
        slot.classList.add('filled');
        // Add image
        const img = document.createElement('img');
        img.src = url;
        slot.appendChild(img);
        
        // Add remove button overlay
        const removeDiv = document.createElement('div');
        removeDiv.classList.add('remove-slot-btn');
        removeDiv.innerHTML = '&times;'; // X symbol
        slot.appendChild(removeDiv);
      } else {
        // Show number
        slot.textContent = index + 1;
      }
    });
  }

  // --- Drag-and-Drop Funktionalität für die Upload-Galerie ---
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
            // Remove placeholder
            const hint = uploadedGallery.querySelector('.is-empty-hint');
            if (hint) hint.remove();

            for (const file of files) {
                if (!file.type.startsWith('image/')) {
                    console.warn(`Skipping non-image file: ${file.name}`);
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
                    // Optionally show an error message in the UI
                }
            }
        }
    });

    // --- Helper function to add image to a gallery ---
    function addImageToGallery(imageData, galleryElement) {
        // Remove placeholder text if it exists
        const hint = galleryElement.querySelector('.is-empty-hint');
        if (hint) hint.remove();

        const fullImageUrl = `http://localhost:8001${imageData.image_url}`;

        const thumbnailImg = document.createElement('img');
        thumbnailImg.src = fullImageUrl;
        thumbnailImg.alt = imageData.prompt || 'Uploaded image';
        thumbnailImg.classList.add('gallery-thumbnail');
        thumbnailImg.draggable = true;

        thumbnailImg.addEventListener('click', () => {
            openImageModal(fullImageUrl);
        });

        thumbnailImg.addEventListener('dragstart', (event) => {
            event.dataTransfer.setData('text/plain', event.target.src);
            event.dataTransfer.effectAllowed = 'copy';
        });

        galleryElement.prepend(thumbnailImg);
    }
  
  
    // --- Mask Data Handling ---
  function getMaskData() {
    if (!maskModeCheckbox.checked || !ctx) {
      console.log("Mask generation skipped: mask mode not active or context not ready");
      return null;
    }
    
    const imgElement = previewContainer.querySelector('img');
    if (!imgElement) {
      console.log("Mask generation failed: no image element found");
      return null;
    }
    
    const originalWidth = imgElement.naturalWidth || 1024;
    const originalHeight = imgElement.naturalHeight || 1024;
    
    console.log(`Generating mask from canvas ${maskCanvas.width}x${maskCanvas.height} to ${originalWidth}x${originalHeight}`);
    
    // 1. High-Res Canvas erstellen (Originalgröße)
    const finalCanvas = document.createElement('canvas');
    finalCanvas.width = originalWidth;
    finalCanvas.height = originalHeight;
    const fCtx = finalCanvas.getContext('2d');
    
    // 2. Alles Schwarz füllen (Das ist der Bereich, der behalten wird)
    fCtx.fillStyle = 'black';
    fCtx.fillRect(0, 0, originalWidth, originalHeight);
    
    // 3. Die Maske ausstanzen (Transparent = Änderung)
    fCtx.globalCompositeOperation = 'destination-out';
    
    // FIX: Glättung deaktivieren für schärfere Masken-Kanten (verhindert Halb-Transparenz)
    fCtx.imageSmoothingEnabled = false; 
    
    // WICHTIG: Wir skalieren den kleinen Canvas auf den großen
    // Da 'maskCanvas' jetzt exakt das Seitenverhältnis des Bildes hat,
    // gibt es keine Verzerrung mehr!
    fCtx.drawImage(
      maskCanvas, 
      0, 0, maskCanvas.width, maskCanvas.height, // Quelle
      0, 0, originalWidth, originalHeight        // Ziel
    );
    
    // Glättung für zukünftige Operationen wieder aktivieren (falls nötig)
    fCtx.imageSmoothingEnabled = true;
    
    const maskData = finalCanvas.toDataURL('image/png');
    console.log("Mask generated successfully");
    
    // --- DEBUG: Maske direkt im UI anzeigen (statt Popup) ---
    let debugContainer = document.getElementById('mask-debug-view');
    if (!debugContainer) {
        debugContainer = document.createElement('div');
        debugContainer.id = 'mask-debug-view';
        debugContainer.style.marginTop = '10px';
        debugContainer.style.border = '2px solid red';
        debugContainer.style.padding = '5px';
        debugContainer.style.background = '#333';
        // Einfügen nach dem Preview Container
        document.querySelector('.image-studio-display').appendChild(debugContainer);
    }
    debugContainer.innerHTML = `
        <p style="color:white; margin:0;">Debug: Gesendete Maske (${originalWidth}x${originalHeight})</p>
        <img src="${maskData}" style="max-width: 200px; background: url('https://www.transparenttextures.com/patterns/checkerboard.png');">
    `;
    
    return maskData;
  }

  // --- Logic ---
  async function loadPricingData() {
    try {
      const response = await fetch('http://localhost:8001/api/images/pricing');
      if (!response.ok) {
        throw new Error('Fehler beim Laden der Preisdaten');
      }
                  pricingData = await response.json();
                  console.log('Loaded pricingData:', pricingData); // Debug-Ausgabe
                  populateProviderSelect();    } catch (error) {
      console.error(error);
      costDisplay.textContent = 'Fehler';
    }
  }

  function populateProviderSelect() {
    providerSelect.innerHTML = '';
    for (const provider in pricingData) {
      const option = document.createElement('option');
      option.value = provider;
      option.textContent = provider;
      providerSelect.appendChild(option);
    }
    populateModelSelect();
  }

  function populateModelSelect() {
    modelSelect.innerHTML = '';
    const selectedProvider = providerSelect.value;
    if (pricingData && pricingData[selectedProvider]) {
      // Filter for image models (type: "image")
      const imageModels = Object.entries(pricingData[selectedProvider]).filter(([modelId, modelData]) => {
          // Check if modelData is an object and has 'type' and 'capabilities' properties
          return typeof modelData === 'object' && modelData.type === 'image' && modelData.capabilities && modelData.capabilities.includes('image_generation');
      });

      console.log('Filtered image models:', imageModels); // Debug-Ausgabe
      imageModels.forEach(([modelId, modelData]) => {
        const option = document.createElement('option');
        option.value = modelId;
        option.textContent = modelData.name; // Display the user-friendly name
        modelSelect.appendChild(option);
      });
    }
    populateDynamicParams();
  }
  
  function populateDynamicParams() {
      dynamicParamsContainer.innerHTML = '';
      const selectedProvider = providerSelect.value;
      const selectedModelId = modelSelect.value; // modelId, e.g., "gpt-image-1.5"
      
      // Ensure resolution control group is hidden by default for all calls
      isResolutionControlGroup.style.display = 'none';

      if(!pricingData || !pricingData[selectedProvider] || !pricingData[selectedProvider][selectedModelId]) {
          updateCost();
          return;
      }

      const modelData = pricingData[selectedProvider][selectedModelId];
      
      // Case 1: OpenAI-style image model with quality and size parameters
      if (modelData.type === 'image' && modelData.pricing) {
          // Dropdown für Qualität
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

          // Dropdown für Größe (Auflösung)
          const sizeDiv = document.createElement('div');
          sizeDiv.classList.add('control-group');
          sizeDiv.innerHTML = `<label for="is-param-size">Auflösung</label><select id="is-param-size" data-param-key="size"></select>`;
          dynamicParamsContainer.appendChild(sizeDiv);
          const sizeSelect = sizeDiv.querySelector('select');

          const populateSizeOptions = () => {
              sizeSelect.innerHTML = ''; // Vorherige Optionen löschen
              const currentQuality = qualitySelect.value;
              const availableSizes = modelData.pricing[currentQuality] ? Object.keys(modelData.pricing[currentQuality]) : [];
              availableSizes.forEach(s => {
                  const option = document.createElement('option');
                  option.value = s;
                  option.textContent = s;
                  sizeSelect.appendChild(option);
              });
              sizeSelect.value = modelData.default_size || availableSizes[0];
              updateCost(); // Kosten aktualisieren, wenn Größenoptionen neu geladen wurden
          };

          // Event-Listener für Qualitätsänderungen
          qualitySelect.addEventListener('change', populateSizeOptions);
          populateSizeOptions(); // Initiale Größenoptionen laden
      } 
      // Case 2: Gemini-style image model with aspect ratios
      else if (modelData.type === 'image' && modelData.aspect_ratios) {
          // Display aspect ratio selector for all Gemini image models
          const ratioDiv = document.createElement('div');
          ratioDiv.classList.add('control-group');
          ratioDiv.innerHTML = `<label for="is-param-aspect-ratio">Seitenverhältnis</label><select id="is-param-aspect-ratio" data-param-key="aspect_ratio"></select>`;
          dynamicParamsContainer.appendChild(ratioDiv);
          const ratioSelect = ratioDiv.querySelector('select');

          // Add aspect ratio options
          modelData.aspect_ratios.forEach(ratio => {
              const option = document.createElement('option');
              option.value = ratio;
              option.textContent = ratio;
              ratioSelect.appendChild(option);
          });
          
          // Set default aspect ratio
          ratioSelect.value = modelData.default_aspect_ratio || "1:1";
          
          // Update cost when aspect ratio changes
          ratioSelect.addEventListener('change', updateCost);
          
          // Specific logic for Gemini 3 Image models (resolution dropdown)
          if (selectedModelId.startsWith('gemini-3')) { // Check if it's a Gemini 3 model
            isResolutionControlGroup.style.display = 'block';
            isResolutionSelect.innerHTML = ''; // Clear existing options

            const availableResolutions = modelData.resolutions || ["1K", "2K"]; // Fallback, falls nicht definiert

            availableResolutions.forEach(res => {
                const option = document.createElement('option');
                option.value = res;
                option.textContent = res;
                isResolutionSelect.appendChild(option);
            });
            isResolutionSelect.value = modelData.default_resolution || availableResolutions[0];
            isResolutionSelect.addEventListener('change', updateCost); // Event Listener für Kosten
          } else {
            isResolutionControlGroup.style.display = 'none'; // Hide if not Gemini 3
          }
          updateCost();

      } else {
          // Generische Behandlung für andere Modelle (wie Textmodelle oder legacy DALL-E)
          isResolutionControlGroup.style.display = 'none'; // Hide resolution dropdown for other models
          const parameterKeys = Object.keys(modelData).filter(key => typeof modelData[key] === 'object' && key !== 'pricing' && key !== 'capabilities');
          
          parameterKeys.forEach(paramKey => {
              const div = document.createElement('div');
              div.classList.add('control-group');
              div.innerHTML = `<label for="is-param-${paramKey}">${paramKey.charAt(0).toUpperCase() + paramKey.slice(1)}</label><select id="is-param-${paramKey}" data-param-key="${paramKey}"></select>`;
              dynamicParamsContainer.appendChild(div);
              const select = div.querySelector('select');
              
              const paramData = modelData[paramKey]; // Correctly get the parameter data
              for(const optionValue in paramData) {
                  const option = document.createElement('option');
                  option.value = optionValue;
                  option.textContent = optionValue;
                  select.appendChild(option);
              }
              select.addEventListener('change', updateCost);
              if(select.value === '') select.value = Object.keys(paramData)[0]; // Standardwert setzen
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
                  console.log('Model Data in populateDynamicParams:', modelData); // Debug-Ausgabe
                        if (!modelData) {
        costDisplay.textContent = 'N/A';
        return;
      }

      let finalCost = 'N/A';

      // If it's an image model with nested pricing (OpenAI DALL-E style)
      if (modelData.type === 'image' && modelData.pricing) {
        isResolutionControlGroup.style.display = 'none'; // Hide resolution dropdown for OpenAI models
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
      // If it's a Gemini image model (aspect ratios and potentially resolutions)
      else if (modelData.type === 'image' && modelData.aspect_ratios) {
          const ratioSelect = dynamicParamsContainer.querySelector('#is-param-aspect-ratio');
          const resolutionSelect = document.getElementById('is-resolution-select'); // Get the new resolution select

          const aspectRatio = ratioSelect ? ratioSelect.value : null;
          const resolution = resolutionSelect ? resolutionSelect.value : null;

          // For Gemini, cost is often token-based. We need tokens_per_image and costs per million tokens.
          // The selected resolution might influence the tokens_per_image for a given aspect ratio.
          // Currently, modelData only contains 'tokens_per_image' at the top level, implying it's fixed
          // or needs more complex lookup. For now, we'll assume a simple calculation.
          
          if (modelData.cost_per_million_tokens_input && modelData.cost_per_million_tokens_output && modelData.tokens_per_resolution) {
              const selectedResolution = resolutionSelect ? resolutionSelect.value : (modelData.default_resolution || "1K");
              const currentTokensPerImage = modelData.tokens_per_resolution[selectedResolution] || modelData.tokens_per_resolution["1K"] || 1120; // Fallback-Wert
              
              const inputCostPerImage = (currentTokensPerImage / 1000000) * modelData.cost_per_million_tokens_input;
              const outputCostPerImage = (currentTokensPerImage / 1000000) * modelData.cost_per_million_tokens_output;
              finalCost = inputCostPerImage + outputCostPerImage;
              
          } else if (modelData.cost_per_image) {
              finalCost = modelData.cost_per_image;
          } else {
              finalCost = 'N/A';
          }

      }
      else {
        isResolutionControlGroup.style.display = 'none'; // Hide resolution dropdown for other models
        // Generic cost calculation for other models (text, websearch, tts, etc.)
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
        costDisplay.textContent = `$${finalCost.toFixed(4)}`;
      } else {
        costDisplay.textContent = 'N/A';
      }

    } catch (e) {
      console.error("Fehler bei der Kostenkalkulation:", e);
      costDisplay.textContent = 'Fehler';
    }
  }

  async function generateImage() {
    previewContainer.innerHTML = '<div class="loader"></div>';
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generiere...';
    
    const refineActive = document.getElementById('is-refine-mode').checked;
    const editModeActive = document.getElementById('is-edit-mode').checked;
    const combineModeActive = document.getElementById('is-combine-mode').checked;
    
    // Collect active images from combine slots
    const activeCombineImages = combineSlotsData.filter(url => url !== null);
    
    // Validate based on mode
    if (combineModeActive && activeCombineImages.length < 1) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte ziehe mindestens ein Bild in die nummerierten Felder.</p>';
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generieren';
      return;
    }
    
    // Validate that we have a reference image in edit mode
    if (editModeActive && !currentImageFullUrl) {
      previewContainer.innerHTML = '<p style="color: red;">Bitte lade zuerst ein Bild hoch, um es zu bearbeiten.</p>';
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generieren';
      return;
    }
    
    // Collect data
    const payload = {
        prompt: promptInput.value,
        provider: providerSelect.value,
        model: modelSelect.value, 
        parameters: {},
        // Include context only if refine mode is active and we have previous IDs and not in combine mode
        previous_response_id: (refineActive && !combineModeActive) ? lastContextIds.response_id : null,
        previous_image_id: (refineActive && !combineModeActive) ? lastContextIds.image_id : null,
        
        // Add history for Gemini refinement
        history: (refineActive && providerSelect.value === 'gemini') ? {
            prompt: lastGeneratedPrompt,
            image_base64: lastGeneratedImageBase64
        } : null,
        
        // FIX: Aggressivere Logik für Cross-Provider Refinement
        // Wenn Refine an ist, aber wir keine Response-ID haben (Gemini Fall),
        // MÜSSEN wir das Bild als URL mitschicken, damit das Backend es als Edit-Upload behandelt.
        reference_image_url: (
            editModeActive || 
            maskModeCheckbox.checked || 
            (refineActive && !lastContextIds.response_id) ||
            (refineActive && providerSelect.value === 'openai' && !lastContextIds.response_id) // Explizit für Gemini->GPT Wechsel
        ) ? currentImageFullUrl : null,
        
        // Combine List (Only send filled slots)
        reference_image_urls: combineModeActive ? activeCombineImages : [],
        
        // Add mask data if inpainting is active
        mask_image_data: (() => {
            if (!maskModeCheckbox.checked) return null;
            
            // High-Res Canvas erstellen (Copy)
            const finalCanvas = document.createElement('canvas');
            finalCanvas.width = maskCanvas.width;   
            finalCanvas.height = maskCanvas.height; 
            const fCtx = finalCanvas.getContext('2d');
            
            // 1. Hintergrund Schwarz (Behalten)
            fCtx.fillStyle = 'black';
            fCtx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);
            
            // 2. Zeichnung ausstanzen (Destination-Out)
            fCtx.globalCompositeOperation = 'destination-out';
            fCtx.drawImage(maskCanvas, 0, 0); 
            
            const maskData = finalCanvas.toDataURL('image/png');
            
            return maskData;
        })()
    };
    
    // Debug logging for context
    console.log("Sending payload:", {
        refineActive,
        editModeActive,
        response_id: payload.previous_response_id,
        image_id: payload.previous_image_id,
        reference_image_url: payload.reference_image_url
    });

    const selectedModelId = modelSelect.value; // Füge dies hinzu
    // Dynamische Parameter sammeln
    dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
        // Direkte Zuordnung für die meisten dynamischen Parameter
        payload.parameters[sel.dataset.paramKey] = sel.value;
    });

    // Spezielle Handhabung für Gemini 3 Modelle und Auflösung
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
        const imageUrl = `http://localhost:8001${result.image_url}`;
        currentImageFullUrl = imageUrl; // Speichere die volle URL
        
        // Save the context IDs for the next turn if they are provided in the response
        if (result.previous_response_id || result.previous_image_id) {
          lastContextIds = {
            response_id: result.previous_response_id || null,
            image_id: result.previous_image_id || null
          };
          console.log("Kontext für das aktuelle Bild gespeichert:", lastContextIds);
        } else {
          // If no context is provided, clear the context
          lastContextIds = { response_id: null, image_id: null };
        }
        
        // Save prompt and image for next refinement (for ALL providers)
        lastGeneratedPrompt = payload.prompt;
        
        // We need the image as Base64 for Gemini Refinement
        // This is inefficient. It would be better if the backend would cache it.
        // But for now, we'll fetch it again.
        fetch(imageUrl)
            .then(res => res.blob())
            .then(blob => {
                const reader = new FileReader();
                reader.onload = () => {
                    lastGeneratedImageBase64 = reader.result.split(',')[1]; // Only the Base64 part
                    console.log("Image cached as Base64 for Gemini Refinement.");
                };
                reader.readAsDataURL(blob);
            });
          
        // Automatically enable refine mode and disable others for the next generation
        document.getElementById('is-refine-mode').checked = true;
        document.getElementById('is-combine-mode').checked = false;
        document.getElementById('is-edit-mode').checked = false;
        document.getElementById('is-mask-mode').checked = false;

        // Extrahiere den Dateinamen aus der URL für das Input-Feld
        const filenameMatch = imageUrl.match(/\/([^\/]+)$/);
        if (filenameMatch && filenameMatch[1]) {
            imageFilenameInput.value = filenameMatch[1].split('.')[0]; // Dateiname ohne Extension
        } else {
            imageFilenameInput.value = "unbenannt";
        }
        
        // --- Bild im Preview Container anzeigen und Click-Handler hinzufügen ---
        previewContainer.innerHTML = ''; // Lade-Spinner entfernen
        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = payload.prompt;
        imgElement.style.maxWidth = '100%';
        imgElement.style.maxHeight = '100%';
        imgElement.style.objectFit = 'contain';
        imgElement.style.cursor = 'pointer'; // Visueller Hinweis
        
        imgElement.addEventListener('click', () => {
            openImageModal(imageUrl); // Öffne das Bild im großen Modal
        });

        previewContainer.appendChild(imgElement);

        // --- Thumbnail zur generierten Galerie hinzufügen (Refactored) ---
        addImageToGallery(result, generatedGallery);

    } catch (error) {
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
        console.error(error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generieren';
    }
  }

  // --- Provider Switch Logic ---
  // Gemini doesn't support mask upload inpainting -> Disable checkbox
  function updateCapabilityUI() {
    const provider = providerSelect.value;
    const maskCheckbox = document.getElementById('is-mask-mode');
    const maskLabel = document.querySelector('label[for="is-mask-mode"]');
    const maskContainer = maskCheckbox.parentElement; // The surrounding div

    if (provider === 'gemini') {
      // Disable
      if (maskCheckbox.checked) {
        maskCheckbox.checked = false;
        // Trigger event to hide canvas
        maskCheckbox.dispatchEvent(new Event('change'));
      }
      maskCheckbox.disabled = true;
      maskContainer.style.opacity = '0.5';
      maskContainer.title = "Inpainting (mask) is currently not supported by Gemini. Please use prompt instructions.";
    } else {
      // Enable (OpenAI)
      maskCheckbox.disabled = false;
      maskContainer.style.opacity = '1';
      maskContainer.title = "";
    }
  }

  // Register listener
  providerSelect.addEventListener('change', updateCapabilityUI);
  
  // Also run once on startup
  updateCapabilityUI();
});