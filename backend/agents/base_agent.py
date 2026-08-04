"""
A.E.G.I.S. Multi-Agent Base Framework
Defines the shared InvestigationContext memory and standard BaseAgent abstract class.
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np

class InvestigationContext:
    """
    Shared memory object carrying case state, evidence, hashes, per-agent outputs,
    and accumulated reasoning chains across the multi-agent investigation platform.
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
    Guarantees consistent payload output, validation, and exception boundary handling.
    """
    name: str = "BaseAgent"
    description: str = "Abstract Specialist Forensic Agent"
    capabilities: List[str] = []

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

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validates that output dictionary conforms to the standard agent structure."""
        required = {"agent", "status", "processing_time", "confidence", "input", "output", "reasoning", "error"}
        return isinstance(output, dict) and required.issubset(output.keys())

    def format_response(
        self,
        status: str,
        processing_time: float,
        confidence: Optional[float],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: List[str],
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
            "reasoning": reasoning,
            "error": error
        }
