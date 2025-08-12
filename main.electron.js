const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'frontend/preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    }
  });

  // Lade die von Vite bereitgestellte URL. Passe den Port an, falls nötig.
  mainWindow.loadURL('http://localhost:5173');

  // Öffne die DevTools.
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
