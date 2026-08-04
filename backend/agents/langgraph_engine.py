"""
A.E.G.I.S. LangGraph State Graph Engine
Manages the enriched InvestigationState, provider-agnostic LLM supervisor planning,
Goal Progression (Goal 1..5), Confidence & Hypothesis Evolution, Memory, Timeline, and Court Readiness.
"""
import time
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from .base_agent import InvestigationContext
from .llm_provider import ProviderFactory, ProceduralFallbackProvider, GeminiProvider

# Specialist Agents
from .intake_agent import EvidenceIntakeAgent
from .privacy_agent import PrivacyShieldAgent
from .enf_agent import ENFPhysicsAgent
from .corneal_agent import CornealTopologyAgent
from .vision_agent import VisionIntelligenceAgent
from .risk_agent import RiskAssessmentAgent
from .fusion_agent import IntelligenceFusionAgent
from .graph_agent import KnowledgeGraphAgent
from .legal_agent import LegalReasoningAgent


class InvestigationState(TypedDict):
    """Enriched LangGraph State Schema for A.E.G.I.S."""
    case_id: str
    media_type: str
    is_video: bool
    goals: List[Dict[str, Any]]
    current_goal_idx: int
    hypotheses: Dict[str, float]
    confidence_evolution: List[Dict[str, Any]]
    confidence_attribution: Dict[str, float]
    investigation_memory: Dict[str, List[str]]
    agent_recommendation_graph: List[Dict[str, Any]]
    investigation_timeline: List[Dict[str, Any]]
    completed_agents: List[str]
    skipped_agents: List[str]
    active_vectors: List[str]
    missing_vectors: List[str]
    environmental_entities: List[str]
    knowledge_graph_entities: List[str]
    planner_reasoning: List[Dict[str, Any]]
    court_ready: bool
    next_agent: str
    context: Any  # InvestigationContext reference


class LangGraphEngine:
    """LangGraph StateGraph Manager for A.E.G.I.S."""

    def __init__(self):
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

    def _planner_node(self, state: InvestigationState) -> InvestigationState:
        """Supervisor node: Uses LLMProvider to perform self-evaluation and select the next agent."""
        provider = ProviderFactory.get_provider()
        
        try:
            next_agent, reasoning, self_eval = provider.plan_next_agent(state)
        except Exception as e:
            fallback = ProceduralFallbackProvider()
            next_agent, reasoning, self_eval = fallback.plan_next_agent(state)
            reasoning = f"[{provider.name} error: {e}] -> {reasoning}"

        ctx: InvestigationContext = state["context"]
        ctx.add_reasoning("Planner", reasoning)

        planner_reasons = list(state.get("planner_reasoning", []))
        planner_reasons.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "provider": provider.name,
            "next_agent": next_agent,
            "reasoning": reasoning,
            "self_eval": self_eval
        })

        return {
            **state,
            "next_agent": next_agent,
            "planner_reasoning": planner_reasons,
            "reasoning_chain": ctx.reasoning_chain
        }

    def _make_agent_node(self, agent_name: str):
        """Creates a node handler for executing a specialized agent and updating shared state."""
        def node_fn(state: InvestigationState) -> InvestigationState:
            agent = self.agents_map[agent_name]
            ctx: InvestigationContext = state["context"]

            agent_res = agent.execute(ctx)
            ctx.agent_results[agent.name] = agent_res

            completed = list(state.get("completed_agents", []))
            skipped = list(state.get("skipped_agents", []))
            if agent_res.get("status") == "skipped":
                if agent_name not in skipped:
                    skipped.append(agent_name)
            else:
                if agent_name not in completed:
                    completed.append(agent_name)

            # Update active/missing vectors & attribution
            active = list(state.get("active_vectors", []))
            missing = list(state.get("missing_vectors", []))
            attribution = dict(state.get("confidence_attribution", {}))
            
            # Memory tracking
            memory = dict(state.get("investigation_memory", {"unresolved_issues": [], "resolved_issues": [], "missing_evidence": []}))
            unresolved = list(memory.get("unresolved_issues", []))
            resolved = list(memory.get("resolved_issues", []))
            missing_ev = list(memory.get("missing_evidence", []))

            # Hypotheses evolution
            hypo = dict(state.get("hypotheses", {"Authentic Media Record": 0.50, "Synthetic AI Fabrication": 0.50}))

            if agent_name == "ENFPhysicsAgent":
                if agent_res.get("output", {}).get("is_enf_available"):
                    active.append("ENF Power Spectrum")
                    attribution["ENF Physics"] = 0.40
                    if agent_res.get("output", {}).get("is_authentic"):
                        hypo["Authentic Media Record"] = min(0.95, hypo["Authentic Media Record"] + 0.35)
                        hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    else:
                        hypo["Synthetic AI Fabrication"] = min(0.95, hypo["Synthetic AI Fabrication"] + 0.40)
                        hypo["Authentic Media Record"] = max(0.05, 1.0 - hypo["Synthetic AI Fabrication"])
                    resolved.append("ENF 50Hz Grid Physics")
                else:
                    missing.append("ENF Power Spectrum")
                    missing_ev.append("ENF Power Spectrum (Static Image / Low FPS)")

            elif agent_name == "CornealTopologyAgent":
                if agent_res.get("output", {}).get("is_quality_sufficient"):
                    active.append("Corneal Specular Topology")
                    attribution["Corneal Specular Topology"] = 0.30
                    if agent_res.get("output", {}).get("is_authentic"):
                        hypo["Authentic Media Record"] = min(0.95, hypo["Authentic Media Record"] + 0.25)
                        hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    else:
                        hypo["Synthetic AI Fabrication"] = min(0.95, hypo["Synthetic AI Fabrication"] + 0.35)
                        hypo["Authentic Media Record"] = max(0.05, 1.0 - hypo["Synthetic AI Fabrication"])
                    resolved.append("Corneal Reflection Symmetry")
                else:
                    missing.append("Corneal Specular Topology")
                    missing_ev.append("Corneal Reflection (Blurry / No Face)")

            elif agent_name == "VisionIntelligenceAgent":
                objs = agent_res.get("output", {}).get("environmental_objects", [])
                if objs:
                    attribution["Vision VLM Scene"] = 0.15
                    hypo["Authentic Media Record"] = min(0.95, hypo["Authentic Media Record"] + 0.15)
                    hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    resolved.append("Room Background Anchors")

            # Update Confidence Evolution History
            conf_evo = list(state.get("confidence_evolution", []))
            conf_evo.append({
                "step": len(conf_evo) + 1,
                "agent": agent_name,
                "authentic_prob": round(hypo["Authentic Media Record"], 2),
                "synthetic_prob": round(hypo["Synthetic AI Fabrication"], 2),
                "attribution": dict(attribution)
            })

            # Record Agent Recommendations into Graph
            recs_graph = list(state.get("agent_recommendation_graph", []))
            if agent_res.get("recommend_next"):
                recs_graph.append({
                    "from_agent": agent_name,
                    "recommended_next": agent_res.get("recommend_next"),
                    "reasoning": agent_res.get("reasoning", [])
                })

            # Update Timeline
            timeline = list(state.get("investigation_timeline", []))
            timeline.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "agent": agent_name,
                "status": agent_res.get("status"),
                "event": f"{agent.name} executed. Finding: {agent_res.get('output', {}).get('verdict_text', 'Completed')}"
            })

            # Update Goals Progression
            goals = [dict(g) for g in state.get("goals", [])]
            curr_goal_idx = state.get("current_goal_idx", 0)

            if agent_name in ["EvidenceIntakeAgent", "PrivacyShieldAgent", "ENFPhysicsAgent", "CornealTopologyAgent"]:
                goals[0]["progress"] = min(100, goals[0].get("progress", 0) + 33)
                if goals[0]["progress"] == 100:
                    goals[0]["status"] = "COMPLETED"
                    curr_goal_idx = max(curr_goal_idx, 1)

            if agent_name in ["VisionIntelligenceAgent"]:
                goals[1]["progress"] = 100
                goals[1]["status"] = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 2)

            if agent_name in ["KnowledgeGraphAgent"]:
                goals[2]["progress"] = 100
                goals[2]["status"] = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 3)

            if agent_name in ["RiskAssessmentAgent", "IntelligenceFusionAgent"]:
                goals[3]["progress"] = 100
                goals[3]["status"] = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 4)

            court_ready = state.get("court_ready", False)
            if agent_name == "LegalReasoningAgent":
                goals[4]["progress"] = 100
                goals[4]["status"] = "COMPLETED"
                court_ready = True

            memory["unresolved_issues"] = unresolved
            memory["resolved_issues"] = resolved
            memory["missing_evidence"] = missing_ev

            return {
                **state,
                "goals": goals,
                "current_goal_idx": curr_goal_idx,
                "hypotheses": hypo,
                "confidence_evolution": conf_evo,
                "confidence_attribution": attribution,
                "investigation_memory": memory,
                "agent_recommendation_graph": recs_graph,
                "investigation_timeline": timeline,
                "completed_agents": completed,
                "skipped_agents": skipped,
                "active_vectors": active,
                "missing_vectors": missing,
                "court_ready": court_ready,
                "reasoning_chain": ctx.reasoning_chain
            }

        return node_fn

    def build_graph(self):
        """Builds and compiles the LangGraph StateGraph."""
        builder = StateGraph(InvestigationState)

        builder.add_node("supervisor", self._planner_node)

        for agent_name in self.agents_map:
            builder.add_node(agent_name, self._make_agent_node(agent_name))

        builder.set_entry_point("supervisor")

        def router_edge(state: InvestigationState) -> str:
            next_agent = state.get("next_agent", "FINISH")
            if next_agent == "FINISH" or state.get("court_ready", False):
                return END
            return next_agent if next_agent in self.agents_map else END

        builder.add_conditional_edges("supervisor", router_edge)

        for agent_name in self.agents_map:
            builder.add_edge(agent_name, "supervisor")

        return builder.compile()

    def run(self, context: InvestigationContext) -> Dict[str, Any]:
        """Runs the LangGraph engine to completion for an InvestigationContext."""
        default_goals = [
            {"goal": "Authenticate Media", "progress": 0, "status": "IN_PROGRESS"},
            {"goal": "Extract Environmental Intelligence", "progress": 0, "status": "PENDING"},
            {"goal": "Correlate Evidence", "progress": 0, "status": "PENDING"},
            {"goal": "Assess Investigative Risk", "progress": 0, "status": "PENDING"},
            {"goal": "Generate Legally Admissible Report", "progress": 0, "status": "PENDING"}
        ]

        initial_state: InvestigationState = {
            "case_id": context.case_id,
            "media_type": "VIDEO" if context.is_video else "IMAGE",
            "is_video": context.is_video,
            "goals": default_goals,
            "current_goal_idx": 0,
            "hypotheses": {"Authentic Media Record": 0.50, "Synthetic AI Fabrication": 0.50},
            "confidence_evolution": [],
            "confidence_attribution": {},
            "investigation_memory": {"unresolved_issues": ["Authenticity unverified", "Room geometry unknown"], "resolved_issues": [], "missing_evidence": []},
            "agent_recommendation_graph": [],
            "investigation_timeline": [{"timestamp": datetime.now().strftime("%H:%M:%S"), "agent": "System", "status": "completed", "event": f"Case {context.case_id} registered."}],
            "completed_agents": [],
            "skipped_agents": [],
            "active_vectors": [],
            "missing_vectors": [],
            "environmental_entities": [],
            "knowledge_graph_entities": [],
            "planner_reasoning": [],
            "court_ready": False,
            "next_agent": "EvidenceIntakeAgent",
            "context": context
        }

        graph = self.build_graph()
        final_state = graph.invoke(initial_state)

        return final_state
