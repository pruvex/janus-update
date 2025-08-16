
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value;
    const provider = document.getElementById('provider-select').value;
    const model = document.getElementById('model-select').value;

    if (!prompt) return;

    appendMessage('user', { text: prompt });
    chatInput.value = '';

    appendMessage('bot', '...'); // Ladeanzeige

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt, provider, model }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }

        const data = await response.json();
        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', data); // Pass the whole data object
        // NEU: Rufe die Kosten-Aktualisierung auf
        if (window.fetchCostData) {
            window.fetchCostData();
        }

    } catch (error) {
        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', { text: error.message }); // Directly use error.message which contains the traceback
    }
});

function scrollToChatBottom() {
    const chatHistory = document.getElementById('chat-messages');
    setTimeout(() => {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }, 0);
}

function appendMessage(sender, data) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('chat-message'); // Add base class

    if (sender === 'user') {
        messageElement.classList.add('user-message');
    } else if (sender === 'bot') {
        messageElement.classList.add('bot-message');
    }

    let textContent = '';
    let imageUrlForSaving = null; // Declare here to be accessible later

    if (typeof data === 'string') {
        textContent = data;
    } else if (typeof data === 'object' && data !== null) {
        textContent = data.text || '';
        
        // Handle image from URL (DALL-E)
        if (data.image_url) {
            const imageElement = document.createElement('img');
            imageElement.src = data.image_url;
            imageUrlForSaving = data.image_url;
            messageElement.appendChild(imageElement);
            imageElement.onload = () => scrollToChatBottom();
            textContent = ''; // Clear textContent if image is present

        // Handle image from Base64 (Imagen)
        } else if (data.image_base64 && data.mime_type) {
            const imageElement = document.createElement('img');
            const imageDataUrl = `data:${data.mime_type};base64,${data.image_base64}`;
            imageElement.src = imageDataUrl;
            imageUrlForSaving = imageDataUrl; // The save function can handle data URLs
            messageElement.appendChild(imageElement);
            imageElement.onload = () => scrollToChatBottom();
            textContent = ''; // Clear textContent if image is present
        }

        // Common image styling and save button
        const imageInMessage = messageElement.querySelector('img');
        if (imageInMessage) {
            imageInMessage.style.maxWidth = '50%';
            imageInMessage.style.height = 'auto';
            imageInMessage.style.borderRadius = '8px';
            imageInMessage.style.display = 'block';
            imageInMessage.style.marginTop = '10px';

            const saveButton = document.createElement('button');
            saveButton.textContent = 'Bild speichern';
            saveButton.classList.add('save-image-button');
            saveButton.onclick = () => {
                if (imageUrlForSaving) {
                    window.electron.saveImage(imageUrlForSaving);
                }
            };
            messageElement.appendChild(saveButton);
        }
    }
    
    const textNode = document.createElement('p');
    textNode.innerText = textContent;
    messageElement.appendChild(textNode);

    chatMessages.appendChild(messageElement);
    scrollToChatBottom(); // Scroll after message is appended
}
