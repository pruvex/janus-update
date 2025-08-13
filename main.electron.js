const { app, BrowserWindow, Menu, MenuItem } = require('electron');
const path = require('path');

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'frontend/preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true,
      nodeIntegrationInSubFrames: true
    }
  });

  // Lade die von Vite bereitgestellte URL. Passe den Port an, falls nötig.
  mainWindow.loadURL('http://localhost:5173');

  // Öffne die DevTools.
  // mainWindow.webContents.openDevTools();

  // Add context menu
  mainWindow.webContents.on('context-menu', (event, params) => {
    const menu = new Menu();

    menu.append(new MenuItem({
      label: 'Copy',
      role: 'copy',
      enabled: params.selectionText.trim().length > 0
    }));
    menu.append(new MenuItem({
      label: 'Select All',
      role: 'selectAll'
    }));

    menu.popup({ window: mainWindow });
  });
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
