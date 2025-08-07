
// Logik für das Einstellungs-Modal
const settingsModal = document.getElementById('settings-modal');
const settingsBtn = document.getElementById('settings-btn');
const closeBtn = document.getElementsByClassName('close')[0];

settingsBtn.onclick = function() {
  settingsModal.style.display = 'block';
}

closeBtn.onclick = function() {
  settingsModal.style.display = 'none';
}

window.onclick = function(event) {
  if (event.target == settingsModal) {
    settingsModal.style.display = 'none';
  }
}

// Mock-Funktion zum Anzeigen von API-Keys
function displayApiKeys() {
  const apiKeyList = document.getElementById('api-key-list');
  const exampleKey = {
    provider: 'OpenAI',
    key: 'sk-....aB3x'
  };
  const listItem = document.createElement('li');
  listItem.textContent = `Provider: ${exampleKey.provider}, Key: ${exampleKey.key}`;
  apiKeyList.appendChild(listItem);
}

displayApiKeys();
