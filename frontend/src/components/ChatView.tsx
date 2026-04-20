import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, TextField, IconButton, Paper, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { uploadRagDocument } from '../services/api';
import { message } from 'antd';

interface ChatViewProps {
  onKnowledgeModalOpen: (documentId: number) => void;
  pendingContext?: { text: string; filename: string; docId: number } | undefined;
  onClearPending?: () => void;
  onCostUpdate?: (cost: { total_cost: number; input_tokens: number; output_tokens: number }) => void;
}

const ChatView: React.FC<ChatViewProps> = ({ onKnowledgeModalOpen, pendingContext, onClearPending, onCostUpdate }) => {
  const { chatId } = useParams<{ chatId: string }>();
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const [inputValue, setInputValue] = useState('');

  React.useEffect(() => {
    if (pendingContext) {
      setInputValue(`Bezugnehmend auf das Dokument '${pendingContext.filename}', Zitat: '${pendingContext.text}' -> Meine Frage dazu: `);
      onClearPending?.();
    }
  }, [pendingContext, onClearPending]);

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const handleSend = async (overrideText?: string) => {
    const payload = overrideText ?? inputValue;
    if (!payload.trim()) return;
    
    console.log("🚀 [DIAG] handleSend START - URL: http://localhost:8001/api/chat/stream");
    
    // Add user message
    const userMessage = { role: 'user', content: payload };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsStreaming(true);

    try {
      const token = localStorage.getItem('auth_token') || '';
      const apiKey = (window as any).electron?.getApiKey?.() || '';
      
      console.log("🚀 [DIAG] Fetch start...");
      
      const response = await fetch('http://localhost:8001/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Janus-Internal-Key': apiKey,
        },
        body: JSON.stringify({
          message: payload,
          chat_id: parseInt(chatId || '0'),
          provider: 'openai',
          model: 'gpt-4o-mini',
        }),
      });

      console.log("🚀 [DIAG] Fetch response received:", response.status, response.statusText);
      console.log("🚀 [DIAG] Content-Type:", response.headers.get('content-type'));

      if (!response.ok) {
        console.error("🚀 [DIAG] HTTP ERROR:", response.status);
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        console.error("🚀 [DIAG] No response body reader!");
        throw new Error('No response body');
      }
      console.log("🚀 [DIAG] Reader obtained, starting read loop...");

      let assistantContent = '';
      const decoder = new TextDecoder();
      let chunkCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log("🚀 [DIAG] Stream DONE signal received");
          break;
        }

        chunkCount++;
        const chunk = decoder.decode(value);
        console.log(`🚀 [DIAG] CHUNK #${chunkCount} RAW:`, chunk.substring(0, 200));

        const lines = chunk.split('\n\n');
        console.log(`🚀 [DIAG] CHUNK #${chunkCount} split into ${lines.length} lines`);

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          if (!line) {
            console.log(`🚀 [DIAG] LINE #${i} is empty/undefined`);
            continue;
          }
          console.log(`🚀 [DIAG] LINE #${i}:`, line.substring(0, 100));
          
          if (!line.startsWith('data: ')) {
            console.log(`🚀 [DIAG] LINE #${i} skipped - no 'data: ' prefix`);
            continue;
          }
          
          const jsonStr = line.slice(6);
          console.log(`🚀 [DIAG] LINE #${i} JSON string:`, jsonStr.substring(0, 100));
          
          try {
            const data = JSON.parse(jsonStr);
            console.log(`🚀 [DIAG] LINE #${i} PARSED data.type:`, data.type);
            
            if (data.type === 'text') {
              console.log(`🚀 [DIAG] TYPE=TEXT, content length:`, data.content?.length || 0);
              assistantContent = data.content;
              setMessages(prev => {
                const last = prev[prev.length - 1];
                if (last?.role === 'assistant') {
                  return [...prev.slice(0, -1), { role: 'assistant', content: assistantContent }];
                }
                return [...prev, { role: 'assistant', content: assistantContent }];
              });
            } else if (data.type === 'metadata') {
              console.log("🚀 [DIAG] TYPE=METADATA - COST DATA RECEIVED!");
              console.log("🚀 [DIAG] metadata.cost:", JSON.stringify(data.cost));
              console.log("🚀 [DIAG] metadata.usage:", JSON.stringify(data.usage));
              
              const costUpdate = {
                total_cost: data.cost?.total_cost || 0,
                input_tokens: data.usage?.input_tokens || 0,
                output_tokens: data.usage?.output_tokens || 0,
              };
              console.log("🚀 [DIAG] Calling onCostUpdate with:", costUpdate);
              
              onCostUpdate?.(costUpdate);
            } else if (data.type === 'done') {
              console.log("🚀 [DIAG] TYPE=DONE - Stream complete");
              setIsStreaming(false);
            } else if (data.type === 'error') {
              console.error("🚀 [DIAG] TYPE=ERROR:", data.message);
            } else {
              console.log(`🚀 [DIAG] UNKNOWN TYPE:`, data.type);
            }
          } catch (e) {
            console.error(`🚀 [DIAG] LINE #${i} JSON PARSE ERROR:`, e);
            console.error(`🚀 [DIAG] Offending string:`, jsonStr);
          }
        }
      }
      
      console.log("🚀 [DIAG] Read loop exited, total chunks:", chunkCount);
    } catch (error) {
      console.error('🚀 [DIAG] Chat stream ERROR:', error);
      message.error('Fehler beim Senden der Nachricht');
      setIsStreaming(false);
    }
    
    console.log("🚀 [DIAG] handleSend END");
  };

  const handleSendMessage = (
    text: string,
    options?: { skipImage?: boolean; isPdfUpload?: boolean } | null,
  ) => {
    if (options === null) {
      console.log('PDF upload prompt - force text-only, drop any image payload');
    } else if (options?.skipImage) {
      console.log('skip image payload for this prompt');
    }
    if (options && options.isPdfUpload) {
      console.log('PDF upload prompt - ensure no image data is attached');
    }
    handleSend(text);
  };

  const resetImageState = () => {
    setAttachedImage(null);
    setImagePreview(null);
  };

  const handleImageUpload = async (file: File) => {
    // Convert file to base64 so downstream vision code can pick it up later
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
    setAttachedImage(dataUrl);
    setImagePreview(dataUrl);
  };

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (!file) return;

    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    const isImage = file.type.startsWith('image/');

    resetImageState();

    if (isPdf) {
      const hide = message.loading(`Janus liest PDF: ${file.name}...`, 0);
      setUploading(true);
      try {
        const res = await uploadRagDocument(file);
        message.success('PDF im Wissensspeicher indiziert.');
        const autoPrompt = `Ich habe gerade das Dokument "${file.name}" hochgeladen. Bitte nutze dein Wissensdatenbank-Tool, lies den Inhalt und gib mir eine kurze Zusammenfassung.`;
        if (typeof handleSendMessage === 'function') {
          handleSendMessage(autoPrompt, null);
        }
        console.log('Triggering Knowledge Center Open for ID:', res.document_id);
        if (typeof onKnowledgeModalOpen === 'function') {
          onKnowledgeModalOpen(res.document_id);
        } else {
          console.error('KRITISCH: onKnowledgeModalOpen Prop ist nicht in ChatView vorhanden!');
        }
      } catch (err) {
        message.error('PDF-Upload fehlgeschlagen.');
        console.error('Upload fehlgeschlagen', err);
      } finally {
        hide();
        setUploading(false);
      }
      return;
    }

    if (isImage) {
      message.info('Bild erkannt. Janus nutzt Vision-Module...');
      if (typeof handleImageUpload === 'function') {
        try {
          await handleImageUpload(file);
        } catch (err) {
          console.error('Bildanalyse fehlgeschlagen', err);
          message.error('Bild konnte nicht analysiert werden.');
        }
      }
      return;
    }

    message.warning('Format nicht unterstützt (nur PDF oder Bilder).');
  };

  return (
    <Box
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      sx={{
        height: 'calc(100vh - 100px)',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative'
      }}
    >
      {isDragging && (
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(25, 118, 210, 0.9)',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'white',
          border: '3px dashed white',
          borderRadius: 2
        }}>
          <CloudUploadIcon sx={{ fontSize: 80, mb: 2 }} />
          <Typography variant="h4">PDF in Janus-Wissen ablegen</Typography>
        </Box>
      )}

      <Box sx={{ flexGrow: 1, p: 2, overflowY: 'auto' }}>
        <Typography variant="h5">Chat {chatId}</Typography>
        <Typography variant="body1" sx={{ mt: 2, color: 'text.secondary' }}>
          Ziehe eine PDF-Datei hierher, um sie der Wissensdatenbank hinzuzufügen.
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Frage Janus etwas..."
          variant="outlined"
          size="small"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <IconButton color="primary" disabled={uploading}>
          {uploading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Paper>
    </Box>
  );
};

export default ChatView;
