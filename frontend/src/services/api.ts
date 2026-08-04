import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Shared Types ──────────────────────────────────────────────────────────────

export interface EvidenceInventory {
  images: number;
  videos: number;
  audio: number;
  documents: number;
  chats: number;
  unknown: number;
}

export interface CaseRegistrationResponse {
  case_id: string;
  name: string;
  sha256: string;
  registered_at: string;
  inventory: EvidenceInventory;
  total_files: number;
  primary_filename: string;
}

export interface CaseLockerEntry {
  case_id: string;
  name: string;
  registered_at: string;
  total_files: number;
  inventory: EvidenceInventory;
  status: 'Ready' | 'Processing' | 'Complete' | 'Error';
}

export interface UploadResponse {
  case_id: string;
  sha256: string;
  metadata: any;
}

export interface AgentResponse {
  agent: string;
  status: 'completed' | 'skipped' | 'failed' | 'warning' | 'running';
  processing_time: number;
  confidence: number | null;
  input: any;
  output: any;
  reasoning: string[];
  error: string | null;
}

export interface MultiAgentInvestigationResponse {
  case_id: string;
  intake: AgentResponse;
  privacy: AgentResponse;
  enf: AgentResponse;
  corneal: AgentResponse;
  vision: AgentResponse;
  fusion: AgentResponse;
  graph: AgentResponse;
  legal_report: AgentResponse;
  reasoning_chain: string[];
}

export interface AgentHealth {
  name: string;
  status: 'online' | 'offline';
}

// ── Case-Based Investigation API ──────────────────────────────────────────────

/** Register a new investigation case from a ZIP archive or single media file. */
export const registerCase = async (file: File): Promise<CaseRegistrationResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/case/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** Get all registered investigation cases for the Evidence Locker. */
export const getLockerCases = async (): Promise<CaseLockerEntry[]> => {
  const response = await api.get('/locker');
  return response.data.cases;
};

/** Start a full multi-agent investigation for a registered case. */
export const startInvestigation = async (caseId: string): Promise<MultiAgentInvestigationResponse> => {
  const response = await api.post('/investigation/start', { case_id: caseId });
  return response.data;
};

// ── Legacy / Secondary API ────────────────────────────────────────────────────

/** Upload a single evidence file (legacy / secondary flow). */
export const uploadEvidence = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** Run analysis on an already-uploaded case (legacy). */
export const analyzeEvidence = async (caseId: string): Promise<MultiAgentInvestigationResponse> => {
  const response = await api.post('/analyze', { case_id: caseId });
  return response.data;
};

export const getSystemHealth = async (): Promise<AgentHealth[]> => {
  const response = await api.get('/health');
  return response.data.agents;
};

export const getGraphData = async (caseId: string) => {
  const response = await api.get(`/graph/${caseId}`);
  return response.data;
};

export const getReportUrl = (caseId: string) =>
  `http://localhost:8000/api/report/${caseId}`;

export default api;
