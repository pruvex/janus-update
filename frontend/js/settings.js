// Logik für das Einstellungs-Modal
const settingsModal = document.getElementById('settings-modal');
const settingsBtn = document.getElementById('settings-btn');
const closeBtn = document.getElementsByClassName('close')[0];
const apiKeyForm = document.getElementById('api-key-form');
const providerInput = document.getElementById('provider-input');
const apiKeyInput = document.getElementById('api-key-input');
const apiKeyList = document.getElementById('api-key-list');

settingsBtn.onclick = function() {
  settingsModal.style.display = 'block';
  loadApiKeys();
}

closeBtn.onclick = function() {
  settingsModal.style.display = 'none';
}

window.onclick = function(event) {
  if (event.target == settingsModal) {
    settingsModal.style.display = 'none';
  }
}

apiKeyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const provider = providerInput.value;
    const api_key = apiKeyInput.value;

    try {
        await fetch(`${API_BASE_URL}/api/keys`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ provider, api_key }),
        });
        apiKeyInput.value = '';
        loadApiKeys(); // Keys neu laden und anzeigen
    } catch (error) {
        console.error('Error saving API key:', error);
        alert('Fehler beim Speichern des API-Keys.');
    }
});

async function loadApiKeys() {
    apiKeyList.innerHTML = ''; // Bestehende Liste leeren
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }

        const data = await response.json();
        for (const provider in data.api_keys) {
            const listItem = document.createElement('li');
            listItem.textContent = `Provider: ${provider}, Key: ****`; // Key maskieren
            apiKeyList.appendChild(listItem);
        }
    } catch (error) {
        console.error('Error loading API keys:', error);
        alert(`Fehler beim Laden der API-Keys: ${error.message}`);
    }
}