// js/modules/image-studio/export.js

import { appState } from './state.js';
import { fetchEstimatedSize } from './api.js';
import { formatFileSize, getBackendBaseUrl } from './utils.js';

// --- Private Modul-Variablen ---
let jpegModal, jpegQualitySlider, jpegQualityValue, jpegSizeEstimate,
    jpegExportConfirm, jpegExportCancel, jpegPreviewImage, jpegPreviewLoader,
    exportCloseX, exportFormatSelect, exportDescription, jpegQualityControls,
    downloadIndicator;

let debounceTimer;

const formatDescriptions = {
    'jpg': `<strong>Der bewährte Allrounder.</strong><ul><li>Sehr gute Qualität bei minimaler Dateigröße.</li><li>Kompatibel mit absolut jedem Gerät und Programm.</li><li><strong>Optimal für:</strong> Webseiten, E-Mails, schnelles Teilen, Social Media.</li></ul>`,
    'png': `<strong>Das digitale Original.</strong><ul><li>Verlustfreie Speicherung: Jeder Pixel bleibt exakt erhalten.</li><li>Unterstützt transparente Hintergründe.</li><li><strong>Optimal für:</strong> Weiterverarbeitung, Grafiken, Screenshots, Archivierung.</li></ul>`,
    'webp': `<strong>Der moderne Standard.</strong><ul><li>Bietet oft bessere Qualität als JPG bei 20-30% kleinerer Dateigröße.</li><li>Unterstützt Transparenz und verlustfreie Kompression.</li><li><strong>Optimal für:</strong> Moderne Webseiten, Apps, Performance-Optimierung.</li></ul>`,
    'avif': `<strong>Die Technologie der Zukunft.</strong><ul><li>Extrem effiziente Kompression, schlägt selbst WebP.</li><li>Hervorragende Qualität auch bei winzigen Dateigrößen.</li><li><strong>Optimal für:</strong> Tech-Enthusiasten, maximale Speichereffizienz.</li></ul>`,
    'tiff_zip': `<strong>Der Profi-Standard.</strong><ul><li>Verlustfreie ZIP-Kompression spart Platz ohne Qualitätsverlust.</li><li>Behält alle Bildinformationen bei.</li><li><strong>Optimal für:</strong> Druckvorstufe, Layout, professionelle Bildbearbeitung.</li></ul>`,
    'tiff': `<strong>Das digitale Negativ.</strong><ul><li>Unkomprimierte Rohdaten für maximale Kompatibilität.</li><li>Keinerlei Rechenaufwand beim Öffnen/Speichern.</li><li><strong>Optimal für:</strong> Langzeitarchivierung, Legacy-Systeme, absolut kompromisslose Qualität.</li></ul>`,
    'pdf': `<strong>Das universelle Dokument.</strong><ul><li>Verpackt das Bild in ein standardisiertes Dokument.</li><li>Kann von jedem geöffnet werden, ohne Bildbetrachter.</li><li><strong>Optimal für:</strong> Kunden-Präsentationen, Rechnungsanhänge, Druckereien.</li></ul>`
};

// --- Private Modul-Funktionen ---

function showDownloadIndicator() {
    if (downloadIndicator) downloadIndicator.style.display = 'flex';
}

function hideDownloadIndicator() {
    if (downloadIndicator) downloadIndicator.style.display = 'none';
}

async function downloadImage(imageId, format) {
    if (!imageId) {
        alert("Fehler: Bild-ID nicht gefunden. Download nicht möglich.");
        return;
    }
    showDownloadIndicator();
    try {
        const downloadUrl = `${getBackendBaseUrl()}/api/images/${imageId}/download?format=${format}`;
        const token = localStorage.getItem('auth_token');
        if (!token) throw new Error("Authentifizierungs-Token nicht gefunden.");

        const response = await fetch(downloadUrl, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unbekannter Serverfehler' }));
            throw new Error(`Download fehlgeschlagen: ${response.status} - ${errorData.detail}`);
        }

        const contentDisposition = response.headers.get('content-disposition');
        let filename = `image_${imageId}.${format}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch && filenameMatch.length > 1) {
                filename = filenameMatch[1];
            }
        }
        
        const blob = await response.blob();
        if (window.electron && window.electron.saveSingleFileDialog) {
            const arrayBuffer = await blob.arrayBuffer();
            const result = await window.electron.saveSingleFileDialog({
                defaultPath: filename,
                data: arrayBuffer
            });
            if (!result.success) console.log('Speichern abgebrochen oder fehlgeschlagen:', result.message || 'Unbekannter Fehler');
        } else {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error("Fehler beim Herunterladen des Bildes:", error);
        alert(`Download fehlgeschlagen: ${error.message}`);
    } finally {
        hideDownloadIndicator();
    }
}


function closeExportModal() {
    if (jpegModal) jpegModal.style.display = 'none';
    appState.currentJpegExportImageId = null;
    appState.originalImageForJpegPreview = null;
    if(jpegPreviewImage) jpegPreviewImage.src = '';
    if(jpegPreviewImage) jpegPreviewImage.style.display = 'none';
    if (jpegModal) jpegModal.dataset.isBatch = 'false';
}

async function calculateSize() {
    // BUGFIX: Wenn kein Bild im State ist, sofort abbrechen
    if (!appState.originalImageForJpegPreview) return; 
    if (!jpegPreviewImage || !jpegPreviewImage.src) return; 

    jpegSizeEstimate.textContent = 'Berechne...';
    
    try {
        const canvas = document.createElement('canvas');
        canvas.width = appState.originalImageForJpegPreview.naturalWidth;
        canvas.height = appState.originalImageForJpegPreview.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(appState.originalImageForJpegPreview, 0, 0);
        
        const base64Image = canvas.toDataURL('image/png');
        const selectedFormat = exportFormatSelect.value;
        let formatParam = selectedFormat;
        if (selectedFormat === 'jpg') {
            formatParam = `jpg_${jpegQualitySlider.value}`;
        }

        const data = await fetchEstimatedSize(base64Image, formatParam);
        const fileSize = data.file_size_bytes;
        
        if (fileSize === -1) {
            jpegSizeEstimate.textContent = 'Größe: Unbekannt';
        } else {
            const displaySize = formatFileSize(fileSize);
            jpegSizeEstimate.textContent = `Größe: ${displaySize}`;
        }
    } catch (error) {
        console.error(error);
        jpegSizeEstimate.textContent = 'Fehler';
    }
}

function debouncedCalculateSize() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(calculateSize, 250);
}

function updateVisualPreview() {
    if (!appState.originalImageForJpegPreview) return;
    
    const selectedFormat = exportFormatSelect.value;
    if (jpegQualityControls) {
        jpegQualityControls.style.display = (selectedFormat === 'jpg') ? 'flex' : 'none';
    }

    let quality = 95;
    if (selectedFormat === 'jpg') {
        quality = parseInt(jpegQualitySlider.value);
        jpegQualityValue.textContent = quality;
    }

    const canvas = document.createElement('canvas');
    canvas.width = appState.originalImageForJpegPreview.naturalWidth;
    canvas.height = appState.originalImageForJpegPreview.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(appState.originalImageForJpegPreview, 0, 0);
    
    let previewMimeType = 'image/png';
    if (selectedFormat === 'jpg') previewMimeType = 'image/jpeg';
    if (selectedFormat === 'webp') previewMimeType = 'image/webp';
    
    const dataUrl = canvas.toDataURL(previewMimeType, quality / 100);
    jpegPreviewImage.src = dataUrl;
    
    if (jpegPreviewImage.style.display === 'none') {
        jpegPreviewLoader.style.display = 'none';
        jpegPreviewImage.style.display = 'block';
    }
}

function handleFormatChange() {
    const selectedFormat = exportFormatSelect.value;
    if (formatDescriptions[selectedFormat] && exportDescription) {
        exportDescription.innerHTML = formatDescriptions[selectedFormat];
    }
    
    // BUGFIX: Nur berechnen, wenn ein Bild vorhanden ist
    if (appState.originalImageForJpegPreview) {
        updateVisualPreview();
        calculateSize();
    }
}

// --- Öffentliche Modul-Funktionen ---

export async function openExportModal(imageId, isBatch = false) {
    if (jpegModal) jpegModal.dataset.isBatch = String(isBatch);
    const titleEl = document.getElementById('export-dialog-title');
    if (titleEl) {
        titleEl.textContent = isBatch ? `${appState.selectedImageIds.size} Bilder exportieren` : 'Bild exportieren';
    }
    appState.currentJpegExportImageId = imageId;
    jpegQualitySlider.value = 95;
    jpegQualityValue.textContent = '95';
    jpegSizeEstimate.textContent = 'Lade Vorschau...';
    jpegPreviewLoader.style.display = 'block';
    jpegPreviewImage.style.display = 'none';
    jpegPreviewImage.src = '';
    jpegModal.style.display = 'flex';
    try {
        const thumb = document.querySelector(`.gallery-thumbnail[data-image-id="${imageId}"]`);
        if (!thumb) throw new Error("Thumbnail nicht gefunden.");
        appState.originalImageForJpegPreview = new Image();
        appState.originalImageForJpegPreview.crossOrigin = "anonymous";
        await new Promise((resolve, reject) => {
            appState.originalImageForJpegPreview.onload = resolve;
            appState.originalImageForJpegPreview.onerror = reject;
            appState.originalImageForJpegPreview.src = thumb.src;
        });
        handleFormatChange();
    } catch (error) {
        console.error("Fehler beim Laden des Vorschaubildes für Export:", error);
        jpegSizeEstimate.textContent = 'Vorschau fehlgeschlagen';
        jpegPreviewLoader.style.display = 'none';
    }
}

export function initExportModule() {
    jpegModal = document.getElementById('is-jpeg-options-modal');
    jpegQualitySlider = document.getElementById('jpeg-quality-slider');
    jpegQualityValue = document.getElementById('jpeg-quality-value');
    jpegSizeEstimate = document.getElementById('jpeg-size-estimate');
    jpegExportConfirm = document.getElementById('jpeg-export-confirm');
    jpegExportCancel = document.getElementById('jpeg-export-cancel');
    jpegPreviewImage = document.getElementById('jpeg-preview-image');
    jpegPreviewLoader = document.getElementById('jpeg-preview-loader');
    exportCloseX = document.getElementById('export-close-x');
    exportFormatSelect = document.getElementById('export-format-select');
    exportDescription = document.getElementById('export-format-description');
    jpegQualityControls = document.getElementById('jpeg-quality-controls');
    downloadIndicator = document.getElementById('is-download-indicator');

    // UI-FIX: Das "Größe"-Feld aus dem Slider-Container verschieben, damit es immer sichtbar ist.
    if (jpegQualityControls && jpegSizeEstimate && jpegQualityControls.contains(jpegSizeEstimate)) {
        jpegQualityControls.parentNode.insertBefore(jpegSizeEstimate, jpegQualityControls.nextSibling);
    }

    if (exportCloseX) exportCloseX.addEventListener('click', closeExportModal);
    if (jpegExportCancel) jpegExportCancel.addEventListener('click', closeExportModal);
    if (jpegModal) jpegModal.addEventListener('click', (e) => {
        if (e.target === jpegModal) closeExportModal();
    });
    if (jpegQualitySlider) {
        jpegQualitySlider.addEventListener('input', () => {
            updateVisualPreview();      // Visuelle Vorschau sofort
            debouncedCalculateSize();   // Größe verzögert berechnen
        });
    }
    if (exportFormatSelect) {
        exportFormatSelect.addEventListener('change', handleFormatChange);
    }

    if (jpegExportConfirm) {
        jpegExportConfirm.addEventListener('click', async () => {
            const isBatch = jpegModal && jpegModal.dataset.isBatch === 'true';
            let formatParam = exportFormatSelect.value;
            if (exportFormatSelect.value === 'jpg') {
                formatParam = `jpg_${jpegQualitySlider.value}`;
            }

            if (isBatch && appState.selectedImageIds.size > 0) {
                jpegExportConfirm.disabled = true;
                try {
                    const folderResult = await window.electron.showFolderDialog();
                    if (!folderResult.success) return;
                    const targetDir = folderResult.path;
                    let successCount = 0;
                    const totalCount = appState.selectedImageIds.size;
                    for (const id of appState.selectedImageIds) {
                        jpegExportConfirm.textContent = `Speichere ${successCount + 1}/${totalCount}...`;
                        try {
                            const url = `${getBackendBaseUrl()}/api/images/${id}/download?format=${formatParam}`;
                            const token = localStorage.getItem('auth_token');
                            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
                            if (!response.ok) throw new Error(`Server-Fehler ${response.status}`);
                            
                            const thumb = document.querySelector(`.gallery-thumbnail[data-image-id="${id}"]`);
                            let baseFilename = `image_${id}`;
                            if (thumb && thumb.src) {
                                const urlParts = thumb.src.split('/');
                                if (urlParts.length > 0) {
                                    const lastPart = urlParts[urlParts.length - 1];
                                    if (lastPart) {
                                        baseFilename = lastPart.split('.').slice(0, -1).join('.');
                                    }
                                }
                            }
                            
                            const extension = exportFormatSelect.value.startsWith('tiff') ? 'tiff' : (exportFormatSelect.value === 'jpg' ? 'jpg' : exportFormatSelect.value);
                            const filename = `${baseFilename}.${extension}`;
                            const fullPath = `${targetDir}\\${filename}`;
                            const arrayBuffer = await response.arrayBuffer();
                            const saveResult = await window.electron.saveFileInPath({ fullPath, data: arrayBuffer });
                            if (!saveResult.success) throw new Error(saveResult.error);
                            successCount++;
                        } catch (e) {
                            console.error(`Fehler bei Bild-ID ${id}:`, e);
                        }
                    }
                    if (successCount > 0) {
                        alert(`${successCount} von ${totalCount} Bildern erfolgreich gespeichert.`);
                    } else {
                        alert("Keine Bilder konnten gespeichert werden.");
                    }
                    closeExportModal();
                    document.querySelectorAll('.gallery-item-wrapper.selected').forEach(el => el.classList.remove('selected'));
                    appState.selectedImageIds.clear();
                } catch (error) {
                    console.error("Fehler beim Speichern der Bilder:", error);
                    alert(`Fehler beim Speichern der Bilder: ${error.message}`);
                } finally {
                    jpegExportConfirm.disabled = false;
                    jpegExportConfirm.textContent = 'Speichern';
                }
            } else {
                try {
                    await downloadImage(appState.currentJpegExportImageId, formatParam);
                    closeExportModal();
                } catch (error) {
                    console.error("Fehler beim Speichern des Bildes:", error);
                }
            }
        });
    }

    if (exportFormatSelect) handleFormatChange();
}