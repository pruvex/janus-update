import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Box,
  Typography,
  CircularProgress,
  IconButton,
  Divider,
  Button,
  TextField,
  InputAdornment,
} from '@mui/material';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import SearchIcon from '@mui/icons-material/Search';
import { Document, Page, pdfjs } from 'react-pdf';
import FloatingWindow from './FloatingWindow';
import { fetchRagDocuments, fetchRagDocumentBlob, searchDocumentIds } from '../services/api';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

declare global {
  interface Window {
    loadDocuments?: () => Promise<void>;
  }
}

const statusColorMap: Record<string, string> = {
  new: '#38bdf8',
  warning: '#f97316',
  verified: '#4ade80',
};

const statusLabelMap: Record<string, string> = {
  new: 'Neu',
  warning: 'Korrekturbedarf',
  verified: 'Verifiziert',
};

const normalizeText = (text: string) =>
  text
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const KnowledgeCenter = ({ visible, onClose, initialDocumentId }: any) => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [pageAspectRatio, setPageAspectRatio] = useState(1 / Math.sqrt(2));
  const containerRef = useRef<HTMLDivElement>(null);
  const activeBlobUrlRef = useRef<string | null>(null);
  const [containerSize, setContainerSize] = useState({ width: 600, height: 800 });
  const [selection, setSelection] = useState<{ text: string; top: number; left: number } | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchHits, setSearchHits] = useState<{ id: number; page: number }[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchDebounceRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);
  const selectedDocIdRef = useRef<number | undefined>(undefined);
  const handleSelectDocument = useCallback(
    (doc: any) => {
      setSelectedDoc(doc);
      setPageNumber(1);
      setSelection(null);
      selectedDocIdRef.current = doc?.id;
    },
    [setSelectedDoc, setPageNumber, setSelection],
  );

  useEffect(() => {
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    if (searchTerm.trim().length <= 2) {
      setSearchHits([]);
      setIsSearching(false);
      return;
    }

    searchDebounceRef.current = window.setTimeout(async () => {
      setIsSearching(true);
      try {
        const ids = await searchDocumentIds(searchTerm.trim());
        setSearchHits(ids || []);
      } catch (error) {
        console.error('Hybrid search failed', error);
        setSearchHits([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [searchTerm]);

  useEffect(() => {
    selectedDocIdRef.current = selectedDoc?.id;
  }, [selectedDoc?.id]);

  useEffect(() => {
    if (!containerRef.current) return;
    let timeoutId: number | undefined;
    const observer = new ResizeObserver(entries => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        const entry = entries[0];
        if (!entry) {
          return;
        }
        const newWidth = Math.floor(entry.contentRect.width);
        const newHeight = Math.floor(entry.contentRect.height);
        if (newWidth > 0 && newHeight > 0) {
          setContainerSize(prev => {
            if (prev.width === newWidth && prev.height === newHeight) {
              return prev;
            }
            return { width: newWidth, height: newHeight };
          });
        }
      }, 50);
    });

    observer.observe(containerRef.current);
    return () => {
      observer.disconnect();
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [visible]);

  const isMountedRef = useRef(false);

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await fetchRagDocuments();
      if (!isMountedRef.current) return;

      setDocuments(docs);

      if (!docs.length) {
        setSelectedDoc(null);
        return;
      }

      if (initialDocumentId) {
        const preferred = docs.find((d: any) => d.id === initialDocumentId);
        if (preferred) {
          setSelectedDoc((prev: any) => (prev?.id === preferred.id ? prev : preferred));
          return;
        }
      }

      setSelectedDoc((prev: any) => {
        if (prev && docs.some((doc: any) => doc.id === prev.id)) {
          return prev;
        }
        return docs[0];
      });
    } catch (error) {
      if (isMountedRef.current) {
        setDocuments([]);
        setSelectedDoc(null);
      }
      console.error('Knowledge Center: Dokumente konnten nicht geladen werden', error);
    } finally {
      if (isMountedRef.current) {
        setIsLoaded(true);
      }
    }
  }, [initialDocumentId]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (window.loadDocuments === loadDocuments) {
        delete window.loadDocuments;
      }
    };
  }, [loadDocuments]);

  useEffect(() => {
    window.loadDocuments = loadDocuments;
  }, [loadDocuments]);

  useEffect(() => {
    if (!visible) return;

    setDocuments([]);
    setSelectedDoc(null);
    setIsLoaded(false);

    loadDocuments();
  }, [visible, loadDocuments]);

  useEffect(() => {
    if (!visible || !selectedDoc) {
      setSelection(null);
      return;
    }

    let active = true;

    const loadPdf = async () => {
      try {
        const blobUrl = await fetchRagDocumentBlob(selectedDoc.id);
        if (!active) {
          URL.revokeObjectURL(blobUrl);
          return;
        }

        setPdfUrl((previousUrl) => {
          if (previousUrl) {
            URL.revokeObjectURL(previousUrl);
          }
          activeBlobUrlRef.current = blobUrl;
          return blobUrl;
        });
      } catch (error) {
        if (active) {
          if (activeBlobUrlRef.current) {
            URL.revokeObjectURL(activeBlobUrlRef.current);
            activeBlobUrlRef.current = null;
          }
          setPdfUrl(null);
        }
      }
    };

    setPdfUrl((previousUrl) => {
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
      activeBlobUrlRef.current = null;
      return null;
    });
    loadPdf();

    return () => {
      active = false;
    };
  }, [visible, selectedDoc?.id]);

  useEffect(() => {
    if (!visible) {
      setSelection(null);
    }
  }, [visible]);

  useEffect(() => {
    setSelection(null);
  }, [selectedDoc?.id]);

  useEffect(() => {
    return () => {
      if (activeBlobUrlRef.current) {
        URL.revokeObjectURL(activeBlobUrlRef.current);
        activeBlobUrlRef.current = null;
      }
    };
  }, []);

  const handleMouseUp = (e: React.MouseEvent) => {
    const releaseX = e.clientX;
    const releaseY = e.clientY;
    setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.type === 'Caret' || sel.isCollapsed || sel.rangeCount === 0) {
        setSelection(null);
        return;
      }

      const text = sel.toString().trim();
      if (text.length > 3) {
        setSelection({
          text,
          top: releaseY - 40,
          left: releaseX,
        });
      } else {
        setSelection(null);
      }
    }, 50);
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
    setPageAspectRatio(1 / Math.sqrt(2));
  };

  const framePadding = 8;
  const availableWidth = Math.max(100, containerSize.width - framePadding * 2);
  const availableHeight = Math.max(100, containerSize.height - framePadding * 2);
  const fitWidth = Math.min(availableWidth, Math.floor(availableHeight * pageAspectRatio));
  const effectiveScale = Math.min(scale, 1);
  const renderWidth = Math.max(120, Math.floor(fitWidth * effectiveScale));
  const normalizedSearchTerm = normalizeText(searchTerm.trim());
  const hasActiveFilter = normalizedSearchTerm.length > 0 || searchHits.length > 0;
  const filteredDocuments = documents.filter((doc) => {
    if (!hasActiveFilter) {
      return true;
    }

    const normalizedFilename = normalizeText(doc.filename);
    const nameMatch = normalizedSearchTerm.length > 0 && normalizedFilename.includes(normalizedSearchTerm);
    const contentMatch = searchHits.some((hit) => hit.id === doc.id);
    return nameMatch || contentMatch;
  });

  useEffect(() => {
    if (searchTerm.trim().length <= 2 || searchHits.length === 0) {
      return;
    }

    const currentHit = searchHits.find((hit) => hit.id === selectedDoc?.id);
    if (!selectedDoc || !searchHits.some((hit) => hit.id === selectedDoc.id)) {
      const firstHit = searchHits[0];
      if (firstHit) {
        const docToOpen = documents.find((doc) => doc.id === firstHit.id);
        if (docToOpen) {
          handleSelectDocument(docToOpen);
          setPageNumber(firstHit.page);
        }
      }
      return;
    }

    if (currentHit) {
      setPageNumber(currentHit.page);
    }
  }, [searchTerm, searchHits, selectedDoc, documents, handleSelectDocument]);

  const textRenderer = useCallback(
    (textItem: any) => {
      const query = searchTerm.trim();
      if (query.length < 3) {
        return textItem.str;
      }

      const regex = new RegExp(`(${query})`, 'gi');
      return textItem.str.replace(regex, (match: string) =>
        `<mark style="background-color: #fef08a; color: black; border-radius: 2px;">${match}</mark>`,
      );
    },
    [searchTerm],
  );

  const pdfStyles = `
    .react-pdf__Document,
    .react-pdf__Page,
    .react-pdf__Page__textContent,
    .react-pdf__Page__annotations {
      background-color: transparent !important;
      background: none !important;
    }

    .react-pdf__Page__canvas {
      background-color: white !important;
      box-shadow: 0 0 20px rgba(0,0,0,0.5) !important;
      display: block !important;
      margin: 0 auto !important;
    }

    .react-pdf__Page__textContent mark {
      background-color: #fef08a !important;
      color: black !important;
      border-radius: 2px !important;
    }

    .react-pdf__Page__textContent {
      left: 50% !important;
      transform: translateX(-50%) !important;
    }
  `;

  return (
    <FloatingWindow title="Janus Wissensdatenbank" isOpen={visible} onClose={onClose}>
      <style>{pdfStyles}</style>
      <Box sx={{ display: 'flex', height: '100%', width: '100%' }} data-testid="knowledge-center-modal">
        <Box sx={{ width: 300, borderRight: '1px solid #ddd', overflowY: 'auto', bgcolor: '#fff', flexShrink: 0 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid #e5e7eb', bgcolor: '#f8fafc' }}>
            <TextField
              variant="outlined"
              size="small"
              placeholder="Dokumente durchsuchen..."
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              fullWidth
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" sx={{ color: '#9ca3af' }} />
                  </InputAdornment>
                ),
              }}
            />
            {isSearching && (
              <Typography variant="caption" sx={{ mt: 0.5, color: '#4b5563' }}>
                Suche in Inhalten...
              </Typography>
            )}
          </Box>
          {isLoaded && documents.length === 0 ? (
            <Box sx={{ p: 2, minHeight: 100 }}>
              <Typography variant="body2" color="text.secondary">
                Keine Dokumente vorhanden. Ziehe eine PDF in den Chat, um sie hier zu speichern.
              </Typography>
            </Box>
          ) : filteredDocuments.length === 0 ? (
            <Box sx={{ p: 2, minHeight: 100, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Keine Dokumente gefunden.
              </Typography>
            </Box>
          ) : (
            <List dense>
              {filteredDocuments.map((doc) => {
                const statusKey = (doc.audit_status || 'new').toLowerCase();
                const badgeColor = statusColorMap[statusKey] || '#38bdf8';
                const badgeLabel = statusLabelMap[statusKey] || 'Neu';
                return (
                  <ListItemButton
                    key={doc.id}
                    selected={selectedDoc?.id === doc.id}
                    onClick={() => handleSelectDocument(doc)}
                    data-testid={`knowledge-doc-item-${doc.id}`}
                    sx={{ py: 2.5, alignItems: 'center', px: 2 }}
                  >
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <PictureAsPdfIcon color="error" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1, alignItems: 'center' }}>
                          <Typography
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              fontSize: '0.95rem',
                              fontWeight: 600,
                            }}
                          >
                            {doc.filename}
                          </Typography>
                          <Box
                            component="span"
                            className={`audit-status-pill status-${statusKey}`}
                            data-testid={`audit-status-pill-${statusKey}`}
                            sx={{
                              backgroundColor: badgeColor,
                              color: '#0f172a',
                              borderRadius: 999,
                              px: 1.25,
                              py: 0.25,
                              fontSize: '0.65rem',
                              fontWeight: 600,
                            }}
                          >
                            {badgeLabel}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItemButton>
                );
              })}
            </List>
          )}
        </Box>

        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            bgcolor: '#525659',
            minWidth: 0,
            px: 0,
          }}
        >
          <Box sx={{ p: 0.5, bgcolor: '#f0f0f0', display: 'flex', justifyContent: 'center', gap: 2 }}>
            <IconButton onClick={() => setPageNumber(p => Math.max(1, p - 1))} disabled={pageNumber <= 1}>
              <NavigateBeforeIcon />
            </IconButton>
            <Typography variant="body2" sx={{ alignSelf: 'center' }} data-testid="knowledge-page-indicator">
              Seite {pageNumber} / {numPages || '-'}
            </Typography>
            <IconButton onClick={() => setPageNumber(p => Math.min(numPages || 1, p + 1))} disabled={pageNumber >= (numPages || 1)}>
              <NavigateNextIcon />
            </IconButton>
            <Divider orientation="vertical" flexItem />
            <IconButton onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>
              <ZoomOutIcon />
            </IconButton>
            <Typography variant="body2" sx={{ alignSelf: 'center' }}>{Math.round(scale * 100)}%</Typography>
            <IconButton onClick={() => setScale(s => Math.min(1, s + 0.1))}>
              <ZoomInIcon />
            </IconButton>
          </Box>

          <Box
            ref={containerRef}
            sx={{
              flexGrow: 1,
              overflow: 'hidden',
              position: 'relative',
              width: '100%',
              p: 0,
            }}
            onMouseUp={handleMouseUp}
          >
            <Box
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                bgcolor: '#323639',
                px: 0,
                py: 1,
              }}
            >
              {pdfUrl ? (
                <Box
                  sx={{
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                  }}
                >
                  <Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess} loading={<CircularProgress sx={{ color: 'white' }} />}>
                    <Page
                      key={`page_${pageNumber}_search_${searchTerm}`}
                      pageNumber={pageNumber}
                      width={renderWidth}
                      onLoadSuccess={(page) => {
                        const width = (page as any)?.originalWidth || (page as any)?.width;
                        const height = (page as any)?.originalHeight || (page as any)?.height;
                        if (width && height) {
                          setPageAspectRatio(width / height);
                        }
                      }}
                      renderTextLayer={true}
                      renderAnnotationLayer={true}
                      className="mx-auto"
                      customTextRenderer={textRenderer}
                    />
                  </Document>
                </Box>
              ) : selectedDoc ? (
                <CircularProgress sx={{ color: 'white', mt: 10 }} />
              ) : (
                <Typography sx={{ color: '#aaa', mt: 10 }}>Kein Dokument ausgewählt.</Typography>
              )}

              {selection && (
                <Button
                  variant="contained"
                  size="small"
                  sx={{ position: 'fixed', top: selection.top, left: selection.left, zIndex: 99999 }}
                  onClick={(event) => {
                    event.stopPropagation();
                    window.dispatchEvent(new CustomEvent('insert-chat-quote', {
                      detail: {
                        text: selection.text,
                        filename: selectedDoc?.filename,
                      },
                    }));
                    setSelection(null);
                    onClose();
                  }}
                >
                  Janus fragen
                </Button>
              )}
            </Box>
          </Box>
        </Box>
      </Box>
    </FloatingWindow>
  );
};

export default KnowledgeCenter;
