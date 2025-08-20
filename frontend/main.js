import { API_BASE_URL } from './js/config.js';

document.addEventListener('DOMContentLoaded', () => {
  const healthCheckButton = document.getElementById('callBackend');
  const responseOutput = document.getElementById('responseOutput');

  healthCheckButton.addEventListener('click', async () => {
    responseOutput.textContent = 'Sende Anfrage...';
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      responseOutput.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      responseOutput.textContent = `Fehler bei der Anfrage: ${error.message}`;
    }
  });
});