import '../css/settings.css';
import { API_BASE_URL } from './config.js';

// Alte Element-Referenzen bleiben gültig
const apiKeyForm = document.getElementById('api-key-form');
const providerInput = document.getElementById('provider-input');
const apiKeyInput = document.getElementById('api-key-input');
const apiKeyList = document.getElementById('api-key-list');

// Funktion zum Laden und Anzeigen der gespeicherten API-Keys (unverändert)
let isLoadApiKeysRunning = false; // Globale Variable für die Sperre

async function loadApiKeys() {
    if (isLoadApiKeysRunning) {
        console.warn("loadApiKeys is already running, skipping this call.");
        return;
    }
    isLoadApiKeysRunning = true;

    apiKeyList.innerHTML = ''; // Bestehende Liste leeren
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }
        const data = await response.json();
        const keys = data.api_keys || {};
        if (Object.keys(keys).length === 0) {
            apiKeyList.innerHTML = '<li>Keine API Keys gespeichert.</li>';
            return;
        }
        for (const provider in keys) {
            const listItem = document.createElement('li');
            listItem.textContent = `Provider: ${provider}, Key: ****`; // Key maskieren
            apiKeyList.appendChild(listItem);
        }
    } catch (error) {
        apiKeyList.innerHTML = '<li>Fehler beim Laden der API-Keys.</li>';
        console.error(`Fehler beim Laden der API-Keys: ${error.message}`);
    } finally {
        isLoadApiKeysRunning = false; // Sperre aufheben
    }
}

// Initiales Laden der API-Keys, wenn das Skript ausgeführt wird.
// Stellt sicher, dass die Liste beim ersten Öffnen der Einstellungen gefüllt ist.
document.addEventListener('DOMContentLoaded', () => {
    loadApiKeys();
});


