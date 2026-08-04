"""
Agent 1: Investigation Orchestrator Agent
The primary brain of the A.E.G.I.S. platform. Builds execution plans, sequences specialist agents,
manages shared memory (InvestigationContext), handles failures, and returns the final payload.
"""
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

# Import all agents
from .intake_agent import EvidenceIntakeAgent
from .privacy_agent import PrivacyShieldAgent
from .enf_agent import ENFPhysicsAgent
from .corneal_agent import CornealTopologyAgent
from .vision_agent import VisionIntelligenceAgent
from .fusion_agent import IntelligenceFusionAgent
from .graph_agent import KnowledgeGraphAgent
from .legal_agent import LegalReasoningAgent

class InvestigationOrchestratorAgent(BaseAgent):
    name = "Investigation Orchestrator"
    description = "Plans and manages multi-agent forensic investigations."
    capabilities = ["Pipeline Construction", "Agent Task Dispatch", "State Management", "Failure Recovery"]

    def __init__(self):
        # Instantiate pool
        self.intake_agent = EvidenceIntakeAgent()
        self.privacy_agent = PrivacyShieldAgent()
        self.enf_agent = ENFPhysicsAgent()
        self.corneal_agent = CornealTopologyAgent()
        self.vision_agent = VisionIntelligenceAgent()
        self.fusion_agent = IntelligenceFusionAgent()
        self.graph_agent = KnowledgeGraphAgent()
        self.legal_agent = LegalReasoningAgent()

    def _build_plan(self, context: InvestigationContext) -> List[BaseAgent]:
        """Dynamically constructs the execution plan based on media type."""
        # Standard pipeline layout (Image/Video specific logic is handled cleanly inside ENF/Corneal agents via SKIPPED statuses)
        return [
            self.intake_agent,
            self.privacy_agent,
            self.enf_agent,
            self.corneal_agent,
            self.vision_agent,
            self.fusion_agent,
            self.graph_agent,
            self.legal_agent
        ]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []
        
        reasoning.append(f"Received investigation request for Case {context.case_id}.")
        context.add_reasoning(self.name, "Constructing dynamic execution plan...")

        plan = self._build_plan(context)
        reasoning.append(f"Execution plan built with {len(plan)} specialist agents.")

        # Execute agents sequentially
        for agent in plan:
            context.add_reasoning(self.name, f"Dispatching task to {agent.name}...")
            
            # Execute Agent
            agent_res = agent.execute(context)
            
            # Store in context memory
            context.agent_results[agent.name] = agent_res
            
            # Log execution outcome
            status = agent_res.get("status", "unknown")
            if status == "failed":
                reasoning.append(f"CRITICAL: {agent.name} encountered a fatal error. Pipeline continuing.")
                context.add_reasoning(self.name, f"{agent.name} failed. Continuing investigation...")
            else:
                reasoning.append(f"{agent.name} completed with status: {status.upper()}.")

        context.add_reasoning(self.name, "Investigation completed. Compiling final intelligence package.")

        # Final Response Compilation
        # Map agent results to frontend keys for backwards compatibility with the UI layout
        output = {
            "case_id": context.case_id,
            "intake": context.agent_results.get("Evidence Intake Agent", {}),
            "privacy": context.agent_results.get("Privacy Shield Agent", {}),
            "enf": context.agent_results.get("ENF Physics Agent", {}),
            "corneal": context.agent_results.get("Corneal Specular Topology Agent", {}),
            "vision": context.agent_results.get("Vision Intelligence Agent", {}),
            "fusion": context.agent_results.get("Intelligence Fusion Agent", {}),
            "graph": context.agent_results.get("Knowledge Graph Agent", {}),
            "legal_report": context.agent_results.get("Legal Reasoning Agent", {}),
            "reasoning_chain": context.reasoning_chain  # Global live activity log
        }

        return self.format_response(
            status="completed",
            processing_time=time.time() - start,
            confidence=100.0,
            input_data={"case_id": context.case_id},
            output_data=output,
            reasoning=reasoning
        )
