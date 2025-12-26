import { API_BASE_URL } from "./config.js";
import { appendMessage, chatInput } from "./chat.js";

let currentChatId = null;

const LAST_ASSISTANT_CHAT_ID_KEY = "janus_last_assistant_chat_id";
const LAST_PROJECT_CHAT_BY_PROJECT_KEY = "janus_last_project_chat_by_project";

function safeParseJson(value, fallback) {
  if (!value) return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function getLastAssistantChatId() {
  const raw = localStorage.getItem(LAST_ASSISTANT_CHAT_ID_KEY);
  if (!raw) return null;
  const parsed = parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function setLastAssistantChatId(chatId) {
  if (!chatId) return;
  localStorage.setItem(LAST_ASSISTANT_CHAT_ID_KEY, String(chatId));
}

function getLastProjectChatId(projectId) {
  if (!projectId) return null;
  const map = safeParseJson(localStorage.getItem(LAST_PROJECT_CHAT_BY_PROJECT_KEY), {});
  const raw = map[String(projectId)];
  const parsed = parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function setLastProjectChatId(projectId, chatId) {
  if (!projectId || !chatId) return;
  const map = safeParseJson(localStorage.getItem(LAST_PROJECT_CHAT_BY_PROJECT_KEY), {});
  map[String(projectId)] = chatId;
  localStorage.setItem(LAST_PROJECT_CHAT_BY_PROJECT_KEY, JSON.stringify(map));
}

function isProjectChat(chat) {
  return chat && (chat.project_id != null || chat.projectId != null);
}

document.addEventListener("DOMContentLoaded", () => {
  const newChatBtn = document.getElementById("new-chat-btn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", createNewChat);
  }
  loadChats();

  const showArchivedCheckbox = document.getElementById("show-archived-chats");
  if (showArchivedCheckbox) {
    showArchivedCheckbox.addEventListener("change", loadChats);
  }
});

export async function loadChats(clear = true, projectId = null) {
  console.log("loadChats: Function entered.");
  const showArchived = document.getElementById("show-archived-chats")?.checked || false;
  
  // Build the URL with query parameters
  let url = `${API_BASE_URL}/api/chats?include_archived=${showArchived}`;
  if (projectId) {
    url += `&project_id=${projectId}`; // Add project filter if provided
  }
  
  console.log("loadChats: Fetching chats from URL:", url);

  try {
    const response = await fetch(url);
    console.log("loadChats: Response received, response.ok:", response.ok);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    let chats = await response.json();
    console.log("loadChats: Chats received:", chats);

    if (!projectId) {
      chats = chats.filter((c) => !isProjectChat(c));
    }

    renderChatList(chats);

    if (!projectId && chats.length > 0) {
      const lastAssistantChatId = getLastAssistantChatId();
      const existsInList = lastAssistantChatId && chats.some((c) => c.id === lastAssistantChatId);
      const desiredChatId = existsInList
        ? lastAssistantChatId
        : chats.some((c) => c.id === currentChatId)
          ? currentChatId
          : chats[0].id;

      if (desiredChatId && desiredChatId !== currentChatId) {
        console.log("loadChats: Restoring assistant chat:", desiredChatId);
        loadChat(desiredChatId, { context: "assistant" });
      } else if (!currentChatId) {
        console.log("loadChats: No currentChatId, loading first assistant chat:", chats[0].id);
        loadChat(chats[0].id, { context: "assistant" });
      }
      return;
    }

    // If there's no current chat selected, and there are chats available, load the first one.
    if (chats.length > 0 && !currentChatId) {
      console.log("loadChats: No currentChatId, loading first chat:", chats[0].id);
      loadChat(chats[0].id, { context: "assistant" });
    } else if (chats.length === 0) {
      // If no chats exist, create a new one
      console.log("loadChats: No chats available, creating a new chat.");
      createNewChat(); // Call createNewChat here
    }
  } catch (error) {
    console.error("loadChats: Error loading chats:", error);
  }
}

function renderChatList(chats) {
  console.log("renderChatList: Function entered with chats:", chats);
  const chatListDiv = document.getElementById("chat-list");
  chatListDiv.innerHTML = ""; // Clear existing list

  chats.forEach((chat) => {
    console.log("renderChatList: Rendering chat item for chat ID:", chat.id, "title:", chat.title);
    const chatItem = document.createElement("div");
    chatItem.classList.add("chat-item");
    if (chat.id === currentChatId) {
      chatItem.classList.add("active");
    }
    chatItem.dataset.chatId = chat.id;
    chatItem.innerHTML = `
            <span class="chat-title">${chat.title || `Chat ${chat.id}`}</span>
            <div class="chat-options-icon">...</div>
        `;
    if (chat.is_archived) {
      chatItem.classList.add("archived-chat");
    }
    chatItem.querySelector(".chat-title").addEventListener("click", () => loadChat(chat.id));
    chatItem.querySelector(".chat-options-icon").addEventListener("click", (event) => {
      event.stopPropagation(); // Prevent chat item click
      toggleContextMenu(event, chat.id, chat.is_archived);
    });

    // Add event listeners for menu items
    chatItem.querySelectorAll(".menu-item").forEach((menuItem) => {
      menuItem.addEventListener("click", async (event) => {
        event.stopPropagation(); // Prevent chat item click and menu toggle
        const action = menuItem.dataset.action;
        const chatId = parseInt(chatItem.dataset.chatId);

        // Hide the menu after selection
        menuItem.closest(".chat-context-menu").style.display = "none";

        switch (action) {
          case "rename":
            await handleRenameChat(chatId);
            break;
          case "archive":
            await handleArchiveChat(chatId);
            break;
          case "export":
            await handleExportChat(chatId);
            break;
          case "delete":
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

  const chatTitleSpan = chatItem.querySelector(".chat-title");
  const currentTitle = chatTitleSpan.textContent;

  const inputField = document.createElement("input");
  inputField.type = "text";
  inputField.value = currentTitle;
  inputField.classList.add("chat-title-input"); // Add a class for styling

  chatTitleSpan.replaceWith(inputField);
  inputField.focus();

  const finishRename = async () => {
    const newTitle = inputField.value.trim();
    if (newTitle !== "" && newTitle !== currentTitle) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/title`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle }),
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        await loadChats(); // Reload all chats to update the list
        loadChat(chatId); // Reload the current chat to update header if active
      } catch (error) {
        console.error("Error renaming chat:", error);
        alert("Fehler beim Umbenennen des Chats.");
      }
    } else {
      // If no change or empty, revert to original title
      chatTitleSpan.textContent = currentTitle;
    }
    inputField.replaceWith(chatTitleSpan); // Revert back to span
  };

  inputField.addEventListener("blur", finishRename);
  inputField.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      inputField.removeEventListener("blur", finishRename); // Prevent blur from firing twice
      finishRename();
    }
  });
}

async function handleArchiveChat(chatId) {
  // Removed confirm() dialog
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/archive`, {
      method: "PUT",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    await loadChats();
  } catch (error) {
    console.error("Error archiving chat:", error);
    alert("Fehler beim Archivieren/De-Archivieren des Chats.");
  }
}

async function handleExportChat(chatId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/export/txt`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const contentDisposition = response.headers.get("Content-Disposition");
    let filename = `chat_${chatId}.txt`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^;"]+)"?/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error exporting chat:", error);
    alert("Fehler beim Exportieren des Chats.");
  }
}

async function handleDeleteChat(chatId) {
  // Removed confirm() dialog
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: "DELETE",
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
    console.error("Error deleting chat:", error);
    alert("Fehler beim Löschen des Chats.");
  }
}

export async function createNewChat() {
  console.log("createNewChat: Function entered.");
  try {
    const response = await fetch(`${API_BASE_URL}/api/chats`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      // Send an empty body, the backend will handle the title
      body: JSON.stringify({}),
    });
    console.log("createNewChat: response.ok =", response.ok);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const newChat = await response.json();

    // 1. Reload the chat list to include the new chat
    await loadChats();

    // 2. Explicitly load the new chat's content and set it as active
    await loadChat(newChat.id);

    chatInput.value = ""; // Clear the input field
  } catch (error) {
    console.error("createNewChat: Error creating new chat:", error);
  }
}

export async function loadChat(chatId) {
  console.log("loadChat: Function entered with chatId:", chatId);
  let options = {};
  if (arguments.length > 1 && typeof arguments[1] === "object" && arguments[1] !== null) {
    options = arguments[1];
  }

  currentChatId = chatId;

  document.querySelectorAll(".chat-item").forEach((item) => {
    item.classList.remove("active");
    if (parseInt(item.dataset.chatId) === chatId) {
      item.classList.add("active");
    }
  });

  const chatMessagesDiv = document.getElementById("chat-messages");
  chatMessagesDiv.innerHTML = "";

  try {
    const chatResponse = await fetch(`${API_BASE_URL}/api/chats/${chatId}`);
    console.log("loadChat: Chat details response received, chatResponse.ok:", chatResponse.ok);
    if (!chatResponse.ok) {
      throw new Error(`HTTP error! status: ${chatResponse.status}`);
    }
    const chatDetails = await chatResponse.json();
    console.log("loadChat: Chat details:", chatDetails);

    if (chatDetails && (chatDetails.project_id != null || chatDetails.projectId != null)) {
      const projectId = chatDetails.project_id ?? chatDetails.projectId;
      setLastProjectChatId(projectId, chatId);
    } else if (options.context === "assistant" || !options.context) {
      setLastAssistantChatId(chatId);
    }

    const chatHeaderElement = document.getElementById("chat-header");
    if (chatHeaderElement) {
      chatHeaderElement.textContent = chatDetails.title;
    } else {
      console.error("Error: chat-header element not found in loadChat!");
    }

    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`);
    console.log("loadChat: Messages response received, response.ok:", response.ok);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const messages = await response.json();
    console.log("loadChat: Messages:", messages);
    messages.forEach((msg) => {
      appendMessage(msg.sender, { text: msg.content, image_url: msg.image_path });
    });
    chatInput.value = ""; // Clear the input field when loading a new chat
  } catch (error) {
    console.error("loadChat: Error loading chat messages:", error);
  }
}

export function getCurrentChatId() {
  return currentChatId;
}

if (typeof window !== "undefined") {
  window.chatManager = window.chatManager || {};
  window.chatManager.loadChats = loadChats;
  window.chatManager.loadChat = loadChat;
  window.chatManager.createNewChat = createNewChat;
  window.chatManager.getCurrentChatId = getCurrentChatId;
  window.chatManager.getLastProjectChatId = getLastProjectChatId;
  window.chatManager.setLastProjectChatId = setLastProjectChatId;
}

let activeContextMenu = null; // To keep track of the currently open context menu

function toggleContextMenu(event, chatId, chatIsArchived) {
  // Hide any other open context menus
  if (activeContextMenu && activeContextMenu !== event.target.nextElementSibling) {
    activeContextMenu.style.display = "none";
  }

  const iconElement = event.target;
  const menu = createContextMenu(chatId, chatIsArchived); // Create the menu

  // Position the menu
  const rect = iconElement.getBoundingClientRect();
  menu.style.position = "fixed";
  menu.style.top = `${rect.bottom + window.scrollY}px`;
  menu.style.left = `${rect.left + window.scrollX}px`;
  menu.style.display = "block";

  document.body.appendChild(menu); // Append to body to avoid z-index issues
  activeContextMenu = menu;

  // Close menu when clicking outside
  const clickOutsideHandler = (e) => {
    if (!menu.contains(e.target) && e.target !== iconElement) {
      menu.style.display = "none";
      document.removeEventListener("click", clickOutsideHandler);
      activeContextMenu = null;
    }
  };
  document.addEventListener("click", clickOutsideHandler);
}

function createContextMenu(chatId, chatIsArchived) {
  const menu = document.createElement("div");
  menu.classList.add("chat-context-menu");

  const menuItems = [
    { action: "rename", text: "Umbenennen" },
    { action: "archive", text: chatIsArchived ? "De-Archivieren" : "Archivieren" },
    { action: "export", text: "Als TXT speichern" },
    { action: "delete", text: "Löschen" },
  ];

  menuItems.forEach((itemData) => {
    const menuItem = document.createElement("div");
    menuItem.classList.add("menu-item");
    menuItem.dataset.action = itemData.action;
    menuItem.textContent = itemData.text;
    menuItem.addEventListener("click", async (event) => {
      event.stopPropagation(); // Prevent menu from closing immediately
      menu.style.display = "none"; // Hide menu after click
      activeContextMenu = null;

      switch (itemData.action) {
        case "rename":
          await handleRenameChat(chatId);
          break;
        case "archive":
          await handleArchiveChat(chatId);
          break;
        case "export":
          await handleExportChat(chatId);
          break;
        case "delete":
          await handleDeleteChat(chatId);
          break;
      }
    });
    menu.appendChild(menuItem);
  });

  return menu;
}
