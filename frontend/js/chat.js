import { API_BASE_URL } from './config.js';
import { getCurrentChatId, loadChats } from './chat-manager.js';

// Configure marked.js for stricter Markdown parsing
marked.setOptions({
  breaks: false, // Do not convert single newlines to <br>
  gfm: true      // Use GitHub Flavored Markdown (stricter paragraph breaks)
});

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
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

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value;
    const provider = document.getElementById('provider-select').value;
    const model = document.getElementById('model-select').value;
    const chat_id = getCurrentChatId(); // Get current chat ID

    if (!prompt) return;

    appendMessage('user', { text: prompt });
    chatInput.value = '';

    appendMessage('bot', '...'); // Ladeanzeige
    const loadingMessageElement = chatMessages.lastChild;

    try {
        // Check if it's a new chat and the first message
        const chatHeader = document.getElementById('chat-header');
        if (!chatHeader) {
            console.error('Error: chat-header element not found in chat.js submit handler!');
            return;
        }
        if (chat_id && chatHeader.textContent.trim() === 'Neuer Chat') {
            const newTitle = prompt.substring(0, 50); // Take first 50 chars of prompt as new title
            await fetch(`${API_BASE_URL}/api/chats/${chat_id}/title`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: newTitle }),
            });
            chatHeader.textContent = newTitle; // Direct update of header
            await loadChats(); // Refresh chat list and header
        }

        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt, provider, model, chat_id }), // Include chat_id
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }

        const data = await response.json();
        chatMessages.removeChild(chatMessages.lastChild);
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
            textContent = '';
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

    if (textContent) {
        console.log("Raw LLM textContent:", textContent); // Added for debugging
        const textNode = document.createElement('p');
        textNode.innerHTML = marked.parse(textContent); // Changed to innerHTML and marked.parse
        bubble.appendChild(textNode);
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