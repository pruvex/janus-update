document.addEventListener('DOMContentLoaded', () => {
  const newProjectBtn = document.getElementById('new-project-btn');
  const projectModal = document.getElementById('project-modal');
  const closeProjectModalBtn = document.getElementById('close-project-modal');
  const selectProjectPathBtn = document.getElementById('select-project-path-btn');
  const projectPathInput = document.getElementById('project-path');
  const projectForm = document.getElementById('project-form');

  if (newProjectBtn) {
    newProjectBtn.addEventListener('click', () => {
      projectModal.style.display = 'block';
    });
  }

  if (closeProjectModalBtn) {
    closeProjectModalBtn.addEventListener('click', () => {
      projectModal.style.display = 'none';
    });
  }

  // Close modal when clicking outside of it
  window.addEventListener('click', (event) => {
    if (event.target === projectModal) {
      projectModal.style.display = 'none';
    }
  });

  if (selectProjectPathBtn) {
    selectProjectPathBtn.addEventListener('click', async () => {
      try {
        const path = await window.electron.openDirectoryDialog();
        if (path) {
          projectPathInput.value = path;
        }
      } catch (error) {
        console.error('Error opening directory dialog:', error);
      }
    });
  }

  if (projectForm) {
    projectForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const projectName = document.getElementById('project-name').value;
      const projectPath = projectPathInput.value;
      const provider = document.getElementById('provider-select')?.value || 'openai';
      const model = document.getElementById('model-select')?.value || 'gpt-4';

      try {
        const result = await window.electron.createProject({ 
          name: projectName,
          description: `Lokaler Pfad: ${projectPath}`,
          activeProvider: provider,
          activeModel: model
        });
        
        if (result.success) {
          console.log('Project created successfully:', result.message);
          // Custom event dispatchen, um andere Teile der App zu benachrichtigen
          const event = new CustomEvent('project-created', { detail: result.project });
          document.dispatchEvent(event);
        } else {
          console.error('Error creating project:', result.error);
        }
      } catch (error) {
        console.error('IPC Error creating project:', error);
      }

      projectModal.style.display = 'none';
      projectForm.reset();
    });
  }
});