import axios from 'axios';
import type { Project } from '../types/project';

const api = axios.create({
  baseURL: 'http://localhost:8001', // ACHTUNG: Port muss 8001 sein!
});

let authBootstrapPromise: Promise<void> | null = null;
let internalApiKeyPromise: Promise<string | null> | null = null;

const ensureAuthToken = async (): Promise<void> => {
  if (localStorage.getItem('auth_token')) {
    return;
  }

  if (authBootstrapPromise) {
    return authBootstrapPromise;
  }

  authBootstrapPromise = (async () => {
    try {
      const response = await fetch('http://localhost:8001/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      if (data?.access_token) {
        localStorage.setItem('auth_token', data.access_token);
      }
    } catch (error) {
      console.warn('Silent auth bootstrap failed in React API client:', error);
    } finally {
      authBootstrapPromise = null;
    }
  })();

  return authBootstrapPromise;
};

const getInternalApiKey = async (): Promise<string | null> => {
  if (!internalApiKeyPromise) {
    internalApiKeyPromise = (async () => {
      try {
        return (window as any).electron?.getApiKey?.() ?? null;
      } catch (error) {
        console.warn('Could not read internal API key for axios client:', error);
        return null;
      }
    })();
  }
  return internalApiKeyPromise;
};

api.interceptors.request.use(async (config) => {
  await ensureAuthToken();

  const headers = (config.headers ?? {}) as Record<string, string>;
  const token = localStorage.getItem('auth_token');

  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const apiKey = await getInternalApiKey();
  if (apiKey && !headers['X-Janus-Internal-Key']) {
    headers['X-Janus-Internal-Key'] = apiKey;
  }

  config.headers = headers as any;
  return config;
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

// --- RAG / Document API (Neu für Phase 2) ---

export interface RagDocument {
  id: number;
  filename: string;
  upload_date: string;
  is_indexed: boolean;
  project_id?: number;
  file_size?: number;
}

export interface RagUploadResponse {
  status: string;
  message: string;
  document_id: number;
  filename: string;
}

// Lädt eine PDF hoch und startet die Vektorisierung (RAG)
export const uploadRagDocument = async (file: File, projectId?: number): Promise<RagUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (projectId) {
    formData.append('project_id', projectId.toString());
  }

  const response = await api.post('/api/rag/upload-document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Holt die Liste aller RAG-Dokumente
export const fetchRagDocuments = async (): Promise<RagDocument[]> => {
  const response = await api.get('/api/rag/documents');
  return response.data;
};

export const fetchRagDocumentBlob = async (documentId: number): Promise<string> => {
  try {
    const response = await api.get(`/api/rag/files/${documentId}`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(response.data);
  } catch (error) {
    console.error('PDF Blob Error:', error);
    throw error;
  }
};

export interface DocumentSearchHit {
  id: number;
  page: number;
}

export const searchDocumentIds = async (query: string): Promise<DocumentSearchHit[]> => {
  if (!query) {
    return [];
  }
  const response = await api.get('/api/rag/search-ids', { params: { query } });
  return response.data;
};
