import { API_BASE_URL } from './config.js';
import { appendMessage, chatInput } from './chat.js';

let currentChatId = null;

document.addEventListener('DOMContentLoaded', () => {
  const newChatBtn = document.getElementById('new-chat-btn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', createNewChat);
  }
  setTimeout(loadChats, 2000);

  const showArchivedCheckbox = document.getElementById('show-archived-chats');
  if (showArchivedCheckbox) {
    showArchivedCheckbox.addEventListener('change', loadChats);
  }
});

export async function loadChats() {
  const showArchived = document.getElementById('show-archived-chats')?.checked || false;
  const url = `${API_BASE_URL}/api/chats?include_archived=${showArchived}`;

  try {
    const response = await fetch(url);
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
    chatItem.innerHTML = `
            <span class="chat-title">${chat.title || `Chat ${chat.id}`}</span>
            <div class="chat-options-icon">...</div>
        `;
    if (chat.is_archived) {
      chatItem.classList.add('archived-chat');
    }
    chatItem.querySelector('.chat-title').addEventListener('click', () => loadChat(chat.id));
    chatItem.querySelector('.chat-options-icon').addEventListener('click', (event) => {
      event.stopPropagation(); // Prevent chat item click
      toggleContextMenu(event, chat.id, chat.is_archived);
    });

    // Add event listeners for menu items
    chatItem.querySelectorAll('.menu-item').forEach(menuItem => {
      menuItem.addEventListener('click', async (event) => {
        event.stopPropagation(); // Prevent chat item click and menu toggle
        const action = menuItem.dataset.action;
        const chatId = parseInt(chatItem.dataset.chatId);

        // Hide the menu after selection
        menuItem.closest('.chat-context-menu').style.display = 'none';

        switch (action) {
        case 'rename':
          await handleRenameChat(chatId);
          break;
        case 'archive':
          await handleArchiveChat(chatId);
          break;
        case 'export':
          await handleExportChat(chatId);
          break;
        case 'delete':
          await handleDeleteChat(chatId);
          break;
        }
      });
    });

    chatListDiv.appendChild(chatItem);
  });
}

async function handleRenameChat(chatId) {
  const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
  if (!chatItem) return;

  const chatTitleSpan = chatItem.querySelector('.chat-title');
  const currentTitle = chatTitleSpan.textContent;

  const inputField = document.createElement('input');
  inputField.type = 'text';
  inputField.value = currentTitle;
  inputField.classList.add('chat-title-input'); // Add a class for styling

  chatTitleSpan.replaceWith(inputField);
  inputField.focus();

  const finishRename = async () => {
    const newTitle = inputField.value.trim();
    if (newTitle !== '' && newTitle !== currentTitle) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/title`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle })
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        await loadChats(); // Reload all chats to update the list
        loadChat(chatId); // Reload the current chat to update header if active
      } catch (error) {
        console.error('Error renaming chat:', error);
        alert('Fehler beim Umbenennen des Chats.');
      }
    } else {
      // If no change or empty, revert to original title
      chatTitleSpan.textContent = currentTitle;
    }
    inputField.replaceWith(chatTitleSpan); // Revert back to span
  };

  inputField.addEventListener('blur', finishRename);
  inputField.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      inputField.removeEventListener('blur', finishRename); // Prevent blur from firing twice
      finishRename();
    }
  });
}

async function handleArchiveChat(chatId) {
  // Removed confirm() dialog
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/archive`, {
      method: 'PUT'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    await loadChats();
  } catch (error) {
    console.error('Error archiving chat:', error);
    alert('Fehler beim Archivieren/De-Archivieren des Chats.');
  }
}

async function handleExportChat(chatId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/export/txt`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `chat_${chatId}.txt`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^;"]+)"?/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exporting chat:', error);
    alert('Fehler beim Exportieren des Chats.');
  }
}

async function handleDeleteChat(chatId) {
  // Removed confirm() dialog
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    await loadChats();
    // If the deleted chat was the current one, load the most recent one or create new
    if (chatId === currentChatId) {
      currentChatId = null; // Reset current chat
      loadChats(); // This will load the most recent or create new
    }
  } catch (error) {
    console.error('Error deleting chat:', error);
    alert('Fehler beim Löschen des Chats.');
  }
}

export async function createNewChat() {
  console.log('createNewChat: Function entered.');
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title: 'Neuer Chat' }),
    });
    console.log('createNewChat: response.ok =', response.ok);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const newChat = await response.json();
    document.getElementById('chat-header').textContent = newChat.title;
    await loadChats();
    loadChat(newChat.id);
    chatInput.value = ''; // Clear the input field
  } catch (error) {
    console.error('createNewChat: Error creating new chat:', error);
  }
}

export async function loadChat(chatId) {
  currentChatId = chatId;
  document.querySelectorAll('.chat-item').forEach(item => {
    item.classList.remove('active');
    if (parseInt(item.dataset.chatId) === chatId) {
      item.classList.add('active');
    }
  });

  const chatMessagesDiv = document.getElementById('chat-messages');
  chatMessagesDiv.innerHTML = '';

  try {
    const chatResponse = await fetch(`${API_BASE_URL}/api/chats/${chatId}`);
    if (!chatResponse.ok) {
      throw new Error(`HTTP error! status: ${chatResponse.status}`);
    }
    const chatDetails = await chatResponse.json();
    const chatHeaderElement = document.getElementById('chat-header');
    if (chatHeaderElement) {
      chatHeaderElement.textContent = chatDetails.title;
    } else {
      console.error('Error: chat-header element not found in loadChat!');
    }

    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const messages = await response.json();
    messages.forEach(msg => {
      appendMessage(msg.sender, { text: msg.content, image_url: msg.image_path });
    });
    chatInput.value = ''; // Clear the input field when loading a new chat
  } catch (error) {
    console.error('Error loading chat messages:', error);
  }
}

export function getCurrentChatId() {
  return currentChatId;
}

let activeContextMenu = null; // To keep track of the currently open context menu

function toggleContextMenu(event, chatId, chatIsArchived) {
  // Hide any other open context menus
  if (activeContextMenu && activeContextMenu !== event.target.nextElementSibling) {
    activeContextMenu.style.display = 'none';
  }

  const iconElement = event.target;
  const menu = createContextMenu(chatId, chatIsArchived); // Create the menu

  // Position the menu
  const rect = iconElement.getBoundingClientRect();
  menu.style.position = 'fixed';
  menu.style.top = `${rect.bottom + window.scrollY}px`;
  menu.style.left = `${rect.left + window.scrollX}px`;
  menu.style.display = 'block';

  document.body.appendChild(menu); // Append to body to avoid z-index issues
  activeContextMenu = menu;

  // Close menu when clicking outside
  const clickOutsideHandler = (e) => {
    if (!menu.contains(e.target) && e.target !== iconElement) {
      menu.style.display = 'none';
      document.removeEventListener('click', clickOutsideHandler);
      activeContextMenu = null;
    }
  };
  document.addEventListener('click', clickOutsideHandler);
}

function createContextMenu(chatId, chatIsArchived) {
  const menu = document.createElement('div');
  menu.classList.add('chat-context-menu');

  const menuItems = [
    { action: 'rename', text: 'Umbenennen' },
    { action: 'archive', text: chatIsArchived ? 'De-Archivieren' : 'Archivieren' },
    { action: 'export', text: 'Als TXT speichern' },
    { action: 'delete', text: 'Löschen' }
  ];

  menuItems.forEach(itemData => {
    const menuItem = document.createElement('div');
    menuItem.classList.add('menu-item');
    menuItem.dataset.action = itemData.action;
    menuItem.textContent = itemData.text;
    menuItem.addEventListener('click', async (event) => {
      event.stopPropagation(); // Prevent menu from closing immediately
      menu.style.display = 'none'; // Hide menu after click
      activeContextMenu = null;

      switch (itemData.action) {
      case 'rename':
        await handleRenameChat(chatId);
        break;
      case 'archive':
        await handleArchiveChat(chatId);
        break;
      case 'export':
        await handleExportChat(chatId);
        break;
      case 'delete':
        await handleDeleteChat(chatId);
        break;
      }
    });
    menu.appendChild(menuItem);
  });

  return menu;
}