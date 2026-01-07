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
        : path.join(process.resourcesPath, 'backend');

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
  // NEUE VALIDIERUNG HINZUFÜGEN
  try {
    const parsedUrl = new URL(url);
    // Erlaube nur HTTP(S) URLs
    if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
      console.warn(`[Electron Main] Blocked attempt to save image from unsupported protocol: ${url}`);
      return { success: false, error: 'Unsupported protocol' };
    }
  } catch (e) {
    console.warn(`[Electron Main] Blocked attempt to save image from invalid URL: ${url}`, e);
    return { success: false, error: 'Invalid URL format' };
  }

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
  // NEUE VALIDIERUNG HINZUFÜGEN
  try {
    const parsedUrl = new URL(url);
    // Erlaube nur HTTP(S) URLs
    if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
      console.warn(`[Electron Main] Blocked attempt to open unsupported protocol: ${url}`);
      return { success: false, error: 'Unsupported protocol' };
    }
  } catch (e) {
    console.warn(`[Electron Main] Blocked attempt to open invalid URL: ${url}`, e);
    return { success: false, error: 'Invalid URL format' };
  }

  const { shell } = require('electron');
  shell.openExternal(url);
  return { success: true }; // Rückgabe des Erfolgsstatus
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

ipcMain.handle('create-project', async (event, projectData) => {
  console.log(`[Electron Main] Received 'create-project' IPC call for:`, projectData.name);

  // NEUE VALIDIERUNG HINZUFÜGEN
  if (!projectData || typeof projectData !== 'object') {
    console.warn(`[Electron Main] Invalid projectData format:`, projectData);
    return { success: false, error: 'Invalid project data format.' };
  }

  const { name, description, activeProvider, activeModel } = projectData;

  if (typeof name !== 'string' || name.trim().length === 0 || name.trim().length > 100) {
    console.warn(`[Electron Main] Invalid project name:`, name);
    return { success: false, error: 'Project name is required and must be between 1 and 100 characters.' };
  }

  if (typeof description !== 'string' || description.length > 500) {
    console.warn(`[Electron Main] Invalid project description:`, description);
    return { success: false, error: 'Project description must be a string and not exceed 500 characters.' };
  }

  // Für activeProvider und activeModel nehmen wir an, dass sie Strings sein müssen
  // Eine strengere Validierung würde hier eine Liste erlaubter Werte prüfen.
  if (typeof activeProvider !== 'string' || activeProvider.trim().length === 0 || activeProvider.trim().length > 50) {
    console.warn(`[Electron Main] Invalid activeProvider:`, activeProvider);
    return { success: false, error: 'Active provider is required and must be between 1 and 50 characters.' };
  }

  if (typeof activeModel !== 'string' || activeModel.trim().length === 0 || activeModel.trim().length > 50) {
    console.warn(`[Electron Main] Invalid activeModel:`, activeModel);
    return { success: false, error: 'Active model is required and must be between 1 and 50 characters.' };
  }
  // ENDE NEUE VALIDIERUNG

  try {
    // Forward the project data to the backend API
    const response = await axios.post('http://localhost:8001/api/projects', {
      name: name,
      description: description,
      active_provider: activeProvider,
      active_model: activeModel
    });

    if (response.status === 200 || response.status === 201) {
      console.log('[Electron Main] Project created successfully on backend.');
      
      // WICHTIG: Sende ein Event zurück an das Frontend, damit es sich aktualisiert
      const win = BrowserWindow.fromWebContents(event.sender);
      if (win) {
        win.webContents.send('project-list-updated');
      }
      
      return { success: true, data: response.data };
    } else {
      throw new Error(`Backend returned status ${response.status}`);
    }
  } catch (error) {
    console.error('[Electron Main] Failed to create project via API:', error.message);
    dialog.showErrorBox('Fehler', 'Das Projekt konnte nicht auf dem Server erstellt werden.');
    return { success: false, error: error.message };
  }
});
console.log('Main process: ipcMain.handle registered for save-image');

function createWindow() {
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
    },
    show: false // Fenster zunächst verstecken
  });

  // Lade die URL basierend auf dem Build-Modus
  const loadApp = () => {
    if (app.isPackaged) {
      mainWindow.loadFile(path.join(__dirname, 'frontend', 'dist', 'index.html'));
    } else {
      mainWindow.loadURL('http://localhost:5173/');
      mainWindow.webContents.openDevTools();
    }
  };

  // Im Entwicklungsmodus auf das Backend warten, bevor geladen wird
  if (!app.isPackaged) {
    waitForBackend()
      .then(() => {
        loadApp();
        mainWindow.show();
      })
      .catch(err => {
        console.error('Failed to start backend:', err);
        app.quit();
      });
  } else {
    // Im Produktionsmodus sofort laden
    loadApp();
    mainWindow.show();
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
    if (app.isPackaged) {
      startBackend(win);
    }
  }
});

app.whenReady().then(() => {
    const win = createWindow();
    if (app.isPackaged) {
      startBackend(win);
    }
    // No need to wait for backend or load URL here as it's already handled in createWindow()
});

app.on('will-quit', stopBackend);
