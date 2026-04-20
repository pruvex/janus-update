// --- Imports ---
import React, { useState, useEffect, useCallback } from 'react';
import { HashRouter as Router, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Sidebar from './components/Sidebar';
import ImageStudioModal from './components/ImageStudioModal';
import ProjectDashboard from './components/ProjectDashboard';
import KnowledgeCenter from './components/KnowledgeCenter';
import ChatView from './components/ChatView';
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
const MainContent = ({
  onKnowledgeCenterOpen,
  pendingContext,
  clearPendingContext,
  costData,
  onCostUpdate,
}: {
  onKnowledgeCenterOpen: (documentId?: number) => void;
  pendingContext: { text: string; filename: string; docId: number } | undefined;
  clearPendingContext: () => void;
  costData: { total_cost: number; input_tokens: number; output_tokens: number } | null;
  onCostUpdate: (cost: { total_cost: number; input_tokens: number; output_tokens: number }) => void;
}) => {
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
        onOpenKnowledgeCenter={() => onKnowledgeCenterOpen()}
        costData={costData}
      />
      <ImageStudioModal open={isImageStudioOpen} onClose={() => setImageStudioOpen(false)} /> 
      <Box component="main" sx={{ flexGrow: 1, p: 3, backgroundColor: (theme) => theme.palette.mode === 'light' ? theme.palette.grey[100] : theme.palette.grey[900], height: '100vh', overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/project/:projectId" element={<ProjectDashboard onKnowledgeModalOpen={onKnowledgeCenterOpen} />} />
          <Route
            path="/chat/:chatId"
            element={
              <ChatView
                onKnowledgeModalOpen={onKnowledgeCenterOpen}
                pendingContext={pendingContext}
                onClearPending={clearPendingContext}
                onCostUpdate={onCostUpdate}
              />
            }
          />
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

// Main App component (unverändert)
const App = () => (
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <Router>
      <AppRouter />
    </Router>
  </ThemeProvider>
);

declare global {
  interface Window {
    openJanusKnowledge?: (documentId?: number) => void;
  }
}

const AppRouter = () => {
  const navigate = useNavigate();
  const [knowledgeVisible, setKnowledgeVisible] = useState(false);
  const [knowledgeDocId, setKnowledgeDocId] = useState<number | null>(null);
  const [pendingContext, setPendingContext] = useState<{ text: string; filename: string; docId: number } | undefined>(undefined);
  const [costData, setCostData] = useState<{ total_cost: number; input_tokens: number; output_tokens: number } | null>(null);

  useEffect(() => {
    (window as any).openJanusKnowledge = (docId?: number) => {
      console.log('!!! BRIDGE TRIGGERED: Opening Knowledge Center with ID:', docId);
      setKnowledgeDocId(docId ?? null);
      setKnowledgeVisible(true);
    };

    const handleEvent = (e: any) => {
      const id = e.detail?.documentId;
      (window as any).openJanusKnowledge(id);
    };

    window.addEventListener('open-knowledge-center', handleEvent);
    console.log('React: Bridge is ready and waiting for signals.');

    return () => window.removeEventListener('open-knowledge-center', handleEvent);
  }, []);

  const openKnowledgeCenter = useCallback((documentId?: number) => {
    setKnowledgeDocId(documentId ?? null);
    setKnowledgeVisible(true);
  }, []);

  const closeKnowledgeCenter = useCallback(() => {
    setKnowledgeVisible(false);
    setKnowledgeDocId(null);
  }, []);

  const handleDiscuss = (context: { text: string; filename: string; docId: number }) => {
    setPendingContext(context);
    closeKnowledgeCenter();
    navigate('/chat/1');
  };

  const clearPendingContext = () => {
    setPendingContext(undefined);
  };
  
  const handleCostUpdate = (cost: { total_cost: number; input_tokens: number; output_tokens: number }) => {
    setCostData(cost);
  };

  return (
    <>
      <MainContent
        onKnowledgeCenterOpen={openKnowledgeCenter}
        pendingContext={pendingContext}
        clearPendingContext={clearPendingContext}
        costData={costData}
        onCostUpdate={handleCostUpdate}
      />
      <KnowledgeCenter
        visible={knowledgeVisible}
        onClose={closeKnowledgeCenter}
        initialDocumentId={knowledgeDocId ?? undefined}
      />
    </>
  );
};

export default App;
