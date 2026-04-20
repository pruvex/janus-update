/**
 * Globaler State für das Image Studio.
 * Dient als Single Source of Truth für alle Module.
 */
export const appState = {
    // --- Upload / Gallery ---
    currentImageFullUrl: null, // String: URL des aktuell großen Bildes
    selectedImageIds: new Set(), // Set: IDs der ausgewählten Bilder (Multi-Select)
    
    // --- Generation & Context ---
    lastContextIds: { 
        response_id: null, 
        image_id: null 
    },
    lastGeneratedPrompt: null,
    lastGeneratedImageBase64: null,
    
    // --- Presets & Data ---
    pricingData: null,      // Object: Die geladenen Preisdaten
    loadedPresetData: null, // Object: Die geladenen Presets
    
    // --- Export ---
    currentJpegExportImageId: null,
    originalImageForJpegPreview: null,
    
    // --- Inpainting / Canvas ---
    isDrawing: false,
    ctx: null,               // Canvas Context 2D
    canvasScaleFactor: 1,
    isInitDone: false,
    
    // --- Combine Mode ---
    combineSlotsData: [null, null, null, null, null], // Array für 5 Slots

    // --- Audio ---
    shutterSoundObjectUrl: null
};

// Hilfsfunktion zum Zurücksetzen von Teilbereichen (optional für später)
export function resetGenerationState() {
    appState.lastContextIds = { response_id: null, image_id: null };
    appState.lastGeneratedPrompt = null;
    appState.lastGeneratedImageBase64 = null;
}
