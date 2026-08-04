from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class UploadResponse(BaseModel):
    case_id: str
    sha256: str
    metadata: Dict[str, Any]

class AnalyzeRequest(BaseModel):
    case_id: str
    gemini_api_key: Optional[str] = None

class StandardResult(BaseModel):
    status: str
    processing_time: float
    confidence: Optional[float] = None
    findings: Dict[str, Any]
    error_message: Optional[str] = None

class AnalyzeResponse(BaseModel):
    pipeline_status: Dict[str, Any]
    privacy: StandardResult
    enf: StandardResult
    corneal: StandardResult
    gemini: StandardResult
    knowledge_graph: StandardResult
    legal_report: StandardResult
