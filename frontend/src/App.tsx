import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Sidebar from './components/Sidebar';
import ImageStudioModal from './components/ImageStudioModal'; // NEU
import type { Project } from './types/project';

// Import API functions
import { fetchProjects, createProject } from './services/api';


// Create a theme instance
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Main content component that uses the Sidebar
const MainContent = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isImageStudioOpen, setImageStudioOpen] = useState(false); // NEU
  const navigate = useNavigate();

  // Function to load projects from the backend
  const loadProjects = async () => {
    try {
      const fetchedProjects = await fetchProjects();
      setProjects(fetchedProjects);
    } catch (error) {
      console.error("Fehler beim Laden der Projekte:", error);
    }
  };

  // Load projects when component mounts
  useEffect(() => {
    loadProjects();
  }, []);

  // Handler when a project is selected from the sidebar
  const handleSelectProject = (projectId: number) => {
    const project = projects.find(p => p.id === projectId) || null;
    setSelectedProject(project);
    if (project) {
      navigate(`/project/${project.id}`);
    }
  };
  
  // Handler for creating a new project
  const handleCreateProject = async (name: string, description: string) => {
    try {
      const newProject = await createProject(name, description);
      // Reload the project list to show the new project
      await loadProjects();
      // Optionally navigate to the new project
      navigate(`/project/${newProject.id}`);
    } catch (error) {
      console.error("Fehler beim Erstellen des Projekts:", error);
    }
  };

  // NEU: Handler zum Öffnen des Image Studios
  const handleOpenImageStudio = () => {
    setImageStudioOpen(true);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar 
        projects={projects} 
        onSelectProject={handleSelectProject}
        onCreateProject={handleCreateProject}
        onOpenImageStudio={handleOpenImageStudio} // NEU
      />
      <ImageStudioModal open={isImageStudioOpen} onClose={() => setImageStudioOpen(false)} /> 
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: 3,
          backgroundColor: (theme) => 
            theme.palette.mode === 'light'
              ? theme.palette.grey[100]
                            : theme.palette.grey[900],
          height: '100vh',
          overflow: 'auto',
        }}
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/project/:projectId" element={<ProjectDashboard />} />
          <Route path="/chat/:chatId" element={<ChatView />} />
        </Routes>
      </Box>
    </Box>
  );
};

// Placeholder components for the routes
const HomePage = () => (
  <div>
    <h1>Welcome to Janus</h1>
    <p>Select a project from the sidebar or start a new chat.</p>
  </div>
);

const ProjectDashboard = () => {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <div>
      <h1>Project {projectId}</h1>
      <p>Project details and content will be displayed here.</p>
    </div>
  );
};

const ChatView = () => {
  const { chatId } = useParams<{ chatId: string }>();
  return (
    <div>
      <h1>Chat {chatId}</h1>
      <p>Chat interface will be displayed here.</p>
    </div>
  );
};

// Main App component
const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <MainContent />
      </Router>
    </ThemeProvider>
  );
};

export default App;
