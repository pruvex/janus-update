const appState = {
    currentView: 'chat'
};

function render() {
    const chatView = document.getElementById('chat-view');
    const settingsView = document.getElementById('settings-view');

    if (appState.currentView === 'chat') {
        chatView.style.display = 'block';
        settingsView.style.display = 'none';
    } else {
        chatView.style.display = 'none';
        settingsView.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const settingsBtn = document.getElementById('settings-btn');
    const backToChatBtn = document.getElementById('back-to-chat-btn');

    settingsBtn.addEventListener('click', () => {
        appState.currentView = 'settings';
        render();
    });

    backToChatBtn.addEventListener('click', () => {
        appState.currentView = 'chat';
        render();
    });

    render(); // Initial render
});