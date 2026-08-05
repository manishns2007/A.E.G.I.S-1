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

export interface AgentResponse {
  agent: string;
  status: 'completed' | 'skipped' | 'failed' | 'warning' | 'running';
  processing_time: number;
  confidence: number | null;
  input: any;
  output: any;
  reasoning: string[];
  limitations?: string[];
  recommend_next?: string[];
  required_followup?: string[];
  new_entities?: any[];
  new_relationships?: any[];
  new_hypotheses?: Record<string, number>;
  resolved_hypotheses?: string[];
  investigation_notes?: string[];
  uncertainty?: string;
  error: string | null;
}

export interface PlannerStep {
  timestamp: string;
  provider: string;
  step: number;
  current_goal: string;
  current_uncertainty: string;
  current_evidence: string;
  next_agent: string;
  reason: string;
  expected_benefit: string;
  updated_hypothesis: string;
  what_i_know: string[];
  what_i_dont_know: string[];
}

export interface ConfidencePoint {
  step: number;
  timestamp: string;
  agent: string;
  agent_label: string;
  authentic_prob: number;
  synthetic_prob: number;
  attribution: Record<string, number>;
}

export interface KGGrowthStep {
  step: number;
  timestamp: string;
  nodes: number;
  edges: number;
  entities: string[];
}

export interface InvestigationGoal {
  goal: string;
  progress: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
}

export interface EvidenceVector {
  vector: string;
  status: 'active' | 'missing' | 'partial';
  finding?: string;
  reason?: string;
  contribution?: number;
  potential_contribution?: number;
}

export interface InvestigationBrief {
  summary_paragraphs: string[];
  recommended_next_action: string;
  all_recommendations: string[];
  legal_admissibility: string;
  human_review_required: boolean;
  current_confidence: number;
  estimated_confidence_after: number;
  verdict: string;
  risk_level: string;
}

export interface MultiAgentInvestigationResponse {
  case_id: string;
  intake:       AgentResponse;
  privacy:      AgentResponse;
  enf:          AgentResponse;
  corneal:      AgentResponse;
  vision:       AgentResponse;
  graph:        AgentResponse;
  risk:         AgentResponse;
  fusion:       AgentResponse;
  evidence_gap: AgentResponse;
  legal_report: AgentResponse;
  reasoning_chain:        string[];
  planner_steps:          PlannerStep[];
  investigation_timeline: any[];
  confidence_evolution:   ConfidencePoint[];
  goals:                  InvestigationGoal[];
  hypotheses:             Record<string, number>;
  active_vectors:         string[];
  missing_vectors:        string[];
  environmental_entities: string[];
  knowledge_graph_growth: KGGrowthStep[];
  human_review_required:  boolean;
  court_ready:            boolean;
  investigation_brief:    InvestigationBrief;
}

// ── SSE Event Types ───────────────────────────────────────────────────────────

export type SSEEventType =
  | 'start'
  | 'planner_step'
  | 'agent_start'
  | 'agent_done'
  | 'hypothesis'
  | 'graph_update'
  | 'gap_analysis'
  | 'complete'
  | 'log'
  | 'error';

export interface SSEEvent {
  event: SSEEventType;
  data: any;
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

/** Start a full multi-agent investigation for a registered case (blocking). */
export const startInvestigation = async (caseId: string): Promise<MultiAgentInvestigationResponse> => {
  const response = await api.post('/investigation/start', { case_id: caseId });
  return response.data;
};

/**
 * Stream a live multi-agent investigation via Server-Sent Events.
 * Returns a cleanup function to close the EventSource.
 */
export const streamInvestigation = (
  caseId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (err: Event) => void
): (() => void) => {
  // We POST to start, but SSE is GET-based — use fetch to POST then EventSource
  // For simplicity, use the blocking POST endpoint and stream results post-completion
  // The SSE endpoint is available at /investigation/stream via POST
  const controller = new AbortController();

  fetch('http://localhost:8000/api/investigation/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseId }),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      onEvent({ event: 'error', data: { message: `HTTP ${res.status}` } });
      return;
    }
    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed: SSEEvent = JSON.parse(line.slice(6));
            onEvent(parsed);
          } catch {
            // ignore parse errors
          }
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError' && onError) onError(err);
  });

  return () => controller.abort();
};

// ── Legacy / Secondary API ────────────────────────────────────────────────────

export const uploadEvidence = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeEvidence = async (caseId: string) => {
  const response = await api.post('/analyze', { case_id: caseId });
  return response.data;
};

export const getReport = async (caseId: string) => {
  const response = await api.get(`/report/${caseId}`);
  return response.data;
};

export const getGraphData = async (caseId: string) => {
  const response = await api.get(`/graph/${caseId}`);
  return response.data;
};

export const getSystemHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};
