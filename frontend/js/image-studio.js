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
  const galleryContainer = document.getElementById('is-gallery'); // NEU: Galerie Container

  let pricingData = null;

  // Da openImageModal jetzt global im window-Objekt verfügbar gemacht wurde:
  const openImageModal = window.openImageModal; // Referenz auf die globale Funktion


  // --- Event Listeners ---
  openBtn.addEventListener('click', () => {
    modal.style.display = 'flex';
    if (!pricingData) {
      loadPricingData();
    }
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
    populateDynamicParams();
    updateCost();

  });
  
  // dynamicParamsContainer.addEventListener('change', (event) => {
  //     if(event.target.tagName === 'SELECT') {
  //         updateCost();
  //     }
  // }); // Dies wird jetzt innerhalb von populateDynamicParams() spezifisch behandelt


  generateBtn.addEventListener('click', generateImage);



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
      
      if(!pricingData || !pricingData[selectedProvider] || !pricingData[selectedProvider][selectedModelId]) {
          updateCost();
          return;
      }

      const modelData = pricingData[selectedProvider][selectedModelId];
      
      // Check if the selected model has a 'pricing' structure (indicating it's an image generation model)
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

          qualitySelect.addEventListener('change', populateSizeOptions);
          sizeSelect.addEventListener('change', updateCost);

          // Initial befüllen
          populateSizeOptions();

      } else {
          // Generische Behandlung für andere Modelle (wie Gemini oder legacy DALL-E)
          // This block should still handle text models or other types that don't have the 'pricing' structure
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

      // If it's an image model with nested pricing
      if (modelData.type === 'image' && modelData.pricing) {
        const qualitySelect = dynamicParamsContainer.querySelector('#is-param-quality');
        const sizeSelect = dynamicParamsContainer.querySelector('#is-param-size');

        const quality = qualitySelect ? qualitySelect.value : null;
        const size = sizeSelect ? sizeSelect.value : null;
        
        if (quality && size && modelData.pricing[quality] && modelData.pricing[quality][size]) {
            finalCost = modelData.pricing[quality][size];
        } else {
            // Fallback for cases where specific quality/size combo isn't found
            finalCost = 'N/A';
        }
      } else {
        // Generic cost calculation for other models (text, websearch, tts, etc.)
        // This block needs to be more robust if there are other complex pricing structures
        // For now, it assumes direct cost_per_image or simple parameter-based lookup
        const params = {};
        dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
            params[sel.dataset.paramKey] = sel.value;
        });

        // Assuming a simple cost_per_image for non-nested image models or other types
        if (modelData.cost_per_image) {
            finalCost = modelData.cost_per_image;
        } else if (modelData.cost_per_token_input && modelData.cost_per_token_output) {
            // This is for text models, which currently don't show up here, but as a fallback
            finalCost = "Variiert"; // Or some other indication
        } else if (modelData.cost_per_query) {
             finalCost = modelData.cost_per_query;
        } else {
            // Attempt to find a direct cost if it exists at the top level of modelData
            const firstParamKey = Object.keys(modelData).find(key => typeof modelData[key] === 'object' && key !== 'pricing' && key !== 'capabilities');
            if (firstParamKey && params[firstParamKey]) {
                 finalCost = modelData[firstParamKey]?.[params[firstParamKey]];
            } else if (typeof modelData === 'number') { // Fallback, if modelData itself is a cost
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
    
    // Collect data
    const payload = {
        prompt: promptInput.value,
        provider: providerSelect.value,
        model: modelSelect.value, // Basismodellname (z.B. "dall-e-3")
        parameters: {},
    };
    
    // Dynamische Parameter sammeln und als 'resolution' und 'quality' speichern
    dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
        if (sel.dataset.paramKey === 'size') { // 'size' vom Frontend wird zu 'resolution' im Backend
            payload.parameters['resolution'] = sel.value;
        } else {
            payload.parameters[sel.dataset.paramKey] = sel.value;
        }
    });

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

        // --- Thumbnail zur Galerie hinzufügen ---
        // Entferne den Platzhaltertext, falls vorhanden
        const galleryPlaceholder = galleryContainer.querySelector('p');
        if (galleryPlaceholder && galleryPlaceholder.textContent.includes('Galerie erscheint hier')) {
            galleryContainer.innerHTML = '';
        }

        const thumbnailImg = document.createElement('img');
        thumbnailImg.src = imageUrl;
        thumbnailImg.alt = payload.prompt;
        thumbnailImg.classList.add('gallery-thumbnail'); // Füge eine Klasse für Styling hinzu

        thumbnailImg.addEventListener('click', () => {
            openImageModal(imageUrl); // Öffne das Bild im großen Modal
        });

        galleryContainer.prepend(thumbnailImg); // Am Anfang der Galerie hinzufügen (neueste zuerst)


    } catch (error) {
        previewContainer.innerHTML = `<p style="color: red;">Fehler: ${error.message}</p>`;
        console.error(error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generieren';
    }
  }
});