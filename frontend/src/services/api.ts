import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
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

export const uploadEvidence = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const analyzeEvidence = async (caseId: string, geminiKey?: string): Promise<AnalyzeResponse> => {
  const response = await api.post('/analyze', {
    case_id: caseId,
    gemini_api_key: geminiKey || null
  });
  return response.data;
};

export const getGraphData = async (caseId: string) => {
  const response = await api.get(`/graph/${caseId}`);
  return response.data;
};

export const getReportUrl = (caseId: string) => {
  return `http://localhost:8000/api/report/${caseId}`;
};

export default api;
