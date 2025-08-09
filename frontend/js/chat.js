
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value;
    const provider = document.getElementById('provider-select').value;
    const model = document.getElementById('model-select').value;

    if (!prompt) return;

    appendMessage('user', prompt);
    chatInput.value = '';

    appendMessage('bot', '...'); // Ladeanzeige

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt, provider }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }

        const data = await response.json();
        const botMessage = data.choices[0].message.content;

        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', botMessage);

    } catch (error) {
        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', `Ein Fehler ist aufgetreten: ${error.message}`);
    }
});

function appendMessage(sender, text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.innerText = text;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
