const { app, BrowserWindow, ipcMain, dialog, Menu, MenuItem } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https'); // For downloading images

function createWindow () {
  // --- Neuer, robuster BrowserWindow-Konstruktor ---
const preloadPath = path.join(__dirname, 'preload.js');
console.log(`[Main Process] Attempting to load preload script from: ${preloadPath}`);

mainWindow = new BrowserWindow({
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

  // Handle save-image IPC call
  ipcMain.on('save-image', async (event, imageUrl) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      defaultPath: path.basename(new URL(imageUrl).pathname), // Suggest filename from URL
      filters: [
        { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!canceled && filePath) {
      const file = fs.createWriteStream(filePath);
      https.get(imageUrl, (response) => {
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          console.log('Image downloaded successfully!');
        });
      }).on('error', (err) => {
        fs.unlink(filePath, () => {}); // Delete the file async.
        console.error('Error downloading image:', err.message);
      });
    }
  });
}

app.whenReady().then(createWindow);

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