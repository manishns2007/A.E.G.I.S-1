from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class UploadResponse(BaseModel):
    case_id: str
    sha256: str
    metadata: Dict[str, Any]


class AnalyzeRequest(BaseModel):
    case_id: str
    gemini_api_key: Optional[str] = None


class AgentResponse(BaseModel):
    agent: str
    status: str
    processing_time: float
    confidence: Optional[float] = None
    input: Dict[str, Any]
    output: Dict[str, Any]
    reasoning: List[str]
    error: Optional[str] = None
    limitations: List[str] = []
    recommend_next: List[str] = []
    required_followup: List[str] = []
    new_entities: List[Any] = []
    new_relationships: List[Any] = []
    new_hypotheses: Dict[str, Any] = {}
    resolved_hypotheses: List[str] = []
    investigation_notes: List[str] = []
    uncertainty: str = "None"


class PlannerStep(BaseModel):
    timestamp: str
    provider: str
    step: int
    current_goal: str
    current_uncertainty: str
    current_evidence: str
    next_agent: str
    reason: str
    expected_benefit: str
    updated_hypothesis: str
    what_i_know: List[str] = []
    what_i_dont_know: List[str] = []


class ConfidencePoint(BaseModel):
    step: int
    timestamp: str
    agent: str
    agent_label: str
    authentic_prob: float
    synthetic_prob: float
    attribution: Dict[str, float] = {}


class KGGrowthStep(BaseModel):
    step: int
    timestamp: str
    nodes: int
    edges: int
    entities: List[str] = []


class InvestigationBrief(BaseModel):
    summary_paragraphs: List[str]
    recommended_next_action: str
    all_recommendations: List[str] = []
    legal_admissibility: str
    human_review_required: bool = False
    current_confidence: float = 0.0
    estimated_confidence_after: float = 0.0
    verdict: str = ""
    risk_level: str = "UNKNOWN"


class MultiAgentInvestigationResponse(BaseModel):
    case_id: str
    # ── 10 Agents ────────────────────────────────────────────────────────────
    intake:       AgentResponse
    privacy:      AgentResponse
    enf:          AgentResponse
    corneal:      AgentResponse
    vision:       AgentResponse
    graph:        AgentResponse
    risk:         AgentResponse
    fusion:       AgentResponse
    evidence_gap: AgentResponse
    legal_report: AgentResponse
    # ── Investigation Memory ──────────────────────────────────────────────────
    reasoning_chain:        List[str] = []
    planner_steps:          List[Dict[str, Any]] = []
    investigation_timeline: List[Dict[str, Any]] = []
    confidence_evolution:   List[Dict[str, Any]] = []
    goals:                  List[Dict[str, Any]] = []
    hypotheses:             Dict[str, float]     = {}
    active_vectors:         List[str]            = []
    missing_vectors:        List[str]            = []
    environmental_entities: List[str]            = []
    knowledge_graph_growth: List[Dict[str, Any]] = []
    human_review_required:  bool                 = False
    court_ready:            bool                 = False
    investigation_brief:    Dict[str, Any]       = {}


# ── Case-Based Ingestion ──────────────────────────────────────────────────────

class EvidenceInventory(BaseModel):
    images:    int = 0
    videos:    int = 0
    audio:     int = 0
    documents: int = 0
    chats:     int = 0
    unknown:   int = 0

    @property
    def total(self) -> int:
        return self.images + self.videos + self.audio + self.documents + self.chats + self.unknown


class CaseRegistrationResponse(BaseModel):
    case_id:          str
    name:             str
    sha256:           str
    registered_at:    str
    inventory:        EvidenceInventory
    total_files:      int
    primary_evidence: str
    primary_filename: str


class CaseLockerEntry(BaseModel):
    case_id:      str
    name:         str
    registered_at: str
    inventory:    EvidenceInventory
    total_files:  int
    status:       str   # "Ready" | "Processing" | "Complete" | "Error"


class InvestigationStartRequest(BaseModel):
    case_id: str


class StreamStartRequest(BaseModel):
    case_id: str
