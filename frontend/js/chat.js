import { API_BASE_URL } from "./config.js";
import { getCurrentChatId, loadChats } from "./chat-manager.js";
import { speakText, isTTSEnabled, initTTS, ttsPreset } from "./tts.js";

let ttsDebounceTimer;

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
  breaks: false, // Do not convert single newlines to <br>
  gfm: true, // Use GitHub Flavored Markdown (stricter paragraph breaks)
});

// Initialize TTS on page load
document.addEventListener("DOMContentLoaded", () => {
  initTTS();

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

const chatForm = document.getElementById("chat-form");
export const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

// Event listener for opening links externally
chatMessages.addEventListener("click", (event) => {
  const target = event.target;
  if (target.tagName === "A" && target.href) {
    event.preventDefault(); // Prevent default link navigation
    if (window.electron && window.electron.openExternal) {
      window.electron.openExternal(target.href); // Open link in external browser
    } else {
      // Fallback for web environment or if electron API is not available
      window.open(target.href, "_blank");
    }
  }
});

const imageUploadBtn = document.getElementById("image-upload-btn");
const imageUploadInput = document.getElementById("image-upload-input");

// Listener to trigger the hidden file input
imageUploadBtn.addEventListener("click", () => {
  imageUploadInput.click();
});

// Listener that handles the file selection and triggers the analysis
imageUploadInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const dataUrl = e.target.result;
    const base64 = dataUrl.split(",")[1];

    // 1. Append user's image to the UI immediately
    appendMessage("user", {
      image_base64: base64,
      mime_type: file.type,
    });

    // 2. Prepare and send the request for analysis
    const provider = document.getElementById("provider-select").value;
    const model = document.getElementById("model-select").value;
    const chat_id = getCurrentChatId();
    const defaultPrompt =
      "Gib eine kurze Bestätigung und die wichtigsten Merkmale des Bildes in einem Satz.";

    const requestBody = {
      content: [
        { type: "text", text: defaultPrompt },
        { type: "image_url", image_url: dataUrl },
      ],
      provider,
      model,
      chat_id,
    };

    // 3. Show loading indicator and send request
    appendMessage("bot", "..."); // Loading indicator
    const loadingMessageElement = chatMessages.lastChild;

    try {
      // Handle new chat title if it's a new chat
      const chatHeader = document.getElementById("chat-header");
      if (chat_id && chatHeader.textContent.trim() === "Neuer Chat") {
        const newTitle = "Bildanalyse";
        await fetch(`${API_BASE_URL}/api/chats/${chat_id}/title`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle }),
        });
        chatHeader.textContent = newTitle;
        await loadChats();
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
      appendMessage("bot", data);
      if (window.fetchCostData) {
        window.fetchCostData();
      }
    } catch (error) {
      if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
        chatMessages.removeChild(loadingMessageElement);
      }
      appendMessage("bot", { text: error.message });
    }
  };

  reader.readAsDataURL(file);

  // Reset the input value to allow uploading the same file again
  imageUploadInput.value = "";
});

// The form submission now only handles text messages
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const promptText = chatInput.value;
  if (!promptText) return;

  const provider = document.getElementById("provider-select").value;
  const model = document.getElementById("model-select").value;
  const chat_id = getCurrentChatId();

  // 1. Append user message to UI
  appendMessage("user", { text: promptText });
  chatInput.value = "";

  // 2. Prepare request body for API (text only)
  const requestBody = {
    content: [{ type: "text", text: promptText }],
    provider,
    model,
    chat_id,
  };

  // 3. Show loading indicator and send request
  appendMessage("bot", "..."); // Loading indicator
  const loadingMessageElement = chatMessages.lastChild;

  try {
    // Handle new chat title
    const chatHeader = document.getElementById("chat-header");
    if (chat_id && chatHeader.textContent.trim() === "Neuer Chat") {
      const newTitle = promptText.substring(0, 50);
      await fetch(`${API_BASE_URL}/api/chats/${chat_id}/title`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });
      chatHeader.textContent = newTitle;
      await loadChats();
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
    appendMessage("bot", data);
    if (window.fetchCostData) {
      window.fetchCostData();
    }
  } catch (error) {
    if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
      chatMessages.removeChild(loadingMessageElement);
    }
    appendMessage("bot", { text: error.message });
  }
});

// --- START: SPEECH-TO-TEXT IMPLEMENTATION ---
const micBtn = document.getElementById("mic-btn");
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

micBtn.addEventListener("click", async () => {
  if (!isRecording) {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.addEventListener("dataavailable", (event) => {
        audioChunks.push(event.data);
      });

      mediaRecorder.addEventListener("stop", async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        // Show visual feedback that transcription is in progress
        chatInput.placeholder = "Transkribiere Audio...";
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
          chatInput.value = data.transcription;
        } catch (error) {
          console.error("Transcription error:", error);
          alert(`Fehler: ${error.message}`);
        } finally {
          // Reset UI
          chatInput.placeholder = "Nachricht an Janus senden...";
          micBtn.textContent = "🎤";
          audioChunks = [];
        }
      });

      mediaRecorder.start();
      isRecording = true;
      micBtn.style.color = "red";
      micBtn.textContent = "🛑"; // Change icon to stop
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Mikrofonzugriff verweigert. Bitte erlaube den Zugriff in den Browser-Einstellungen.");
    }
  } else {
    // Stop recording
    mediaRecorder.stop();
    isRecording = false;
    micBtn.style.color = ""; // Reset color
    micBtn.textContent = "🎤"; // Change icon back to mic
  }
});
// --- END: SPEECH-TO-TEXT IMPLEMENTATION ---

function scrollToChatBottom() {
  const chatHistory = document.getElementById("chat-messages");
  setTimeout(() => {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }, 0);
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

export function appendMessage(sender, data) {
  const messageContainer = document.createElement("div");
  messageContainer.classList.add("message", sender === "user" ? "user" : "assistant");

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  let textContent = "";
  let imageUrlForSaving = null;
  let fullImageUrl = null;

  if (typeof data === "string") {
    textContent = data;
  } else if (typeof data === "object" && data !== null) {
    textContent = data.text || "";

    // NEU: Für DALL-E Bilder, die image_url im textContent haben
    if (textContent.includes("/user_images/") && !data.image_url && sender === "bot") {
        const imageUrlRegex = /(\/user_images\/[^\s)\]]+)/; // Sucht nach /user_images/...
        const match = textContent.match(imageUrlRegex);
        if (match && match[1]) {
            const relativeImageUrl = match[1];
            fullImageUrl = normalizeMediaUrl(relativeImageUrl); // Umwandlung in absolute URL
            imageUrlForSaving = fullImageUrl; // Auch für den Save Button speichern

            // NEU: Umschließe den relativen Pfad mit Markdown-Bild-Syntax und voller URL
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
      textContent = ""; // Bei Base64 ist kein Textinhalt vom LLM zu erwarten
    }

    // WENN ES EIN BILD GIBT, FÜGE ES ALS MARKDOWN HINZU, DAMIT MARKED.PARSE ES HANDHABT
    if (fullImageUrl && !textContent.includes(fullImageUrl)) {
        // Wenn kein Textinhalt vom LLM kam, aber ein Bild, dann füge Platzhalter-Markdown hinzu
        if (!textContent.trim()) {
            textContent = `![Generated Image](${fullImageUrl})`;
        } else {
            // Versuche, vorhandenes Markdown zu finden und zu ersetzen, falls nötig
            const markdownImageRegex = /!\[.*?\]\((.*?)\)/;
            if (!markdownImageRegex.test(textContent)) { // Nur wenn noch kein Markdown-Bild existiert
                textContent += `\n\n![Generated Image](${fullImageUrl})`;
            }
        }
    }
  }

  if (textContent) {
    console.log("Raw LLM textContent:", textContent);
    console.log("textContent before marked.parse:", textContent); // NEU
    const textNode = document.createElement("p"); // Kann auch div oder span sein, um img aufzunehmen
    textNode.innerHTML = marked.parse(textContent);
    console.log("textNode.innerHTML after marked.parse:", textNode.innerHTML); // NEU
    normalizeLinksAndImages(textNode);
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
          const llmProvider = document.getElementById("provider-select").value;
          // Rufe die eigentliche Wiedergabefunktion auf
          speakText(plainText, "de", llmProvider);
        }, 500); // Eine Verzögerung von 500ms ist ein guter Startwert
      }
    }
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
  scrollToChatBottom();
}
