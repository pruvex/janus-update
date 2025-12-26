import axios from 'axios';
import { Project } from '../types/project';

const api = axios.create({
  baseURL: 'http://localhost:8001', // ACHTUNG: Port muss 8001 sein!
});

// Funktion, um alle Projekte abzurufen
export const fetchProjects = async (): Promise<Project[]> => {
  const response = await api.get('/api/projects');
  return response.data;
};

// Funktion, um ein neues Projekt zu erstellen
export const createProject = async (name: string, description: string): Promise<Project> => {
  const response = await api.post('/api/projects', { name, description });
  return response.data;
};

// Funktion zum Hochladen von Dateien in ein Projekt
export const uploadFileToProject = async (projectId: number, file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  
  await api.post(`/api/projects/${projectId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// --- Image Studio API ---

export interface GenerateImagePayload {
  prompt: string;
  provider: string;
  model: string;
  parameters: Record<string, string>;
  style_preset?: string;
  use_dalle2_inpainting?: boolean;
}

// Funktion, um die Preisstruktur abzurufen
export const getImagePricing = async (): Promise<any> => {
  const response = await api.get('/api/images/pricing');
  return response.data;
};

// Funktion, um ein Bild zu generieren
export const generateImage = async (payload: GenerateImagePayload): Promise<any> => { // Der Rückgabetyp sollte genauer sein, z.B. GeneratedImage
  const response = await api.post('/api/images/generate', payload);
  return response.data;
};
