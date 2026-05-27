console.log('Main process: Script started (Root main.electron.js)'); // Unique identifier

const { app, BrowserWindow, ipcMain, dialog, Menu, MenuItem, net, session, shell, protocol } = require('electron');

// ============================================================
// YOUTUBE ORIGIN FIX: Disable site-per-process isolation to prevent iframe blocking
// disable-site-isolation-trials was removed in v0.4.16-beta.3 as it caused
// startup instability without measurable benefit for YouTube embedding.
// ============================================================
app.commandLine.appendSwitch('disable-features', 'IsolateOrigins,site-per-process');
const path = require('path');
const fs = require('fs');
const http = require('http'); // For health check
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');
const axios = require('axios');
const { initJanusUpdateManager } = require('./electron/update-manager.cjs');
const { readUpdateState, transitionUpdateState } = require('./electron/update-state.cjs');

const DOCS_LOG_DIR = path.join(__dirname, 'documentation', 'logs');
const FRONTEND_LOG_FILE = path.join(DOCS_LOG_DIR, 'janus_frontend.log');

function ensureFrontendLogDir() {
  try {
    fs.mkdirSync(DOCS_LOG_DIR, { recursive: true });
  } catch (error) {
    console.error('[FrontendLog] Failed to create documentation/logs directory:', error);
  }
}

function appendFrontendRendererLog(level, message, sourceId, line) {
  try {
    ensureFrontendLogDir();
    const ts = new Date().toISOString().replace('T', ' ').replace('Z', '');
    const lvl = String(level || 'INFO').toUpperCase();
    const src = String(sourceId || 'renderer');
    const ln = Number.isFinite(Number(line)) ? Number(line) : -1;
    const msg = String(message ?? '');
    const rendered = `${ts} - janus_frontend - [${lvl}] - ${src}:${ln} - ${msg}\n`;
    fs.appendFileSync(FRONTEND_LOG_FILE, rendered, 'utf8');
  } catch (error) {
    console.error('[FrontendLog] Failed to append renderer log line:', error);
  }
}

// ============================================================
// STARTUP TELEMETRY (Dev Context Only)
// ============================================================
const { getStartupTelemetryConfig, StartupTelemetryLogger } = require('./electron/startup-telemetry.cjs');
const telemetryConfig = getStartupTelemetryConfig();
const telemetryLogger = new StartupTelemetryLogger({
  enabled: telemetryConfig.enabled,
  logFilePath: telemetryConfig.log_file_path,
  maxFileSizeBytes: telemetryConfig.max_file_size_bytes,
  maxBackupFiles: telemetryConfig.max_backup_files
});

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
// Moved to app.ready to prevent startup crash in some Electron versions

// ============================================================
// DIAMANT-STANDARD UPDATE KONFIGURATION
// ============================================================

autoUpdater.allowPrerelease = true; 
autoUpdater.channel = 'beta';
autoUpdater.allowDowngrade = false;
autoUpdater.disableDifferentialDownload = true;
autoUpdater.disableWebInstaller = true;

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
    icon: path.join(__dirname, 'frontend/assets/icon.png'),
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      sandbox: true,
      // ============================================================
      // YOUTUBE ORIGIN FIX (v0.4.16-beta.3): Dedicated persistent session partition.
      // Gives YouTube iframe a stable cookie jar for CONSENT cookies and
      // recommendation state, which reduces Error 150/153 occurrences.
      // ============================================================
      partition: "persist:janus",
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

  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    const levelMap = {
      0: 'INFO',
      1: 'WARN',
      2: 'ERROR',
      3: 'DEBUG',
    };
    const lvl = levelMap[level] || 'INFO';
    appendFrontendRendererLog(lvl, message, sourceId, line);
  });

  // ============================================================
  // YOUTUBE ORIGIN FIX (reverted to beta.3 state): UA-only, diagnostic logging.
  // We log the ORIGINAL Referer/Origin/Sec-Fetch values so we can see what
  // Electron actually sends before any spoofing. This is diagnostic-first —
  // we will decide the actual header strategy based on what the logs show.
  // ============================================================
  const CHROME_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
  let _ytRequestLogCount = 0;
  mainWindow.webContents.session.webRequest.onBeforeSendHeaders(
    { urls: ['*://*.youtube.com/*', '*://*.youtube-nocookie.com/*', '*://*.googlevideo.com/*'] },
    (details, callback) => {
      if (_ytRequestLogCount < 30) {
        _ytRequestLogCount++;
        const ref = details.requestHeaders['Referer'] || details.requestHeaders['referer'] || '(none)';
        const org = details.requestHeaders['Origin'] || details.requestHeaders['origin'] || '(none)';
        const sfs = details.requestHeaders['Sec-Fetch-Site'] || '(none)';
        const sfm = details.requestHeaders['Sec-Fetch-Mode'] || '(none)';
        console.log(`[YT-REQ ${_ytRequestLogCount}] ${details.method} ${details.url.substring(0, 100)} | ref=${ref.substring(0, 50)} origin=${org} sfs=${sfs} sfm=${sfm}`);
      }
      // Only normalize User-Agent (avoid "Electron/x.x.x" substring block).
      // Do NOT touch Referer/Origin/Sec-Fetch-* — we log them instead to diagnose.
      details.requestHeaders['User-Agent'] = CHROME_UA;
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
    // Allow all permissions from local renderer origins
    // (file://, janus:// legacy, http://127.0.0.1:8001 and http://localhost:* for Vite dev)
    if (requestingOrigin && (
      requestingOrigin.startsWith('file://') ||
      requestingOrigin.startsWith('janus://') ||
      requestingOrigin.startsWith('http://127.0.0.1:8001') ||
      requestingOrigin.startsWith('http://localhost:')
    )) {
      console.log('[PERMISSION CHECK] ALLOWED: local origin', requestingOrigin);
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
    // Allow all permissions from local renderer origins
    // (file://, janus:// legacy, http://127.0.0.1:8001 and http://localhost:* for Vite dev)
    const requestingOrigin = (details && details.requestingUrl) || webContents.getURL();
    if (requestingOrigin && (
      requestingOrigin.startsWith('file://') ||
      requestingOrigin.startsWith('janus://') ||
      requestingOrigin.startsWith('http://127.0.0.1:8001') ||
      requestingOrigin.startsWith('http://localhost:')
    )) {
      console.log('[PERMISSION REQUEST] ALLOWED: local origin', requestingOrigin);
      callback(true);
      return;
    }
    // For openExternal with no origin yet (initial navigation to janus://), allow as well
    if (permission === 'openExternal' && (!requestingOrigin || requestingOrigin === '' || requestingOrigin.startsWith('janus:') || requestingOrigin === 'about:blank')) {
      console.log('[PERMISSION REQUEST] ALLOWED: openExternal during janus:// navigation');
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
      // v0.4.16-beta.9: Load packaged app from http://127.0.0.1:8001/ instead
      // of a custom scheme. Required by YouTube's embed player (Error 153 was
      // caused by the non-http `janus://` origin). The backend's FastAPI app
      // already mounts frontend/dist at `/`, so it serves the UI over HTTP.
      // Dev mode keeps Vite's hot-reload server at http://localhost:5173/.
      const loadPromise = app.isPackaged
        ? (() => {
            if (process.env.NODE_ENV === 'development') {
                mainWindow.webContents.openDevTools({ mode: 'detach' });
            }
            console.log('[LOAD] Using HTTP origin: http://127.0.0.1:8001/');
            return mainWindow.loadURL('http://127.0.0.1:8001/');
          })()
        : (() => {
            if (process.env.NODE_ENV === 'development') {
                mainWindow.webContents.openDevTools();
            }
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
      // STARTUP TELEMETRY: Backend start phase (measure before startRun)
      const backendStart = Date.now();
      let backendStartDuration = 0;
      if (app.isPackaged) {
        await startBackend();
        backendStartDuration = Date.now() - backendStart;
      } else {
        // In dev mode, backend might already be running or started separately
        backendStartDuration = 0;
      }

      // Wait for backend to be ready
      let attempts = 0;
      const maxAttempts = 120; // 120 seconds (2 minutes) max
      let telemetryStarted = false;

      while (attempts < maxAttempts) {
        const isReady = await checkBackendReady();
        if (isReady) {
          console.log('[Electron Main] Backend ready, loading app...');

          // STARTUP TELEMETRY: Start run on first successful backend health check
          if (!telemetryStarted) {
            telemetryLogger.startRun();
            telemetryStarted = true;

            // Log backend_start phase after startRun
            if (app.isPackaged) {
              telemetryLogger.logPhase('backend_start', backendStartDuration);
            } else {
              telemetryLogger.logPhase('backend_start', 0, { note: 'Dev mode - backend not started by Electron' });
            }
          }

          // STARTUP TELEMETRY: Frontend load phase
          const frontendStart = Date.now();
          await loadApp();
          telemetryLogger.logPhase('frontend_load', Date.now() - frontendStart);

          // STARTUP TELEMETRY: App ready phase (window shown, Janus is usable)
          const appReadyStart = Date.now();
          mainWindow.show();
          if (splashWindow) {
            splashWindow.close();
            splashWindow = null;
          }
          telemetryLogger.logPhase('app_ready', Date.now() - appReadyStart);

          // STARTUP TELEMETRY: End run when Janus is actually usable
          telemetryLogger.endRun(success=true);

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
      
      // STARTUP TELEMETRY: Log startup failure
      telemetryLogger.endRun(success=false, errorMessage=err.message);
      
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

ipcMain.handle('debug:write-frontend-log', async (event, payload = {}) => {
  try {
    const content = typeof payload.content === 'string' ? payload.content : '';
    if (!content.trim()) {
      return { success: false, error: 'Frontend debug log content is empty' };
    }

    const isDev = process.env.NODE_ENV === 'development';
    const debugDir = isDev
      ? path.join(process.cwd(), 'debug_logs')
      : path.join(app.getPath('userData'), 'debug_logs');
    await fs.promises.mkdir(debugDir, { recursive: true });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filePath = path.join(debugDir, `frontend_log_${timestamp}.md`);
    await fs.promises.writeFile(filePath, content, 'utf8');

    log.info(`[DebugLog] Frontend debug log exported: ${filePath}`);
    return { success: true, path: filePath };
  } catch (error) {
    log.error('[DebugLog] Failed to export frontend debug log:', error);
    return { success: false, error: error.message };
  }
});

// ===================================================================
//  APP INITIALIZATION
// ===================================================================
app.whenReady().then(async () => {
    // STARTUP TELEMETRY: Start run will be triggered on first successful backend health check
    // (not here, to ensure we capture time from "backend ready" to "Janus usable")

    // YOUTUBE ORIGIN FIX: Mask Janus as real Chrome browser globally (set here to avoid startup race conditions).
    // Note: command-line switches like disable-features are set at the top of the script (before app init).
    app.userAgentFallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

    // ============================================================
    // YOUTUBE ORIGIN FIX (v0.4.16-beta.5): Register janus:// protocol handler.
    // Root cause of Error 153: Production used loadFile() → file:// origin →
    // YouTube embed endpoint refuses any non-http(s) referrer.
    // Fix: Serve frontend/dist via custom 'janus' scheme (registered as
    // privileged+secure+standard at top of script). Origin becomes janus://app,
    // which YouTube treats as a standard web origin.
    // ============================================================
    const { protocol: electronProtocol, session: electronSession } = require('electron');
    const distRoot = path.join(__dirname, 'frontend', 'dist');
    const MIME_TYPES = {
      '.html': 'text/html; charset=utf-8',
      '.js':   'text/javascript; charset=utf-8',
      '.mjs':  'text/javascript; charset=utf-8',
      '.css':  'text/css; charset=utf-8',
      '.json': 'application/json; charset=utf-8',
      '.map':  'application/json; charset=utf-8',
      '.png':  'image/png',
      '.jpg':  'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif':  'image/gif',
      '.svg':  'image/svg+xml',
      '.webp': 'image/webp',
      '.ico':  'image/x-icon',
      '.woff':  'font/woff',
      '.woff2': 'font/woff2',
      '.ttf':   'font/ttf',
      '.otf':   'font/otf',
      '.mp3':  'audio/mpeg',
      '.wav':  'audio/wav',
      '.mp4':  'video/mp4',
      '.txt':  'text/plain; charset=utf-8',
    };
    const janusHandler = async (request) => {
      try {
        const parsed = new URL(request.url);
        let relPath = decodeURIComponent(parsed.pathname).replace(/^\/+/, '');
        if (!relPath || relPath.endsWith('/')) relPath += 'index.html';
        const absPath = path.normalize(path.join(distRoot, relPath));
        if (!absPath.startsWith(distRoot)) {
          console.warn(`[JANUS-PROTO] Blocked path traversal: ${request.url}`);
          return new Response('Forbidden', { status: 403 });
        }
        let data;
        try {
          data = await fs.promises.readFile(absPath);
        } catch (readErr) {
          console.warn(`[JANUS-PROTO] File not found: ${absPath} (url=${request.url})`);
          return new Response('Not Found', { status: 404 });
        }
        const ext = path.extname(absPath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        console.log(`[JANUS-PROTO] Served: ${relPath} (${data.length} bytes, ${contentType})`);
        return new Response(data, {
          status: 200,
          headers: { 'Content-Type': contentType, 'Cache-Control': 'no-cache' },
        });
      } catch (err) {
        console.error('[JANUS-PROTO] Handler error:', err && err.stack ? err.stack : err);
        return new Response('Internal Error', { status: 500 });
      }
    };

    // Register on default session (for safety / fallback)
    electronProtocol.handle('janus', janusHandler);
    // CRITICAL: Also register on the persist:janus partition session,
    // because our BrowserWindow uses `partition: "persist:janus"` which is
    // a separate session with its own protocol registry.
    const partitionSession = electronSession.fromPartition('persist:janus');
    partitionSession.protocol.handle('janus', janusHandler);
    console.log(`[JANUS-PROTO] Custom scheme registered on default + persist:janus sessions, serving from: ${distRoot}`);

    // NOTE: Previous beta.6 introduced a YouTube Referer/Origin rewriter via
    // webRequest.onBeforeSendHeaders. It was removed in beta.8 because:
    //  - It did not fix the reported Error 153 (reproducible in plain browser
    //    on the affected machine, not an Electron issue).
    //  - Manipulating Referer/Origin/Sec-Fetch headers can INCREASE YouTube's
    //    bot-detection score for normal users. Browser defaults are trusted
    //    signals; leaving them untouched is the safer baseline.

    // 1. Splash zeigen
    createSplashWindow();

    // 2. Hauptfenster erstellen
    const win = createWindow();

    // 3. WICHTIG: Update SOFORT prüfen (vor Backend-Start)
    // Dadurch kann sich die App auch bei kritischen Fehlern selbst updaten
    setTimeout(() => {
        initJanusUpdateManager({ app, autoUpdater, mainWindow: win, log });
    }, 1000);

    // NOTE: Telemetry starts on first successful backend health check in startApp()
    // Phases before that (splash, window, update) are not logged
});

// ===================================================================
//  UPDATE IPC HANDLERS
// ===================================================================

ipcMain.handle('update:get-state', () => {
    return readUpdateState(app);
});

ipcMain.on('update:install-now', () => {
    const state = readUpdateState(app);
    if (state.status === 'ready_to_install') {
        log.info('[UpdateIPC] Installing update...');
        autoUpdater.quitAndInstall();
    }
});

ipcMain.on('update:retry', () => {
    const state = readUpdateState(app);
    if (state.status === 'download_failed' || state.status === 'validation_failed' || state.status === 'install_failed') {
        log.info(`[UpdateIPC] Retrying update from state: ${state.status}`);
        const newState = transitionUpdateState(app, {
            status: 'checking',
            retryCount: 0,
            errorCode: null,
            errorMessage: null,
            downloadProgress: null,
        });
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('update-state-changed', newState);
        }
        autoUpdater.checkForUpdates();
    }
});

ipcMain.on('update:dismiss-normal', () => {
    const state = readUpdateState(app);
    if (state.status === 'ready_to_install' && state.isCritical === false) {
        log.info('[UpdateIPC] Dismissing normal update');
        transitionUpdateState(app, { status: 'idle', downloadProgress: null });
    }
});

app.on('will-quit', stopBackend);
