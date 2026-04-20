import { API_BASE_URL } from "./config.js";
import { openModal, bringToFront, isVideoUrl } from "./modal-api.js";
import { normalizeVideoEmbedUrl } from "./video-player.js";
import { patchChatTitleInUI, scheduleSmartTitleRefresh } from "./chat-manager.js";
import { speakText, isTTSEnabled, initTTS, ttsPreset } from "./tts.js";
import {
  paneId,
  getActiveWindowId,
  getActiveChatIdForWindow,
  getWindowState,
  setActiveWindow,
  setWindowMinimized,
  WINDOW_IDS,
  getDockModuleState,
} from "./window-state.js";
import { sanitizeChatHtml, sanitizeErrorHtml } from "./dompurify-config.js";

// Globaler Debugger für die Bridge
window.addEventListener("open-knowledge-center", (e) => {
  console.log("!!! EVENT-CHECK: Knowledge Center Signal empfangen!", e.detail);
});

window.addEventListener('open-knowledge-center', (e) => {
  console.log("REACT-BRIDGE-LOG: Event empfangen für DocID", e.detail?.documentId);
});

let ttsDebounceTimer;
let lastVideoModalRequest = null;
const VIDEO_MODAL_CACHE_KEY = "janus_video_modal_by_chat_v1";
// 💎 VIDEO-LIST-METADATA: Global storage for video list data from SSE metadata events
let lastVideoListMetadata = null;

function _readVideoModalCache() {
  try {
    const raw = localStorage.getItem(VIDEO_MODAL_CACHE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function _writeVideoModalCache(map) {
  try {
    localStorage.setItem(VIDEO_MODAL_CACHE_KEY, JSON.stringify(map || {}));
  } catch {
    // ignore localStorage errors
  }
}

function persistVideoModalForChat(chatId, modalRequest) {
  const cid = Number(chatId);
  if (!Number.isFinite(cid) || !modalRequest || typeof modalRequest !== "object") return;
  const map = _readVideoModalCache();
  map[String(cid)] = modalRequest;
  _writeVideoModalCache(map);
}

export function getCachedVideoModalForChat(chatId) {
  const cid = Number(chatId);
  if (!Number.isFinite(cid)) return null;
  const map = _readVideoModalCache();
  const entry = map[String(cid)];
  return entry && typeof entry === "object" ? entry : null;
}

/**
 * Canonical watch/page URL from backend `modal_request` (matches `payload.url` from orchestrator).
 * Never infer from chat markdown links — avoids mismatch with the automatic "Video ansehen" control.
 */
function canonicalWatchUrlFromModalRequest(modalRequest) {
  if (!modalRequest || typeof modalRequest !== "object") return "";
  const t = String(modalRequest.type || "").trim().toLowerCase();
  if (t !== "video") return "";
  const payload = modalRequest.payload && typeof modalRequest.payload === "object" ? modalRequest.payload : {};
  const primary = String(payload.url || "").trim();
  if (primary) return primary;
  const embed = String(payload.embed_url || "").trim();
  const yt = embed.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/);
  if (yt) return `https://www.youtube.com/watch?v=${yt[1]}`;
  const vm = embed.match(/player\.vimeo\.com\/video\/(\d+)/);
  if (vm) return `https://vimeo.com/${vm[1]}`;
  return "";
}

/** Remove LLM-inlined YouTube/Vimeo links; keep the system "Video ansehen" control as the only video link. */
function stripInlineAssistantVideoLinks(rootElement) {
  // TEMPORÄR DEAKTIVIERT - Links werden nicht mehr gelöscht, solange das System instabil ist
  return;
  if (!rootElement || typeof rootElement.querySelectorAll !== "function") return;
  rootElement.querySelectorAll("a[href]").forEach((a) => {
    if (a.dataset?.janusAction === "reopen-video-modal") return;
    const href = String(a.getAttribute("href") || "").trim();
    if (!href || href === "#") return;
    if (!isVideoUrl(href)) return;
    const plain = document.createTextNode(a.textContent || "");
    a.replaceWith(plain);
  });
}

// NEU: Image Modal Elemente
const imageModal = document.getElementById("image-modal");
const imageModalImg = document.getElementById("image-modal-img");
const closeImageModalButton = document.getElementById("close-image-modal"); // <--- UMBENANNT

// NEU: Funktionen zum Öffnen und Schließen des Image Modals
window.openImageModal = function(imageUrl) {
  console.log("openImageModal called with URL:", imageUrl);
  imageModalImg.src = ''; // Erst leeren, damit onload immer feuert
  imageModal.style.display = "block";

  const modalContent = imageModal.querySelector('.modal-content');
  if (modalContent) {
    // Verstecke das Modal-Content temporär, während das Bild geladen wird
    modalContent.style.visibility = 'hidden'; 
    
    const tempImage = new Image();
    tempImage.onload = () => {
      imageModalImg.src = imageUrl; // Bild setzen, nachdem es geladen ist
      
      // Setze die Größe des Bildes basierend auf Originalgröße, aber beschränkt auf 1024x1024
      // und den Viewport
      const originalWidth = tempImage.width;
      const originalHeight = tempImage.height;

      const maxWidth = Math.min(originalWidth, 1024, window.innerWidth - 40); // 40px Padding/Margin
      const maxHeight = Math.min(originalHeight, 1024, window.innerHeight - 40 - 50); // 40px Padding/Margin + Header

      // Skaliere das Bild proportional
      let finalWidth = originalWidth;
      let finalHeight = originalHeight;

      if (finalWidth > maxWidth) {
        finalHeight = (maxWidth / finalWidth) * finalHeight;
        finalWidth = maxWidth;
      }

      if (finalHeight > maxHeight) {
        finalWidth = (maxHeight / finalHeight) * finalWidth;
        finalHeight = maxHeight;
      }

      imageModalImg.style.width = `${finalWidth}px`;
      imageModalImg.style.height = `${finalHeight}px`;
      
      imageModalImg.src = imageUrl; // Bild setzen, nachdem es geladen ist (und Größe gesetzt)
      
      // Setze data-attribute für interactjs, falls es wieder aktiviert wird
      const rect = modalContent.getBoundingClientRect();
      modalContent.setAttribute("data-x", rect.left);
      modalContent.setAttribute("data-y", rect.top);
      
      modalContent.style.visibility = 'visible'; // Wieder sichtbar machen
    };
    tempImage.onerror = () => {
        console.error("Failed to load image:", imageUrl);
        imageModal.style.display = 'none'; // Modal bei Fehler schließen
        alert("Fehler beim Laden des Bildes.");
    };
    tempImage.src = imageUrl; // Starte das Laden des Bildes
  }
}

function closeImageModal() {
  imageModal.style.display = "none";
  imageModalImg.src = ""; // Bild zurücksetzen, um Speicher freizugeben
}


// Configure marked.js for stricter Markdown parsing
marked.setOptions({
  breaks: true, // Convert single newlines to <br> for better link rendering
  gfm: true, // Use GitHub Flavored Markdown (stricter paragraph breaks)
});

// 💎 MCL: Hydrate video links with class and click handlers after stream rendering
function hydrateVideoLinks(element) {
  if (!element) return;
  element.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (href.includes('youtube.com') || href.includes('youtu.be'))) {
      link.classList.add('mcl-video-link');
      // Ensure click handler is attached
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("MCL VIDEO-LINK CLICKED:", href);
        if (typeof window.openModal === 'function') {
          window.openModal({
            type: "video",
            payload: { url: href }
          });
        } else {
          window.dispatchEvent(new CustomEvent('janus:open-modal', {
            detail: { type: 'video', payload: { url: href } }
          }));
        }
      });
    }
  });
}

// Initialize TTS on page load
document.addEventListener("DOMContentLoaded", () => {
  initTTS();

  document.getElementById("chat-window-minimize-btn-A")?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    setWindowMinimized("A", true);
  });
  document.getElementById("chat-window-minimize-btn-B")?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    setWindowMinimized("B", true);
  });

  // NEU: Event-Listener für Image Modal
  if (closeImageModalButton) {
    closeImageModalButton.addEventListener("click", closeImageModal);
  }
  if (imageModal) {
    imageModal.addEventListener("click", (e) => {
      // Schließe nur, wenn der Klick direkt auf das Overlay erfolgte
      // UND kein Dragging gerade beendet wurde
      if (e.target === imageModal) {
        if (!window.justDragged) {
            closeImageModal();
        }
        window.justDragged = false; // Flag nach Gebrauch zurücksetzen
      }
    });
  }
});

/** Aktives Composer-Textfeld (Fenster mit Fokus / letztem Klick). */
export function getActiveUserInputEl() {
  return document.getElementById(paneId("user-input", getActiveWindowId()));
}

/**
 * POST /api/chats + loadChat für Fenster, ohne zirkulären Static-Import chat↔chat-manager.
 */
async function ensureChatForWindow(windowId) {
  const existing = getActiveChatIdForWindow(windowId);
  if (existing != null) {
    return existing;
  }
  const response = await fetch(`${API_BASE_URL}/api/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const newChat = await response.json();
  const { loadChats, loadChat } = await import("./chat-manager.js");
  await loadChats(true, null, { suppressAutoCreate: true });
  await loadChat(newChat.id, { windowId });
  return newChat.id;
}

/** Fenster-Header-Override oder Sidebar (#provider-select / #model-select). */
function effectiveProviderModelForWindow(windowId) {
  const w = getWindowState().windows[windowId];
  const sp = document.getElementById("provider-select")?.value;
  const sm = document.getElementById("model-select")?.value;
  return {
    provider: w.provider != null && w.provider !== "" ? w.provider : sp,
    model: w.modelId != null && w.modelId !== "" ? w.modelId : sm,
  };
}

const USER_INPUT_MAX_PX = 200;

/**
 * Textarea auto-resize (keyboard, paste, context menu, drag-drop — all emit `input`).
 * Synchronous; not debounced. Listeners + rAF live in app.js.
 */
export function autoResize() {
  if (!this || this.tagName !== "TEXTAREA") return;
  // 1. Must be first: reset height so scrollHeight reflects full content (grow, shrink, paste)
  this.style.height = "auto";
  // 2. Cap height at 200px
  const newHeight = Math.min(this.scrollHeight, USER_INPUT_MAX_PX);
  // 3. Apply
  this.style.height = `${newHeight}px`;
  // 4. Inner scrollbar only when content exceeds the visible box
  this.style.overflowY = this.scrollHeight > USER_INPUT_MAX_PX ? "auto" : "hidden";
  // 5. Show end of text / caret inside the textarea (browser clamps scrollTop as needed)
  this.scrollTop = this.scrollHeight;
  // 6. Main chat transcript follows the growing composer (scrollToBottom in app.js)
  const m = this.id && String(this.id).match(/user-input-([AB])$/);
  const wid = m ? m[1] : getActiveWindowId();
  scrollChatToBottom({ behavior: "auto", windowId: wid });
}

export function resetUserInputHeight(windowId) {
  const wid = windowId ?? getActiveWindowId();
  const input = document.getElementById(paneId("user-input", wid));
  if (input) autoResize.call(input);
}

// LISTENER FÜR ZITATE
window.addEventListener('insert-chat-quote', (event) => {
  console.log('Legacy Chat received quote:', event.detail);
  const input = document.getElementById(paneId("user-input", getActiveWindowId())) ||
                document.getElementById("chat-input") ||
                document.getElementById("message-input") ||
                document.querySelector("textarea");

  if (input) {
    const quote = `Bezugnehmend auf "${event.detail?.filename || 'Dokument'}":\n> "${event.detail?.text || ''}"\n\nMeine Frage dazu: `;
    input.value = quote;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.focus();
    input.scrollIntoView({ behavior: 'smooth' });
  } else {
    console.error('CRITICAL: Chat input field not found!');
  }
});

// Event listener for opening links externally (beide Panes)
WINDOW_IDS.forEach((wid) => {
  const el = document.getElementById(paneId("chat-messages", wid));
  if (!el) return;
  el.addEventListener("click", (event) => {
    const target = event.target;
    const link = target?.closest?.("a");
    if (!link) return;
    // 💎 MCL: Handle "Video ansehen" links from LLM synthesis
    if (link.textContent.includes("Video ansehen")) {
      event.preventDefault();
      const url = String(link.getAttribute("href") || "").trim();
      if (url && isVideoUrl(url)) {
        openModal({ type: "video", payload: { url } });
      }
      return;
    }
    if (link.dataset?.janusAction === "reopen-video-modal") {
      event.preventDefault();
      const fallbackVideoUrl = String(link.dataset.videoUrl || "").trim();
      if (lastVideoModalRequest && lastVideoModalRequest.type === "video") {
        reopenLastVideoModal();
      } else {
        const activeChatId = getActiveChatIdForWindow(getActiveWindowId());
        const cached = getCachedVideoModalForChat(activeChatId);
        if (cached && typeof cached === "object" && String(cached.type || "").toLowerCase() === "video") {
          lastVideoModalRequest = cached;
          reopenLastVideoModal();
        } else if (fallbackVideoUrl && isVideoUrl(fallbackVideoUrl)) {
          openModal({ type: "video", payload: { url: fallbackVideoUrl } });
        }
      }
      return;
    }
    const clickedUrl = String(link.getAttribute("href") || link.href || "").trim();
    if (clickedUrl && isVideoUrl(clickedUrl)) {
      event.preventDefault();
      openModal({ type: "video", payload: { url: clickedUrl } });
      return;
    }
    if (link.href) {
      event.preventDefault();
      if (window.electron && window.electron.openExternal) {
        window.electron.openExternal(link.href);
      } else {
        window.open(link.href, "_blank");
      }
    }
  });
});


function isConsentPrompt(text) {
  const normalized = String(text || "").toLowerCase();
  return (
    normalized.includes("diese aktion erfordert eine freigabe")
    && normalized.includes("1.")
    && normalized.includes("2.")
    && normalized.includes("3.")
  );
}

// --- NEU: Zentrale Funktion zur Dateiverarbeitung (für Button UND Drag & Drop) ---
async function processFile(file, paneWindowId) {
  const windowId = paneWindowId ?? getActiveWindowId();
  const chatMessages = document.getElementById(paneId("chat-messages", windowId));
  if (!file || !chatMessages) return;

  if (getActiveChatIdForWindow(windowId) == null) {
    try {
      await ensureChatForWindow(windowId);
    } catch (e) {
      console.error("[processFile] ensureChatForWindow failed:", e);
      return;
    }
  }

  const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  const isImage = typeof file.type === "string" && file.type.startsWith("image/");

  if (isPdf) {
    const loadingText = `PDF wird indiziert: ${file.name}...`;
    appendMessage("bot", { text: loadingText }, { windowId });
    const loadingMessageElement = chatMessages.lastChild?.querySelector('.bubble') || chatMessages.lastChild;

    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(`${API_BASE_URL}/api/rag/upload-document`, {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "PDF-Upload fehlgeschlagen.");
      }

      const uploadResult = await uploadResponse.json();
      console.log("Upload Result:", uploadResult);
      if (uploadResult.status === "already_exists") {
        if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
          chatMessages.removeChild(loadingMessageElement);
        }
        appendMessage("bot", { text: "💡 " + uploadResult.message }, { windowId });
        // MCL: Knowledge Center mit docId öffnen
        if (typeof window.openModal === 'function') {
          window.openModal({ type: 'document', payload: { docId: uploadResult.document_id } });
        } else if (typeof window.openJanusKnowledge === 'function') {
          window.openJanusKnowledge(uploadResult.document_id);
        }
        return;
      }
      console.log("Opening Knowledge Center via MCL...");
      // MCL: Knowledge Center mit docId öffnen
      if (typeof window.openModal === 'function') {
        window.openModal({ type: 'document', payload: { docId: uploadResult.document_id } });
      } else if (typeof window.openJanusKnowledge === 'function') {
        window.openJanusKnowledge(uploadResult.document_id);
      } else {
        window.dispatchEvent(new CustomEvent('open-knowledge-center', {
          detail: { documentId: uploadResult.document_id, open: true },
        }));
      }

      const { provider, model } = effectiveProviderModelForWindow(windowId);
      const chat_id = getActiveChatIdForWindow(windowId);
      appendMessage("user", { text: `Ich habe das Dokument '${file.name}' hochgeladen.` }, { windowId });

      const autoPrompt = `SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD '${file.name}':
Ich habe dieses Dokument hochgeladen. Führe jetzt den Audit durch.

!!! STOPP !!! Lies KEINE alten Zusammenfassungen aus dem Gedächtnis! Du MUSST zwingend das Tool 'knowledge_read_full_text' (oder 'knowledge.query') mit dem Dateinamen '${file.name}' aufrufen, um das NEUE Dokument zu lesen. Wenn du antwortest, ohne ein Tool aufgerufen zu haben, ist das ein kritischer Systemfehler!

GEFORDERTES AUSGABE-FORMAT (Halte dich exakt daran!):

### Zusammenfassung
[Hier 2-3 Sätze zum Inhalt der PDF]

### Die 3 wichtigsten Punkte
1. [Punkt 1 aus der PDF]
2. [Punkt 2 aus der PDF]
3. [Punkt 3 aus der PDF]

### Faktencheck
[Hier NUR EINE der folgenden zwei Zeilen ausgeben:]
✅ Bestanden. Alle geprüften Fakten sind plausibel.
❌ Nicht bestanden. Folgende Abweichungen gefunden:
- [PDF behauptet X, aber Wikipedia sagt Y]
- [PDF Daten sind veraltet (Stand: Jahr), aktuell ist: ...]

[NUR WENN NICHT BESTANDEN:]
Wähle eine Aktion (Antworte mit 1, 2 oder 3):
1️⃣ Ignorieren (Keine Änderung)
2️⃣ Kopie erstellen (Aktualisierte Version als neue Datei speichern)
3️⃣ Original ersetzen (Aktualisierte Version überschreibt diese Datei)`;

      // SSE-Streaming-Integration für /api/chat/stream
      const chatStreamResponse = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: [{ type: "text", text: autoPrompt }],
          provider,
          model,
          chat_id,
          audit_file: file.name,  // 💎 ANTI-HALLUCINATION: Marker for file upload audit intent
        }),
      });
      if (!chatStreamResponse.ok) {
        throw new Error("SSE-Stream: HTTP " + chatStreamResponse.status);
      }
      const reader = chatStreamResponse.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let chatText = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split("\n\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6);
          let data;
          try {
            data = JSON.parse(jsonStr);
          } catch (e) {
            continue;
          }
          if (data.type === "text") {
            chatText = data.partial ? chatText + data.content : data.content;
            loadingMessageElement.innerHTML = sanitizeChatHtml(marked.parse(chatText));
            hydrateVideoLinks(loadingMessageElement);
          } else if (data.type === "metadata") {
            if (window.updateSidebarCost) window.updateSidebarCost(data.cost, data.usage);
            const metaTitle = data.title ?? data.chat_title;
            if (metaTitle) {
              patchChatTitleInUI(data.chat_id ?? chat_id, metaTitle);
            }
            // 💎 VIDEO-LIST-METADATA: Store video list data from SSE metadata event
            if (data.videos && Array.isArray(data.videos) && data.mode === "list") {
              lastVideoListMetadata = {
                videos: data.videos,
                count: data.count,
                mode: data.mode,
                query: data.query
              };
              console.log("💎 VIDEO-LIST-METADATA: Stored video list data:", lastVideoListMetadata);
            }
          } else if (data.type === "done") {
            break;
          }
        }
      }
      loadingMessageElement.innerHTML = sanitizeChatHtml(marked.parse(chatText));
      hydrateVideoLinks(loadingMessageElement);
      applyMCLLinkStyling(loadingMessageElement);
      if (chat_id) {
        scheduleSmartTitleRefresh(chat_id);
      }
      return;
    } catch (error) {
      const _msgContainer = loadingMessageElement?.closest('.message') || loadingMessageElement;
      if (_msgContainer && _msgContainer.parentNode === chatMessages) {
        chatMessages.removeChild(_msgContainer);
      }
      appendMessage("bot", { text: error.message || "PDF-Verarbeitung fehlgeschlagen." }, { windowId });
      return;
    }
  }

  if (!isImage) {
    appendMessage("bot", { text: "Format nicht unterstützt. Bitte nur PDF oder Bild hochladen." }, { windowId });
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const dataUrl = e.target.result;
    const base64 = dataUrl.split(",")[1];

    // 1. User-Bild sofort im UI anzeigen
    appendMessage(
      "user",
      {
        image_base64: base64,
        mime_type: file.type,
      },
      { windowId }
    );

    // 2. Request vorbereiten
    const { provider, model } = effectiveProviderModelForWindow(windowId);
    const chat_id = getActiveChatIdForWindow(windowId);
    // Der Standard-Prompt, der später im UI ausgeblendet wird
    const defaultPrompt = "Gib eine kurze Bestätigung und die wichtigsten Merkmale des Bildes in einem Satz.";

    const requestBody = {
      content: [
        { type: "text", text: defaultPrompt },
        { type: "image_url", image_url: dataUrl },
      ],
      provider,
      model,
      chat_id,
    };

    // 3. Loading Indicator und Request senden
    appendMessage("bot", "...", { windowId });
    const loadingMessageElement = chatMessages.lastChild;

    try {
      // Kein voreiliger PUT: Backend Smart-Naming + ggf. lokales Label nur im Header
      const chatHeader = document.getElementById(paneId("chat-header", windowId));
      const titleTarget =
        chatHeader?.querySelector(".chat-header-title-label") || chatHeader;
      if (chat_id && titleTarget && titleTarget.textContent.trim() === "Neuer Chat") {
        titleTarget.textContent = "Bildanalyse";
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unknown error");
      }

      const data = await response.json();
      if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
        chatMessages.removeChild(loadingMessageElement);
      }
      appendMessage("bot", data, { windowId });
      if (chat_id) {
        scheduleSmartTitleRefresh(chat_id);
      }
      if (window.fetchCostData) {
        window.fetchCostData();
      }
    } catch (error) {
      if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
        chatMessages.removeChild(loadingMessageElement);
      }
      appendMessage("bot", { text: error.message }, { windowId });
    }
  };

  reader.readAsDataURL(file);
}

// 1. Bild-Upload-Button pro Pane
WINDOW_IDS.forEach((wid) => {
  const imageUploadBtn = document.getElementById(paneId("image-upload-btn", wid));
  const imageUploadInput = document.getElementById(paneId("image-upload-input", wid));
  if (!imageUploadBtn || !imageUploadInput) return;
  imageUploadBtn.addEventListener("click", () => {
    imageUploadInput.click();
  });
  imageUploadInput.addEventListener("change", (event) => {
    processFile(event.target.files[0], wid);
    imageUploadInput.value = "";
  });
});

// 2. Drag & Drop pro Chat-Pane
WINDOW_IDS.forEach((wid) => {
  const cm = document.getElementById(paneId("chat-messages", wid));
  if (!cm) return;
  cm.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    cm.classList.add("drag-over");
  });
  cm.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    cm.classList.remove("drag-over");
  });
  cm.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    cm.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFile(files[0], wid);
    }
  });
});

/**
 * Sends the current composer text (same path as form submit).
 * Enter without Shift calls this; Shift+Enter inserts a newline.
 */
export async function sendMessage(fromWindowId) {
  const windowId = fromWindowId ?? getActiveWindowId();
  setActiveWindow(windowId);
  const chatInputEl = document.getElementById(paneId("user-input", windowId));
  const chatMessagesEl = document.getElementById(paneId("chat-messages", windowId));
  if (!chatInputEl || !chatMessagesEl) return;
  const promptText = chatInputEl.value.trim();
  if (!promptText) return;

  const { provider, model } = effectiveProviderModelForWindow(windowId);
  let chat_id = getActiveChatIdForWindow(windowId);
  if (chat_id == null) {
    try {
      chat_id = await ensureChatForWindow(windowId);
    } catch (e) {
      console.error("[sendMessage] ensureChatForWindow failed:", e);
      return;
    }
    if (chat_id == null) {
      return;
    }
  }

  // 1. Append user message to UI
  appendMessage("user", { text: promptText }, { windowId });
  chatInputEl.value = "";
  resetUserInputHeight(windowId);

  // 2. Prepare request body for API (text only)
  const requestBody = {
    content: [{ type: "text", text: promptText }],
    provider,
    model,
    chat_id,
  };

  // 3. Show loading indicator
  appendMessage("bot", "...", { windowId });
  const loadingMessageElement = chatMessagesEl.lastChild?.querySelector('.bubble') || chatMessagesEl.lastChild;

  try {
    // Kein PUT mit Erstsatz — verhindert auto_generated=false und blockiert Smart Chat Naming.

    // SSE-STREAMING IMPLEMENTATION
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error("SSE-Stream: HTTP " + response.status);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let chatText = "";
    let streamModalRequest = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split("\n\n");
      buffer = lines.pop(); // Keep incomplete chunk
      
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        
        const jsonStr = line.slice(6);
        let data;
        try {
          data = JSON.parse(jsonStr);
        } catch (e) {
          console.warn("[SSE] JSON parse error, skipping chunk");
          continue;
        }
        
        if (data.type === "text") {
          chatText = data.partial ? chatText + data.content : data.content;
          // Heilt nackte URLs vom Modell
          const healedText = chatText.replace(/Video ansehen\s*\((https?:\/\/[^\s)]+)\)/g, '[Video ansehen]($1)');
          loadingMessageElement.innerHTML = sanitizeChatHtml(marked.parse(healedText));
          normalizeLinksAndImages(loadingMessageElement);
          scrollChatToBottom({ behavior: "auto", windowId });
        } else if (data.type === "metadata") {
          // DISPATCH CUSTOM EVENT for sidebar update
          window.dispatchEvent(new CustomEvent("janus:metadata", {
            detail: { cost: data.cost, usage: data.usage }
          }));
          const metaTitle = data.title ?? data.chat_title;
          if (metaTitle) {
            patchChatTitleInUI(data.chat_id ?? chat_id, metaTitle);
          }
          // 💎 VIDEO-LIST-METADATA: Store video list data from SSE metadata event
          if (data.videos && Array.isArray(data.videos) && data.mode === "list") {
            lastVideoListMetadata = {
              videos: data.videos,
              count: data.count,
              mode: data.mode,
              query: data.query
            };
            console.log("💎 VIDEO-LIST-METADATA: Stored video list data:", lastVideoListMetadata);
          }
        } else if (data.type === "modal_request") {
          streamModalRequest = data.modal_request ?? null;
          stripInlineAssistantVideoLinks(loadingMessageElement);
          ensureVideoReopenLinkForStreamMessage(loadingMessageElement, streamModalRequest);
        } else if (data.type === "done") {
          break;
        } else if (data.type === "error") {
          console.error("[SSE] Error chunk:", data.message);
          loadingMessageElement.innerHTML = sanitizeErrorHtml(`<span style="color:red">[Stream Error] ${data.message}</span>`);
          scrollChatToBottom({ behavior: "auto", windowId });
        }
      }
    }
    
    // Final render
    // Heilt nackte URLs vom Modell
    const healedText = chatText.replace(/Video ansehen\s*\((https?:\/\/[^\s)]+)\)/g, '[Video ansehen]($1)');
    loadingMessageElement.innerHTML = sanitizeChatHtml(marked.parse(healedText));
    normalizeLinksAndImages(loadingMessageElement);
    // Keine weiteren Hydration-Calls hier nötig, da der Window-Listener alles abfängt!
    scrollChatToBottom({ behavior: "auto", windowId });

    applyBotModalRequestFromData({ text: chatText, modal_request: streamModalRequest });

    // 💎 VIDEO-LIST-POST-STREAM: Deaktiviert - wir nutzen nur noch Markdown-Links
    // if (lastVideoListMetadata && lastVideoListMetadata.mode === "list" && lastVideoListMetadata.videos && Array.isArray(lastVideoListMetadata.videos)) {
    //   const botMessages = document.querySelectorAll('.message.assistant .bubble');
    //   const lastBubble = botMessages[botMessages.length - 1];
    //   if (lastBubble) {
    //     console.log("💎 SSE-DONE-TRIGGER: Drawing video cards now.");
    //     renderVideoListCards(lastBubble, lastVideoListMetadata);
    //   }
    //   lastVideoListMetadata = null;
    // }

    if (chat_id) {
      scheduleSmartTitleRefresh(chat_id);
    }
    
  } catch (error) {
    console.error("[SSE] Chat stream error:", error);
    const _msgContainer = loadingMessageElement?.closest('.message') || loadingMessageElement;
    if (_msgContainer && _msgContainer.parentNode === chatMessagesEl) {
      chatMessagesEl.removeChild(_msgContainer);
    }
    appendMessage("bot", { text: error.message || "Fehler beim Senden der Nachricht." }, { windowId });
  }
}

WINDOW_IDS.forEach((wid) => {
  const f = document.getElementById(paneId("chat-form", wid));
  f?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendMessage(wid);
  });
});

let chatComposerUiInitialized = false;

/**
 * Auto-resize textarea, Enter-to-send, Shift+Enter for newline.
 * Called from app.js setupEventListeners.
 */
export function initChatComposer() {
  if (chatComposerUiInitialized) return;
  let any = false;
  WINDOW_IDS.forEach((wid) => {
    const input = document.getElementById(paneId("user-input", wid));
    const form = document.getElementById(paneId("chat-form", wid));
    if (!input || !form) return;
    any = true;
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        void sendMessage(wid);
      }
    });
  });
  if (any) chatComposerUiInitialized = true;
}

// EVENT-LISTENER für SSE Metadata (Sidebar Kosten-Update)
window.addEventListener("janus:metadata", (e) => {
  const detail = e.detail;
  console.log("DOM-UPDATE-DATA:", JSON.stringify(detail));

  const { cost, usage } = detail;

  // Normalize cost keys: backend may send total_cost, total, or cost_usd
  const totalCost = cost?.total_cost ?? cost?.total ?? cost?.cost_usd ?? 0;
  const inputTokens = usage?.input_tokens ?? usage?.prompt_tokens ?? 0;
  const outputTokens = usage?.output_tokens ?? usage?.completion_tokens ?? 0;
  const totalTokens = usage?.total_tokens ?? (inputTokens + outputTokens);


  // Store globally for modal and other consumers
  window.lastMetadata = {
    cost: totalCost,
    inputTokens,
    outputTokens,
    totalTokens,
    timestamp: Date.now(),
  };
  console.log("[JANUS:METADATA] window.lastMetadata set:", window.lastMetadata);

  // DIRECT DOM WRITE — German locale format
  const costFormatted = totalCost.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + " €";

  const currentMonthCost = document.getElementById("current-month-cost");
  if (currentMonthCost) {
    currentMonthCost.textContent = `Letzte Anfrage: ${costFormatted}`;
    console.log("[JANUS:METADATA] #current-month-cost updated to:", currentMonthCost.textContent);
  }

  const monthlyBudget = document.getElementById("monthly-budget");
  if (monthlyBudget) {
    monthlyBudget.textContent = `Tokens: ${inputTokens} In / ${outputTokens} Out`;
  }

  // Delay DB refresh by 3s to let backend persist KPI first
  setTimeout(() => {
    if (window.fetchCostData) {
      window.fetchCostData();
    }
  }, 3000);
});

// --- START: SPEECH-TO-TEXT IMPLEMENTATION (pro Pane ein Mic) ---

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
/** @type {HTMLElement | null} */
let activeMicBtn = null;

WINDOW_IDS.forEach((wid) => {
  const micBtn = document.getElementById(paneId("mic-btn", wid));
  if (!micBtn) return;
  micBtn.addEventListener("click", async () => {
    const userInput = document.getElementById(paneId("user-input", wid));
    if (!userInput) return;

    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        activeMicBtn = micBtn;

        mediaRecorder.addEventListener("dataavailable", (event) => {
          audioChunks.push(event.data);
        });

        mediaRecorder.addEventListener("stop", async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
          const formData = new FormData();
          formData.append("file", audioBlob, "recording.webm");

          userInput.placeholder = "Transkribiere Audio...";
          micBtn.textContent = "⏳";

          try {
            const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
              method: "POST",
              body: formData,
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.detail || "Fehler bei der Transkription.");
            }

            const data = await response.json();
            userInput.value = data.transcription;
            autoResize.call(userInput);
          } catch (error) {
            console.error("Transcription error:", error);
            alert(`Fehler: ${error.message}`);
          } finally {
            userInput.placeholder = "Nachricht an Janus senden...";
            micBtn.textContent = "🎤";
            audioChunks = [];
            activeMicBtn = null;
          }
        });

        mediaRecorder.start();
        isRecording = true;
        micBtn.style.color = "red";
        micBtn.textContent = "🛑";
      } catch (error) {
        console.error("Error accessing microphone:", error);
        alert("Mikrofonzugriff verweigert. Bitte erlaube den Zugriff in den Browser-Einstellungen.");
      }
    } else {
      mediaRecorder.stop();
      isRecording = false;
      if (activeMicBtn) {
        activeMicBtn.style.color = "";
        activeMicBtn.textContent = "🎤";
      }
    }
  });
});
// --- END: SPEECH-TO-TEXT IMPLEMENTATION ---

/**
 * Scroll the main chat transcript to the latest content.
 * Uses rAF twice so layout (markdown, images, textarea shrink) has settled.
 * @param {{ behavior?: "auto" | "smooth" }} [options] — smooth for history load; auto for streaming/typing
 */
export function scrollChatToBottom(options = {}) {
  const { behavior = "auto", windowId = getActiveWindowId() } = options;
  const el = document.getElementById(paneId("chat-messages", windowId));
  if (!el) return;

  const run = () => {
    const top = el.scrollHeight;
    if (behavior === "smooth" && typeof el.scrollTo === "function") {
      el.scrollTo({ top, behavior: "smooth" });
    } else {
      el.scrollTop = top;
    }
  };

  run();
  requestAnimationFrame(() => {
    run();
    requestAnimationFrame(run);
  });
}

function normalizeMediaUrl(url) {
  if (!url || typeof url !== "string") return url;
  let normalized = url.replace(/\\/g, "/");
  if (normalized.startsWith("sandbox:")) {
    normalized = normalized.replace(/^sandbox:/, "");
  }
  if (normalized.startsWith("/user_images/")) {
    return API_BASE_URL + normalized;
  }
  return normalized;
}

function normalizeLinksAndImages(rootElement) {
  if (!rootElement || typeof rootElement.querySelectorAll !== "function") return;

  rootElement.querySelectorAll("img").forEach((img) => {
    const rawSrc = img.getAttribute("src");
    const fixedSrc = normalizeMediaUrl(rawSrc);
    if (fixedSrc && fixedSrc !== rawSrc) {
      img.setAttribute("src", fixedSrc);
    }
  });

  rootElement.querySelectorAll("a").forEach((a) => {
    const rawHref = a.getAttribute("href");
    const fixedHref = normalizeMediaUrl(rawHref);
    if (fixedHref && fixedHref !== rawHref) {
      a.setAttribute("href", fixedHref);
    }
  });
}

function removePlaceholderImageMarkdown(text) {
  if (typeof text !== "string" || !text) return text;
  const cleaned = text
    .replace(/!\[[^\]]*\]\(\s*Generated Image\s*\)/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return cleaned;
}

/**
 * MCL: öffnet Dock-Modal wenn die API ``modal_request`` liefert (POST /chat oder SSE-Nachlauf-Chunk).
 * @param {{ modal_request?: object, text?: string }} payload
 */
function applyBotModalRequestFromData(payload) {
  if (!payload || typeof payload !== "object" || !payload.modal_request || typeof payload.modal_request !== "object") {
    return;
  }
  const mr = payload.modal_request;
  const type = String(mr.type || "").trim();
  const autoOpen = mr.options?.auto_open !== false;
  if (!autoOpen || !type) return;
  const dataPayload = mr.data && typeof mr.data === "object" ? mr.data : {};
  const p = { ...(mr.payload || {}) };
  if (!p.url && dataPayload.url) p.url = String(dataPayload.url).trim();
  if (!p.title && dataPayload.title) p.title = String(dataPayload.title).trim();
  if (!p.video_id && dataPayload.video_id) p.video_id = String(dataPayload.video_id).trim();
  if (type === "video" && !p.embed_url && p.url) {
    const embed = normalizeVideoEmbedUrl(p.url);
    if (embed) p.embed_url = embed;
  }
  if (type === "video") {
    lastVideoModalRequest = {
      type: "video",
      payload: p,
      options: { ...(mr.options || {}) },
    };
    const activeChatId = getActiveChatIdForWindow(getActiveWindowId());
    persistVideoModalForChat(activeChatId, lastVideoModalRequest);
  }
  setTimeout(() => {
    openModal({ type, payload: p, options: mr.options || {} });
  }, 500);
}

function reopenLastVideoModal() {
  if (!lastVideoModalRequest || lastVideoModalRequest.type !== "video") return;
  const current = getDockModuleState("video-player");
  if (current?.isOpen && !current?.minimized) {
    bringToFront("video-player");
    return;
  }
  openModal({
    type: "video",
    payload: { ...(lastVideoModalRequest.payload || {}) },
    options: { ...(lastVideoModalRequest.options || {}) },
  });
}

/**
 * Rendert Video-Liste als Karten wenn die API videos[] liefert (List-Mode).
 * @param {HTMLElement} messageEl - Das Bot-Message-Element (bubble)
 * @param {object} payload - Die API-Response data (mit videos[] Array)
 */
function renderVideoListCards(messageEl, payload) {
  if (!payload || !Array.isArray(payload.videos) || payload.videos.length === 0) return false;

  const container = document.createElement("div");
  container.className = "video-list-cards";
  container.style.cssText = "display: flex; flex-direction: column; gap: 4px; margin-top: 10px;";

  for (const video of payload.videos) {
    if (!video || typeof video !== "object") continue;

    const card = document.createElement("div");
    card.className = "video-list-card";
    card.style.cssText = "background: none; border: none; padding: 0; color: var(--accent-color); text-decoration: underline; cursor: pointer; font-size: 0.9rem; text-align: left;";

    const title = video.title || "Video";
    const isEmbeddable = video.is_embeddable !== false;
    const videoId = video.video_id || "";
    const watchUrl = video.watch_url || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : "");
    const embedUrl = video.embed_url || (videoId ? `https://www.youtube.com/embed/${videoId}?rel=0` : "");

    card.innerHTML = `<span>▶ Video ansehen: ${title}</span>`;

    card.addEventListener("click", () => {
      openModal({
        type: "video",
        payload: {
          source: "youtube",
          url: watchUrl || "",
          title: title,
          embed_url: embedUrl || "",
          is_embeddable: isEmbeddable,
        },
        options: { auto_open: true, pinnable: true },
      });
    });

    card.addEventListener("mouseenter", () => { card.style.transform = "scale(1.02)"; });
    card.addEventListener("mouseleave", () => { card.style.transform = "scale(1)"; });

    container.appendChild(card);
  }

  if (container.childElementCount === 0) return false;

  messageEl.appendChild(container);
  return true;
}

function extractFirstVideoUrlFromElement(rootElement) {
  if (!rootElement || typeof rootElement.querySelectorAll !== "function") return "";
  const anchors = rootElement.querySelectorAll("a");
  for (const a of anchors) {
    const href = String(a.getAttribute("href") || a.href || "").trim();
    if (href && isVideoUrl(href)) return href;
  }
  return "";
}

function wireVideoReopenLink(rootElement, apiPayload) {
  if (!rootElement || !apiPayload || typeof apiPayload !== "object") return;
  const mr = apiPayload.modal_request;
  const type = String(mr?.type || "").trim().toLowerCase();
  if (type !== "video") return;
  const modalUrl = canonicalWatchUrlFromModalRequest(mr);
  const anchors = rootElement.querySelectorAll("a");
  anchors.forEach((a) => {
    const label = String(a.textContent || "").trim().toLowerCase();
    const href = String(a.getAttribute("href") || "").trim().toLowerCase();
    const looksLikeVideoLink =
      label.includes("hier ansehen") ||
      href.includes("youtube.com") ||
      href.includes("youtu.be") ||
      href.includes("vimeo.com");
    if (!looksLikeVideoLink) return;
    a.setAttribute("href", "#");
    a.dataset.janusAction = "reopen-video-modal";
    if (modalUrl) {
      a.dataset.videoUrl = modalUrl;
    }
  });
  const hasReopenLink = rootElement.querySelector('a[data-janus-action="reopen-video-modal"]');
  if (!hasReopenLink) {
    appendVideoReopenLink(rootElement, modalUrl);
  }
}

function appendVideoReopenLink(rootElement, fallbackVideoUrl = "") {
  if (!rootElement || typeof rootElement.querySelector !== "function") return;
  const existing = rootElement.querySelector('a[data-janus-action="reopen-video-modal"]');
  const canon = String(fallbackVideoUrl || "").trim();
  const firstVideoUrl = canon || extractFirstVideoUrlFromElement(rootElement);
  if (existing) {
    if (canon) {
      existing.dataset.videoUrl = canon;
    } else if (firstVideoUrl && !existing.dataset.videoUrl) {
      existing.dataset.videoUrl = firstVideoUrl;
    }
    return;
  }
  const p = document.createElement("p");
  const a = document.createElement("a");
  a.href = "#";
  a.dataset.janusAction = "reopen-video-modal";
  if (firstVideoUrl) {
    a.dataset.videoUrl = firstVideoUrl;
  }
  a.textContent = "Video ansehen";
  p.appendChild(a);
  rootElement.appendChild(p);
}

function ensureVideoReopenLinkForStreamMessage(messageElement, modalRequest) {
  if (!messageElement || !modalRequest || typeof modalRequest !== "object") return;
  const mrType = String(modalRequest.type || "").trim().toLowerCase();
  if (mrType !== "video") return;
  const candidateUrl = canonicalWatchUrlFromModalRequest(modalRequest);
  appendVideoReopenLink(messageElement, candidateUrl);
}

function ensureVideoReopenLinkForRenderedMessage(messageElement, apiPayload) {
  if (!messageElement) return;
  const mr = apiPayload?.modal_request;
  const modalUrl = canonicalWatchUrlFromModalRequest(mr);
  if (modalUrl) {
    appendVideoReopenLink(messageElement, modalUrl);
    return;
  }
  if (!extractFirstVideoUrlFromElement(messageElement)) return;
  appendVideoReopenLink(messageElement);
}

export function appendMessage(sender, data, appendOpts = {}) {
  const windowId = appendOpts.windowId ?? getActiveWindowId();
  const chatMessages = document.getElementById(paneId("chat-messages", windowId));
  if (!chatMessages) {
    console.error("appendMessage: chat-messages not found for window", windowId);
    return;
  }
  const skipScroll = appendOpts.skipScroll === true;
  const messageContainer = document.createElement("div");
  messageContainer.classList.add("message", sender === "user" ? "user" : "assistant");

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  let textContent = "";
  let imageUrlForSaving = null;
  let fullImageUrl = null;
  const dataIsObject = typeof data === "object" && data !== null;
  const apiPayload =
    typeof data === "object" && data !== null ? data : typeof data === "string" ? { text: data } : {};

  // 🔍 FRONTEND DATA CHECK: Debug logging for Bot messages
  if (sender === "bot") {
    console.log("🔍 FRONTEND DATA CHECK:", apiPayload);
  }

  if (typeof data === "string") {
    textContent = data;
  } else if (dataIsObject) {
    textContent = data.text || "";

    // --- NEU: Filterung des Standard-Image-Analyse-Prompts ---
    // Dieser Prompt wird an die KI gesendet, sollte aber nicht im UI für den User angezeigt werden.
    const defaultImageAnalysisPrompt = "Gib eine kurze Bestätigung und die wichtigsten Merkmale des Bildes in einem Satz.";
    const hasImageMarkdown = /!\[.*?\]\((.*?)\)/.test(textContent); // Prüft, ob ein Markdown-Bild im Text ist

    if (hasImageMarkdown && textContent.includes(defaultImageAnalysisPrompt)) {
      textContent = textContent.replace(defaultImageAnalysisPrompt, '').trim();
    }
    // --- Ende der Filterung des Standard-Image-Analyse-Prompts ---

    // --- Bestehende Filterung des SYSTEM_VISION_CONTEXT (Internal AI Notes) ---
    const systemContextRegex = /<system_vision_context>[\s\S]*?<\/system_vision_context>/g;
    textContent = textContent.replace(systemContextRegex, '').trim();
    // --- Ende der Filterung des SYSTEM_VISION_CONTEXT ---

    // NEU: Für DALL-E Bilder, die image_url im textContent haben
    if (textContent.includes("/user_images/") && !data.image_url && sender !== "user") {
        const imageUrlRegex = /(\/user_images\/[^\s)\]]+)/; 
        const match = textContent.match(imageUrlRegex);
        if (match && match[1]) {
            const relativeImageUrl = match[1];
            fullImageUrl = normalizeMediaUrl(relativeImageUrl); 
            imageUrlForSaving = fullImageUrl; 

            textContent = textContent.replace(relativeImageUrl, `![Generated Image](${fullImageUrl})`);
        }
    }

    if (data.image_url) {
      fullImageUrl = normalizeMediaUrl(data.image_url);
      if (
        fullImageUrl &&
        !fullImageUrl.startsWith("http://") &&
        !fullImageUrl.startsWith("https://") &&
        !fullImageUrl.startsWith("data:")
      ) {
        fullImageUrl = API_BASE_URL + fullImageUrl;
      }
      imageUrlForSaving = fullImageUrl;
    } else if (data.image_base64 && data.mime_type) {
      fullImageUrl = "data:" + data.mime_type + ";base64," + data.image_base64;
      imageUrlForSaving = fullImageUrl;
      // Hier textContent NICHT leeren, da es den User-Prompt (falls manuell eingegeben) enthalten könnte
    }

    textContent = removePlaceholderImageMarkdown(textContent);
  }

  const isInlineImage = typeof fullImageUrl === "string" && fullImageUrl.startsWith("data:image/");
  const hasImage = !!(
    (typeof data === "object" && data !== null && data.image_url) ||
    (typeof data === "object" && data !== null && data.image_base64) ||
    textContent.includes("![")
  );

  const normalizedText = textContent.trim();
  if (
    normalizedText.startsWith("{\"query_text\"") ||
    normalizedText.startsWith("{\"tool_call\"")
  ) {
    console.warn("Technisches Tool-Fragment unterdrückt.");
    return;
  }

  if (!textContent.trim() && !hasImage) {
    console.warn("Abbruch: Leere Nachricht empfangen.");
    return;
  }

  if (isInlineImage && !textContent.includes(fullImageUrl)) {
    if (!textContent.trim()) {
      // Nur wenn KEIN anderer User-Text vorhanden ist, fügen wir den Standard-Bild-Markdown ein
      textContent = `![Hochgeladenes Bild](${fullImageUrl})`;
    } else {
      // Wenn User-Text UND Bild da sind, hängen wir das Bild einfach an
      const markdownImageRegex = /!\[.*?\]\((.*?)\)/;
            if (!markdownImageRegex.test(textContent)) {
                textContent += `\n\n![Hochgeladenes Bild](${fullImageUrl})`;
            }
        }
    }

  if (textContent) {
    console.log("Raw LLM textContent:", textContent);
    console.log("textContent before marked.parse:", textContent); // NEU
    const textNode = document.createElement("p"); // Kann auch div oder span sein, um img aufzunehmen
    textNode.innerHTML = sanitizeChatHtml(marked.parse(textContent));
    console.log("textNode.innerHTML after marked.parse:", textNode.innerHTML); // NEU
    normalizeLinksAndImages(textNode);
    hydrateVideoLinks(textNode);
    if (
      sender === "bot" &&
      apiPayload?.modal_request &&
      String(apiPayload.modal_request.type || "").trim().toLowerCase() === "video"
    ) {
      stripInlineAssistantVideoLinks(textNode);
    }
    wireVideoReopenLink(textNode, apiPayload);
    ensureVideoReopenLinkForRenderedMessage(textNode, apiPayload);
    if (
      sender === "bot" &&
      apiPayload?.video_list_metadata &&
      apiPayload.video_list_metadata.mode === "list" &&
      Array.isArray(apiPayload.video_list_metadata.videos)
    ) {
      renderVideoListCards(textNode, apiPayload.video_list_metadata);
    }
    bubble.appendChild(textNode);

    // Füge Event-Listener zu allen img-Tags innerhalb der Blase hinzu
    textNode.querySelectorAll("img").forEach(img => {
        img.addEventListener("click", (event) => {
            event.stopPropagation();
            console.log("Image clicked from marked.parse, opening modal for URL:", img.src, "Target:", event.target);
            openImageModal(img.src);
        });
        img.style.cursor = "pointer"; // Visueller Hinweis, dass es klickbar ist
    });

    // TTS: If this is a bot message and TTS is enabled, speak the text
    if (sender === "bot" && isTTSEnabled() && textContent.trim() !== "...") {
      // Remove markdown syntax for TTS
      const plainText = textContent
        .replace(/[*_~`#]/g, "") // Remove markdown formatting
        .replace(/\[([^\]]+)]\([^)]+\)/g, "$1") // Replace links with text only
        .replace(/\n+/g, " ") // Replace newlines with spaces
        .trim();

      if (plainText) {
        // Lösche den vorherigen Timer, falls die Nachricht noch streamt
        clearTimeout(ttsDebounceTimer);
        // Setze einen neuen Timer. Die Wiedergabe startet nur,
        // wenn sich der Text für 500ms nicht mehr geändert hat.
        ttsDebounceTimer = setTimeout(() => {
          const { provider: llmProvider } = effectiveProviderModelForWindow(windowId);
          speakText(plainText, "de", llmProvider);
        }, 500);
      }
    }

    if (sender === "bot" && isConsentPrompt(textContent)) {
      const consentBox = document.createElement("div");
      consentBox.classList.add("consent-actions");
      consentBox.setAttribute("data-testid", "consent-actions");

      const options = [
        { value: "1", label: "1 - Einmalig erlauben", testid: "consent-option-1" },
        { value: "2", label: "2 - Immer erlauben", testid: "consent-option-2" },
        { value: "3", label: "3 - Abbrechen", testid: "consent-option-3" },
      ];

      options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.classList.add("consent-action-btn");
        button.textContent = option.label;
        button.setAttribute("data-testid", option.testid);
        button.addEventListener("click", () => {
          const inputEl = document.getElementById(paneId("user-input", windowId));
          const formEl = document.getElementById(paneId("chat-form", windowId));
          if (inputEl) inputEl.value = option.value;
          formEl?.requestSubmit();
        });
        consentBox.appendChild(button);
      });

      bubble.appendChild(consentBox);
    }
  }

  // Provider-unabhängig: Falls ein Video-Modal geliefert wurde, immer einen
  // kurzen Reopen-Link in der Bubble anbieten (auch wenn LLM-Text keinen Link enthält).
  if (
    sender === "bot" &&
    apiPayload &&
    typeof apiPayload === "object" &&
    apiPayload.modal_request &&
    String(apiPayload.modal_request.type || "").trim().toLowerCase() === "video"
  ) {
    appendVideoReopenLink(bubble, canonicalWatchUrlFromModalRequest(apiPayload.modal_request));
  }

  // Füge den Save Image Button hinzu, falls ein Bild generiert wurde
  if (fullImageUrl && sender === "bot") { // <-- Nur wenn ein Bild da ist und von Bot
    const saveButton = document.createElement("button");
    saveButton.textContent = "Bild speichern";
    saveButton.classList.add("save-image-button");
    saveButton.onclick = () => {
      if (imageUrlForSaving) {
        window.electron.saveImage(imageUrlForSaving);
      }
    };
    bubble.appendChild(saveButton);
  }


  messageContainer.appendChild(bubble);

  const timestamp = document.createElement("div");
  timestamp.classList.add("timestamp");
  const now = new Date();
  timestamp.textContent = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
  messageContainer.appendChild(timestamp);

  chatMessages.appendChild(messageContainer);

  if (sender === "bot") {
    // Single-Mode: Normales Verhalten (Auto-Modal bei modal_request)
    // Video-List-Rendering erfolgt jetzt POST-STREAM im SSE 'done' Handler
    applyBotModalRequestFromData(apiPayload);
  }

  if (!skipScroll) {
    scrollChatToBottom({ behavior: "auto", windowId });
  }
}

window.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href') || link.href || "";
    if (href.includes('youtube.com') || href.includes('youtu.be')) {
        e.preventDefault(); e.stopPropagation();
        openModal({ type: "video", payload: { url: href } });
    }
}, true);

// 💎 MCL: Post-processing to add CSS class to "Video ansehen" links after message rendering
function applyMCLLinkStyling(messageElement) {
    if (!messageElement) return;
    messageElement.querySelectorAll('a').forEach(link => {
        if (link.innerText.trim() === 'Video ansehen') {
            link.classList.add('janus-mcl-link');
        }
    });
}

// Hook into appendMessage to apply styling after rendering
const originalAppendMessage = window.appendMessage;
if (typeof originalAppendMessage === 'function') {
    window.appendMessage = function(sender, data, opts) {
        const result = originalAppendMessage.call(this, sender, data, opts);
        // Apply styling after a short delay to ensure DOM is updated
        setTimeout(() => {
            const windowId = opts?.windowId || getActiveWindowId();
            const chatMessages = document.getElementById(paneId("chat-messages", windowId));
            if (chatMessages) {
                const lastMessage = chatMessages.lastElementChild;
                if (lastMessage) {
                    applyMCLLinkStyling(lastMessage);
                }
            }
        }, 50);
        return result;
    };
}

window.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href') || link.href || "";
    if (href.includes('youtube.com') || href.includes('youtu.be')) {
        e.preventDefault(); e.stopPropagation();
        openModal({ type: "video", payload: { url: href } });
    }
}, true);
