const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  saveImage: (url) => ipcRenderer.invoke('save-image', url),
  // Other existing functions...
  send: (channel, data) => {
    // whitelist channels
    let validChannels = ['save-image'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  receive: (channel, func) => {
    let validChannels = ['image-saved']; // Example of a channel to receive from main
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender` which is a remote object
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  }
});