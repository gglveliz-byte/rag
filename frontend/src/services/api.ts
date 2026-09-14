import axios from 'axios';
import {
  APIKeyItem,
  ChatRequestPayload,
  ChatResponseData,
  DocumentItem,
  JobItem,
  KnowledgeStats,
  SearchResponse,
  SystemHealth,
  UserProfile,
} from '../types';

const rawBase = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = rawBase
  ? (rawBase.endsWith('/api') ? rawBase : `${rawBase.replace(/\/+$/, '')}/api`)
  : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// Helper to get or initialize a guest session UUID
export const getGuestSessionId = (): string => {
  let sessId = localStorage.getItem('guest_session_id');
  if (!sessId) {
    sessId = 'sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    localStorage.setItem('guest_session_id', sessId);
  }
  return sessId;
};

// Interceptor to attach Authorization JWT and X-Guest-Session header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['X-Guest-Session'] = getGuestSessionId();
  return config;
});

// Authentication & Account
export const registerUser = async (email: string, password: string) => {
  const res = await api.post('/auth/register', { email, password });
  localStorage.setItem('auth_token', res.data.access_token);
  return res.data;
};

export const loginUser = async (email: string, password: string) => {
  const res = await api.post('/auth/login', { email, password });
  localStorage.setItem('auth_token', res.data.access_token);
  return res.data;
};

export const logoutUser = () => {
  localStorage.removeItem('auth_token');
};

export const getUserProfile = async (): Promise<UserProfile | null> => {
  try {
    const res = await api.get('/auth/me');
    return res.data;
  } catch {
    return null;
  }
};

export const createApiKey = async (name: string): Promise<APIKeyItem> => {
  const res = await api.post('/auth/api-keys', { name });
  return res.data;
};

export const listApiKeys = async (): Promise<APIKeyItem[]> => {
  const res = await api.get('/auth/api-keys');
  return res.data;
};

export const revokeApiKey = async (keyId: string): Promise<void> => {
  await api.delete(`/auth/api-keys/${keyId}`);
};

export const claimGuestSession = async (guestSessionId: string) => {
  const res = await api.post('/auth/claim-session', { guest_session_id: guestSessionId });
  return res.data;
};

// Ingestion
export const uploadFile = async (
  file: File,
  targets: string = 'postgres',
  tags: string = '',
  replaceIfExists: boolean = false
): Promise<{ job_id: string; filename: string; message: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('targets', targets);
  formData.append('tags', tags);
  formData.append('replace_if_exists', String(replaceIfExists));

  const res = await api.post('/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const ingestDrive = async (
  url: string,
  targets: string[] = ['postgres'],
  tags: string[] = [],
  replaceIfExists: boolean = false
): Promise<{ job_id: string; message: string }> => {
  const res = await api.post('/drive', {
    url,
    targets,
    tags,
    replace_if_exists: replaceIfExists,
  });
  return res.data;
};

// Jobs
export const listJobs = async (): Promise<JobItem[]> => {
  const res = await api.get('/jobs');
  return res.data;
};

export const getJob = async (jobId: string): Promise<JobItem> => {
  const res = await api.get(`/jobs/${jobId}`);
  return res.data;
};

// Search
export const searchKnowledge = async (
  query: string,
  topK: number = 5,
  store: 'postgres' | 'mongo' | 'both' = 'postgres',
  scoreThreshold: number = 0.0
): Promise<SearchResponse> => {
  const res = await api.post('/search', {
    query,
    top_k: topK,
    store,
    score_threshold: scoreThreshold,
  });
  return res.data;
};

// Knowledge Base
export const listDocuments = async (): Promise<DocumentItem[]> => {
  const res = await api.get('/knowledge/documents');
  return res.data;
};

export const getDocumentDetails = async (documentId: string) => {
  const res = await api.get(`/knowledge/documents/${documentId}`);
  return res.data;
};

export const getKnowledgeStats = async (): Promise<KnowledgeStats> => {
  const res = await api.get('/knowledge/stats');
  return res.data;
};

export const deleteDocument = async (documentId: string): Promise<void> => {
  await api.delete(`/knowledge/documents/${documentId}`);
};

// Backups
export const exportBackup = async () => {
  const res = await api.post('/backup/export', null, {
    responseType: 'blob',
  });
  const blob = new Blob([res.data], { type: 'application/gzip' });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.setAttribute('download', `knowledge_backup_${Date.now()}.ragpkg`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const importBackup = async (file: File, targets: string = 'postgres') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('targets', targets);
  const res = await api.post('/backup/import', formData);
  return res.data;
};

// Grounded RAG Agent Chat
export const sendChatMessage = async (payload: ChatRequestPayload): Promise<ChatResponseData> => {
  const res = await api.post('/chat', payload);
  return res.data;
};

export const fetchChatSuggestions = async (): Promise<string[]> => {
  try {
    const res = await api.get('/chat/suggestions');
    return res.data;
  } catch {
    return [];
  }
};

// System Health
export const getSystemHealth = async (): Promise<SystemHealth> => {
  const res = await api.get('/health');
  return res.data;
};

export default api;
