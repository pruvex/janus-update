// --- Imports ---
import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Sidebar from './components/Sidebar';
import ImageStudioModal from './components/ImageStudioModal';
import type { Project } from './types/project';
import { fetchProjects, createProject } from './services/api';

// --- Routes ---

// Create a theme instance (unverändert)
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});

// Main content component (logisch unverändert)
const MainContent = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isImageStudioOpen, setImageStudioOpen] = useState(false);
  const navigate = useNavigate();

  const loadProjects = async () => {
    try {
      const fetchedProjects = await fetchProjects();
      setProjects(fetchedProjects);
    } catch (error) {
      console.error("Fehler beim Laden der Projekte:", error);
    }
  };

  useEffect(() => { loadProjects(); }, []);

  const handleSelectProject = (projectId: number) => {
    const project = projects.find(p => p.id === projectId) || null;
    setSelectedProject(project);
    if (project) {
      navigate(`/project/${project.id}`);
    }
  };
  
  const handleCreateProject = async (name: string, description: string) => {
    try {
      const newProject = await createProject(name, description);
      await loadProjects();
      navigate(`/project/${newProject.id}`);
    } catch (error) {
      console.error("Fehler beim Erstellen des Projekts:", error);
    }
  };

  const handleOpenImageStudio = () => { setImageStudioOpen(true); };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar 
        projects={projects} 
        onSelectProject={handleSelectProject}
        onCreateProject={handleCreateProject}
        onOpenImageStudio={handleOpenImageStudio}
      />
      <ImageStudioModal open={isImageStudioOpen} onClose={() => setImageStudioOpen(false)} /> 
      <Box component="main" sx={{ flexGrow: 1, p: 3, backgroundColor: (theme) => theme.palette.mode === 'light' ? theme.palette.grey[100] : theme.palette.grey[900], height: '100vh', overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/project/:projectId" element={<ProjectDashboard />} />
          <Route path="/chat/:chatId" element={<ChatView />} />
        </Routes>
      </Box>
    </Box>
  );
};

// --- HomePage Komponente ---
const HomePage = () => (
  <div>
    <h1>Welcome to Janus</h1>
    <p>Select a project from the sidebar or start a new chat.</p>
  </div>
);

// Placeholder components (unverändert)
const ProjectDashboard = () => {
  const { projectId } = useParams<{ projectId: string }>();
  return (<div><h1>Project {projectId}</h1><p>Project details and content will be displayed here.</p></div>);
};
const ChatView = () => {
  const { chatId } = useParams<{ chatId: string }>();
  return (<div><h1>Chat {chatId}</h1><p>Chat interface will be displayed here.</p></div>);
};

// Main App component (unverändert)
const App = () => (
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <Router><MainContent /></Router>
  </ThemeProvider>
);

export default App;
