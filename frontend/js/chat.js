import { API_BASE_URL } from './config.js';
import { getCurrentChatId, loadChats } from './chat-manager.js';
import { speakText, isTTSEnabled, initTTS, ttsPreset } from './tts.js';

// Configure marked.js for stricter Markdown parsing
marked.setOptions({
  breaks: false, // Do not convert single newlines to <br>
  gfm: true      // Use GitHub Flavored Markdown (stricter paragraph breaks)
});

// Initialize TTS on page load
document.addEventListener('DOMContentLoaded', () => {
  initTTS();
});

const chatForm = document.getElementById('chat-form');
export const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

// Event listener for opening links externally
chatMessages.addEventListener('click', (event) => {
  const target = event.target;
  if (target.tagName === 'A' && target.href) {
    event.preventDefault(); // Prevent default link navigation
    if (window.electron && window.electron.openExternal) {
      window.electron.openExternal(target.href); // Open link in external browser
    } else {
      // Fallback for web environment or if electron API is not available
      window.open(target.href, '_blank');
    }
  }
});

const imageUploadBtn = document.getElementById('image-upload-btn');
const imageUploadInput = document.getElementById('image-upload-input');

// Listener to trigger the hidden file input
imageUploadBtn.addEventListener('click', () => {
  imageUploadInput.click();
});

// Listener that handles the file selection and triggers the analysis
imageUploadInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const dataUrl = e.target.result;
    const base64 = dataUrl.split(',')[1];

    // 1. Append user's image to the UI immediately
    appendMessage('user', { 
      image_base64: base64,
      mime_type: file.type
    });

    // 2. Prepare and send the request for analysis
    const provider = document.getElementById('provider-select').value;
    const model = document.getElementById('model-select').value;
    const chat_id = getCurrentChatId();
    const defaultPrompt = 'Gib eine kurze Bestätigung und die wichtigsten Merkmale des Bildes in einem Satz.';

    const requestBody = {
      content: [
        { type: 'text', text: defaultPrompt },
        { type: 'image_url', image_url: dataUrl }
      ],
      provider,
      model,
      chat_id
    };

    // 3. Show loading indicator and send request
    appendMessage('bot', '...'); // Loading indicator
    const loadingMessageElement = chatMessages.lastChild;

    try {
      // Handle new chat title if it's a new chat
      const chatHeader = document.getElementById('chat-header');
      if (chat_id && chatHeader.textContent.trim() === 'Neuer Chat') {
        const newTitle = 'Bildanalyse';
        await fetch(`${API_BASE_URL}/api/chats/${chat_id}/title`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle }),
        });
        chatHeader.textContent = newTitle;
        await loadChats();
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Unknown error');
      }

      const data = await response.json();
      if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
        chatMessages.removeChild(loadingMessageElement);
      }
      appendMessage('bot', data);
      if (window.fetchCostData) {
        window.fetchCostData();
      }

    } catch (error) {
      if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
        chatMessages.removeChild(loadingMessageElement);
      }
      appendMessage('bot', { text: error.message });
    }
  };
    
  reader.readAsDataURL(file);
    
  // Reset the input value to allow uploading the same file again
  imageUploadInput.value = ''; 
});

// The form submission now only handles text messages
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const promptText = chatInput.value;
  if (!promptText) return;

  const provider = document.getElementById('provider-select').value;
  const model = document.getElementById('model-select').value;
  const chat_id = getCurrentChatId();

  // 1. Append user message to UI
  appendMessage('user', { text: promptText });
  chatInput.value = '';

  // 2. Prepare request body for API (text only)
  const requestBody = { 
    content: [{ type: 'text', text: promptText }],
    provider, 
    model, 
    chat_id 
  };

  // 3. Show loading indicator and send request
  appendMessage('bot', '...'); // Loading indicator
  const loadingMessageElement = chatMessages.lastChild;

  try {
    // Handle new chat title
    const chatHeader = document.getElementById('chat-header');
    if (chat_id && chatHeader.textContent.trim() === 'Neuer Chat') {
      const newTitle = promptText.substring(0, 50);
      await fetch(`${API_BASE_URL}/api/chats/${chat_id}/title`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });
      chatHeader.textContent = newTitle;
      await loadChats();
    }

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Unknown error');
    }

    const data = await response.json();
    if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
      chatMessages.removeChild(loadingMessageElement);
    }
    appendMessage('bot', data);
    if (window.fetchCostData) {
      window.fetchCostData();
    }

  } catch (error) {
    if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages) {
      chatMessages.removeChild(loadingMessageElement);
    }
    appendMessage('bot', { text: error.message });
  }
});

// --- START: SPEECH-TO-TEXT IMPLEMENTATION ---
const micBtn = document.getElementById('mic-btn');
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

micBtn.addEventListener('click', async () => {
  if (!isRecording) {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.addEventListener('dataavailable', event => {
        audioChunks.push(event.data);
      });

      mediaRecorder.addEventListener('stop', async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        // Show visual feedback that transcription is in progress
        chatInput.placeholder = 'Transkribiere Audio...';
        micBtn.textContent = '⏳';

        try {
          const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Fehler bei der Transkription.');
          }

          const data = await response.json();
          chatInput.value = data.transcription;

        } catch (error) {
          console.error('Transcription error:', error);
          alert(`Fehler: ${error.message}`);
        } finally {
          // Reset UI
          chatInput.placeholder = 'Nachricht an Janus senden...';
          micBtn.textContent = '🎤';
          audioChunks = [];
        }
      });

      mediaRecorder.start();
      isRecording = true;
      micBtn.style.color = 'red';
      micBtn.textContent = '🛑'; // Change icon to stop

    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Mikrofonzugriff verweigert. Bitte erlaube den Zugriff in den Browser-Einstellungen.');
    }
  } else {
    // Stop recording
    mediaRecorder.stop();
    isRecording = false;
    micBtn.style.color = ''; // Reset color
    micBtn.textContent = '🎤'; // Change icon back to mic
  }
});
// --- END: SPEECH-TO-TEXT IMPLEMENTATION ---

function scrollToChatBottom() {
  const chatHistory = document.getElementById('chat-messages');
  setTimeout(() => {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }, 0);
}

export function appendMessage(sender, data) {
  const messageContainer = document.createElement('div');
  messageContainer.classList.add('message', sender === 'user' ? 'user' : 'assistant');

  const bubble = document.createElement('div');
  bubble.classList.add('bubble');

  let textContent = '';
  let imageUrlForSaving = null;

  if (typeof data === 'string') {
    textContent = data;
  } else if (typeof data === 'object' && data !== null) {
    textContent = data.text || '';

    let imageElement = null;

    if (data.image_url) {
      imageElement = document.createElement('img');
      let fullImageUrl = data.image_url.replace(/\\/g, '/');
      if (!fullImageUrl.startsWith('http://') && !fullImageUrl.startsWith('https://')) {
        fullImageUrl = API_BASE_URL + fullImageUrl;
      }
      imageElement.src = fullImageUrl;
      imageUrlForSaving = fullImageUrl;
    } else if (data.image_base64 && data.mime_type) {
      imageElement = document.createElement('img');
      const imageDataUrl = 'data:' + data.mime_type + ';base64,' + data.image_base64;
      imageElement.src = imageDataUrl;
      imageUrlForSaving = imageDataUrl;
      textContent = '';
    }

    if (imageElement) {
      imageElement.onload = () => scrollToChatBottom();
      bubble.appendChild(imageElement);

      if (sender === 'bot') {
        const saveButton = document.createElement('button');
        saveButton.textContent = 'Bild speichern';
        saveButton.classList.add('save-image-button');
        saveButton.onclick = () => {
          if (imageUrlForSaving) {
            window.electron.saveImage(imageUrlForSaving);
          }
        };
        bubble.appendChild(saveButton);
      }
    }
  }

  if (textContent) {
    console.log('Raw LLM textContent:', textContent); // Added for debugging
    const textNode = document.createElement('p');
    textNode.innerHTML = marked.parse(textContent); // Changed to innerHTML and marked.parse
    bubble.appendChild(textNode);
    
    // TTS: If this is a bot message and TTS is enabled, speak the text
    if (sender === 'bot' && isTTSEnabled() && textContent.trim() !== '...') {
      // Remove markdown syntax for TTS
      const plainText = textContent
        .replace(/[*_~`#]/g, '')  // Remove markdown formatting
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')  // Replace links with text only
        .replace(/\n+/g, ' ')  // Replace newlines with spaces
        .trim();
      
      if (plainText) {
        speakText(plainText, 'de', ttsPreset || 'assistenz'); // Pass preset to speakText
      }
    }
  }

  messageContainer.appendChild(bubble);

  const timestamp = document.createElement('div');
  timestamp.classList.add('timestamp');
  const now = new Date();
  timestamp.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  messageContainer.appendChild(timestamp);

  chatMessages.appendChild(messageContainer);
  scrollToChatBottom();
}