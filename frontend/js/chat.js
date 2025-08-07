
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const providerSelect = document.getElementById('provider-select');
const chatMessages = document.getElementById('chat-messages');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value;
    const provider = providerSelect.value;

    if (!prompt) return;

    appendMessage('user', prompt);
    chatInput.value = '';

    appendMessage('bot', '...'); // Ladeanzeige

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt, provider }),
        });

        const data = await response.json();
        const botMessage = data.choices[0].message.content;

        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', botMessage);

    } catch (error) {
        console.error('Error:', error);
        // Entferne Ladeanzeige
        chatMessages.removeChild(chatMessages.lastChild);
        appendMessage('bot', 'Ein Fehler ist aufgetreten.');
    }
});

function appendMessage(sender, text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.innerText = text;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
