import { API_BASE_URL } from "./config.js";

// Function to render the project dashboard
export function renderProjectDashboard(project) {
    const titleElement = document.getElementById('project-dashboard-title');
    if (titleElement) {
        titleElement.textContent = project.name || 'Project Dashboard';
    }

    // Load project chats
    loadProjectChats(project.id);
    
    // Setup drag and drop for file uploads
    setupDragAndDrop(project.id);
}

// Load chats specific to a project
async function loadProjectChats(projectId, ensureOne = true) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chats?project_id=${projectId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const chats = await response.json();

        if (ensureOne && (!chats || chats.length === 0)) {
            const createResponse = await fetch(`${API_BASE_URL}/api/chats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId,
                    title: `Chat ${new Date().toLocaleString()}`
                }),
            });

            if (createResponse.ok) {
                await loadProjectChats(projectId, false);
                return;
            }
        }

        renderProjectChatList(chats, projectId);
        if (window.chatManager && typeof window.chatManager.loadChat === 'function' && chats && chats.length > 0) {
            const lastProjectChatId = window.chatManager.getLastProjectChatId
                ? window.chatManager.getLastProjectChatId(projectId)
                : null;
            const desiredChatId = (lastProjectChatId && chats.some(c => c.id === lastProjectChatId))
                ? lastProjectChatId
                : chats[0].id;

            window.chatManager.loadChat(desiredChatId, { context: 'project', projectId });
        }
    } catch (error) {
        console.error('Error loading project chats:', error);
    }
}

// Render the list of chats in the project
function renderProjectChatList(chats, projectId) {
    const chatListContainer = document.getElementById('project-chat-list');
    if (!chatListContainer) return;

    chatListContainer.innerHTML = ''; // Clear existing content

    if (!chats || chats.length === 0) {
        chatListContainer.innerHTML = '<p>No chats found in this project.</p>';
        return;
    }

    const ul = document.createElement('ul');
    chats.forEach(chat => {
        const li = document.createElement('li');
        li.textContent = chat.title || `Chat ${chat.id}`;
        li.addEventListener('click', () => {
            // Load the chat in the main chat view
            if (window.chatManager && typeof window.chatManager.loadChat === 'function') {
                window.chatManager.loadChat(chat.id, { context: 'project', projectId });
                // Switch back to chat view
            }
        });
        ul.appendChild(li);
    });
    chatListContainer.appendChild(ul);
}

// Set up drag and drop for file uploads
function setupDragAndDrop(projectId) {
    const dropzone = document.getElementById('project-files-dropzone');
    if (!dropzone) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropzone.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropzone.classList.add('highlight');
    }

    function unhighlight() {
        dropzone.classList.remove('highlight');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files, projectId);
    }
}

// Handle file uploads
async function handleFiles(files, projectId) {
    const formData = new FormData();
    
    // Add files to form data
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    // Add project ID to form data
    formData.append('project_id', projectId);

    try {
        const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/files`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Files uploaded successfully:', result);
        // Refresh file list
        loadProjectFiles(projectId);
    } catch (error) {
        console.error('Error uploading files:', error);
    }
}

// Load files for a project
async function loadProjectFiles(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/files`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const files = await response.json();
        renderProjectFiles(files);
    } catch (error) {
        console.error('Error loading project files:', error);
    }
}

// Render the list of files in the project
function renderProjectFiles(files) {
    const filesList = document.getElementById('project-files-list');
    if (!filesList) return;

    filesList.innerHTML = ''; // Clear existing content

    if (!files || files.length === 0) {
        filesList.innerHTML = '<p>No files found in this project.</p>';
        return;
    }

    const ul = document.createElement('ul');
    files.forEach(file => {
        const li = document.createElement('li');
        li.textContent = file.name || `File ${file.id}`;
        // Add click handler to view/download file
        li.addEventListener('click', () => {
            // Implement file view/download logic here
            console.log('File clicked:', file);
        });
        ul.appendChild(li);
    });
    filesList.appendChild(ul);
}

window.renderProjectDashboard = renderProjectDashboard;
window.projectDashboard = window.projectDashboard || {};
window.projectDashboard.loadProjectFiles = loadProjectFiles;

// Listen for view switch events
document.addEventListener('switchView', (event) => {
    if (event.detail && event.detail.view) {
        const viewName = event.detail.view;
        const data = event.detail.chatId ? { chatId: event.detail.chatId } : null;
        
        // Get the switchView function from the global scope or window object
        if (typeof window.switchView === 'function') {
            window.switchView(viewName, data);
        }
    }
});
