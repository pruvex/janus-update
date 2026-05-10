const { app, BrowserWindow } = require('electron')
const path = require('path')

let mainWindow
let retryCount = 0
const MAX_RETRIES = 10
const RETRY_DELAY = 2000

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#09090b',
    show: false,
    titleBarStyle: 'hiddenInset',
    icon: path.join(__dirname, '../resources/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
      devTools: false,
    },
  })

  loadWithRetry()

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function loadWithRetry() {
  const url = 'http://127.0.0.1:5174'
  
  mainWindow.loadURL(url).catch((err) => {
    console.error(`Failed to load UI (attempt ${retryCount + 1}/${MAX_RETRIES}):`, err.message)
    
    if (retryCount < MAX_RETRIES) {
      retryCount++
      console.log(`Retrying in ${RETRY_DELAY / 1000} seconds...`)
      setTimeout(() => loadWithRetry(), RETRY_DELAY)
    } else {
      console.error('Max retries reached. Please ensure the UI dev server is running on http://127.0.0.1:5174')
      app.quit()
    }
  })
}

app.whenReady().then(() => {
  createWindow()
})

app.on('window-all-closed', () => {
  app.quit()
})
