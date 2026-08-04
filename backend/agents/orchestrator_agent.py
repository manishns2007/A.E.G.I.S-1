"""
Agent 1: Investigation Orchestrator Agent
The primary brain of the A.E.G.I.S. platform.
Delegates orchestration to the LangGraphEngine (provider-agnostic state graph engine).
Supports Groq (Llama-3), Gemini, and Procedural Fallback seamlessly via ProviderFactory.
"""
import time
from typing import Dict, Any

from .base_agent import BaseAgent, InvestigationContext
from .langgraph_engine import LangGraphEngine


def _make_default_agent_res(agent_name: str) -> Dict[str, Any]:
    """Generates a valid Pydantic-compatible default response for any un-executed or skipped agent."""
    return {
        "agent": agent_name,
        "status": "skipped",
        "processing_time": 0.0,
        "confidence": 0.0,
        "input": {},
        "output": {"verdict_text": "Skipped"},
        "reasoning": [f"{agent_name} execution was skipped for this evidence payload."],
        "error": None
    }


class InvestigationOrchestratorAgent(BaseAgent):
    name = "Investigation Orchestrator"
    description = "Plans and manages multi-agent forensic investigations using LangGraph and provider-agnostic LLMs."
    capabilities = ["LangGraph State Graph", "Multi-LLM Planning", "Task Dispatch", "Failure Recovery"]

    def __init__(self):
        self.langgraph_engine = LangGraphEngine()

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        context.add_reasoning("Planner", f"Initializing multi-agent workspace for Case {context.case_id}...")

        # Run LangGraph State Graph Engine
        final_state = self.langgraph_engine.run(context)
        void = final_state  # state is stored inside context

        # Final Response Compilation with Pydantic-safe default fallbacks
        output = {
            "case_id":      context.case_id,
            "intake":       context.agent_results.get("Evidence Intake Agent") or _make_default_agent_res("Evidence Intake Agent"),
            "privacy":      context.agent_results.get("Privacy Shield Agent") or _make_default_agent_res("Privacy Shield Agent"),
            "enf":          context.agent_results.get("ENF Physics Agent") or _make_default_agent_res("ENF Physics Agent"),
            "corneal":      context.agent_results.get("Corneal Specular Topology Agent") or _make_default_agent_res("Corneal Specular Topology Agent"),
            "vision":       context.agent_results.get("Vision Intelligence Agent") or _make_default_agent_res("Vision Intelligence Agent"),
            "graph":        context.agent_results.get("Knowledge Graph Agent") or _make_default_agent_res("Knowledge Graph Agent"),
            "risk":         context.agent_results.get("Risk Assessment Agent") or _make_default_agent_res("Risk Assessment Agent"),
            "fusion":       context.agent_results.get("Intelligence Fusion Agent") or _make_default_agent_res("Intelligence Fusion Agent"),
            "legal_report": context.agent_results.get("Legal Reasoning Agent") or _make_default_agent_res("Legal Reasoning Agent"),
            "reasoning_chain": context.reasoning_chain,
        }

        return self.format_response(
            status="completed",
            processing_time=time.time() - start,
            confidence=100.0,
            input_data={"case_id": context.case_id},
            output_data=output,
            reasoning=[],
        )
