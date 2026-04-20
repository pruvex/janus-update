console.log('Main process: Script started (Root main.electron.js)'); // Unique identifier

const { app, BrowserWindow, ipcMain, dialog, Menu, MenuItem, net, session, shell, protocol } = require('electron');

// ============================================================
// YOUTUBE ORIGIN FIX: Disable site-per-process isolation to prevent iframe blocking
// ============================================================
app.commandLine.appendSwitch('disable-features', 'IsolateOrigins,site-per-process');
const path = require('path');
const fs = require('fs');
const http = require('http'); // For health check
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');
const axios = require('axios');

// ============================================================
// YOUTUBE ORIGIN FIX: Register custom scheme as privileged
// ============================================================
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'janus',
    privileges: {
      secure: true,
      allowServiceWorkers: true,
      standard: true,
      supportFetchAPI: true,
      corsEnabled: true,
    },
  },
]);

// ============================================================
// YOUTUBE ORIGIN FIX: Mask Janus as real Chrome browser globally
// ============================================================
app.userAgentFallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

// ============================================================
// DIAMANT-STANDARD UPDATE KONFIGURATION
// ============================================================

autoUpdater.allowPrerelease = true; 
autoUpdater.allowDowngrade = false;

// KORREKTUR: Wir laden das Log-Modul hier direkt. 
// So ist es egal, wo 'const log' im Rest der Datei steht.
autoUpdater.logger = require('electron-log');
autoUpdater.logger.transports.file.level = 'info';
// ============================================================

let backendProcess = null;

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        const windows = BrowserWindow.getAllWindows();
        const win = windows.length ? windows[0] : null;
        if (win) {
            if (win.isMinimized()) win.restore();
            win.focus();
        }
    });
}

function isBackendReady() {
    return new Promise((resolve) => {
        const req = http.get('http://127.0.0.1:8001/api/health', (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    resolve(res.statusCode === 200 && json.status === 'ready');
                } catch (e) {
                    resolve(false);
                }
            });
        });

        req.on('error', () => resolve(false));
        req.end();
    });
}

function getBackendPath() {
    // In production, electron-builder unpacks the exe to the resources path
    // In development, we run it from the project's dist folder
    const isDev = process.env.NODE_ENV === 'development';
    const unpackedPath = isDev 
        ? path.join(__dirname, 'dist', 'janus_backend')
        : path.join(process.resourcesPath, 'backend');

    return path.join(unpackedPath, 'janus_backend.exe');
}

async function startBackend(mainWindow) {
    const backendPath = getBackendPath();
    log.info(`[Electron] Starting backend from: ${backendPath}`);

    if (!fs.existsSync(backendPath)) {
        const errorMsg = `Backend executable not found at ${backendPath}`;
        log.error(`[Electron] ${errorMsg}`);
        dialog.showErrorBox('Backend Error', errorMsg);
        app.quit();
        return;
    }

    if (backendProcess) {
        log.info('[Electron] Backend process already spawned in this session. Skipping start.');
        return;
    }

    const alreadyRunning = await isBackendReady();
    if (alreadyRunning) {
        log.info('[Electron] Backend already responding on :8001. Skipping spawn.');
        return;
    }

    // Ensure any previous backend process is stopped
    stopBackend();
    
    // Add a small delay to allow the port to be released
    setTimeout(() => {
        backendProcess = spawn(backendPath, [], {
            cwd: path.dirname(backendPath), // Set working directory
            stdio: ['ignore', 'pipe', 'pipe'],
            windowsHide: true
        });

        // Log stdout to electron-log
        backendProcess.stdout.on('data', (data) => {
            const msg = data.toString().trim();
            if (msg) {
                log.info(`[Backend]: ${msg}`);
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.webContents.send('backend-log', msg);
                }
            }
        });

        // Log stderr to electron-log as error
        backendProcess.stderr.on('data', (data) => {
            const msg = data.toString().trim();
            if (msg) {
                log.error(`[Backend Error]: ${msg}`);
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.webContents.send('backend-log', `ERROR: ${msg}`);
                }
            }
        });

        backendProcess.on('close', (code) => {
            log.info(`[Backend] Process exited with code ${code}`);
            backendProcess = null;
            
            // Optionally try to restart the backend if it crashed
            if (code !== 0 && mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('backend-log', `Backend process exited with code ${code}. Attempting to restart...`);
                setTimeout(async () => {
                    const running = await isBackendReady();
                    if (!running) {
                        startBackend(mainWindow);
                    } else {
                        log.info('[Electron] Backend is already responding on :8001. Not restarting.');
                    }
                }, 2000); // Retry after 2 seconds
            }
        });

        backendProcess.on('error', (err) => {
            log.error('[Backend] Failed to start backend process:', err);
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('backend-log', `CRITICAL ERROR: ${err.message}`);
                dialog.showErrorBox('Backend Critical Error', 
                    `Failed to start backend process: ${err.message}.\n\n` +
                    'Please check the logs in the application data directory.');
            }
            app.quit();
        });
    }, 1000); // 1 second delay
}

// ===================================================================
//  ZENTRALE FUNKTION ZUM BEENDEN DES BACKENDS (AGGRESSIVE VERSION)
// ===================================================================
function stopBackend() {
    const imageName = 'janus_backend.exe'; 
    
    console.log(`[Main Process] Executing AGGRESSIVE termination for: ${imageName}`);
    
    try {
        // SCHLAG 1: Der erste Versuch
        spawn('taskkill', ['/F', '/IM', imageName, '/T']);
        
        // SCHLAG 2: Sofort hinterher (für den Fall, dass einer entwischte)
        spawn('taskkill', ['/F', '/IM', imageName, '/T']);

        // SCHLAG 3: Ein kleiner Zeitversatz (Trick 17)
        // Wir nutzen hier exec statt spawn für den verzögerten Aufruf, 
        // um sicherzugehen, dass es auch feuert, wenn Node schon fast zu ist.
        const { exec } = require('child_process');
        // Warte 1s und töte nochmal alles was so heißt.
        // Das bricht den Zyklus, falls der Wrapper den Server gerade neu gestartet hat.
        exec(`timeout /t 1 & taskkill /F /IM ${imageName} /T`);

        backendProcess = null; 
        console.log('[Main Process] Termination sequence initiated.');
    } catch (e) {
        console.error(`[Main Process] Failed to execute termination sequence:`, e);
    }
}

function waitForBackend(retries = 10, delay = 2000) { // Längere Pausen!
    return new Promise((resolve, reject) => {
        console.log(`[Electron Main] Waiting for backend... (Max retries: ${retries})`);
        
        function check() {
            // Wir nutzen axios für den Check
            axios.get('http://127.0.0.1:8001/api/health', { timeout: 1000 })
                .then(() => {
                    console.log('[Electron Main] Backend is ready and responding!');
                    resolve(true);
                })
                .catch((error) => {
                    console.log(`[Electron Main] Backend not ready yet. Retries left: ${retries}`);
                    if (retries === 0) {
                        console.error('[Electron Main] Backend timed out.');
                        // Wir geben trotzdem resolve() zurück, damit das Fenster aufgeht 
                        // und der User wenigstens eine Fehlermeldung sieht, statt gar nichts.
                        resolve(false); 
                    } else {
                        retries--;
                        setTimeout(check, delay);
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

  // Safe window access pattern
  const { BrowserWindow } = require('electron');
  const allWindows = BrowserWindow.getAllWindows();
  const targetWindow = (allWindows.length > 0) ? allWindows[0] : null;
  
  if (!targetWindow || targetWindow.isDestroyed()) {
    return { success: false, error: 'Window not available' };
  }

  const { filePath } = await dialog.showSaveDialog(targetWindow, {
    title: 'Bild speichern unter...',
    defaultPath: path.join(app.getPath('downloads'), 'janus-image.png'),
    filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }]
  });

  if (filePath) {
    try {
      const response = await axios({ url, responseType: 'arraybuffer' });
      fs.writeFileSync(filePath, Buffer.from(response.data));
      
      // Safe window check before sending success message
      if (targetWindow && !targetWindow.isDestroyed() && targetWindow.webContents) {
        targetWindow.webContents.send('save-image-success', { success: true, path: filePath });
      }
      return { success: true, path: filePath };
    } catch (error) {
      console.error('Failed to save image:', error);
      // Safe window check before sending error message
      if (targetWindow && !targetWindow.isDestroyed() && targetWindow.webContents) {
        targetWindow.webContents.send('save-image-error', { success: false, error: error.message });
      }
      return { success: false, error: error.message };
    }
  }
  return { success: false, error: 'Save dialog cancelled.' };
});
// --- ENDE HANDLER ---

// --- HANDLER FÜR SPEICHERN-UNTER-DIALOG ---
ipcMain.handle('save-image-dialog', async (event, { imageUrl, defaultFilename }) => {
  // 1. Den nativen "Speichern unter"-Dialog öffnen
  const { canceled, filePath } = await dialog.showSaveDialog({
    title: 'Bild speichern unter...',
    defaultPath: path.join(app.getPath('pictures'), defaultFilename || 'image.png'),
    buttonLabel: 'Speichern',
    filters: [
      { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'tiff'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });

  // Wenn der Benutzer den Dialog abgebrochen hat
  if (canceled || !filePath) {
    return { success: false, message: 'Speichern abgebrochen.' };
  }

  // 2. Das Bild von der URL herunterladen
  try {
    const fileStream = fs.createWriteStream(filePath);
    const protocol = imageUrl.startsWith('https') ? require('https') : require('http');

    await new Promise((resolve, reject) => {
      protocol.get(imageUrl, (response) => {
        if (response.statusCode !== 200) {
          reject(new Error(`Server-Antwort: ${response.statusCode}`));
          return;
        }
        response.pipe(fileStream);
        fileStream.on('finish', () => {
          fileStream.close(resolve);
        });
      }).on('error', (err) => {
        fs.unlink(filePath, () => {}); // Lösche die (leere) Datei bei einem Fehler
        reject(err);
      });
    });

    return { success: true, path: filePath };
  } catch (error) {
    console.error('Fehler beim Herunterladen oder Speichern des Bildes:', error);
    return { success: false, message: error.message };
  }
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

// --- NEUER HANDLER FÜR API KEY ---
ipcMain.handle('get-api-key', async () => {
    try {
        // Diese Logik spiegelt exakt das Verhalten von 'get_app_data_dir()' aus dem Python-Backend wider.
        const appDataRoot = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Preferences' : process.env.HOME + "/.config");
        const configDir = path.join(appDataRoot, 'Janus Projekt'); // Wichtig: mit Leerzeichen!
        const configPath = path.join(configDir, 'config.json');
        
        if (!fs.existsSync(configPath)) {
            console.error(`[Electron Main] API key config not found at correct path: ${configPath}`);
            return null;
        }
        
        const configFile = await fs.promises.readFile(configPath, 'utf8');
        const config = JSON.parse(configFile);
        
        if (config && config.api_key) {
            console.log("[Electron Main] Successfully read API key from config.");
            return config.api_key;
        } else {
            console.error(`[Electron Main] 'api_key' not found in config file at: ${configPath}`);
            return null;
        }
    } catch (error) {
        console.error('[Electron Main] Failed to read or parse API key config:', error);
        return null;
    }
});
// --- ENDE API KEY HANDLER ---

console.log('Main process: ipcMain.handle registered for save-image');

let splashWindow = null;
let mainWindow = null;

function createSplashWindow() {
  console.log('Creating splash window...');
  try {
    // First try to load the splash screen with transparency
    splashWindow = new BrowserWindow({
      width: 400,
      height: 300,
      transparent: true,  // Try with transparency first
      frame: false,
      alwaysOnTop: true,
      center: true,
      resizable: false,
      show: false,  // Don't show until we've loaded the content
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        backgroundThrottling: false
      }
    });
    
    // Log the splash.html path for debugging
    const splashPath = path.join(__dirname, 'splash.html');
    console.log(`Loading splash screen from: ${splashPath}`);
    
    // Load the splash screen
    splashWindow.loadFile(splashPath)
      .then(() => {
        console.log('Splash screen loaded successfully');
        splashWindow.show();
      })
      .catch(err => {
        console.error('Failed to load splash screen:', err);
        // Fallback to non-transparent window if loading fails
        if (splashWindow) splashWindow.close();
        
        splashWindow = new BrowserWindow({
          width: 400,
          height: 300,
          transparent: false,  // Fallback to non-transparent
          frame: false,
          alwaysOnTop: true,
          center: true,
          resizable: false,
          webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
          }
        });
        splashWindow.loadFile(splashPath);
      });
      
    splashWindow.on('closed', () => { 
      console.log('Splash window closed');
      splashWindow = null; 
    });
    
    return splashWindow;
  } catch (error) {
    console.error('Error creating splash window:', error);
    return null;
  }
}

function createWindow() {
  console.log('Main process: createWindow called');
  const preloadPath = path.join(__dirname, 'frontend/preload.js');
  console.log(`[Main Process] Attempting to load preload script from: ${preloadPath}`);

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    show: false, // Initially hidden
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      sandbox: true,
      // ============================================================
      // YOUTUBE ORIGIN FIX: Allow running insecure content for YouTube embedding
      // ============================================================
      allowRunningInsecureContent: true
    },
    // ============================================================
    // YOUTUBE ORIGIN FIX: Disable PreloadMediaEngagementData to prevent YouTube blocking
    // ============================================================
    additionalArguments: ["--disable-features=PreloadMediaEngagementData"],
    // ============================================================
    // YOUTUBE ORIGIN FIX: Mask Janus as real Chrome browser
    // ============================================================
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
  });

  // ============================================================
  // YOUTUBE ORIGIN FIX: Referer/Origin Spoofing + Header-Stripping
  // ============================================================
  // --- Request-Header: User-Agent hardening for YouTube ---
  mainWindow.webContents.session.webRequest.onBeforeSendHeaders(
    { urls: ['*://*.youtube.com/*'] },
    (details, callback) => {
      // Force User-Agent to match Chrome 124 (same as window userAgent and app.userAgentFallback)
      details.requestHeaders['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
      callback({ cancel: false, requestHeaders: details.requestHeaders });
    }
  );

  // --- Response-Header: X-Frame-Options & CSP strippen ---
  mainWindow.webContents.session.webRequest.onHeadersReceived(
    { urls: ['*://*.youtube.com/*', '*://*.youtube-nocookie.com/*', '*://*.googlevideo.com/*'] },
    (details, callback) => {
      const responseHeaders = details.responseHeaders || {};
      // Delete X-Frame-Options and CSP headers for ALL Google/YouTube domains
      delete responseHeaders['x-frame-options'];
      delete responseHeaders['X-Frame-Options'];
      delete responseHeaders['content-security-policy'];
      delete responseHeaders['Content-Security-Policy'];
      callback({ cancel: false, responseHeaders });
    }
  );

  // ============================================================
  // PERMISSION HANDLERS: Allow clipboard, fullscreen, and ALL YouTube permissions
  // ============================================================
  const allowedPermissions = ['clipboard-read', 'clipboard-sanitized-write', 'fullscreen', 'media', 'display-capture', 'background-sync'];

  mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
    console.log('[PERMISSION CHECK]', permission, details?.requestingUrl || requestingOrigin);
    // Allow all permissions from YouTube origins via details.requestingUrl (safer wildcard)
    if (details && details.requestingUrl && (details.requestingUrl.includes('youtube.com') || details.requestingUrl.includes('youtube-nocookie.com'))) {
      console.log('[PERMISSION CHECK] ALLOWED: YouTube origin');
      return true;
    }
    // Allow all permissions from file:// origin (renderer runs locally)
    if (requestingOrigin && requestingOrigin.startsWith('file://')) {
      console.log('[PERMISSION CHECK] ALLOWED: file:// origin');
      return true;
    }
    // Allow clipboard, fullscreen, and background-sync permissions for app context
    if (allowedPermissions.includes(permission)) {
      console.log('[PERMISSION CHECK] ALLOWED: allowedPermissions list');
      return true;
    }
    console.log('[PERMISSION CHECK] DENIED');
    return false;
  });

  mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback, details) => {
    console.log('[PERMISSION REQUEST]', permission, details?.requestingUrl || webContents.getURL());
    // Allow all permissions from YouTube origins via details.requestingUrl (safer wildcard)
    if (details && details.requestingUrl && (details.requestingUrl.includes('youtube.com') || details.requestingUrl.includes('youtube-nocookie.com') || details.requestingUrl.includes('googlevideo.com'))) {
      console.log('[PERMISSION REQUEST] ALLOWED: YouTube/GoogleVideo origin');
      callback(true);
      return;
    }
    // Allow all permissions from file:// origin (renderer runs locally)
    const requestingOrigin = webContents.getURL();
    if (requestingOrigin && requestingOrigin.startsWith('file://')) {
      console.log('[PERMISSION REQUEST] ALLOWED: file:// origin');
      callback(true);
      return;
    }
    // Allow clipboard and fullscreen permissions for app context
    if (allowedPermissions.includes(permission)) {
      console.log('[PERMISSION REQUEST] ALLOWED: allowedPermissions list');
      callback(true);
      return;
    }
    console.log('[PERMISSION REQUEST] DENIED');
    callback(false);
  });

  // Function to load the main app content
  const loadApp = () => {
    return new Promise((resolve, reject) => {
      const loadPromise = app.isPackaged
        ? mainWindow.loadFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
        : (() => {
            mainWindow.webContents.openDevTools();
            return mainWindow.loadURL('http://localhost:5173/');
          })();
      
      loadPromise.then(resolve).catch(reject);
    });
  };

  // Check if backend is ready by verifying the /api/health endpoint
  const checkBackendReady = () => {
    return new Promise((resolve) => {
      // Use http.get since axios would be overkill here
      const req = http.get('http://127.0.0.1:8001/api/health', (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          try {
            const json = JSON.parse(data);
            // NOW WE CHECK THE RESPONSE CONTENT!
            if (res.statusCode === 200 && json.status === 'ready') {
              resolve(true); // Backend is really ready!
            } else {
              resolve(false); // Backend is started but not ready (e.g., 503)
            }
          } catch (e) {
            resolve(false); // Error parsing response, so not ready yet
          }
        });
      });

      // If connection completely fails (CONNECTION_REFUSED)
      req.on('error', () => {
        resolve(false);
      });

      req.end();
    });
  };

  // Start the backend and wait for it to be ready
  const startApp = async () => {
    try {
      if (app.isPackaged) {
        await startBackend();
      }
      
      // Wait for backend to be ready
      let attempts = 0;
      const maxAttempts = 120; // 120 seconds (2 minutes) max
      
      while (attempts < maxAttempts) {
        const isReady = await checkBackendReady();
        if (isReady) {
          console.log('[Electron Main] Backend ready, loading app...');
          await loadApp();
          mainWindow.show();
          if (splashWindow) {
            splashWindow.close();
            splashWindow = null;
          }
          return;
        }
        
        // Update splash screen status with more informative message
        if (splashWindow) {
          // Better user message
          const status = (attempts < 15) 
            ? `Starte Dienste... (${attempts + 1})` 
            : `Lade Modelle (kann dauern)... (${attempts + 1})`;
            
          splashWindow.webContents.executeJavaScript(`
            document.querySelector('.status').textContent = '${status}';
          `);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
      }
      
      throw new Error('Backend did not start in time');
    } catch (err) {
      console.error('Failed to start app:', err);
      if (splashWindow) {
        splashWindow.close();
      }
      dialog.showErrorBox('Startup Error', 'Failed to start application. Please check logs.');
      app.quit();
    }
  };

  // Start the app initialization
  startApp();

  mainWindow.webContents.on('context-menu', (event, params) => {
    const menu = new Menu();
    menu.append(new MenuItem({ label: 'Kopieren', role: 'copy' }));
    menu.popup({ window: mainWindow });
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url !== mainWindow.webContents.getURL() && (url.startsWith('http:') || url.startsWith('https:'))) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });
 
  return mainWindow;
}

// ===================================================================
//  EVENT-HANDLER FÜR DAS SCHLIESSEN DER ANWENDUNG
// ===================================================================

// Wird aufgerufen, wenn alle Fenster geschlossen sind (Haupt-Trigger)
app.on('window-all-closed', () => {
  console.log('[Main Process] All windows closed. Initiating shutdown.');
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Wird aufgerufen, kurz bevor die App sich endgültig beendet (Sicherheitsnetz)
app.on('before-quit', () => {
  console.log('[Main Process] Before-quit event triggered. Ensuring backend is terminated.');
  stopBackend();
});

// Fängt Strg+C im Terminal ab (nützlich für die Entwicklung)
process.on('SIGINT', () => {
  console.log('[Main Process] SIGINT signal received. Shutting down.');
  stopBackend();
  process.exit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    const win = createWindow();
    if (app.isPackaged) {
      startBackend(win);
    }
  }
});

// --- AUTO UPDATER LOGIK (Robust & Geloggt) ---
const log = require('electron-log');

// Log-Level setzen
autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';

function initAutoUpdater(window) {
    log.info('[AutoUpdater] initAutoUpdater called. app.isPackaged:', app.isPackaged);
    if (!app.isPackaged) {
        log.info('[AutoUpdater] Skipping update check (Development Mode)');
        return;
    }

    log.info('[AutoUpdater] Initializing...');

    // Einstellungen für den Workflow wie im Screenshot
    autoUpdater.autoDownload = true; // Lädt sofort, damit der Balken sich bewegt
    autoUpdater.autoInstallOnAppQuit = false; // WICHTIG: Damit wir den "Neu starten"-Button nutzen können
    autoUpdater.requestHeaders = { 'User-Agent': 'Janus-Project' }; // GitHub API要求
    autoUpdater.fullChangelog = true; // Vollständige Changelog-Informationen

    // Events an das Frontend senden
    autoUpdater.on('checking-for-update', () => {
        log.info('[AutoUpdater] Checking for update...');
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('update-status', 'Prüfe auf Updates...');
        }
    });

    autoUpdater.on('update-available', (info) => {
        log.info(`[AutoUpdater] Update available: ${info.version}`);
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('update-status', `Update gefunden: ${info.version}`);
            splashWindow.webContents.send('update-progress', 'Lade Update herunter...');
        }
        if (window && !window.isDestroyed()) {
            // Sendet das Event, das dein React-Modal öffnet
            window.webContents.send('update-available', {
                version: info.version,
                releaseNotes: info.releaseNotes || 'Siehe GitHub für Details.'
            });
        }
    });

    autoUpdater.on('download-progress', (progressObj) => {
        // Sendet den Fortschritt an deinen Balken im Screenshot
        if (window && !window.isDestroyed()) {
            window.webContents.send('download-progress', progressObj);
        }
        if (splashWindow && !splashWindow.isDestroyed()) {
            const percent = Math.round(progressObj.percent);
            splashWindow.webContents.send('update-progress', `Lade Update... ${percent}%`);
        }
    });

    autoUpdater.on('update-downloaded', (info) => {
        log.info('[AutoUpdater] Update downloaded.');
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('update-complete');
        }
        if (window && !window.isDestroyed()) {
            window.webContents.send('update-downloaded');
        }
    });
    
    autoUpdater.on('error', (err) => {
        log.error('[AutoUpdater] Error:', err);
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('update-status', 'Update-Check fehlgeschlagen, starte App...');
        }
    });

    // SOFORTIGER CHECK OHNE NOTIFICATION (Das UI macht die Anzeige)
    // Timeout nach 10 Sekunden, falls GitHub API nicht antwortet
    const updateCheckTimeout = setTimeout(() => {
        log.warn('[AutoUpdater] Update check timeout - starting app anyway');
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('update-status', 'Update-Check timeout, starte App...');
        }
    }, 10000);

    autoUpdater.checkForUpdates().then(() => {
        clearTimeout(updateCheckTimeout);
    }).catch((err) => {
        clearTimeout(updateCheckTimeout);
        log.error('[AutoUpdater] Check failed:', err);
    });
}

// ===================================================================
//  FOLDER SELECTION HANDLER
// ===================================================================
ipcMain.handle('show-folder-dialog', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    title: 'Zielordner für Export auswählen',
    properties: ['openDirectory']
  });
  if (canceled || !filePaths || filePaths.length === 0) {
    return { success: false };
  }
  return { success: true, path: filePaths[0] };
});

// ===================================================================
//  FILE SAVE HANDLER (HARDENED)
// ===================================================================
ipcMain.handle('save-file-in-path', async (event, { fullPath, data }) => {
  try {
    // Normalize and resolve the path to prevent directory traversal
    const normalizedPath = path.normalize(fullPath);
    const resolvedPath = path.resolve(normalizedPath);

    // Define allowed root directories
    // NOTE: userData is NOT included to prevent overwriting config.json (contains JWT secret)
    const allowedRoots = [
      app.getPath('documents'),
      app.getPath('desktop'),
      app.getPath('pictures'),
      app.getPath('downloads'),
      app.getPath('temp')
    ].map(p => path.resolve(p));

    // Check if the resolved path is within any allowed root
    const isAllowed = allowedRoots.some(root => 
      resolvedPath.startsWith(root + path.sep) || resolvedPath === root
    );

    if (!isAllowed) {
      console.warn(`[SECURITY] save-file-in-path blocked: path outside allowed directories: ${resolvedPath}`);
      // Force native dialog for non-standard directories
      const { canceled, filePath } = await dialog.showSaveDialog({
        title: 'Speichern unter...',
        defaultPath: path.basename(fullPath)
      });
      if (canceled || !filePath) {
        return { success: false, message: 'Speichern abgebrochen (Pfad nicht erlaubt)' };
      }
      // Re-validate the user-selected path
      const newResolvedPath = path.resolve(filePath);
      const isNewAllowed = allowedRoots.some(root => 
        newResolvedPath.startsWith(root + path.sep) || newResolvedPath === root
      );
      if (!isNewAllowed) {
        return { success: false, message: 'Pfad nicht erlaubt (außerhalb von Benutzerordnern)' };
      }
      // Write to the user-selected path
      await fs.promises.writeFile(newResolvedPath, Buffer.from(data));
      return { success: true, path: newResolvedPath };
    }

    // Block critical Windows paths
    const lowerPath = resolvedPath.toLowerCase();
    const blockedPaths = [
      path.join(process.env.WINDIR || 'C:\\Windows', 'System32').toLowerCase(),
      path.join(process.env.WINDIR || 'C:\\Windows', 'System').toLowerCase(),
      path.join(process.env.WINDIR || 'C:\\Windows', 'SysWOW64').toLowerCase(),
      'C:\\Program Files',
      'C:\\Program Files (x86)',
      'C:\\ProgramData',
      'C:\\Windows'
    ];
    for (const blocked of blockedPaths) {
      if (lowerPath.startsWith(blocked.toLowerCase())) {
        console.error(`[SECURITY] save-file-in-path blocked: critical system path: ${resolvedPath}`);
        return { success: false, message: 'Zugriff auf Systempfade nicht erlaubt' };
      }
    }

    // Block hidden files (starting with .)
    const basename = path.basename(resolvedPath);
    if (basename.startsWith('.')) {
      console.warn(`[SECURITY] save-file-in-path blocked: hidden file: ${resolvedPath}`);
      return { success: false, message: 'Versteckte Dateien nicht erlaubt' };
    }

    // Block sensitive file extensions (config, databases, keys)
    const blockedExtensions = ['.json', '.db', '.key', '.pem', '.db-journal', '.db-shm', '.db-wal'];
    const ext = path.extname(basename).toLowerCase();
    if (blockedExtensions.includes(ext)) {
      console.warn(`[SECURITY] save-file-in-path blocked: sensitive extension ${ext}: ${resolvedPath}`);
      return { success: false, message: 'Dateien dieses Typs sind nicht erlaubt' };
    }

    // Write to the validated path
    await fs.promises.writeFile(resolvedPath, Buffer.from(data));
    return { success: true, path: resolvedPath };
  } catch (error) {
    console.error(`Fehler beim Schreiben von ${fullPath}:`, error);
    return { success: false, error: error.message };
  }
});

// ===================================================================
//  SINGLE FILE SAVE HANDLER
// ===================================================================
ipcMain.handle('save-single-file-dialog', async (event, { defaultPath, data }) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    title: 'Bild speichern unter...',
    defaultPath: defaultPath
  });

  if (canceled || !filePath) {
    return { success: false, message: 'Speichern abgebrochen' };
  }

  try {
    await fs.promises.writeFile(filePath, Buffer.from(data));
    return { success: true, path: filePath };
  } catch (error) {
    console.error(`Fehler beim Schreiben der Datei ${filePath}:`, error);
    return { success: false, error: error.message };
  }
});

// ===================================================================
//  CLIPBOARD READ HANDLER (FALLBACK FOR PERMISSION DENIED)
// ===================================================================
const { clipboard } = require('electron');
ipcMain.handle('read-clipboard', () => {
  try {
    return clipboard.readText();
  } catch (error) {
    console.error('[IPC] Failed to read clipboard:', error);
    return '';
  }
});
ipcMain.handle('clipboard:read', () => {
  try {
    return clipboard.readText();
  } catch (error) {
    console.error('[IPC] Failed to read clipboard (clipboard:read):', error);
    return '';
  }
});

// ===================================================================
//  APP INITIALIZATION
// ===================================================================
app.whenReady().then(async () => {
    // 💎 YOUTUBE FIX: Disable site isolation to allow YouTube embedding
    app.commandLine.appendSwitch('disable-features', 'IsolateOrigins,site-per-process');

    // 1. Splash zeigen
    createSplashWindow();

    // 2. Hauptfenster erstellen
    const win = createWindow();

    // 3. WICHTIG: Update SOFORT prüfen (vor Backend-Start)
    // Dadurch kann sich die App auch bei kritischen Fehlern selbst updaten
    setTimeout(() => {
        initAutoUpdater(win);
    }, 1000);

    // 4. Globaler Listener für den Neustart-Button im Frontend
    ipcMain.on('restart-app-for-update', () => {
        log.info('[AutoUpdater] Restarting app to install update...');
        autoUpdater.quitAndInstall();
    });
});

app.on('will-quit', stopBackend);
