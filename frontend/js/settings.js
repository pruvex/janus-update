import { API_BASE_URL } from './config.js';

// Alte Element-Referenzen bleiben gültig
const apiKeyForm = document.getElementById('api-key-form');
const providerInput = document.getElementById('provider-input');
const apiKeyInput = document.getElementById('api-key-input');
const apiKeyList = document.getElementById('api-key-list');

// Neue Element-Referenzen für die Navigation
const settingsNav = document.getElementById('settings-nav');
const navLinks = document.querySelectorAll('.settings-nav-link');
const contentSections = document.querySelectorAll('.settings-section');

// Event Listener für das Speichern von API-Keys (unverändert)
apiKeyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const provider = providerInput.value;
    const api_key = apiKeyInput.value;

    if (!api_key) {
        alert('Bitte geben Sie einen API-Key ein.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ provider, api_key }),
        });
        if (!response.ok) throw new Error('Fehler beim Speichern des Keys.');
        
        apiKeyInput.value = '';
        loadApiKeys(); // Keys neu laden und anzeigen
        alert('API Key erfolgreich gespeichert.');
    } catch (error) {
        console.error('Error saving API key:', error);
        alert('Fehler beim Speichern des API-Keys.');
    }
});

// Funktion zum Laden und Anzeigen der gespeicherten API-Keys (unverändert)
async function loadApiKeys() {
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
    }
}

// NEUE LOGIK: Steuerung der Navigation in den Einstellungen
settingsNav.addEventListener('click', (e) => {
    // Sicherstellen, dass ein Link geklickt wurde
    const link = e.target.closest('.settings-nav-link');
    if (!link) return;
    
    e.preventDefault();

    const targetId = link.dataset.target;

    // Alle aktiven Klassen von den Links entfernen
    navLinks.forEach(navLink => navLink.classList.remove('active-setting'));
    // Dem geklickten Link die aktive Klasse geben
    link.classList.add('active-setting');

    // Alle Inhalts-Sektionen ausblenden
    contentSections.forEach(section => {
        section.style.display = 'none';
    });

    // Die Ziel-Sektion einblenden
    const targetSection = document.getElementById(targetId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
});

// Initiales Laden der API-Keys, wenn das Skript ausgeführt wird.
// Stellt sicher, dass die Liste beim ersten Öffnen der Einstellungen gefüllt ist.
document.addEventListener('DOMContentLoaded', () => {
    loadApiKeys();
});

// Da das Skript als Modul geladen wird, kann es sein, dass DOMContentLoaded schon vorbei ist.
// Wir rufen es sicherheitshalber auch direkt auf.
loadApiKeys();
