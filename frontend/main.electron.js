const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https'); // For downloading images

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'), // Ensure preload script is loaded
      contextIsolation: true, // Enable context isolation
      nodeIntegration: false, // Disable node integration
    }
  });

  // Lade die index.html in das FENSTER (den Renderer Process).
  mainWindow.loadFile('index.html');
  mainWindow.webContents.openDevTools();

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