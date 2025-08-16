console.log('Main process: Script started (Root main.electron.js)'); // Unique identifier

const { app, BrowserWindow, ipcMain, dialog, Menu, MenuItem } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');

// --- HANDLER FÜR BILD SPEICHERN ---
ipcMain.handle('save-image', async (event, url) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (!win) return { success: false, error: 'Window not found.' };

  const { filePath } = await dialog.showSaveDialog(win, {
    title: 'Bild speichern unter...', 
    defaultPath: path.join(app.getPath('downloads'), 'janus-image.png'),
    filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }]
  });

  if (filePath) {
    try {
      const response = await axios({ url, responseType: 'arraybuffer' });
      fs.writeFileSync(filePath, Buffer.from(response.data));
      return { success: true, path: filePath };
    } catch (error) {
      console.error('Failed to save image:', error);
      return { success: false, error: error.message };
    }
  }
  return { success: false, error: 'Save dialog cancelled.' };
});
// --- ENDE HANDLER ---
console.log('Main process: ipcMain.handle registered for save-image');

function createWindow () {
  console.log('Main process: createWindow called');
  // --- Neuer, robuster BrowserWindow-Konstruktor ---
  const preloadPath = path.join(__dirname, 'frontend/preload.js'); // Correct path to preload.js
  console.log(`[Main Process] Attempting to load preload script from: ${preloadPath}`);

  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
        preload: preloadPath,
        contextIsolation: true, // Entscheidend für die Sicherheit und Funktion der contextBridge
        nodeIntegration: false // Aus Sicherheitsgründen deaktivieren
    }
  });
  // --- Ende des neuen Blocks ---

  // Lade die index.html in das FENSTER (den Renderer Process).
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173/');
  } else {
    mainWindow.loadFile('index.html');
  }
  mainWindow.webContents.openDevTools();

  mainWindow.webContents.on('context-menu', (event, params) => {
    const menu = new Menu();

    // Add 'Kopieren' option
    menu.append(new MenuItem({
      label: 'Kopieren',
      role: 'copy'
    }));

    // Show the custom context menu
    menu.popup({ window: mainWindow });
  });
}

// Quit when all windows are closed, except on macOS. There's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

console.log('Main process: app.whenReady().then(createWindow) called');
app.whenReady().then(createWindow);