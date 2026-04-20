function getProjectModal() {
  return document.getElementById("project-modal");
}

function syncProjectSidebarActive() {
  const modal = getProjectModal();
  const btn = document.getElementById("sidebar-nav-projects");
  const open = !!modal?.classList.contains("modal--open");
  btn?.classList.toggle("sidebar-nav-item--active", open);
}

let lastDetailProject = null;

/**
 * Right pane: welcome | create form | project detail
 * @param {'welcome'|'create'|'detail'} mode
 * @param {object} [project]  API project object for detail
 */
export function showProjectModalView(mode, project) {
  const welcome = document.getElementById("project-modal-view-welcome");
  const create = document.getElementById("project-modal-view-create");
  const detail = document.getElementById("project-modal-view-detail");
  const cancelBtn = document.getElementById("project-form-cancel");
  if (!welcome || !create || !detail) return;

  welcome.hidden = mode !== "welcome";
  create.hidden = mode !== "create";
  detail.hidden = mode !== "detail";

  if (cancelBtn) {
    cancelBtn.style.display = mode === "create" ? "" : "none";
  }

  if (mode === "detail" && project) {
    lastDetailProject = project;
    const nameEl = document.getElementById("project-detail-name");
    const descEl = document.getElementById("project-detail-description");
    const metaEl = document.getElementById("project-detail-meta");
    if (nameEl) nameEl.textContent = project.name || "";
    if (descEl) {
      const d = project.description;
      descEl.textContent = d && String(d).trim() ? d : "Keine Beschreibung.";
    }
    if (metaEl) {
      const parts = [];
      if (project.created_at) {
        try {
          parts.push(`Angelegt: ${new Date(project.created_at).toLocaleString("de-DE")}`);
        } catch (_) {
          /* ignore */
        }
      }
      if (Array.isArray(project.files)) {
        parts.push(`${project.files.length} Datei(en)`);
      }
      metaEl.textContent = parts.join(" · ") || "";
    }
  }
}

/**
 * Sync right pane when project list has loaded and modal is open.
 * @param {Array} projects  visible projects (already filtered)
 * @param {number|string|null} activeProjectId  appState.currentProjectId
 */
export function initProjectModalAfterListLoad(projects, activeProjectId) {
  const modal = getProjectModal();
  if (!modal || !modal.classList.contains("modal--open")) return;

  const cancelBtn = document.getElementById("project-form-cancel");

  if (!projects.length) {
    if (cancelBtn) cancelBtn.style.display = "none";
    showProjectModalView("create");
    return;
  }

  if (cancelBtn) cancelBtn.style.display = "";

  const active =
    activeProjectId != null
      ? projects.find((p) => Number(p.id) === Number(activeProjectId))
      : null;

  if (active) {
    showProjectModalView("detail", active);
  } else {
    showProjectModalView("welcome");
  }
}

/** Show backdrop + centered panel; use flex so .modal centering rules apply. */
export function openProjectModal() {
  const projectModal = getProjectModal();
  if (!projectModal) {
    console.warn("project-modal element not found");
    return;
  }
  projectModal.classList.add("modal--open");
  projectModal.style.display = "flex";
  syncProjectSidebarActive();
  document.dispatchEvent(new CustomEvent("project-modal-opened"));
}

export function closeProjectModal() {
  const projectModal = getProjectModal();
  if (!projectModal) return;
  projectModal.classList.remove("modal--open");
  projectModal.style.display = "none";
  syncProjectSidebarActive();
}

function projectListHasItems() {
  return document.querySelectorAll("#project-list .project-item").length > 0;
}

document.addEventListener("DOMContentLoaded", () => {
  const projectModal = getProjectModal();
  const closeProjectModalBtn = document.getElementById("close-project-modal");
  const selectProjectPathBtn = document.getElementById("select-project-path-btn");
  const projectPathInput = document.getElementById("project-path");
  const projectForm = document.getElementById("project-form");
  const newSidebarBtn = document.getElementById("new-project-btn");
  const modalNewBtn = document.getElementById("project-modal-new-btn");
  const cancelBtn = document.getElementById("project-form-cancel");
  const openWorkspaceBtn = document.getElementById("project-modal-open-workspace");

  if (newSidebarBtn) {
    newSidebarBtn.addEventListener("click", openProjectModal);
  }

  if (modalNewBtn) {
    modalNewBtn.addEventListener("click", () => {
      if (cancelBtn) cancelBtn.style.display = "";
      showProjectModalView("create");
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      if (projectListHasItems()) {
        showProjectModalView("welcome");
      } else {
        closeProjectModal();
      }
      if (projectForm) projectForm.reset();
    });
  }

  if (openWorkspaceBtn) {
    openWorkspaceBtn.addEventListener("click", () => {
      if (!lastDetailProject) return;
      if (typeof window.switchView === "function") {
        window.switchView("project", { project: lastDetailProject });
      }
      closeProjectModal();
    });
  }

  if (closeProjectModalBtn) {
    closeProjectModalBtn.addEventListener("click", () => {
      closeProjectModal();
    });
  }

  window.addEventListener("click", (event) => {
    if (event.target === projectModal) {
      closeProjectModal();
    }
  });

  if (selectProjectPathBtn) {
    selectProjectPathBtn.addEventListener("click", async () => {
      try {
        const path = await window.electron.openDirectoryDialog();
        if (path) {
          projectPathInput.value = path;
        }
      } catch (error) {
        console.error("Error opening directory dialog:", error);
      }
    });
  }

  if (projectForm) {
    projectForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const projectName = document.getElementById("project-name").value;
      const projectPath = projectPathInput.value;
      const provider = document.getElementById("provider-select")?.value || "openai";
      const model = document.getElementById("model-select")?.value || "gpt-5.4-nano";

      try {
        const result = await window.electron.createProject({
          name: projectName,
          description: `Lokaler Pfad: ${projectPath}`,
          activeProvider: provider,
          activeModel: model,
        });

        if (result.success) {
          console.log("Project created successfully:", result.message);
          document.dispatchEvent(new CustomEvent("project-created", { detail: result.project }));
        } else {
          console.error("Error creating project:", result.error);
        }
      } catch (error) {
        console.error("IPC Error creating project:", error);
      }

      projectForm.reset();
    });
  }
});
