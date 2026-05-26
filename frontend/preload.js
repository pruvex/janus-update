const { contextBridge, ipcRenderer } = require("electron");

// Expose clipboard IPC under dedicated electronAPI namespace
contextBridge.exposeInMainWorld("electronAPI", {
  readClipboard: () => ipcRenderer.invoke('clipboard:read'),
});

contextBridge.exposeInMainWorld("electron", {
  
  // === NACHRICHTEN AN DEN MAIN-PROZESS SENDEN ===
  // (Frontend -> Main)
  send: (channel, data) => {
    // Liste der erlaubten Kanäle, um sicherzustellen, dass das Frontend
    // nur vordefinierte Aktionen auslösen kann.
    const validChannels = []; 
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },

  // === AUFGABEN IM MAIN-PROZESS AUSFÜHREN (mit Antwort) ===
  // (Frontend -> Main -> Frontend)
  saveImage: (url) => ipcRenderer.invoke("save-image", url),
  saveImageDialog: (options) => ipcRenderer.invoke("save-image-dialog", options),
  showFolderDialog: () => ipcRenderer.invoke('show-folder-dialog'),
  saveFileInPath: (data) => ipcRenderer.invoke("save-file-in-path", data),
  openExternalLink: (url) => ipcRenderer.invoke("open-external-link", url),
  openDirectoryDialog: () => ipcRenderer.invoke("open-directory-dialog"),
  createProject: (projectData) => ipcRenderer.invoke("create-project", projectData),
  getApiKey: () => ipcRenderer.invoke('get-api-key'),
  readClipboard: () => ipcRenderer.invoke('read-clipboard'),
  writeFrontendDebugLog: (payload) => ipcRenderer.invoke('debug:write-frontend-log', payload),

  // === UPDATE IPC CONTRACTS ===
  getUpdateState: () => ipcRenderer.invoke('update:get-state'),
  installUpdateNow: () => ipcRenderer.send('update:install-now'),
  retryUpdate: () => ipcRenderer.send('update:retry'),
  dismissNormalUpdate: () => ipcRenderer.send('update:dismiss-normal'),

  // === NACHRICHTEN VOM MAIN-PROZESS EMPFANGEN ===
  // (Main -> Frontend)
  on: (channel, callback) => {
    // Liste der erlaubten Kanäle für eingehende Nachrichten
    const validChannels = ['update-state-changed', 'project-list-updated', 'backend-log'];
    if (validChannels.includes(channel)) {
      // Sichere Weiterleitung an den Renderer
      const subscription = (event, ...args) => callback(...args);
      ipcRenderer.on(channel, subscription);

      // Wichtig: Bietet eine "Aufräum"-Funktion an, die der Renderer nutzen kann
      return () => ipcRenderer.removeListener(channel, subscription);
    }
  },
  onUpdateStateChanged: (callback) => ipcRenderer.on('update-state-changed', (event, state) => callback(state)),
});