export interface DocumentItem {
  document_id: string;
  tenant_id: string;
  filename: string;
  file_hash: string;
  file_type: string;
  file_size_bytes: number;
  total_chunks: number;
  tags: string[];
  created_at: string;
  is_ephemeral: boolean;
  expires_at: string | null;
  version: number;
}

export interface ChunkItem {
  chunk_id: string;
  document_id: string;
  tenant_id: string;
  content: string;
  embedding?: number[];
  chunk_index: number;
  token_count: number;
  metadata: Record<string, any>;
}


export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  source_file: string;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total_results: number;
  query_time_ms: number;
}

export interface JobItem {
  job_id: string;
  filename: string;
  status: 'queued' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'completed' | 'failed';
  progress: number;
  stage_message: string;
  created_at: string;
  error?: string | null;
}

export interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  total_size_bytes: number;
  is_ephemeral: boolean;
  expires_in_hours: number | null;
}

export interface UserProfile {
  user_id: string;
  email: string;
  created_at: string;
  active_api_keys_count: number;
}

export interface APIKeyItem {
  key_id: string;
  name: string;
  masked_key: string;
  raw_key?: string | null;
  created_at: string;
  is_active: boolean;
}

export interface SystemHealth {
  status: string;
  postgres_connected: boolean;
  mongo_connected: boolean;
  dashscope_configured: boolean;
  mock_mode: boolean;
  timestamp: string;
}

export interface CitationItem {
  chunk_id: string;
  filename: string;
  content: string;
  similarity_score: number;
  chunk_index: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: CitationItem[];
  has_grounding?: boolean;
  is_conversational?: boolean;
  query_mode?: 'precise' | 'full';
  primary_source?: string;
  primary_score?: number;
  model?: string;
  execution_time_ms?: number;
  timestamp: string;
}

export interface ChatRequestPayload {
  query: string;
  store?: string;
  top_k?: number;
  score_threshold?: number;
  mode?: 'precise' | 'full';
}

export interface ChatResponseData {
  query: string;
  answer: string;
  has_grounding: boolean;
  is_conversational?: boolean;
  query_mode?: 'precise' | 'full';
  primary_source?: string;
  primary_score?: number;
  citations: CitationItem[];
  total_citations: number;
  model: string;
  execution_time_ms: number;
}

