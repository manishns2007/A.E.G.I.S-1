"""
Agent 1: Investigation Orchestrator Agent
The primary brain of the A.E.G.I.S. platform. Uses Gemini Native Function Calling to plan execution flow,
select appropriate specialist agents, and coordinate execution.
Includes a procedural fallback loop if Gemini is offline.
"""
import os
import time
import json
from typing import Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import content_types

from .base_agent import BaseAgent, InvestigationContext

# Import all agents
from .intake_agent import EvidenceIntakeAgent
from .privacy_agent import PrivacyShieldAgent
from .enf_agent import ENFPhysicsAgent
from .corneal_agent import CornealTopologyAgent
from .vision_agent import VisionIntelligenceAgent
from .risk_agent import RiskAssessmentAgent
from .fusion_agent import IntelligenceFusionAgent
from .graph_agent import KnowledgeGraphAgent
from .legal_agent import LegalReasoningAgent

class InvestigationOrchestratorAgent(BaseAgent):
    name = "Investigation Orchestrator"
    description = "Plans and manages multi-agent forensic investigations using Gemini."
    capabilities = ["LLM Planning", "Agent Task Dispatch", "State Management", "Failure Recovery"]

    def __init__(self):
        # Instantiate pool
        self.intake_agent = EvidenceIntakeAgent()
        self.privacy_agent = PrivacyShieldAgent()
        self.enf_agent = ENFPhysicsAgent()
        self.corneal_agent = CornealTopologyAgent()
        self.vision_agent = VisionIntelligenceAgent()
        self.graph_agent = KnowledgeGraphAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.fusion_agent = IntelligenceFusionAgent()
        self.legal_agent = LegalReasoningAgent()
        
        self.agents_map = {
            "EvidenceIntakeAgent": self.intake_agent,
            "PrivacyShieldAgent": self.privacy_agent,
            "ENFPhysicsAgent": self.enf_agent,
            "CornealTopologyAgent": self.corneal_agent,
            "VisionIntelligenceAgent": self.vision_agent,
            "KnowledgeGraphAgent": self.graph_agent,
            "RiskAssessmentAgent": self.risk_agent,
            "IntelligenceFusionAgent": self.fusion_agent,
            "LegalReasoningAgent": self.legal_agent
        }

    def _get_agent_tools_schema(self):
        """Builds tool schemas for Gemini based on agent descriptions."""
        # Define mock Python functions to represent tools for Gemini
        def call_evidence_intake_agent():
            """Analyzes file metadata, extracts cryptographic hashes, and classifies media type."""
            pass
            
        def call_privacy_shield_agent():
            """Detects human faces and applies redaction to preserve subject privacy."""
            pass
            
        def call_enf_physics_agent():
            """Analyzes video luminance time-series to detect 50 Hz power grid hum. ONLY run on Video."""
            pass
            
        def call_corneal_topology_agent():
            """Analyzes specular reflections in eyes to detect AI-generated facial inconsistencies. Good for Images."""
            pass
            
        def call_vision_intelligence_agent():
            """Extracts semantic environmental entities and scene layout using a VLM."""
            pass
            
        def call_knowledge_graph_agent():
            """Compiles semantic entities into a relationship map. Requires VisionIntelligenceAgent to run first."""
            pass
            
        def call_risk_assessment_agent():
            """Evaluates findings from all forensic vectors to assign a Case Risk Level. Run before Fusion."""
            pass
            
        def call_intelligence_fusion_agent():
            """Synthesizes independent vectors into a unified verdict and leads. Run near the end."""
            pass
            
        def call_legal_reasoning_agent():
            """Formats the fused findings into a BSA-2023 compliant court document. Always run last."""
            pass
            
        return [
            call_evidence_intake_agent,
            call_privacy_shield_agent,
            call_enf_physics_agent,
            call_corneal_topology_agent,
            call_vision_intelligence_agent,
            call_knowledge_graph_agent,
            call_risk_assessment_agent,
            call_intelligence_fusion_agent,
            call_legal_reasoning_agent
        ]

    def _execute_agent(self, agent_name: str, context: InvestigationContext) -> Dict[str, Any]:
        """Executes a specialist agent and records its result."""
        agent = self.agents_map.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found."}
            
        # context.add_reasoning("Planner", f"Dispatching {agent.name}...")
        agent_res = agent.execute(context)
        context.agent_results[agent.name] = agent_res
        
        status = agent_res.get("status", "unknown")
        if status == "failed":
            context.add_reasoning("Planner", f"CRITICAL: {agent.name} encountered a fatal error. Investigation continuing.")
        elif status == "skipped":
            context.add_reasoning("Planner", f"{agent.name} was skipped. Reason: {agent_res.get('output', {}).get('verdict_text', 'N/A')}")
        else:
            # We don't need to add planner logs here if the agent already logs its own reasoning.
            pass
            
        # Return a summarized dict to Gemini
        return {
            "status": status,
            "confidence": agent_res.get("confidence"),
            "recommend_next": agent_res.get("recommend_next", [])
        }

    def _procedural_fallback(self, context: InvestigationContext):
        """Runs the deterministic fallback loop if LLM is offline."""
        context.add_reasoning("Planner", "WARNING: LLM Orchestrator offline. Switching to procedural fallback.")
        
        plan = [
            self.intake_agent, self.privacy_agent, self.enf_agent, self.corneal_agent,
            self.vision_agent, self.graph_agent, self.risk_agent, self.fusion_agent, self.legal_agent
        ]
        
        for agent in plan:
            context.add_reasoning("Planner", f"Dispatching task to {agent.name}...")
            agent_res = agent.execute(context)
            context.agent_results[agent.name] = agent_res

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        
        context.add_reasoning("Planner", f"Initializing multi-agent workspace for Case {context.case_id}...")
        
        # 1. Check Gemini Availability
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self._procedural_fallback(context)
        else:
            try:
                genai.configure(api_key=api_key)
                
                # Define system instructions for predictable conditional orchestration
                system_instruction = (
                    "You are the Investigation Orchestrator for A.E.G.I.S. "
                    "Your job is to select the next specialized forensic agent to run. "
                    "Rules:\n"
                    "1. Always run EvidenceIntakeAgent first to classify media.\n"
                    "2. Run PrivacyShieldAgent.\n"
                    "3. If media is Video, run ENFPhysicsAgent. If Image, run CornealTopologyAgent.\n"
                    "4. Run VisionIntelligenceAgent.\n"
                    "5. Run KnowledgeGraphAgent.\n"
                    "6. Run RiskAssessmentAgent.\n"
                    "7. Run IntelligenceFusionAgent.\n"
                    "8. Run LegalReasoningAgent last.\n"
                    "Call the appropriate function for the next agent based on the history. "
                    "When LegalReasoningAgent finishes, output 'FINISH' in text."
                )
                
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    tools=self._get_agent_tools_schema(),
                    system_instruction=system_instruction
                )
                
                chat = model.start_chat()
                context.add_reasoning("Planner", "LLM Orchestrator initialized. Commencing investigation.")
                
                # Initial trigger
                response = chat.send_message("Start the investigation.")
                
                max_turns = 12
                turns = 0
                
                while turns < max_turns:
                    turns += 1
                    
                    if not response.parts:
                        break
                        
                    part = response.parts[0]
                    
                    if "FINISH" in getattr(part, 'text', '') or "FINISH" in getattr(response, 'text', ''):
                        context.add_reasoning("Planner", "Investigation complete. Finalizing case.")
                        break
                        
                    if part.function_call:
                        func_name = part.function_call.name
                        # Map function name back to Agent string
                        agent_map_name = func_name.replace("call_", "").replace("_agent", "Agent").replace("_", " ").title().replace(" ", "")
                        
                        context.add_reasoning("Planner", f"Decided to invoke {agent_map_name} based on evidence state.")
                        
                        # Execute the agent
                        result = self._execute_agent(agent_map_name, context)
                        
                        # Send result back to Gemini
                        response = chat.send_message(
                            genai.types.Part.from_function_response(
                                name=func_name,
                                response={"result": result}
                            )
                        )
                    else:
                        # Sometimes it replies with text before a function call, just say continue
                        if "FINISH" not in response.text:
                            response = chat.send_message("Continue with the next agent.")
                        else:
                            break
                            
            except Exception as e:
                context.add_reasoning("Planner", f"LLM error: {str(e)}")
                self._procedural_fallback(context)

        # Final Response Compilation
        output = {
            "case_id": context.case_id,
            "intake": context.agent_results.get("Evidence Intake Agent", {}),
            "privacy": context.agent_results.get("Privacy Shield Agent", {}),
            "enf": context.agent_results.get("ENF Physics Agent", {}),
            "corneal": context.agent_results.get("Corneal Specular Topology Agent", {}),
            "vision": context.agent_results.get("Vision Intelligence Agent", {}),
            "graph": context.agent_results.get("Knowledge Graph Agent", {}),
            "risk": context.agent_results.get("Risk Assessment Agent", {}),
            "fusion": context.agent_results.get("Intelligence Fusion Agent", {}),
            "legal_report": context.agent_results.get("Legal Reasoning Agent", {}),
            "reasoning_chain": context.reasoning_chain
        }

        return self.format_response(
            status="completed",
            processing_time=time.time() - start,
            confidence=100.0,
            input_data={"case_id": context.case_id},
            output_data=output,
            reasoning=[]
        )
