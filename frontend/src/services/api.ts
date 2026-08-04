import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

export interface UploadResponse {
  case_id: string;
  sha256: string;
  metadata: any;
}

export interface AnalyzeResponse {
  pipeline_status: any;
  privacy: any;
  enf: any;
  corneal: any;
  gemini: any;
  knowledge_graph: any;
  legal_report: any;
}

export interface LockerItem {
  case_ref: string;
  filename: string;
  file_type: string;
  size_kb: number;
  registered_at: string;
  status: string;
  path: string;
}

export interface AgentHealth {
  name: string;
  status: 'online' | 'offline';
}

export const uploadEvidence = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeEvidence = async (caseId: string): Promise<AnalyzeResponse> => {
  const response = await api.post('/analyze', { case_id: caseId });
  return response.data;
};

export const getLockerItems = async (): Promise<LockerItem[]> => {
  const response = await api.get('/locker');
  return response.data.items;
};

export const startInvestigation = async (lockerFilename: string): Promise<AnalyzeResponse> => {
  const response = await api.post('/investigation/start', { locker_filename: lockerFilename });
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
