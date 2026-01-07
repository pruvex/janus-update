// Check if we're running in Electron or a web browser
const isElectron = window.electron && typeof window.electron === 'object';

// Set the API base URL - use Electron's API if available, otherwise fall back to default
const API_BASE_URL = isElectron && window.electron.getApiBaseUrl 
  ? window.electron.getApiBaseUrl() 
  : 'http://127.0.0.1:8001';

// Make sure the API_BASE_URL is available globally
window.API_BASE_URL = API_BASE_URL;

console.log(`API Base URL is set to: ${API_BASE_URL}`);

export { API_BASE_URL };
