import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChatBubbleOutline as ChatIcon,
  Folder as ProjectIcon,
  Folder as FolderIcon,
  Add as AddIcon,
  PhotoCamera as PhotoCameraIcon, // NEU
} from '@mui/icons-material';
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
}

const Sidebar: React.FC<SidebarProps> = ({ projects, onSelectProject, onCreateProject, onOpenImageStudio }) => {
  console.log('Sidebar props:', { onOpenImageStudio }); // DEBUGGING
  const [open, setOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
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
        </List>
      </Drawer>
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
