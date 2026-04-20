/**
 * Ermittelt die Basis-URL für API-Calls.
 */
export function getBackendBaseUrl() {
    return (window.location.protocol === 'file:')
        ? 'http://localhost:8001'
        : (window.location.port === '5173')
          ? 'http://localhost:8001'
          : window.location.origin;
}

/**
 * Formatiert Bytes in lesbare Strings (KB/MB).
 */
export function formatFileSize(bytes) {
    if (bytes === -1) return 'Größe: Unbekannt';
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Extrahiert den Dateinamen (ohne Extension) aus einer URL.
 */
export function extractFilenameFromUrl(url) {
    try {
        const filenameWithExtension = new URL(url).pathname.split('/').pop();
        return filenameWithExtension.split('.').slice(0, -1).join('.');
    } catch (e) {
        console.warn("Konnte Dateinamen aus URL nicht extrahieren:", e);
        return "unbenannt";
    }
}
