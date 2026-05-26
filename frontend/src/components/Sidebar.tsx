import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import type { Theme, CSSObject } from '@mui/material/styles';
import {
  Box,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  IconButton,
  Typography,
  Modal,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChatBubbleOutline as ChatIcon,
  Folder as ProjectIcon,
  Folder as FolderIcon,
  Add as AddIcon,
  PhotoCamera as PhotoCameraIcon, // NEU
} from '@mui/icons-material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import type { Project } from '../types/project';

const drawerWidth = 240;

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
});

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: `calc(${theme.spacing(7)} + 1px)`,
  [theme.breakpoints.up('sm')]: {
    width: `calc(${theme.spacing(8)} + 1px)`,
  },
});

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
}));

interface SidebarProps {
  projects: Project[];
  onSelectProject: (projectId: number) => void;
  onCreateProject: (name: string, description: string) => Promise<void>;
  onOpenImageStudio: () => void; // NEU
  onOpenKnowledgeCenter: () => void;
  costData?: { total_cost: number; input_tokens: number; output_tokens: number } | null;
}

interface ModelCostSummary {
  model: string;
  total_cost: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens_saved: number;
  total_cost_saved: number;
  image_count: number;
  search_count: number;
}

const Sidebar: React.FC<SidebarProps> = ({ projects, onSelectProject, onCreateProject, onOpenImageStudio, onOpenKnowledgeCenter, costData }) => {
  const [open, setOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCostModalOpen, setIsCostModalOpen] = useState(false);
  const [modelSummary, setModelSummary] = useState<ModelCostSummary[]>([]);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const fetchModelSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const res = await fetch('/api/system/costs/summary-by-model');
      if (res.ok) {
        const data = await res.json();
        setModelSummary(data.filter((e: ModelCostSummary) => e.model !== '__WEB_SEARCHES__'));
      }
    } catch (_) {
      // silent
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  const handleOpenCostModal = () => {
    setIsCostModalOpen(true);
    fetchModelSummary();
  };
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const navigate = useNavigate();

  const handleCreateProject = async () => {
    if (projectName.trim()) {
      await onCreateProject(projectName, projectDescription);
      setProjectName('');
      setProjectDescription('');
      setIsModalOpen(false);
    }
  };

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  const handleProjectClick = (projectId: number) => {
    onSelectProject(projectId);
    navigate(`/project/${projectId}`);
  };

  const handleChatClick = () => {
    navigate('/');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <ProjectModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreateProject}
        projectName={projectName}
        projectDescription={projectDescription}
        setProjectName={setProjectName}
        setProjectDescription={setProjectDescription}
      />
      <Drawer
        variant="permanent"
        open={open}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
          ...(open && {
            ...openedMixin,
            '& .MuiDrawer-paper': openedMixin,
          }),
          ...(!open && {
            ...closedMixin,
            '& .MuiDrawer-paper': closedMixin,
          }),
        }}
      >
        <DrawerHeader>
          <IconButton onClick={handleDrawerToggle}>
            <MenuIcon />
          </IconButton>
        </DrawerHeader>
        <Divider />
        <List>
          <ListItem disablePadding sx={{ display: 'block' }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
              onClick={() => setIsModalOpen(true)}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                <AddIcon />
              </ListItemIcon>
              <ListItemText primary="Neues Projekt" sx={{ opacity: open ? 1 : 0 }} />
            </ListItemButton>
          </ListItem>
        </List>
        <Divider />
        <List>
          <ListItem key="chats" disablePadding sx={{ display: 'block' }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
              onClick={handleChatClick}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                <ChatIcon />
              </ListItemIcon>
              <ListItemText primary="Chats" sx={{ opacity: open ? 1 : 0 }} />
            </ListItemButton>
          </ListItem>

          <ListItem key="knowledge" disablePadding sx={{ display: 'block', mb: 1 }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                py: 1.5,
                px: 2.5,
                borderRadius: '12px',
              }}
              onClick={onOpenKnowledgeCenter}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                  '& .MuiSvgIcon-root': {
                    color: 'primary.main',
                  },
                }}
              >
                <AutoStoriesIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="Wissensdatenbank"
                primaryTypographyProps={{ fontSize: '0.9rem', fontWeight: 'bold' }}
                sx={{ opacity: open ? 1 : 0 }}
              />
            </ListItemButton>
          </ListItem>

          {/* NEUER EINTRAG */}
          <ListItem key="image-studio" disablePadding sx={{ display: 'block' }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
              onClick={onOpenImageStudio}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                <PhotoCameraIcon />
              </ListItemIcon>
              <ListItemText primary="Image Studio" sx={{ opacity: open ? 1 : 0 }} />
            </ListItemButton>
          </ListItem>
          
          <Divider sx={{ my: 1 }} />
          
          <ListItem key="projects-header" sx={{ display: 'block' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', px: 2.5, py: 1 }}>
              <ProjectIcon sx={{ mr: 2 }} />
              {open && <Typography variant="subtitle2">Projects</Typography>}
            </Box>
          </ListItem>
          
          {projects.map((project) => (
            <ListItem key={`project-${project.id}`} disablePadding sx={{ display: 'block' }}>
              <ListItemButton
                sx={{
                  minHeight: 48,
                  justifyContent: open ? 'initial' : 'center',
                  px: 2.5,
                }}
                onClick={() => handleProjectClick(project.id)}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: open ? 3 : 'auto',
                    justifyContent: 'center',
                  }}
                >
                  <FolderIcon />
                </ListItemIcon>
                <ListItemText 
                  primary={project.name} 
                  sx={{ opacity: open ? 1 : 0 }} 
                  primaryTypographyProps={{
                    noWrap: true,
                    textOverflow: 'ellipsis',
                    overflow: 'hidden',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
          
          <ListItem disablePadding sx={{ display: 'block' }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
              onClick={() => {}}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                <AddIcon />
              </ListItemIcon>
              <ListItemText 
                primary="New Project" 
                sx={{ opacity: open ? 1 : 0 }} 
              />
            </ListItemButton>
          </ListItem>
          
          {/* Cost Display — klickbar öffnet Kosten-Modal */}
          {costData && open && (
            <ListItem sx={{ display: 'block', mt: 2 }}>
              <Box
                onClick={handleOpenCostModal}
                sx={{ px: 2.5, py: 1, backgroundColor: 'grey.100', borderRadius: 1, cursor: 'pointer', '&:hover': { backgroundColor: 'grey.200' } }}
              >
                <Typography variant="caption" color="text.secondary">
                  💰 Session Kosten
                </Typography>
                <Typography variant="body2" fontWeight="bold" color="primary.main">
                  € {costData.total_cost.toFixed(4)}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  {costData.input_tokens + costData.output_tokens} Tokens · Details →
                </Typography>
              </Box>
            </ListItem>
          )}
        </List>
      </Drawer>

      {/* ── Kosten-Detail-Modal ── */}
      <Modal open={isCostModalOpen} onClose={() => setIsCostModalOpen(false)}>
        <Box sx={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          width: 560, maxHeight: '80vh', overflowY: 'auto',
          bgcolor: 'background.paper', borderRadius: 2, boxShadow: 24, p: 3,
        }}>
          <Typography variant="h6" fontWeight="bold" mb={2}>
            📊 Kostenübersicht – dieser Monat
          </Typography>

          {summaryLoading && <LinearProgress sx={{ mb: 2 }} />}

          {!summaryLoading && modelSummary.length === 0 && (
            <Typography variant="body2" color="text.secondary">Noch keine Daten für diesen Monat.</Typography>
          )}

          {modelSummary.map((row) => {
            const efficiencyPct = row.total_cost > 0
              ? Math.round((row.total_cost_saved / (row.total_cost + row.total_cost_saved)) * 100)
              : 0;
            const hasSavings = row.total_cost_saved > 0;
            return (
              <Box key={row.model} sx={{ mb: 2, p: 1.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" fontWeight="bold" noWrap sx={{ maxWidth: 260 }}>
                    {row.model}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold" color="error.main">
                    {row.total_cost.toFixed(4)} €
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {(row.total_input_tokens + row.total_output_tokens).toLocaleString()} Tokens
                  {' '}({row.total_input_tokens.toLocaleString()} in / {row.total_output_tokens.toLocaleString()} out)
                </Typography>
                {hasSavings && (
                  <Box sx={{ mt: 0.5 }}>
                    <Chip
                      size="small"
                      color="success"
                      variant="outlined"
                      label={`Janus Caching: -${row.total_cost_saved.toFixed(4)} € | ${efficiencyPct}% gespart`}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                )}
              </Box>
            );
          })}

          {/* Footer: Gesamtersparnis */}
          {modelSummary.length > 0 && (() => {
            const totalSaved = modelSummary.reduce((s, r) => s + r.total_cost_saved, 0);
            const totalSpent = modelSummary.reduce((s, r) => s + r.total_cost, 0);
            const totalEffPct = (totalSpent + totalSaved) > 0
              ? Math.round((totalSaved / (totalSpent + totalSaved)) * 100)
              : 0;
            return totalSaved > 0 ? (
              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'grey.300' }}>
                <Typography variant="body2" color="success.main" fontWeight="bold">
                  💚 Gesamtersparnis durch Janus Caching: {totalSaved.toFixed(4)} € ({totalEffPct}% aller Prompt-Kosten)
                </Typography>
              </Box>
            ) : null;
          })()}

          <Box sx={{ mt: 2, textAlign: 'right' }}>
            <Typography
              variant="caption"
              color="primary"
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => setIsCostModalOpen(false)}
            >
              Schließen
            </Typography>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

// Project Creation Modal
const ProjectModal: React.FC<{
  open: boolean;
  onClose: () => void;
  onCreate: (name: string, description: string) => void;
  projectName: string;
  projectDescription: string;
  setProjectName: (name: string) => void;
  setProjectDescription: (description: string) => void;
}> = ({ open, onClose, onCreate, projectName, projectDescription, setProjectName, setProjectDescription }) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: open ? 'flex' : 'none',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1300,
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        width: '400px',
        maxWidth: '90%',
      }}>
        <h2>Neues Projekt erstellen</h2>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>Projektname*</label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc',
            }}
            placeholder="Mein Projekt"
          />
        </div>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>Beschreibung</label>
          <textarea
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              minHeight: '80px',
            }}
            placeholder="Beschreibe dein Projekt..."
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              background: 'white',
              cursor: 'pointer',
            }}
          >
            Abbrechen
          </button>
          <button
            onClick={() => onCreate(projectName, projectDescription)}
            disabled={!projectName.trim()}
            style={{
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              background: '#1976d2',
              color: 'white',
              cursor: 'pointer',
              opacity: projectName.trim() ? 1 : 0.5,
            }}
          >
            Erstellen
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
