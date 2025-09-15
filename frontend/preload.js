const { contextBridge, ipcRenderer, shell } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  saveImage: (url) => ipcRenderer.invoke('save-image', url),
  openExternal: (url) => ipcRenderer.invoke('open-external-link', url), // Changed to use ipcRenderer.invoke
  // we can also expose variables, not just functions
});