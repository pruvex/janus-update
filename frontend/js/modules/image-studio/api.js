import { getBackendBaseUrl } from './utils.js';

const BASE_URL = getBackendBaseUrl();

/**
 * Holt Daten von einem API-Endpunkt. Behandelt Fehler und JSON-Parsing.
 * @param {string} endpoint Der API-Endpunkt (z.B. '/api/images/pricing')
 * @returns {Promise<any>} Die geparsten JSON-Daten.
 * @throws {Error} Wenn die Anfrage fehlschlägt.
 */
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`);
        if (!response.ok) {
            // Versuche, eine detailliertere Fehlermeldung vom Backend zu erhalten
            let errorDetails = `HTTP-Fehler ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetails = errorData.detail || errorDetails;
            } catch (e) {
                // Keine JSON-Fehlermeldung vorhanden
            }
            throw new Error(errorDetails);
        }
        return await response.json();
    } catch (error) {
        console.error(`Fehler beim Abrufen von ${endpoint}:`, error);
        throw error; // Fehler weiterwerfen, damit die aufrufende Funktion ihn behandeln kann
    }
}

/**
 * Lädt die Preisdaten für die Bildmodelle vom Backend.
 */
export function fetchPricingData() {
    return fetchData('/api/images/pricing');
}

/**
 * Lädt die verfügbaren Stil-Presets vom Backend.
 */
export function fetchStylePresets() {
    return fetchData('/api/images/presets/list');
}

/**
 * Sendet Daten an einen API-Endpunkt mittels POST.
 * @param {string} endpoint Der API-Endpunkt.
 * @param {object} body Das zu sendende JavaScript-Objekt.
 * @returns {Promise<any>} Die geparsten JSON-Daten der Antwort.
 * @throws {Error} Wenn die Anfrage fehlschlägt.
 */
async function postData(endpoint, body) {
    const token = localStorage.getItem('auth_token');
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            let errorDetails = `HTTP-Fehler ${response.status}`;
            try {
                const errorData = await response.json();
                // Wenn das Backend ein Detail-Feld schickt (Standard bei FastAPI), nimm das
                if (errorData.detail) {
                    errorDetails = typeof errorData.detail === 'object' 
                        ? JSON.stringify(errorData.detail) 
                        : errorData.detail;
                }
            } catch (e) { /* Fallback auf Standard-Text */ }
            throw new Error(errorDetails);
        }
        return await response.json();
    } catch (error) {
        console.error(`Fehler beim POST zu ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Fragt das Backend nach der geschätzten Dateigröße für ein Bild in einem bestimmten Format.
 * @param {string} imageBase64 Das Bild als Base64-String.
 * @param {string} format Das gewünschte Format (z.B. 'jpg_95').
 * @returns {Promise<{file_size_bytes: number}>}
 */
export function fetchEstimatedSize(imageBase64, format) {
    return postData('/api/images/preview/size', {
        image_base64: imageBase64,
        format: format
    });
}

/**
 * Sendet eine Anfrage zur Bildgenerierung an das Backend.
 * @param {object} payload Das komplette Payload-Objekt für die Generierungs-API.
 * @returns {Promise<any>} Das Ergebnisobjekt vom Backend.
 */
export function generateImageApi(payload) {
    // Wir verwenden hier direkt die postData-Funktion, da sie bereits alles Nötige tut.
    return postData('/api/images/generate', payload);
}
