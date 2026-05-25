import { API_BASE_URL } from "./config.js";
import { appendMessage, getCachedVideoModalForChat, resetUserInputHeight, scrollChatToBottom } from "./chat.js";
import { sanitizeTemplateHtml } from "./dompurify-config.js";
import {
  paneId,
  getActiveWindowId,
  getActiveChatIdForWindow,
  getWindowState,
  setChatForWindow,
  setActiveWindow,
  setWindowOpen,
  setWindowLlm,
  closeSecondWindow,
  subscribeWindowState,
  syncActiveWindowDom,
  WINDOW_IDS,
} from "./window-state.js";

const LAST_ASSISTANT_CHAT_ID_KEY = "janus_last_assistant_chat_id";
const LAST_PROJECT_CHAT_BY_PROJECT_KEY = "janus_last_project_chat_by_project";
const CHAT_LIST_SORT_STORAGE_KEY = "janus_chat_list_sort_mode";

/** Letzte Assistant-Chatliste für Sortierung/Suche ohne erneuten Fetch */
let _sidebarChatsSnapshot = [];

const CHAT_CATEGORY_ORDER = ["coding", "cooking", "business", "research", "personal", "general"];
const CHAT_CATEGORY_LABELS = {
  coding: "Coding",
  cooking: "Cooking",
  business: "Business",
  research: "Research",
  personal: "Personal",
  general: "General",
};

function normalizeChatCategory(raw) {
  const s = String(raw || "general")
    .toLowerCase()
    .trim();
  if (CHAT_CATEGORY_ORDER.includes(s)) return s;
  return "general";
}

function getChatListSortMode() {
  const sel = document.getElementById("chat-list-sort-select");
  const v = sel?.value;
  if (v === "category" || v === "alphabetical" || v === "recent") return v;
  return "recent";
}

function getChatListSearchQuery() {
  const inp = document.getElementById("chat-list-search");
  return String(inp?.value || "")
    .trim()
    .toLowerCase();
}

function filterChatsBySearchQuery(chats, q) {
  if (!q) return chats;
  return chats.filter((c) => {
    const title = String(c.title || `Chat ${c.id}`).toLowerCase();
    return title.includes(q);
  });
}

function sortChatsByRecent(chats) {
  return [...chats].sort((a, b) => (b.id || 0) - (a.id || 0));
}

function sortChatsAlphabetical(chats) {
  return [...chats].sort((a, b) => {
    const ta = String(a.title || `Chat ${a.id}`).toLowerCase();
    const tb = String(b.title || `Chat ${b.id}`).toLowerCase();
    return ta.localeCompare(tb, "de", { sensitivity: "base" });
  });
}

/**
 * Sortiert Chats und teilt sie nach Backend-Kategorie (Task 027) in Ordner auf.
 * @returns {{ key: string, label: string, chats: object[] }[]}
 */
function groupChatsByCategory(chats) {
  const sorted = sortChatsByRecent(chats);
  const buckets = new Map();
  for (const key of CHAT_CATEGORY_ORDER) {
    buckets.set(key, []);
  }
  for (const chat of sorted) {
    const k = normalizeChatCategory(chat.category);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(chat);
  }
  return CHAT_CATEGORY_ORDER.filter((key) => (buckets.get(key) || []).length > 0).map((key) => ({
    key,
    label: CHAT_CATEGORY_LABELS[key] || key,
    chats: buckets.get(key) || [],
  }));
}

function updateChatInSidebarSnapshot(chatId, partial) {
  const id = Number(chatId);
  if (!Number.isFinite(id) || !partial) return;
  const row = _sidebarChatsSnapshot.find((c) => c.id === id);
  if (row) Object.assign(row, partial);
}

function rerenderChatListFromCache() {
  renderChatList(_sidebarChatsSnapshot);
}

/** Kurzes visuelles Feedback am Ziel-Chatfenster nach Sidebar-Zuweisung (Task 026). */
function flashWindowAssignFeedback(windowId) {
  const el = document.getElementById(`chat-window-${windowId}`);
  if (!el) return;
  const cls = windowId === "A" ? "janus-assign-feedback--a" : "janus-assign-feedback--b";
  el.classList.remove("janus-assign-feedback--a", "janus-assign-feedback--b");
  void el.offsetWidth;
  el.classList.add(cls);
  window.setTimeout(() => {
    el.classList.remove(cls);
  }, 750);
}

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

function normalizeChatLlmValue(value) {
  const s = String(value ?? "").trim();
  return s ? s : null;
}

function syncLoadedChatHeaderLlm(chatId, provider, model) {
  const id = Number(chatId);
  if (!Number.isFinite(id)) return;
  const normalizedProvider = normalizeChatLlmValue(provider);
  const normalizedModel = normalizeChatLlmValue(model);
  for (const wid of WINDOW_IDS) {
    if (Number(getActiveChatIdForWindow(wid)) === id) {
      setWindowLlm(wid, normalizedProvider, normalizedModel);
    }
  }
}

export async function saveChatHeaderSelection(chatId, provider, model) {
  const id = Number(chatId);
  if (!Number.isFinite(id)) return null;

  const response = await fetch(`${API_BASE_URL}/api/chats/${id}/llm`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      provider: normalizeChatLlmValue(provider),
      model: normalizeChatLlmValue(model),
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const updatedChat = await response.json();
  updateChatInSidebarSnapshot(id, {
    header_provider: updatedChat.header_provider ?? null,
    header_model: updatedChat.header_model ?? null,
  });
  syncLoadedChatHeaderLlm(
    id,
    updatedChat.header_provider ?? null,
    updatedChat.header_model ?? null
  );
  return updatedChat;
}

function getChatTitleFromSidebarList(chatId) {
  if (chatId == null) return null;
  const el = document.querySelector(`#chat-list .chat-item[data-chat-id="${chatId}"] .chat-title`);
  if (!el) return null;
  const t = el.textContent?.trim();
  return t || null;
}

function getChatTitleFromPaneHeader(windowId, chatId) {
  const header = document.getElementById(paneId("chat-header", windowId));
  const label = header?.querySelector?.(".chat-header-title-label");
  const text = label?.textContent?.trim();
  if (text) return text;
  return chatId != null ? `Chat ${chatId}` : "—";
}

/** Titel für die Active-Chat-Bar: Liste → Header im Pane → Fallback. */
function getTitleForActiveBarWindow(windowId) {
  const cid = getActiveChatIdForWindow(windowId);
  if (cid == null) return "—";
  return getChatTitleFromSidebarList(cid) || getChatTitleFromPaneHeader(windowId, cid);
}

function syncActiveChatBar() {
  const titleA = document.getElementById("active-chat-title-a");
  const titleB = document.getElementById("active-chat-title-b");
  const chipA = document.getElementById("active-chat-chip-a");
  const chipB = document.getElementById("active-chat-chip-b");
  if (!titleA || !titleB || !chipA || !chipB) return;

  const bOpen = getWindowState().windows.B.isOpen;

  titleA.textContent = getTitleForActiveBarWindow("A");
  if (!bOpen) {
    titleB.textContent = "+ Zweites Fenster";
  } else {
    titleB.textContent = getTitleForActiveBarWindow("B");
  }

  chipB.classList.toggle("active-chat-chip--b-closed", !bOpen);

  const activeW = getActiveWindowId();
  chipA.classList.toggle("active-chat-chip--focus", activeW === "A");
  chipB.classList.toggle("active-chat-chip--focus", bOpen && activeW === "B");
}

function applyWindowBHostVisibility() {
  const hostB = document.getElementById("chat-window-host-B");
  if (!hostB) return;
  const open = getWindowState().windows.B.isOpen;
  hostB.classList.toggle("chat-window-host--b-closed", !open);
  hostB.setAttribute("aria-hidden", open ? "false" : "true");
}

/**
 * Sidebar-Zeilen an `window-state` spiegeln (subscribeWindowState + nach renderChatList).
 * `chat-item--pane-a|b` = Chat in Fenster A/B geladen; `chat-item--active-focus` = Chat im fokussierten Fenster.
 */
function applyChatListWindowIndicators() {
  const idA = getActiveChatIdForWindow("A");
  const idB = getActiveChatIdForWindow("B");
  const bOpen = getWindowState().windows.B.isOpen;
  const activeW = getActiveWindowId();
  const focusedChatId = getActiveChatIdForWindow(activeW);

  document.querySelectorAll("#chat-list .chat-item").forEach((item) => {
    const cid = parseInt(item.dataset.chatId, 10);
    if (!Number.isFinite(cid)) return;

    const inA = idA != null && cid === idA;
    const inB = bOpen && idB != null && cid === idB;
    const openSomewhere = inA || inB;

    item.classList.toggle("active", openSomewhere);
    item.classList.toggle("chat-item--pane-a", inA);
    item.classList.toggle("chat-item--pane-b", inB);
    item.classList.toggle(
      "chat-item--active-focus",
      focusedChatId != null && cid === focusedChatId
    );
  });
}

export function syncSidebarWindowContextUi() {
  try {
    document.body.dataset.janusActiveWindow = getActiveWindowId();
  } catch (_) {
    /* ignore */
  }
  applyWindowBHostVisibility();
  applyChatListWindowIndicators();
  syncActiveChatBar();
}

subscribeWindowState(() => {
  syncSidebarWindowContextUi();
});

/** Verhindert parallele „leere Liste → createNewChat“-Läufe (Doppel-Anlage). */
let _autoCreateFromLoadChatsInFlight = false;

document.addEventListener("DOMContentLoaded", () => {
  const newChatBtn = document.getElementById("new-chat-btn");
  if (newChatBtn) {
    if (!newChatBtn.dataset.janusBound) {
      newChatBtn.dataset.janusBound = "1";
      newChatBtn.addEventListener("click", () => void createNewChat());
    }
  }

  document.querySelectorAll("[data-window][id^='active-chat-chip-']").forEach((btn) => {
    if (btn.dataset.janusBound) return;
    btn.dataset.janusBound = "1";
    btn.addEventListener("click", () => {
      const w = btn.getAttribute("data-window");
      if (w === "A") {
        setActiveWindow("A");
        return;
      }
      if (w === "B") {
        if (!getWindowState().windows.B.isOpen) {
          setWindowOpen("B", true);
        }
        setActiveWindow("B");
      }
    });
  });

  const closeBtnB = document.getElementById("chat-window-close-btn-B");
  if (closeBtnB && !closeBtnB.dataset.janusBound) {
    closeBtnB.dataset.janusBound = "1";
    closeBtnB.addEventListener("click", (e) => {
      e.stopPropagation();
      closeSecondWindow();
    });
  }

  syncSidebarWindowContextUi();

  // Kein loadChats() hier: app.js lädt nach Auth einmal — sonst doppelter Auto-Create.

  const showArchivedCheckbox = document.getElementById("show-archived-chats");
  if (showArchivedCheckbox) {
    showArchivedCheckbox.addEventListener("change", loadChats);
  }

  const sortSel = document.getElementById("chat-list-sort-select");
  if (sortSel && !sortSel.dataset.janusBound) {
    sortSel.dataset.janusBound = "1";
    const saved = localStorage.getItem(CHAT_LIST_SORT_STORAGE_KEY);
    if (saved === "recent" || saved === "category" || saved === "alphabetical") {
      sortSel.value = saved;
    }
    sortSel.addEventListener("change", () => {
      localStorage.setItem(CHAT_LIST_SORT_STORAGE_KEY, sortSel.value);
      rerenderChatListFromCache();
    });
  }

  const searchInp = document.getElementById("chat-list-search");
  if (searchInp && !searchInp.dataset.janusBound) {
    searchInp.dataset.janusBound = "1";
    let searchTmr = null;
    searchInp.addEventListener("input", () => {
      window.clearTimeout(searchTmr);
      searchTmr = window.setTimeout(() => rerenderChatListFromCache(), 140);
    });
  }
});

/**
 * @param {boolean} clear ungenutzt (Legacy)
 * @param {number|null} projectId
 * @param {{ suppressAutoCreate?: boolean }} [options] — bei createNewChat() immer suppressAutoCreate: true setzen
 */
export async function loadChats(clear = true, projectId = null, options = {}) {
  console.log("loadChats: Function entered.");
  const suppressAutoCreate = options.suppressAutoCreate === true;
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
      let idA = getActiveChatIdForWindow("A");
      let idB = getActiveChatIdForWindow("B");
      const bOpen = getWindowState().windows.B.isOpen;

      const chatExists = (id) => id == null || chats.some((c) => c.id === id);
      if (!chatExists(idA)) {
        setChatForWindow("A", null);
        idA = null;
      }
      if (!chatExists(idB)) {
        setChatForWindow("B", null);
        idB = null;
      }

      if (idA != null || idB != null) {
        try {
          if (idA != null) {
            await loadChat(idA, { context: "assistant", windowId: "A" });
          } else {
            const lastAssistantChatId = getLastAssistantChatId();
            const existsInList = lastAssistantChatId && chats.some((c) => c.id === lastAssistantChatId);
            const pickA = existsInList ? lastAssistantChatId : chats[0].id;
            await loadChat(pickA, { context: "assistant", windowId: "A" });
          }
          if (idB != null) {
            await loadChat(idB, {
              context: "assistant",
              windowId: "B",
              restoreClosedPane: !bOpen,
            });
          }
          syncActiveWindowDom();
        } catch (e) {
          console.warn("[loadChats] persisted workspace restore failed:", e);
        }
        return;
      }

      const lastAssistantChatId = getLastAssistantChatId();
      const existsInList = lastAssistantChatId && chats.some((c) => c.id === lastAssistantChatId);
      const idInA = getActiveChatIdForWindow("A");
      const desiredChatId = existsInList
        ? lastAssistantChatId
        : chats.some((c) => c.id === idInA)
          ? idInA
          : chats[0].id;

      if (desiredChatId && desiredChatId !== idInA) {
        console.log("loadChats: Restoring assistant chat:", desiredChatId);
        loadChat(desiredChatId, { context: "assistant", windowId: "A" });
      } else if (!idInA) {
        console.log("loadChats: No chat in pane A, loading first assistant chat:", chats[0].id);
        loadChat(chats[0].id, { context: "assistant", windowId: "A" });
      }
      return;
    }

    // If there's no current chat selected, and there are chats available, load the first one.
    const anyPane =
      getActiveChatIdForWindow("A") != null || getActiveChatIdForWindow("B") != null;
    if (chats.length > 0 && !anyPane) {
      console.log("loadChats: No chat in any pane, loading first chat:", chats[0].id);
      loadChat(chats[0].id, { context: "assistant", windowId: "A" });
    } else if (chats.length === 0 && !suppressAutoCreate) {
      if (_autoCreateFromLoadChatsInFlight) {
        console.log("loadChats: empty list but auto-create already running — skip.");
      } else {
        console.log("loadChats: No chats available, creating one (awaited).");
        _autoCreateFromLoadChatsInFlight = true;
        try {
          await createNewChat();
        } finally {
          _autoCreateFromLoadChatsInFlight = false;
        }
      }
    }
  } catch (error) {
    console.error("loadChats: Error loading chats:", error);
  }
}

/**
 * Eine Sidebar-Zeile inkl. A/B-Actions (Task 026) und Kontextmenü-Trigger.
 */
function createChatItemElement(chat) {
  const chatItem = document.createElement("div");
  chatItem.classList.add("chat-item");
  chatItem.dataset.chatId = chat.id;
  const safeTitle = sanitizeTemplateHtml(chat.title || `Chat ${chat.id}`);
  chatItem.innerHTML = `
            <div class="chat-item-main">
              <span class="chat-title">${safeTitle}</span>
            </div>
            <div class="chat-item-actions" role="group" aria-label="Chat Fenster A oder B zuweisen">
              <button type="button" class="btn-assign-a" title="In Fenster A öffnen">A</button>
              <button type="button" class="btn-assign-b" title="In Fenster B öffnen">B</button>
            </div>
            <div class="chat-options-icon">...</div>
        `;
  if (chat.is_archived) {
    chatItem.classList.add("archived-chat");
  }
  chatItem.querySelector(".chat-title").addEventListener("click", () =>
    loadChat(chat.id, { windowId: getActiveWindowId() })
  );
  chatItem.querySelector(".btn-assign-a")?.addEventListener("click", (e) => {
    e.stopPropagation();
    void (async () => {
      await loadChat(chat.id, { windowId: "A", context: "assistant" });
      setActiveWindow("A");
      flashWindowAssignFeedback("A");
    })();
  });
  chatItem.querySelector(".btn-assign-b")?.addEventListener("click", (e) => {
    e.stopPropagation();
    void (async () => {
      setWindowOpen("B", true);
      await loadChat(chat.id, { windowId: "B", context: "assistant" });
      setActiveWindow("B");
      flashWindowAssignFeedback("B");
    })();
  });
  chatItem.querySelector(".chat-options-icon").addEventListener("click", (event) => {
    event.stopPropagation();
    toggleContextMenu(event, chat.id, chat.is_archived);
  });
  return chatItem;
}

function renderChatList(chats) {
  console.log("renderChatList: Function entered with chats:", chats);
  _sidebarChatsSnapshot = Array.isArray(chats) ? chats : [];

  const chatListDiv = document.getElementById("chat-list");
  if (!chatListDiv) return;
  chatListDiv.innerHTML = "";

  const q = getChatListSearchQuery();
  const filtered = filterChatsBySearchQuery(_sidebarChatsSnapshot, q);
  const mode = getChatListSortMode();

  const appendItems = (listEl, chatList) => {
    chatList.forEach((chat) => {
      console.log("renderChatList: Rendering chat item for chat ID:", chat.id, "title:", chat.title);
      listEl.appendChild(createChatItemElement(chat));
    });
  };

  if (mode === "category") {
    const groups = groupChatsByCategory(filtered);
    if (groups.length === 0) {
      syncSidebarWindowContextUi();
      return;
    }
    groups.forEach((group) => {
      const folder = document.createElement("div");
      folder.className = "chat-folder";
      folder.dataset.categoryKey = group.key;

      const header = document.createElement("button");
      header.type = "button";
      header.className = "chat-folder__header";
      header.setAttribute("aria-expanded", "true");
      header.setAttribute(
        "aria-label",
        `Ordner ${group.label}: Inhalt ${group.chats.length} Chat(s), zuklappen`
      );
      header.innerHTML = `
        <span class="chat-folder__chevron" aria-hidden="true">▼</span>
        <span class="chat-folder__icon" aria-hidden="true">📁</span>
        <span class="chat-folder__label"></span>
        <span class="chat-folder__count"></span>
      `;
      header.querySelector(".chat-folder__label").textContent = group.label;
      header.querySelector(".chat-folder__count").textContent = String(group.chats.length);

      header.addEventListener("click", () => {
        folder.classList.toggle("chat-folder--collapsed");
        const collapsed = folder.classList.contains("chat-folder--collapsed");
        header.setAttribute("aria-expanded", collapsed ? "false" : "true");
        header.setAttribute(
          "aria-label",
          collapsed
            ? `Ordner ${group.label}: ${group.chats.length} Chat(s), aufklappen`
            : `Ordner ${group.label}: ${group.chats.length} Chat(s), zuklappen`
        );
      });

      const body = document.createElement("div");
      body.className = "chat-folder__body";
      appendItems(body, group.chats);

      folder.appendChild(header);
      folder.appendChild(body);
      chatListDiv.appendChild(folder);
    });
  } else {
    const ordered = mode === "alphabetical" ? sortChatsAlphabetical(filtered) : sortChatsByRecent(filtered);
    appendItems(chatListDiv, ordered);
  }

  syncSidebarWindowContextUi();
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
        for (const wid of WINDOW_IDS) {
          if (getActiveChatIdForWindow(wid) === chatId) {
            await loadChat(chatId, { windowId: wid });
          }
        }
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
    for (const wid of WINDOW_IDS) {
      if (getActiveChatIdForWindow(wid) === chatId) {
        setChatForWindow(wid, null);
      }
    }
    await loadChats();
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

    // 1. Liste neu laden — ohne erneuten Auto-Create bei leerer Antwort (sonst 2× POST)
    await loadChats(true, null, { suppressAutoCreate: true });

    // 2. Explicitly load the new chat's content and set it as active
    await loadChat(newChat.id, { windowId: getActiveWindowId() });

    const inp = document.getElementById(paneId("user-input", getActiveWindowId()));
    if (inp) inp.value = "";
    resetUserInputHeight(getActiveWindowId());
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

  const windowId = options.windowId ?? getActiveWindowId();

  if (
    windowId === "B" &&
    !getWindowState().windows.B.isOpen &&
    !options.restoreClosedPane
  ) {
    setWindowOpen("B", true);
  }

  const chatMessagesDiv = document.getElementById(paneId("chat-messages", windowId));
  if (!chatMessagesDiv) {
    console.error("loadChat: chat-messages pane not found for window", windowId);
    return;
  }

  setChatForWindow(windowId, chatId);
  setWindowLlm(windowId, null, null);

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

    syncLoadedChatHeaderLlm(
      chatId,
      chatDetails.header_provider ?? null,
      chatDetails.header_model ?? null
    );
    updateChatInSidebarSnapshot(chatId, {
      header_provider: chatDetails.header_provider ?? null,
      header_model: chatDetails.header_model ?? null,
    });

    const chatHeaderElement = document.getElementById(paneId("chat-header", windowId));
    if (chatHeaderElement) {
      const titleLabel = chatHeaderElement.querySelector(".chat-header-title-label");
      if (titleLabel) titleLabel.textContent = chatDetails.title;
      else chatHeaderElement.textContent = chatDetails.title;
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
    let lastAssistantIndex = -1;
    messages.forEach((msg, idx) => {
      if (String(msg.sender || "").toLowerCase() === "model") {
        lastAssistantIndex = idx;
      }
    });
    const cachedModal = getCachedVideoModalForChat(chatId);
    messages.forEach((msg, idx) => {
      let modalRequest = msg.modal_request || null;
      if (!modalRequest && cachedModal && idx === lastAssistantIndex && String(msg.sender || "").toLowerCase() === "model") {
        modalRequest = cachedModal;
      }
      appendMessage(
        msg.sender,
        {
          text: msg.content,
          image_url: msg.image_path,
          modal_request: modalRequest,
          video_list_metadata: msg.video_list_metadata || null,
        },
        { skipScroll: true, windowId }
      );
    });
    scrollChatToBottom({ behavior: "smooth", windowId });
    const inp = document.getElementById(paneId("user-input", windowId));
    if (inp) inp.value = "";
    resetUserInputHeight(windowId);
    syncSidebarWindowContextUi();
  } catch (error) {
    console.error("loadChat: Error loading chat messages:", error);
  }
}

export function getCurrentChatId() {
  return getActiveChatIdForWindow(getActiveWindowId());
}

/**
 * Aktualisiert Sidebar-Titel und ggf. Chat-Header ohne vollständiges loadChats (Smart Chat Naming).
 */
export function patchChatTitleInUI(chatId, title) {
  if (chatId == null || title == null) return;
  const id = Number(chatId);
  const safe = String(title);
  updateChatInSidebarSnapshot(id, { title: safe });

  for (const wid of WINDOW_IDS) {
    if (getActiveChatIdForWindow(wid) === id) {
      const header = document.getElementById(paneId("chat-header", wid));
      if (header) {
        const titleLabel = header.querySelector(".chat-header-title-label");
        if (titleLabel) titleLabel.textContent = safe;
        else header.textContent = safe;
      }
    }
  }
  try {
    window.dispatchEvent(
      new CustomEvent("janus:chat-title-updated", { detail: { chatId: id, title: safe } })
    );
  } catch (_) {
    /* ignore */
  }

  if (_sidebarChatsSnapshot.length > 0) {
    rerenderChatListFromCache();
  } else {
    const span = document.querySelector(`#chat-list [data-chat-id="${id}"] .chat-title`);
    if (span) span.textContent = safe;
    syncActiveChatBar();
  }
}

/**
 * Nach dem ersten Stream holt der Backend-Titel-Job den echten Namen — mehrere leichte Versuche,
 * ohne die UI zu blockieren (Background).
 */
export function scheduleSmartTitleRefresh(chatId) {
  if (chatId == null || chatId === 9999) return;
  const delaysMs = [400, 1500, 3200];
  delaysMs.forEach((delay) => {
    setTimeout(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`);
        if (!response.ok) return;
        const chat = await response.json();
        const t = chat.title;
        if (t != null && String(t).trim() !== "") {
          updateChatInSidebarSnapshot(chatId, {
            title: t,
            category: chat.category,
          });
          patchChatTitleInUI(chatId, t);
        }
      } catch (e) {
        console.warn("[TITLE-REFRESH] GET /api/chats failed:", e);
      }
    }, delay);
  });
}

if (typeof window !== "undefined") {
  window.chatManager = window.chatManager || {};
  window.chatManager.loadChats = loadChats;
  window.chatManager.loadChat = loadChat;
  window.chatManager.createNewChat = createNewChat;
  window.chatManager.getCurrentChatId = getCurrentChatId;
  window.chatManager.getLastProjectChatId = getLastProjectChatId;
  window.chatManager.setLastProjectChatId = setLastProjectChatId;
  window.chatManager.saveChatHeaderSelection = saveChatHeaderSelection;
  window.chatManager.patchChatTitleInUI = patchChatTitleInUI;
  window.chatManager.scheduleSmartTitleRefresh = scheduleSmartTitleRefresh;
  window.chatManager.syncSidebarWindowContextUi = syncSidebarWindowContextUi;
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
