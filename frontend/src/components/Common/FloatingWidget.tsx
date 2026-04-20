import React, { useState, useRef } from 'react';
import { Paper, Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';

interface FloatingWidgetProps {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  initialWidth?: number;
  initialHeight?: number;
}

const FloatingWidget: React.FC<FloatingWidgetProps> = ({
  title,
  isOpen,
  onClose,
  children,
  initialWidth = 800,
  initialHeight = 600,
}) => {
  const [position, setPosition] = useState({
    x: window.innerWidth - initialWidth - 50,
    y: 100,
  });
  const isDragging = useRef(false);
  const dragOffset = useRef({ x: 0, y: 0 });

  if (!isOpen) return null;

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging.current) return;
    setPosition({
      x: e.clientX - dragOffset.current.x,
      y: e.clientY - dragOffset.current.y,
    });
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    dragOffset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <Paper
      elevation={8}
      sx={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: initialWidth,
        height: initialHeight,
        zIndex: 1300,
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid rgba(0,0,0,0.1)',
        resize: 'both',
        overflow: 'hidden',
      }}
    >
      <Box
        onMouseDown={handleMouseDown}
        sx={{
          p: 1,
          bgcolor: 'primary.main',
          color: 'white',
          cursor: 'move',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          userSelect: 'none',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DragIndicatorIcon fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold">
            {title}
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: 'white' }}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', bgcolor: 'background.paper' }}>
        {children}
      </Box>
    </Paper>
  );
};

export default FloatingWidget;
