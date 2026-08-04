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

class MultiAgentInvestigationResponse(BaseModel):
    case_id: str
    intake: AgentResponse
    privacy: AgentResponse
    enf: AgentResponse
    corneal: AgentResponse
    vision: AgentResponse
    graph: AgentResponse
    risk: AgentResponse
    fusion: AgentResponse
    legal_report: AgentResponse
    reasoning_chain: List[str]


# ── Case-Based Ingestion ──────────────────────────────────────────────────────

class EvidenceInventory(BaseModel):
    images: int = 0
    videos: int = 0
    audio: int = 0
    documents: int = 0
    chats: int = 0
    unknown: int = 0

    @property
    def total(self) -> int:
        return self.images + self.videos + self.audio + self.documents + self.chats + self.unknown

class CaseRegistrationResponse(BaseModel):
    case_id: str
    name: str
    sha256: str
    registered_at: str
    inventory: EvidenceInventory
    total_files: int
    primary_evidence: str   # path of primary file fed to the pipeline
    primary_filename: str   # display name

class CaseLockerEntry(BaseModel):
    case_id: str
    name: str
    registered_at: str
    inventory: EvidenceInventory
    total_files: int
    status: str             # "Ready" | "Processing" | "Complete"

class InvestigationStartRequest(BaseModel):
    case_id: str
