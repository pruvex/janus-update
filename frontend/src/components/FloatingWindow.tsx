import React, { useState, useRef, useEffect } from 'react';
import { Paper, Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import OpenWithIcon from '@mui/icons-material/OpenWith';

const FloatingWindow = ({ title, isOpen, onClose, children }: any) => {
  const viewportBottomGap = 105;
  const largeWidth = Math.floor(window.innerWidth * 0.45);
  const startX = window.innerWidth > 1000 ? window.innerWidth - largeWidth - 100 : 50;
  const startY = 0;
  const startWidth = window.innerWidth > 1000 ? largeWidth : 800;
  const startHeight = window.innerHeight - viewportBottomGap;

  const [pos, setPos] = useState({ x: startX, y: startY });
  const [size, setSize] = useState({ w: startWidth, h: startHeight });
  const dragging = useRef(false);
  const resizing = useRef(false);
  const offset = useRef({ x: 0, y: 0, w: 0, h: 0, ratio: 1 });

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 1000 && !dragging.current && !resizing.current) {
        const newWidth = Math.floor(window.innerWidth * 0.45);
        setPos(prev => ({ ...prev, x: window.innerWidth - newWidth - 100 }));
        setSize(prev => ({ ...prev, w: newWidth, h: window.innerHeight - viewportBottomGap }));
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!isOpen) return null;

  const onMouseDown = (e: React.MouseEvent) => {
    dragging.current = true;
    offset.current = { x: e.clientX - pos.x, y: e.clientY - pos.y, w: 0, h: 0, ratio: 1 };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onResizeDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    resizing.current = true;
    offset.current = { x: e.clientX, y: e.clientY, w: size.w, h: size.h, ratio: size.h / size.w };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onMouseMove = (e: MouseEvent) => {
    if (dragging.current) {
      setPos({ x: e.clientX - offset.current.x, y: e.clientY - offset.current.y });
    } else if (resizing.current) {
      const nextWidth = Math.max(400, offset.current.w + (e.clientX - offset.current.x));
      const nextHeight = Math.max(300, Math.round(nextWidth * offset.current.ratio));
      setSize({
        w: nextWidth,
        h: nextHeight,
      });
    }
  };

  const onMouseUp = () => {
    dragging.current = false;
    resizing.current = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  };

  return (
    <Paper
      elevation={10}
      sx={{
        position: 'fixed',
        left: pos.x,
        top: pos.y,
        width: size.w,
        height: size.h,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid #555',
        resize: 'both',
      }}
    >
      <Box
        onMouseDown={onMouseDown}
        sx={{
          p: 1,
          bgcolor: '#1976d2',
          color: 'white',
          cursor: 'grab',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          userSelect: 'none',
        }}
      >
        <Typography variant="subtitle2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <OpenWithIcon fontSize="small" />
          {title}
        </Typography>
        <IconButton size="small" onClick={onClose} sx={{ color: 'white' }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {children}
        <Box
          onMouseDown={onResizeDown}
          sx={{
            position: 'absolute',
            right: 0,
            bottom: 0,
            width: 20,
            height: 20,
            cursor: 'nwse-resize',
            zIndex: 10001,
            background: 'linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.2) 50%)',
          }}
        />
      </Box>
    </Paper>
  );
};
export default FloatingWindow;
