console.log('Main process: Script started (Root main.electron.js)'); // Unique identifier

const { app, BrowserWindow, ipcMain, dialog, Menu, MenuItem } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const { spawn, exec } = require('child_process');

let backendProcess = null;

function getBackendPath() {
    // In production, electron-builder unpacks the exe to the resources path
    // In development, we run it from the project's dist folder
    const isDev = process.env.NODE_ENV === 'development';
    const unpackedPath = isDev 
        ? path.join(__dirname, 'dist', 'janus_backend')
        : path.join(process.resourcesPath, 'dist', 'janus_backend');

    return path.join(unpackedPath, 'janus_backend.exe');
}

function startBackend(mainWindow) {
    const backendPath = getBackendPath();
    console.log(`[Electron Main] Starting backend from: ${backendPath}`);

    if (!fs.existsSync(backendPath)) {
        console.error(`[Electron Main] Backend executable not found at ${backendPath}`);
        dialog.showErrorBox('Backend Error', `Backend executable not found at ${backendPath}`);
        app.quit();
        return;
    }

    // Ensure any previous backend process is stopped
    stopBackend();
    // Add a small delay to allow the port to be released
    // This is a hacky solution, a better way would be to check if the port is free
    // but for now, this might work.
    setTimeout(() => {
        const outputLogPath = path.join(app.getPath('userData'), 'backend_output.log');
        const errorLogPath = path.join(app.getPath('userData'), 'backend_error.log');

        // Clear previous logs
        if (fs.existsSync(outputLogPath)) fs.unlinkSync(outputLogPath);
        if (fs.existsSync(errorLogPath)) fs.unlinkSync(errorLogPath);

        const outputStream = fs.createWriteStream(outputLogPath, { flags: 'a' });
        const errorStream = fs.createWriteStream(errorLogPath, { flags: 'a' });

        backendProcess = spawn(backendPath, [], {
            stdio: ['ignore', 'pipe', 'pipe'] // Use 'pipe' to capture output
        });

        backendProcess.stdout.pipe(outputStream);
        backendProcess.stderr.pipe(errorStream);

        // Still log to console for immediate feedback during development
        backendProcess.stdout.on('data', (data) => {
            console.log(`[Backend STDOUT]: ${data.toString()}`);
            if (mainWindow) {
                mainWindow.webContents.send('backend-log', data.toString());
            }
        });

        backendProcess.stderr.on('data', (data) => {
            console.error(`[Backend STDERR]: ${data.toString()}`);
            if (mainWindow) {
                mainWindow.webContents.send('backend-log', `ERROR: ${data.toString()}`);
            }
        });

        backendProcess.on('close', (code) => {
            console.log(`[Backend Process] exited with code ${code}`);
            backendProcess = null;
            outputStream.end();
            errorStream.end();
            // Optionally, notify the user or try to restart
        });

        backendProcess.on('error', (err) => {
            console.error(`[Backend Process] Failed to start or encountered an error: ${err.message}`);
            if (mainWindow) {
                mainWindow.webContents.send('backend-log', `CRITICAL ERROR: ${err.message}`);
            }
            dialog.showErrorBox('Backend Critical Error', `Failed to start backend process: ${err.message}. Please check logs.`);
            app.quit();
        });

        backendProcess.on('exit', (code, signal) => {
            console.log(`[Backend Process] exited with code ${code} and signal ${signal}`);
            if (mainWindow) {
                mainWindow.webContents.send('backend-log', `Backend exited with code ${code} and signal ${signal}`);
            }
            if (code !== 0) {
                // Only show error box if it's an unexpected exit
                // dialog.showErrorBox('Backend Exited Unexpectedly', `Backend process exited with code ${code}. Please check logs.`);
            }
        });
    }, 1000); // 1 second delay
}

function stopBackend() {
    if (backendProcess) {
        console.log('[Electron Main] Stopping backend process...');
        // Use taskkill on Windows for a more forceful shutdown
        if (process.platform === "win32") {
            exec(`taskkill /pid ${backendProcess.pid} /f /t`);
        } else {
            backendProcess.kill('SIGINT'); // Send SIGINT first for graceful shutdown
        }
        backendProcess = null;
    }
}

function waitForBackend(retries = 30, delay = 1000) {
    return new Promise((resolve, reject) => {
        function check() {
            axios.get('http://127.0.0.1:8001/api/models/catalog') // A simple endpoint to check if backend is alive
                .then(() => {
                    console.log('[Electron Main] Backend is ready!');
                    resolve(true);
                })
                .catch((error) => {
                    console.log(`[Electron Main] Waiting for backend... Retries left: ${retries}`);
                    if (retries === 0) {
                        console.error('[Electron Main] Backend did not start in time.', error);
                        dialog.showErrorBox('Backend Error', 'Backend did not start in time. Please check logs.');
                        app.quit();
                        reject(false);
                    } else {
                        setTimeout(check, delay);
                        retries--;
                    }
                });
        }
        check();
    });
}

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

// --- HANDLER FÜR EXTERNEN LINK ÖFFNEN ---
ipcMain.handle('open-external-link', async (event, url) => {
  const { shell } = require('electron'); // Import shell here
  shell.openExternal(url);
});
// --- ENDE HANDLER ---

ipcMain.handle('open-directory-dialog', async () => {
  const { dialog } = require('electron');
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  if (result.canceled) {
    return null;
  } else {
    return result.filePaths[0];
  }
});
console.log('Main process: ipcMain.handle registered for save-image');

function createWindow () {
  console.log('Main process: createWindow called');
  const preloadPath = path.join(__dirname, 'frontend/preload.js');
  console.log(`[Main Process] Attempting to load preload script from: ${preloadPath}`);

  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false
    }
  });

  // The window content will be loaded after the backend is ready
  // if (process.env.NODE_ENV === 'development') {
  //   mainWindow.loadURL('http://localhost:5173/');
  // } else {
  //   // In production, serve the index.html file
  //   mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  // }
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.webContents.on('context-menu', (event, params) => {
    const menu = new Menu();
    menu.append(new MenuItem({ label: 'Kopieren', role: 'copy' }));
    menu.popup({ window: mainWindow });
  });
  
  return mainWindow;
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    const win = createWindow();
    if (process.env.NODE_ENV !== 'development') {
      startBackend(win);
    }
    waitForBackend().then(() => {
        if (process.env.NODE_ENV === 'development') {
            win.loadURL('http://localhost:5173/');
        } else {
            win.loadFile(path.join(__dirname, 'dist', 'index.html'));
        }
    });
  }
});

app.whenReady().then(() => {
    const win = createWindow();
    if (process.env.NODE_ENV !== 'development') {
      startBackend(win);
    }
    waitForBackend().then(() => {
        if (process.env.NODE_ENV === 'development') {
            win.loadURL('http://localhost:5173/');
        } else {
            win.loadFile(path.join(__dirname, 'dist', 'index.html'));
        }
    });
});

app.on('will-quit', stopBackend);
