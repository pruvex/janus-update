import React, { useState, useEffect } from 'react';
import { 
  Dialog, DialogTitle, DialogContent, Grid, Box, Typography, IconButton,
  TextField, FormControl, InputLabel, Select, MenuItem, Button, Stack, CircularProgress, Alert, Card, CardMedia,
  FormControlLabel, Checkbox
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { getImagePricing, generateImage, GenerateImagePayload } from '../services/api';

interface ImageStudioModalProps {
  open: boolean;
  onClose: () => void;
}

const ImageStudioModal: React.FC<ImageStudioModalProps> = ({ open, onClose }) => {
  // State für die API-Daten und Auswahl
  const [pricingData, setPricingData] = useState<any>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelParameters, setModelParameters] = useState<Record<string, string>>({});
  const [prompt, setPrompt] = useState<string>('');
  const [useDalle2Inpainting, setUseDalle2Inpainting] = useState<boolean>(false);
  const [estimatedCost, setEstimatedCost] = useState<number | string>('N/A');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [latestGeneratedImage, setLatestGeneratedImage] = useState<string | null>(null);

  // Lade Preisdaten, wenn das Modal geöffnet wird
  useEffect(() => {
    if (open) {
      const fetchPricing = async () => {
        setIsLoading(true);
        try {
          const data = await getImagePricing();
          setPricingData(data);
          if (!selectedProvider) setSelectedProvider('openai');
        } catch (error) {
          console.error("Fehler beim Laden der Preisdaten:", error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchPricing();
    }
  }, [open]);

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    setSelectedModel('');
    setModelParameters({});
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setModelParameters({});
  }

  const handleParameterChange = (param: string, value: string) => {
    setModelParameters(prev => ({ ...prev, [param]: value }));
  }

  useEffect(() => {
    if (!pricingData || !selectedProvider || !selectedModel) {
      setEstimatedCost('N/A');
      return;
    }
    try {
      let costPath = pricingData[selectedProvider]?.[selectedModel];
      if (!costPath) {
        setEstimatedCost('N/A');
        return;
      }
      const paramKeys = Object.keys(modelParameters);
      let finalCost = costPath;
      
      // Navigiere durch die Preis-Struktur basierend auf der Auswahl
      const relevantParamKeys = Object.keys(finalCost).filter(k => typeof finalCost[k] === 'object');
      for(const key of relevantParamKeys) {
          const selectedValue = modelParameters[key];
          if(selectedValue && finalCost[selectedValue]) {
              finalCost = finalCost[selectedValue];
          } else {
              setEstimatedCost('...');
              return;
          }
      }

      if (typeof finalCost === 'number') {
        setEstimatedCost(finalCost.toFixed(4));
      } else {
        // Falls nach der Auswahl immer noch ein Objekt übrig ist (z.B. bei DALL-E 3)
        const quality = modelParameters['quality'] || 'standard';
        const resolution = modelParameters['resolution'] || '1024x1024';
        const cost = pricingData[selectedProvider]?.[selectedModel]?.[quality]?.[resolution];
        if (typeof cost === 'number') {
           setEstimatedCost(cost.toFixed(4));
        } else {
           setEstimatedCost('...');
        }
      }
    } catch (e) {
      setEstimatedCost('Fehler');
    }
  }, [pricingData, selectedProvider, selectedModel, modelParameters]);


  const handleGenerateClick = async () => {
    const payload: GenerateImagePayload = {
      prompt,
      provider: selectedProvider,
      model: selectedModel,
      parameters: modelParameters,
      use_dalle2_inpainting: useDalle2Inpainting
    };
    
    setIsLoading(true);
    setLatestGeneratedImage(null);
    try {
      const result = await generateImage(payload);
      // Annahme: Das Backend gibt ein Objekt mit `image_url` zurück.
      // Der Pfad muss eventuell mit der Base-URL des Backends kombiniert werden.
      const imageUrl = `http://localhost:8001${result.image_url}`;
      setLatestGeneratedImage(imageUrl);
    } catch (error) {
      console.error("Fehler bei der Bildgenerierung:", error);
      // Hier könnte man eine Fehlermeldung im UI anzeigen
    } finally {
      setIsLoading(false);
    }
  };
  
  const renderParameterSelectors = () => {
    if (!pricingData || !selectedProvider || !selectedModel) return null;

    let currentLevel = pricingData[selectedProvider]?.[selectedModel];
    if (!currentLevel || typeof currentLevel === 'number') return null;

    // Finde die Parameter, die Objekte als Werte haben (d.h. sie sind verschachtelt)
    const parameterKeys = Object.keys(currentLevel).filter(key => typeof currentLevel[key] === 'object');

    return parameterKeys.map(paramKey => {
        const options = Object.keys(currentLevel[paramKey]);
        return (
            <FormControl fullWidth margin="normal" key={paramKey}>
            <InputLabel>{paramKey.charAt(0).toUpperCase() + paramKey.slice(1)}</InputLabel>
            <Select
                value={modelParameters[paramKey] || ''}
                label={paramKey.charAt(0).toUpperCase() + paramKey.slice(1)}
                onChange={(e) => handleParameterChange(paramKey, e.target.value as string)}
            >
                {options.map(opt => <MenuItem key={opt} value={opt}>{opt}</MenuItem>)}
            </Select>
            </FormControl>
        );
    });
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xl" PaperProps={{ sx: { height: '90vh', maxHeight: '90vh' } }}>
      <DialogTitle sx={{ m: 0, p: 2 }}>
        Image Studio
        <IconButton aria-label="close" onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8, color: (theme) => theme.palette.grey[500] }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 0 }}>
        <Grid container sx={{ height: '100%' }}>
          <Grid item xs={12} md={4} sx={{ borderRight: '1px solid', borderColor: 'divider', p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>Einstellungen</Typography>
            <Stack spacing={2} sx={{ flexGrow: 1 }}>
              <TextField
                label="Prompt"
                multiline
                rows={4}
                fullWidth
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                variant="outlined"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Provider</InputLabel>
                <Select
                  value={selectedProvider}
                  label="Provider"
                  onChange={(e) => handleProviderChange(e.target.value as string)}
                >
                  {pricingData && Object.keys(pricingData).map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
                </Select>
              </FormControl>
              
              {selectedProvider && (
                <FormControl fullWidth margin="normal" disabled={!pricingData}>
                  <InputLabel>Modell</InputLabel>
                  <Select
                    value={selectedModel}
                    label="Modell"
                    onChange={(e) => handleModelChange(e.target.value as string)}
                  >
                    {pricingData && pricingData[selectedProvider] && Object.keys(pricingData[selectedProvider]).map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                  </Select>
                </FormControl>
              )}
              
              {renderParameterSelectors()}

              {selectedModel && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={useDalle2Inpainting}
                      onChange={(e) => setUseDalle2Inpainting(e.target.checked)}
                      name="dalle2-inpainting-checkbox"
                    />
                  }
                  label="Pixelgenaue Ersetzung (DALL-E 2)"
                />
              )}

            </Stack>
            <Box sx={{ mt: 2, flexShrink: 0 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Geschätzte Kosten / Bild: <strong>${estimatedCost}</strong>
              </Alert>
              <Button 
                variant="contained" 
                fullWidth 
                onClick={handleGenerateClick}
                disabled={isLoading || !prompt || String(estimatedCost).includes('...')}
                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
              >
                {isLoading ? 'Generiere...' : 'Generieren'}
              </Button>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={8} sx={{ p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ flexShrink: 0, height: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2, position: 'relative' }}>
              {isLoading && <CircularProgress sx={{position: 'absolute'}} />}
              {!isLoading && !latestGeneratedImage && (
                <Typography color="text.secondary">Vorschau des generierten Bildes</Typography>
              )}
              {latestGeneratedImage && (
                 <Card sx={{ width: '100%', height: '100%'}}>
                    <CardMedia
                        component="img"
                        image={latestGeneratedImage}
                        alt="Generated Image"
                        sx={{ objectFit: 'contain', width: '100%', height: '100%' }}
                    />
                 </Card>
              )}
            </Box>
            <Box sx={{ flexGrow: 1, borderTop: '1px solid', borderColor: 'divider', pt: 2 }}>
               <Typography variant="h6" gutterBottom>Generierte Bilder</Typography>
              <Box sx={{ border: '1px dashed grey', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                 <Typography color="text.secondary">Die Galerie Ihrer generierten Bilder erscheint hier</Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
};

export default ImageStudioModal;
