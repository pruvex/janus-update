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
      populateProviderSelect();
    } catch (error) {
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
      for (const model in pricingData[selectedProvider]) {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
      }
    }
    populateDynamicParams();
  }
  
  function populateDynamicParams() {
      dynamicParamsContainer.innerHTML = '';
      const selectedProvider = providerSelect.value;
      const selectedModelBase = modelSelect.value; // z.B. "dall-e-3"
      
      if(!pricingData || !pricingData[selectedProvider] || !pricingData[selectedProvider][selectedModelBase]) {
          updateCost();

          return;
      }

      let modelPricing = pricingData[selectedProvider][selectedModelBase];

      // Spezielle Behandlung für OpenAI DALL-E Modelle
      if (selectedProvider === 'openai' && selectedModelBase.startsWith('dall-e')) {
          // Dropdown für Qualität
          const qualityDiv = document.createElement('div');
          qualityDiv.classList.add('control-group');
          qualityDiv.innerHTML = `<label for="is-param-quality">Qualität</label><select id="is-param-quality" data-param-key="quality"></select>`;
          dynamicParamsContainer.appendChild(qualityDiv);
          const qualitySelect = qualityDiv.querySelector('select');

          for(const q in modelPricing) { // modelPricing now contains keys like "standard", "hd"
              const option = document.createElement('option');
              option.value = q;
              option.textContent = q.charAt(0).toUpperCase() + q.slice(1);
              qualitySelect.appendChild(option);
          }
          if(qualitySelect.value === '') qualitySelect.value = Object.keys(modelPricing)[0]; // Standardwert setzen

          // Dropdown für Größe (Auflösung)
          const sizeDiv = document.createElement('div');
          sizeDiv.classList.add('control-group');
          sizeDiv.innerHTML = `<label for="is-param-size">Auflösung</label><select id="is-param-size" data-param-key="size"></select>`;
          dynamicParamsContainer.appendChild(sizeDiv);
          const sizeSelect = sizeDiv.querySelector('select');

          const populateSizeOptions = () => {
              sizeSelect.innerHTML = ''; // Vorherige Optionen löschen
              const currentQuality = qualitySelect.value;
              const availableSizes = modelPricing[currentQuality] ? Object.keys(modelPricing[currentQuality]) : [];
              availableSizes.forEach(s => {
                  const option = document.createElement('option');
                  option.value = s;
                  option.textContent = s;
                  sizeSelect.appendChild(option);
              });
              if(sizeSelect.value === '') sizeSelect.value = availableSizes[0]; // Standardwert setzen
              updateCost(); // Kosten aktualisieren, wenn Größenoptionen neu geladen wurden

          };

          qualitySelect.addEventListener('change', populateSizeOptions);
          sizeSelect.addEventListener('change', updateCost);


          // Initial befüllen
          populateSizeOptions();

      } else {
          // Generische Behandlung für andere Modelle (wie Gemini)
          const parameterKeys = Object.keys(modelPricing).filter(key => typeof modelPricing[key] === 'object');
          
          parameterKeys.forEach(paramKey => {
              const div = document.createElement('div');
              div.classList.add('control-group');
              div.innerHTML = `<label for="is-param-${paramKey}">${paramKey.charAt(0).toUpperCase() + paramKey.slice(1)}</label><select id="is-param-${paramKey}" data-param-key="${paramKey}"></select>`;
              dynamicParamsContainer.appendChild(div);
              const select = div.querySelector('select');

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
    const selectedModelBase = modelSelect.value; // z.B. "dall-e-3"

    if (!pricingData || !selectedProvider || !selectedModelBase) {
      costDisplay.textContent = 'N/A';
      return;
    }

    try {
      let currentCostLookup = pricingData[selectedProvider]?.[selectedModelBase];

      if (!currentCostLookup) {
        costDisplay.textContent = 'N/A';
        return;
      }

      let finalCost = 'N/A';

      if (selectedProvider === 'openai' && selectedModelBase.startsWith('dall-e')) {
        const qualitySelect = dynamicParamsContainer.querySelector('#is-param-quality');
        const sizeSelect = dynamicParamsContainer.querySelector('#is-param-size');

        const quality = qualitySelect ? qualitySelect.value : null;
        const size = sizeSelect ? sizeSelect.value : null;

        if (quality && size) {
          finalCost = currentCostLookup?.[quality]?.[size];
        }
      } else {
        // Generische Kostenberechnung für andere Modelle
        const params = {};
        dynamicParamsContainer.querySelectorAll('select').forEach(sel => {
            params[sel.dataset.paramKey] = sel.value;
        });

        // Hier müsste die generische Logik angepasst werden, wenn sie mehr als eine Ebene hat.
        // Für den aktuellen Stand reicht es, die erste dynamische Ebene zu nehmen (z.B. Gemini Standard)
        const firstParamKey = Object.keys(currentCostLookup).find(key => typeof currentCostLookup[key] === 'object');
        if (firstParamKey && params[firstParamKey]) {
            finalCost = currentCostLookup[firstParamKey]?.[params[firstParamKey]];
        } else if (typeof currentCostLookup === 'number') { // Fallback, falls keine weiteren Parameter
            finalCost = currentCostLookup;
        } else {
             // Für Gemini-Modelle ohne weitere verschachtelte Parameter (die nur "standard" unter sich haben)
             if (currentCostLookup.standard) {
                 finalCost = currentCostLookup.standard['1024x1024']; // Oder einen anderen Standardwert
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