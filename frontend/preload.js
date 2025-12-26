const { contextBridge, ipcRenderer, shell } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  saveImage: (url) => ipcRenderer.invoke("save-image", url),
  openExternal: (url) => ipcRenderer.invoke("open-external-link", url),
  openDirectoryDialog: () => ipcRenderer.invoke("open-directory-dialog"), // Exposed directory dialog
  createProject: (projectData) => ipcRenderer.invoke("create-project", projectData), // Exposed createProject method
  on: (channel, callback) => {
    ipcRenderer.on(channel, (event, ...args) => callback(...args));
  },
});