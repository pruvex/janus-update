document.addEventListener('DOMContentLoaded', () => {
  const healthCheckButton = document.getElementById('callBackend');
  const responseOutput = document.getElementById('responseOutput');

  healthCheckButton.addEventListener('click', async () => {
    responseOutput.textContent = 'Sende Anfrage...';
    try {
      const response = await fetch('http://127.0.0.1:8000/api/health');
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