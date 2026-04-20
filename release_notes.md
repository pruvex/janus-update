# Janus Projekt 0.4.15-beta.11
**Released:** 2026-04-20 16:12

### Fixed
- Clipboard IPC Fallback: navigator.clipboard.readText() durch window.electronAPI.readClipboard() ersetzt (Permission Denied Fix). main.electron.cjs: ipcMain.handle('clipboard:read') und ipcMain.handle('read-clipboard') implementiert; preload.js: window.electronAPI exponiert.
- YouTube Error 152-4 Regression: Referer/Origin Spoofing aus onBeforeSendHeaders entfernt (YouTube blockiert als Bot bei Mismatch). onHeadersReceived für X-Frame-Options/CSP-Stripping intakt gelassen.
- Permission Handlers: setPermissionCheckHandler und setPermissionRequestHandler erweitert mit console.log Visibility, file:// Origin Bypass und allowedPermissions Array.
- frontend/js/video-player.js: YouTube Embed URL auf youtube-nocookie.com ohne enablejsapi und origin Parameter geändert.

### Changed
- Version bumped to 0.4.15-beta.11
## 📦 Installation
Download the installer from the GitHub releases page.

## 🐛 Known Issues
None reported for this release.
