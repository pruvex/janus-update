import { API_BASE_URL } from './config.js';
import { updateActivePersonalityDisplay } from './settings.js';

export class PersonalitySettings {
  constructor(containerId = 'personality-settings') {
    this.container = document.getElementById(containerId);
    this.activePersonality = null;
    this.personalities = [];
        
    if (!this.container) {
      console.error('Personality settings container not found');
      return;
    }
        
    this.init();
  }
    
  async init() {
    await this.loadPersonalities();
    await this.loadActivePersonality();
    this.render();
  }
    
  async loadPersonalities() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/personalities`);
      if (!response.ok) throw new Error('Failed to load personalities');
      this.personalities = await response.json();
    } catch (error) {
      console.error('Error loading personalities:', error);
    }
  }
    
  async loadActivePersonality() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/personalities/active`);
      if (!response.ok) throw new Error('Failed to load active personality');
      const data = await response.json();
      this.activePersonality = data.active_personality_id || 'ai_assistant';
    } catch (error) {
      console.error('Error loading active personality:', error);
      this.activePersonality = 'ai_assistant';
    }
  }
    
  async setActivePersonality(personalityId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/personalities/active`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          personality_id: personalityId
        })
      });
            
      if (!response.ok) throw new Error('Failed to set active personality');
            
      this.activePersonality = personalityId;
      this.render();
      updateActivePersonalityDisplay(); // Update the display in the sidebar
            
      // Show success message
      const message = document.createElement('div');
      message.className = 'success-message';
      message.textContent = 'Persönlichkeit erfolgreich geändert';
      this.container.appendChild(message);
            
      // Remove message after 3 seconds
      setTimeout(() => {
        message.remove();
      }, 3000);
            
    } catch (error) {
      console.error('Error setting active personality:', error);
      const errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.textContent = `Fehler: ${error.message}`;
      this.container.appendChild(errorElement);
            
      // Remove error message after 5 seconds
      setTimeout(() => {
        errorElement.remove();
      }, 5000);
    }
  }
    
  render() {
    if (this.personalities.length === 0) {
      this.container.innerHTML = '<p>Keine Persönlichkeiten verfügbar.</p>';
      return;
    }
        
    let html = `
            <div class="personality-options">
                ${this.personalities.map(persona => `
                    <div class="personality-option ${this.activePersonality === persona.id ? 'active' : ''}" 
                         data-personality-id="${persona.id}">
                        <h4>${persona.name}</h4>
                        <p class="personality-description">${persona.prompt.substring(0, 100)}${persona.prompt.length > 100 ? '...' : ''}</p>
                        ${this.activePersonality === persona.id ? 
    '<span class="active-indicator">Aktiv</span>' : 
    '<button class="select-personality">Auswählen</button>'}
                    </div>
                `).join('')}
            </div>
            <div class="personality-preview">
                <h4>Vorschau</h4>
                <div class="preview-content">
                    ${this.getActivePersonalityPreview()}
                </div>
            </div>
        `;
        
    this.container.innerHTML = html;
        
    // Add event listeners
    this.container.querySelectorAll('.select-personality').forEach(button => {
      button.addEventListener('click', (e) => {
        const personalityId = e.target.closest('.personality-option').dataset.personalityId;
        this.setActivePersonality(personalityId);
      });
    });
  }
    
  getActivePersonalityPreview() {
    const persona = this.personalities.find(p => p.id === this.activePersonality);
    if (!persona) return '<p>Keine aktive Persönlichkeit ausgewählt.</p>';
        
    return `
            <h5>${persona.name}</h5>
            <p>${persona.prompt}</p>
        `;
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize if we're on the settings page
  if (document.getElementById('settings-view') && document.getElementById('personality-settings')) {
    new PersonalitySettings();
  }
});
