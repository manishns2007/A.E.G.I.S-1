"""
A.E.G.I.S. Multi-Agent Base Framework
Defines shared InvestigationContext memory, BaseAgent abstract class,
Machine-Readable Agent Capability Registry, and Enriched Forensic Intelligence Payloads.
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np

class InvestigationContext:
    """
    Shared memory object carrying case state, evidence, hashes, per-agent outputs,
    hypotheses, confidence evolution, timeline, and accumulated reasoning chains.
    """
    def __init__(self, case_id: str, file_path: str, is_video: bool, original_filename: str, file_bytes: bytes):
        self.case_id = case_id
        self.file_path = file_path
        self.is_video = is_video
        self.original_filename = original_filename
        self.file_bytes = file_bytes
        self.sha256: str = ""
        self.metadata: Dict[str, Any] = {}
        
        # Shared media buffers
        self.img_bgr: Optional[np.ndarray] = None
        self.shielded_bgr: Optional[np.ndarray] = None
        self.shielded_vid_path: Optional[str] = None
        
        # Agent outputs map: agent_name -> Standard Agent Response Dict
        self.agent_results: Dict[str, Dict[str, Any]] = {}
        
        # Unified investigation reasoning chain
        self.reasoning_chain: List[str] = []
        
        # Intermediate outputs
        self.fusion_output: Dict[str, Any] = {}
        self.knowledge_graph_fig: Optional[Dict[str, Any]] = None
        self.legal_docket: Optional[Dict[str, Any]] = None

    def add_reasoning(self, agent_name: str, message: str):
        entry = f"[{agent_name.upper()}] {message}"
        self.reasoning_chain.append(entry)


class BaseAgent(ABC):
    """
    Standard interface contract for all specialized forensic agents in A.E.G.I.S.
    Exposes Machine-Readable Capability Manifests and Structured Intelligence Payloads.
    """
    name: str = "BaseAgent"
    purpose: str = "Abstract Specialist Forensic Agent"
    inputs: List[str] = []
    outputs: List[str] = []
    capabilities: List[str] = []
    produces: List[str] = []
    consumes: List[str] = []
    dependencies: List[str] = []
    limitations: List[str] = []
    typical_runtime_sec: float = 0.5

    @classmethod
    def get_capability_manifest(cls) -> Dict[str, Any]:
        """Returns a machine-readable capability manifest for dynamic discovery by LLM planners."""
        return {
            "name": cls.name,
            "purpose": cls.purpose,
            "inputs": cls.inputs,
            "outputs": cls.outputs,
            "capabilities": cls.capabilities,
            "produces": cls.produces,
            "consumes": cls.consumes,
            "dependencies": cls.dependencies,
            "limitations": cls.limitations,
            "typical_runtime_sec": cls.typical_runtime_sec
        }

    @abstractmethod
    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        """
        Main execution entry point. Reads and updates InvestigationContext.
        Returns a standardized dictionary following the A.E.G.I.S. agent payload contract.
        """
        pass

    def validate_input(self, context: InvestigationContext) -> bool:
        """Validates that necessary inputs exist in context prior to execution."""
        return context is not None and bool(context.file_path)

    def format_response(
        self,
        status: str,
        processing_time: float,
        confidence: Optional[float],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: List[str],
        limitations: List[str] = None,
        recommend_next: List[str] = None,
        required_followup: List[str] = None,
        new_entities: List[Dict[str, Any]] = None,
        new_relationships: List[Dict[str, Any]] = None,
        new_hypotheses: Dict[str, float] = None,
        resolved_hypotheses: List[str] = None,
        investigation_notes: List[str] = None,
        uncertainty: str = "None",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Utility method to assemble standard A.E.G.I.S. agent response dictionaries."""
        return {
            "agent": self.name,
            "status": status,  # "completed" | "skipped" | "failed" | "warning" | "running"
            "processing_time": round(processing_time, 3),
            "confidence": round(confidence, 1) if confidence is not None else None,
            "input": input_data,
            "output": output_data,
            "findings": output_data,
            "reasoning": reasoning,
            "limitations": limitations or self.limitations,
            "recommend_next": recommend_next or [],
            "required_followup": required_followup or [],
            "new_entities": new_entities or [],
            "new_relationships": new_relationships or [],
            "new_hypotheses": new_hypotheses or {},
            "resolved_hypotheses": resolved_hypotheses or [],
            "investigation_notes": investigation_notes or [],
            "uncertainty": uncertainty,
            "error": error
        }
