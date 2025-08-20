
import { API_BASE_URL } from './config.js';
import { appendMessage } from './chat.js';

let currentChatId = null;

document.addEventListener('DOMContentLoaded', () => {
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }
    setTimeout(loadChats, 2000);
});

export async function loadChats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chats`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const chats = await response.json();
        renderChatList(chats);
        if (chats.length > 0 && !currentChatId) {
            // Load the most recent chat if no chat is currently selected
            loadChat(chats[0].id);
        } else if (chats.length === 0) {
            // If no chats exist, create a new one
            createNewChat();
        }
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

function renderChatList(chats) {
    const chatListDiv = document.getElementById('chat-list');
    chatListDiv.innerHTML = ''; // Clear existing list

    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.classList.add('chat-item');
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }
        chatItem.dataset.chatId = chat.id;
        chatItem.textContent = chat.title || `Chat ${chat.id}`;
        chatItem.addEventListener('click', () => loadChat(chat.id));
        chatListDiv.appendChild(chatItem);
    });
}

export async function createNewChat() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chats`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: 'Neuer Chat' }), // Default title
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const newChat = await response.json();
        document.getElementById('chat-header').textContent = newChat.title; // Update header immediately
        await loadChats(); // Reload the list to include the new chat
        loadChat(newChat.id); // Load the newly created chat
    } catch (error) {
        console.error('Error creating new chat:', error);
    }
}

export async function loadChat(chatId) {
    currentChatId = chatId;
    // Update active state in UI
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.chatId) === chatId) {
            item.classList.add('active');
        }
    });

    // Clear current messages
    const chatMessagesDiv = document.getElementById('chat-messages');
    chatMessagesDiv.innerHTML = '';

    try {
        // Fetch chat details to get the title
        const chatResponse = await fetch(`${API_BASE_URL}/api/chats/${chatId}`);
        if (!chatResponse.ok) {
            throw new Error(`HTTP error! status: ${chatResponse.status}`);
        }
        const chatDetails = await chatResponse.json();
        const chatHeaderElement = document.getElementById('chat-header');
        if (chatHeaderElement) {
            chatHeaderElement.textContent = chatDetails.title; // Update header
        } else {
            console.error('Error: chat-header element not found in loadChat!');
        }

        const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const messages = await response.json();
        messages.forEach(msg => {
            // Assuming appendMessage can handle the message structure from the backend
            // You might need to adjust appendMessage in chat.js to correctly display
            // messages loaded from the database, especially for images.
            appendMessage(msg.sender, { text: msg.content, image_url: msg.image_path });
        });
    } catch (error) {
        console.error('Error loading chat messages:', error);
    }
}

export function getCurrentChatId() {
    return currentChatId;
}


