// js/modules/image-studio/presets.js

import { appState } from './state.js';
import { fetchStylePresets } from './api.js';
import { getBackendBaseUrl } from './utils.js';

// --- Private Module Variables (DOM Elements) ---
let presetsContainer, styleSelect, variationSelect, 
    stylePreviewContainer, stylePreviewImg, styleImagePlaceholder,
    presetInfoDisplay, providerSelect;

// --- State Checkboxes ---
let presetsModeCheckbox, applyPresetCheckbox, applyPresetToRefineCheckbox;
let editModeCheckbox, refineModeCheckbox;

/**
 * Initialisiert das Presets-Modul.
 * Bindet Event-Listener und lädt die Daten vom Backend.
 */
export function initPresetsModule() {
    // 1. DOM Elemente referenzieren
    presetsContainer = document.getElementById('is-presets-container');
    styleSelect = document.getElementById('is-style-select');
    variationSelect = document.getElementById('is-variation-select');
    stylePreviewContainer = document.getElementById('is-style-preview-container');
    stylePreviewImg = document.getElementById('current-style-image');
    styleImagePlaceholder = document.getElementById('style-image-placeholder');
    presetInfoDisplay = document.getElementById('preset-info-display');
    
    // Dependency: Provider Select wird für die Bild-Vorschau benötigt (z.B. variation_openai.png)
    providerSelect = document.getElementById('is-provider-select'); 

    // 2. Checkboxes referenzieren
    presetsModeCheckbox = document.getElementById('is-presets-mode');
    applyPresetCheckbox = document.getElementById('is-apply-preset-to-edit');
    applyPresetToRefineCheckbox = document.getElementById('is-apply-preset-to-refine');
    
    // Externe Modi (read-only Access für Visibility Logic)
    editModeCheckbox = document.getElementById('is-edit-mode');
    refineModeCheckbox = document.getElementById('is-refine-mode');

    // 3. Event Listeners setzen
    if (styleSelect) styleSelect.addEventListener('change', populateVariationSelect);
    
    if (variationSelect) {
        variationSelect.addEventListener('change', () => {
            updatePresetInfoBox();
            updateStylePreviewImage();
        });
    }

    if (applyPresetToRefineCheckbox) {
        applyPresetToRefineCheckbox.addEventListener('change', () => { updatePresetVisibility(); });
    }
    if (applyPresetCheckbox) {
        applyPresetCheckbox.addEventListener('change', () => { updatePresetVisibility(); updateStylePreviewImage(); });
    }
    
    // Initiales Laden der Daten
    loadPresets();
    updatePresetVisibility(); 
}

/**
 * Lädt die Presets vom Backend (API Call).
 * Speichert das Ergebnis in appState.loadedPresetData.
 */
async function loadPresets() {
    try {
        appState.loadedPresetData = await fetchStylePresets();
        populateStyleSelect(); 
    } catch (error) {
        console.error("Error loading presets:", error);
        if (styleSelect) {
            styleSelect.innerHTML = '<option>Fehler beim Laden</option>';
        }
    }
}

/**
 * Befüllt das Kategorie-Dropdown (styleSelect).
 */
function populateStyleSelect() {
    if (!styleSelect) return;
    styleSelect.innerHTML = '';
    
    if (!appState.loadedPresetData || Object.keys(appState.loadedPresetData).length === 0) {
        styleSelect.innerHTML = '<option>Lade...</option>';
        return;
    }
    
    for (const styleName in appState.loadedPresetData) {
        const option = document.createElement('option');
        option.value = styleName;
        option.textContent = styleName;
        styleSelect.appendChild(option);
    }

    // FIX: Explizit den ersten Eintrag wählen, falls nichts selektiert ist
    if (!styleSelect.value && styleSelect.options.length > 0) {
        styleSelect.selectedIndex = 0;
    }

    populateVariationSelect();
}

/**
 * Befüllt das Variations-Dropdown basierend auf der gewählten Kategorie.
 */
function populateVariationSelect() {
    if (!styleSelect || !variationSelect) return;
    const selectedStyle = styleSelect.value;
    variationSelect.innerHTML = '';
    
    if (appState.loadedPresetData && appState.loadedPresetData[selectedStyle]) {
        const variations = appState.loadedPresetData[selectedStyle];
        Object.keys(variations).forEach(variationName => {
            const option = document.createElement('option');
            option.value = variationName;
            option.textContent = variationName;
            variationSelect.appendChild(option);
        });
    }

    // FIX: Sicherstellen, dass ein Wert gesetzt ist
    if (variationSelect.options.length > 0) {
        variationSelect.selectedIndex = 0;
    }

    // WICHTIG: Jetzt die Updates für die UI-Boxen manuell aufrufen
    updatePresetInfoBox();
    updateStylePreviewImage();
}

/**
 * Zeigt die Diamond-Standard Metadaten an.
 * Mappt exakt auf die Python `PresetConfig` Struktur.
 */
function updatePresetInfoBox() {
    if (!styleSelect || !variationSelect || !presetInfoDisplay) return;

    const style = styleSelect.value;
    const variation = variationSelect.value;
    
    if (!appState.loadedPresetData || !appState.loadedPresetData[style] || !appState.loadedPresetData[style][variation]) {
        presetInfoDisplay.style.display = 'none';
        return;
    }
    
    const config = appState.loadedPresetData[style][variation];
    const usageText = config.recommended_use || "Standard preset configuration.";
    
    // HTML Template passend zum Dark Mode UI
    presetInfoDisplay.innerHTML = `
        <div style="margin-bottom: 10px;">
            <strong style="color: var(--accent-color); display:block; font-size: 0.85em; margin-bottom:4px; text-transform:uppercase;">🎯 ${config.name}</strong>
            <div style="font-size: 0.9em; color: #ddd; line-height: 1.4; margin-bottom: 6px;">${config.preset_intent}</div>
            <div style="font-size: 0.85em; color: #aaa; font-style: italic; border-left: 2px solid var(--accent-color); padding-left: 8px; margin-bottom: 6px;">
                Empfohlen für: ${usageText}
            </div>
            ${config.gemini_style_keywords ? `
                <div style="font-size: 0.75em; color: #999; border-left: 2px solid rgba(255,255,255,0.1); padding-left: 8px; margin-top: 6px;">
                    Keywords: ${config.gemini_style_keywords}
                </div>` : ''}
        </div>
        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 0.8em; color: #bbb;">
            <div>📸 ${config.camera}</div>
            <div>🔍 ${config.lens}</div>
            <div>🎞️ ${config.film_stock}</div>
            <div>💡 ${config.lighting}</div>
        </div>
    `;
    presetInfoDisplay.style.display = 'block';
}

/**
 * Lädt das Vorschaubild (z.B. "1950s_flash_gemini.png").
 * Berücksichtigt den aktuell gewählten AI-Provider.
 */
export function updateStylePreviewImage() {
    if (!appState.loadedPresetData) return;
    if (!stylePreviewImg || !styleImagePlaceholder) return;
    
    // Wir holen den Provider frisch aus dem DOM, da er sich ändern kann
    const currentProvider = providerSelect ? providerSelect.value : 'unknown';
    const variation = variationSelect ? variationSelect.value : null;
    
    // Wenn Container unsichtbar, sparen wir uns den Request
    if (stylePreviewContainer && stylePreviewContainer.style.display === 'none') return;

    if (!currentProvider || !variation) {
        stylePreviewImg.style.display = 'none';
        styleImagePlaceholder.style.display = 'flex';
        styleImagePlaceholder.textContent = "Wähle ein Preset";
        return;
    }

    // Normalisierung des Dateinamens (muss zum Backend-Asset passen)
    const cleanVar = variation.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
    const filename = `${cleanVar}_${currentProvider}.png`;
    const imageUrl = `${getBackendBaseUrl()}/backend_assets/previews/${filename}?t=${new Date().getTime()}`;
    
    const imgTester = new Image();
    imgTester.onload = () => {
        stylePreviewImg.src = imageUrl;
        stylePreviewImg.style.display = 'block';
        styleImagePlaceholder.style.display = 'none';
    };
    imgTester.onerror = () => {
        stylePreviewImg.style.display = 'none';
        styleImagePlaceholder.style.display = 'flex';
        styleImagePlaceholder.innerHTML = `<div style="text-align:center; font-size:0.8em; color:#666;">Keine Vorschau:<br>${filename}</div>`;
    };
    imgTester.src = imageUrl;
}

/**
 * Steuert die Sichtbarkeit des gesamten Preset-Containers.
 * Basierend auf: Globalem Preset-Mode ODER Edit-Mode-Preset ODER Refine-Mode-Preset.
 */
export function updatePresetVisibility() {
    const presetsActive = presetsModeCheckbox?.checked || false;
    const editModeActive = editModeCheckbox?.checked || false;
    const applyToEditActive = applyPresetCheckbox?.checked || false;
    const refineModeActive = refineModeCheckbox?.checked || false;
    const applyToRefineActive = applyPresetToRefineCheckbox?.checked || false;

    const shouldBeVisible = presetsActive || (editModeActive && applyToEditActive) || (refineModeActive && applyToRefineActive);
    
    if (presetsContainer) presetsContainer.style.display = shouldBeVisible ? 'flex' : 'none';
    if (stylePreviewContainer) stylePreviewContainer.style.display = shouldBeVisible ? 'flex' : 'none';
    
    if (!shouldBeVisible) {
        if (stylePreviewImg) stylePreviewImg.style.display = 'none';
        if (styleImagePlaceholder) styleImagePlaceholder.style.display = 'flex';
    } else {
        // FIX: Wenn die Sektion sichtbar wird, erzwinge ein Update der Beschreibungen und Bilder
        updatePresetInfoBox();
        updateStylePreviewImage();
    }
}

/**
 * Stellt ein Preset wieder her (z.B. beim Laden eines Bildes aus der History).
 */
export function restorePresetSettings(style, variation) {
    if (!style || !variation) return;
    
    if (styleSelect) {
        styleSelect.value = style;
        // Befüllt die Variationen passend zum neuen Stil
        populateVariationSelect(); 
    }
    
    if (variationSelect) {
        variationSelect.value = variation;
    }

    // FIX: Explizit nach dem Setzen beider Werte die Boxen füllen
    updatePresetInfoBox();
    updateStylePreviewImage();
}

// --- Helper UI Toggles (Aufgerufen von Main Script Checkbox-Events) ---

export function togglePresetForRefineUI() {
    const container = document.getElementById('apply-preset-to-refine-container');
    if (!refineModeCheckbox || !container) return;
    
    if (refineModeCheckbox.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        // Wenn Refine aus ist, muss auch die Preset-Option dafür aus sein
        if (applyPresetToRefineCheckbox) applyPresetToRefineCheckbox.checked = false;
    }
    updatePresetVisibility();
}

export function togglePresetForEditUI() {
    const container = document.getElementById('apply-preset-to-edit-container');
    if (!editModeCheckbox || !container) return;
    
    if (editModeCheckbox.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        if (applyPresetCheckbox) applyPresetCheckbox.checked = false;
    }
    updatePresetVisibility();
}

/**
 * Gibt die aktuell gewählten Werte zurück (für den API Call).
 */
export function getSelectedPresetValues() {
    return {
        style: styleSelect ? styleSelect.value : null,
        variation: variationSelect ? variationSelect.value : null
    };
}
