import { appState } from './state.js';

let maskCanvas, maskControls, clearMaskBtn, brushSizeInput, previewWrapper;

export function initInpaintingModule() {
    maskCanvas = document.getElementById('is-mask-canvas');
    maskControls = document.getElementById('mask-controls');
    clearMaskBtn = document.getElementById('clear-mask-btn');
    brushSizeInput = document.getElementById('brush-size');
    previewWrapper = document.getElementById('is-preview-wrapper');

    if (maskCanvas) {
        maskCanvas.addEventListener('mousedown', startDrawing);
        maskCanvas.addEventListener('mousemove', draw);
        window.addEventListener('mouseup', stopDrawing);
    }
    if (clearMaskBtn) clearMaskBtn.addEventListener('click', clearMaskCanvas);
    if (brushSizeInput) brushSizeInput.addEventListener('input', updateBrushStyle);
}

export function initCanvasSize() {
    const img = previewWrapper?.querySelector('img');
    if (!img || !maskCanvas) return;

    if (!img.complete) { img.onload = initCanvasSize; return; }

    // Wir setzen den Canvas auf die exakte Größe des Wrappers
    // Da der Wrapper dank CSS jetzt 'relative' ist, passt 'absolute 0,0' perfekt.
    maskCanvas.width = img.naturalWidth;
    maskCanvas.height = img.naturalHeight;
    
    // Visuelle Größe (muss 100% des Wrappers sein)
    maskCanvas.style.width = '100%';
    maskCanvas.style.height = '100%';
    
    // Skalierung berechnen (Verhältnis echte Pixel zu angezeigten Pixeln)
    // clientWidth ist die Breite des Wrappers/Bildes im Browser
    if (img.clientWidth > 0) {
        appState.canvasScaleFactor = img.naturalWidth / img.clientWidth;
    }
    
    appState.ctx = maskCanvas.getContext('2d');
    updateBrushStyle();
}

export function toggleInpaintingUI(active) {
    // --- SICHERHEITS-CHECK: Sind Controls da? ---
    maskControls = document.getElementById('mask-controls');
    if (!maskControls && active) {
        // console.warn("[Inpainting] Controls fehlen! Erstelle sie neu..."); // Debug-Log entfernt
        const controlsDiv = document.createElement('div');
        controlsDiv.id = 'mask-controls';
        // Fester Style, immer sichtbar, immer oben
        controlsDiv.style.cssText = "display:flex; position:absolute; bottom:50px; left:50%; transform:translateX(-50%); background:white; padding:10px; border:2px solid red; z-index:999999; gap:10px; align-items:center; color:black;";
        
        controlsDiv.innerHTML = `
            <span style="font-weight:bold;">Pinsel:</span>
            <input type="range" id="brush-size" min="5" max="100" value="30" style="width:100px;">
            <button id="clear-mask-btn" style="background:#ff4444; color:white; border:none; padding:5px 10px; cursor:pointer;">Löschen</button>
        `;
        
        // In den Wrapper hängen
        document.body.appendChild(controlsDiv);
        
        // Referenzen neu binden
        maskControls = controlsDiv;
        clearMaskBtn = document.getElementById('clear-mask-btn');
        brushSizeInput = document.getElementById('brush-size');
        
        // Listener neu binden
        if (clearMaskBtn) clearMaskBtn.addEventListener('click', clearMaskCanvas);
        if (brushSizeInput) brushSizeInput.addEventListener('input', updateBrushStyle);
    }
    
    // --- UI SCHALTEN ---
    if (maskControls) {
        maskControls.style.display = active ? 'flex' : 'none';
    }
    
    if (maskCanvas) {
        maskCanvas.style.pointerEvents = active ? 'auto' : 'none';
        maskCanvas.style.zIndex = active ? '100' : '0';
        maskCanvas.style.opacity = active ? '1' : '0';
    }
    
    const img = previewWrapper?.querySelector('img');
    if (img) {
        img.draggable = !active;
    }

    if (active) initCanvasSize();
    else clearMaskCanvas();
}

export function getMaskData() {
    return maskCanvas ? maskCanvas.toDataURL('image/png') : null;
}

// --- ZEICHEN LOGIK ---

function startDrawing(e) {
    e.preventDefault();
    e.stopPropagation();
    appState.isDrawing = true;
    draw(e);
}

function draw(e) {
    if (!appState.isDrawing || !appState.ctx) return;
    e.preventDefault();

    // Wir nutzen offsetX/Y, das ist relativ zum Canvas-Element. Viel stabiler!
    const x = e.offsetX * appState.canvasScaleFactor;
    const y = e.offsetY * appState.canvasScaleFactor;

    const ctx = appState.ctx;
    ctx.lineTo(x, y);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(x, y);
}

function stopDrawing() {
    appState.isDrawing = false;
    if (appState.ctx) appState.ctx.beginPath();
}

function clearMaskCanvas() {
    if (appState.ctx && maskCanvas) {
        appState.ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    }
}

function updateBrushStyle() {
    if (!appState.ctx) return;
    const size = brushSizeInput ? brushSizeInput.value : 30;
    
    appState.ctx.lineWidth = size * appState.canvasScaleFactor;
    appState.ctx.strokeStyle = 'rgba(255, 0, 0, 0.6)'; // Roter Pinsel
    appState.ctx.lineCap = 'round';
    appState.ctx.lineJoin = 'round';
}