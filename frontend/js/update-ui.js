// ============================================================
// STATE-DRIVEN UPDATE UI
// ============================================================

let updateToast = null;
let updateModal = null;
let updateErrorBanner = null;
/** @type {string | null} */
let sidebarVersionBase = null;

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** @param {{ status?: string, downloadProgress?: number | null }} state */
function renderSidebarUpdateFooter(state) {
  const el = document.getElementById('sidebar-version');
  if (!el || !sidebarVersionBase) return;

  const status = state?.status;
  const pct = state?.downloadProgress;

  if (status === 'downloading' && typeof pct === 'number' && Number.isFinite(pct)) {
    // 0%-rule: Only show percentage when progress > 0
    if (pct > 0) {
      el.innerHTML = `
        <span class="sidebar-footer-version">${escapeHtml(sidebarVersionBase)}</span>
        <span class="sidebar-footer-update-msg" aria-live="polite">Lade Update: ${pct}%</span>
      `;
    } else {
      el.innerHTML = `
        <span class="sidebar-footer-version">${escapeHtml(sidebarVersionBase)}</span>
        <span class="sidebar-footer-update-msg" aria-live="polite">Update lädt...</span>
      `;
    }
    return;
  }

  if (status === 'update_available') {
    el.innerHTML = `
      <span class="sidebar-footer-version">${escapeHtml(sidebarVersionBase)}</span>
      <span class="sidebar-footer-update-msg" aria-live="polite">Update lädt...</span>
    `;
    return;
  }

  if (status === 'validating') {
    el.innerHTML = `
      <span class="sidebar-footer-version">${escapeHtml(sidebarVersionBase)}</span>
      <span class="sidebar-footer-update-msg" aria-live="polite">Prüfe Datei...</span>
    `;
    return;
  }

  el.textContent = sidebarVersionBase;
}

/**
 * Basis-Version wie im Build (z. B. „v0.4.17-beta.10“). Wird beim App-Login gesetzt.
 * @param {string} label
 */
function setSidebarVersionBase(label) {
  sidebarVersionBase = label;
  if (!window.electron?.getUpdateState) {
    const el = document.getElementById('sidebar-version');
    if (el) el.textContent = label;
    return;
  }
  window.electron
    .getUpdateState()
    .then((state) => renderSidebarUpdateFooter(state))
    .catch(() => {
      const el = document.getElementById('sidebar-version');
      if (el) el.textContent = label;
    });
}

function renderUpdateUI(state) {
    renderSidebarUpdateFooter(state);
    // Remove all existing update UI elements
    removeUpdateUI();

    if (state.status === 'ready_to_install' && state.isCritical === false) {
        // Normal Update: Non-blocking toast/banner
        showNormalUpdateToast(state);
    } else if (state.status === 'ready_to_install' && state.isCritical === true) {
        // Critical Update: Blocking modal
        showCriticalUpdateModal(state);
    } else if (
        state.status === 'download_failed' ||
        state.status === 'validation_failed' ||
        state.status === 'install_failed'
    ) {
        // Error states: Persistent error banner with retry
        showErrorBanner(state);
    }
    // All other states: UI remains hidden (already removed)
}

function removeUpdateUI() {
    if (updateToast) {
        updateToast.remove();
        updateToast = null;
    }
    if (updateModal) {
        updateModal.remove();
        updateModal = null;
    }
    if (updateErrorBanner) {
        updateErrorBanner.remove();
        updateErrorBanner = null;
    }
}

function showNormalUpdateToast(state) {
    updateToast = document.createElement('div');
    updateToast.className = 'update-toast update-toast--normal';
    updateToast.innerHTML = `
        <div class="update-toast-content">
            <span class="update-toast-message">Update verfügbar: Version ${state.targetVersion || 'neue Version'}</span>
            <div class="update-toast-actions">
                <button class="update-toast-button update-toast-button--secondary" id="update-dismiss-btn">Später</button>
                <button class="update-toast-button update-toast-button--primary" id="update-install-btn">Installieren</button>
            </div>
        </div>
    `;
    document.body.appendChild(updateToast);

    document.getElementById('update-install-btn').addEventListener('click', () => {
        if (window.electron && typeof window.electron.installUpdateNow === 'function') {
            window.electron.installUpdateNow();
        }
    });

    document.getElementById('update-dismiss-btn').addEventListener('click', () => {
        if (window.electron && typeof window.electron.dismissNormalUpdate === 'function') {
            window.electron.dismissNormalUpdate();
        }
    });
}

function showCriticalUpdateModal(state) {
    updateModal = document.createElement('div');
    updateModal.className = 'update-modal update-modal--critical';
    updateModal.innerHTML = `
        <div class="update-modal-content">
            <div class="update-modal-header">
                <h2 class="update-modal-title">⚠️ Kritisches Update erforderlich</h2>
            </div>
            <div class="update-modal-body">
                <p class="update-modal-message">
                    Ein kritisches Update (${state.targetVersion || 'neue Version'}) muss installiert werden,
                    um die Sicherheit und Stabilität von Janus zu gewährleisten.
                </p>
                ${state.releaseNotes ? `
                    <div class="update-modal-notes">
                        <h3>Änderungen in dieser Version:</h3>
                        <div class="update-modal-notes-content">${state.releaseNotes}</div>
                    </div>
                ` : ''}
            </div>
            <div class="update-modal-footer">
                <button class="update-modal-button update-modal-button--primary" id="update-critical-install-btn">Installieren</button>
            </div>
        </div>
    `;
    document.body.appendChild(updateModal);

    document.getElementById('update-critical-install-btn').addEventListener('click', () => {
        if (window.electron && typeof window.electron.installUpdateNow === 'function') {
            window.electron.installUpdateNow();
        }
    });
}

function showErrorBanner(state) {
    const errorMessage = state.errorMessage || state.errorCode || 'Unbekannter Fehler';
    updateErrorBanner = document.createElement('div');
    updateErrorBanner.className = 'update-error-banner';
    updateErrorBanner.innerHTML = `
        <div class="update-error-banner-content">
            <span class="update-error-message">Update fehlgeschlagen: ${errorMessage}</span>
            <button class="update-error-retry-btn" id="update-retry-btn">Retry</button>
        </div>
    `;
    document.body.appendChild(updateErrorBanner);

    document.getElementById('update-retry-btn').addEventListener('click', () => {
        if (window.electron && typeof window.electron.retryUpdate === 'function') {
            window.electron.retryUpdate();
        }
    });
}

function initUpdateUI() {
    if (!window.electron) {
        console.warn('[UpdateUI] window.electron not available');
        return;
    }

    // Initial state fetch
    if (typeof window.electron.getUpdateState === 'function') {
        window.electron.getUpdateState().then((state) => {
            renderUpdateUI(state);
        }).catch((err) => {
            console.error('[UpdateUI] Failed to fetch initial state:', err);
        });
    }

    // Subscribe to state changes
    if (typeof window.electron.onUpdateStateChanged === 'function') {
        window.electron.onUpdateStateChanged((state) => {
            renderUpdateUI(state);
        });
    }
}

export { initUpdateUI, setSidebarVersionBase };
