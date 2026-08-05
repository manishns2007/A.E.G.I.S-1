"""
A.E.G.I.S. LangGraph State Graph Engine — Enhanced PoC Edition
================================================================
Manages the enriched InvestigationState with:
- 10 specialist agents including Evidence Gap Agent
- Dynamic LLM-driven planning at every step (Groq → Gemini → Procedural)
- Structured planner reasoning (goal / uncertainty / evidence / reason / benefit)
- 6 investigation goals with live progress tracking
- Confidence & hypothesis evolution timeline
- Knowledge graph growth steps
- Challenge loop before Legal Agent
- Human-in-the-Loop interrupt when confidence < 60%
- Evidence gap analysis integrated into state
"""
import time
import json
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from .base_agent import InvestigationContext
from .llm_provider import ProviderFactory, ProceduralFallbackProvider, VALID_AGENTS

# Specialist Agents
from .intake_agent    import EvidenceIntakeAgent
from .privacy_agent   import PrivacyShieldAgent
from .enf_agent       import ENFPhysicsAgent
from .corneal_agent   import CornealTopologyAgent
from .vision_agent    import VisionIntelligenceAgent
from .graph_agent     import KnowledgeGraphAgent
from .risk_agent      import RiskAssessmentAgent
from .fusion_agent    import IntelligenceFusionAgent
from .evidence_gap_agent import EvidenceGapAgent
from .legal_agent     import LegalReasoningAgent


# ── State Schema ──────────────────────────────────────────────────────────────

class InvestigationState(TypedDict):
    """Enriched LangGraph State — the central memory of A.E.G.I.S."""
    case_id:               str
    media_type:            str          # "VIDEO" | "IMAGE"
    is_video:              bool
    goals:                 List[Dict[str, Any]]
    current_goal_idx:      int
    hypotheses:            Dict[str, float]
    confidence_evolution:  List[Dict[str, Any]]
    confidence_attribution: Dict[str, float]
    investigation_memory:  Dict[str, List[str]]
    agent_recommendation_graph: List[Dict[str, Any]]
    investigation_timeline: List[Dict[str, Any]]
    completed_agents:      List[str]
    skipped_agents:        List[str]
    active_vectors:        List[str]
    missing_vectors:       List[str]
    environmental_entities: List[str]
    knowledge_graph_entities: List[str]
    knowledge_graph_growth: List[Dict[str, Any]]   # snapshots of graph growth
    planner_reasoning:     List[Dict[str, Any]]     # structured planner steps
    court_ready:           bool
    human_review_required: bool
    next_agent:            str
    context:               Any   # InvestigationContext


# ── LangGraph Engine ──────────────────────────────────────────────────────────

class LangGraphEngine:
    """Builds and runs the A.E.G.I.S. LangGraph state graph."""

    def __init__(self):
        self.intake_agent   = EvidenceIntakeAgent()
        self.privacy_agent  = PrivacyShieldAgent()
        self.enf_agent      = ENFPhysicsAgent()
        self.corneal_agent  = CornealTopologyAgent()
        self.vision_agent   = VisionIntelligenceAgent()
        self.graph_agent    = KnowledgeGraphAgent()
        self.risk_agent     = RiskAssessmentAgent()
        self.fusion_agent   = IntelligenceFusionAgent()
        self.gap_agent      = EvidenceGapAgent()
        self.legal_agent    = LegalReasoningAgent()

        self.agents_map: Dict[str, Any] = {
            "EvidenceIntakeAgent":    self.intake_agent,
            "PrivacyShieldAgent":     self.privacy_agent,
            "ENFPhysicsAgent":        self.enf_agent,
            "CornealTopologyAgent":   self.corneal_agent,
            "VisionIntelligenceAgent": self.vision_agent,
            "KnowledgeGraphAgent":    self.graph_agent,
            "RiskAssessmentAgent":    self.risk_agent,
            "IntelligenceFusionAgent": self.fusion_agent,
            "EvidenceGapAgent":       self.gap_agent,
            "LegalReasoningAgent":    self.legal_agent,
        }

    # ── Planner Node ──────────────────────────────────────────────────────────

    def _planner_node(self, state: InvestigationState) -> InvestigationState:
        """Dynamic Supervisor: reads InvestigationState and selects the next agent."""
        provider = ProviderFactory.get_provider()
        ctx: InvestigationContext = state["context"]

        try:
            next_agent, planner_output, _raw = provider.plan_next_agent(state)
        except Exception as e:
            fallback = ProceduralFallbackProvider()
            next_agent, planner_output, _raw = fallback.plan_next_agent(state)
            planner_output["_provider_error"] = str(e)

        # Build human-readable reasoning chain entries
        current_goal    = planner_output.get("current_goal",        "Investigate evidence")
        uncertainty     = planner_output.get("current_uncertainty",  "Unknown")
        evidence        = planner_output.get("current_evidence",     "None yet")
        reason          = planner_output.get("reason_for_selection", "Next logical step")
        benefit         = planner_output.get("expected_benefit",     "Reduce uncertainty")
        updated_hypo    = planner_output.get("updated_hypothesis",   "Pending")

        # Emit structured reasoning into the shared chain
        ctx.add_reasoning("Planner", f"Current Goal: {current_goal}")
        ctx.add_reasoning("Planner", f"Current Uncertainty: {uncertainty}")
        ctx.add_reasoning("Planner", f"Current Evidence: {evidence}")
        ctx.add_reasoning("Planner", f"Decision: Dispatch {next_agent}")
        ctx.add_reasoning("Planner", f"Reason: {reason}")
        ctx.add_reasoning("Planner", f"Expected Benefit: {benefit}")
        ctx.add_reasoning("Planner", f"Updated Hypothesis: {updated_hypo}")

        # Emit agent_start event so the browser knows which agent is being dispatched
        if next_agent and next_agent not in ("FINISH", "HUMAN_REVIEW"):
            ctx.emit("agent_start", {
                "agent": next_agent,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

        # Accumulate structured planner steps
        planner_steps = list(state.get("planner_reasoning", []))
        planner_steps.append({
            "timestamp":         datetime.now().strftime("%H:%M:%S"),
            "provider":          provider.name,
            "step":              len(planner_steps) + 1,
            "current_goal":      current_goal,
            "current_uncertainty": uncertainty,
            "current_evidence":  evidence,
            "next_agent":        next_agent,
            "reason":            reason,
            "expected_benefit":  benefit,
            "updated_hypothesis": updated_hypo,
            "what_i_know":       planner_output.get("what_i_know", []),
            "what_i_dont_know":  planner_output.get("what_i_dont_know", []),
        })

        human_review = (next_agent == "HUMAN_REVIEW")

        return {
            **state,
            "next_agent":            next_agent if next_agent in self.agents_map else ("FINISH" if not human_review else "HUMAN_REVIEW"),
            "planner_reasoning":     planner_steps,
            "human_review_required": human_review,
        }

    # ── Agent Node Factory ────────────────────────────────────────────────────

    def _make_agent_node(self, agent_name: str):
        """Creates a LangGraph node handler for a specialist agent."""
        def node_fn(state: InvestigationState) -> InvestigationState:
            agent = self.agents_map[agent_name]
            ctx: InvestigationContext = state["context"]

            ts_start = datetime.now().strftime("%H:%M:%S")
            ctx.add_reasoning(agent.name.upper(), f"Agent dispatched at {ts_start}.")

            agent_res = agent.execute(ctx)
            ctx.agent_results[agent.name] = agent_res

            status = agent_res.get("status", "completed")

            # Emit agent_done event immediately after the agent completes
            ctx.emit("agent_done", {
                "key": agent_name,
                "agent": agent_res
            })
            completed = list(state.get("completed_agents", []))
            skipped   = list(state.get("skipped_agents", []))

            if status == "skipped":
                if agent_name not in skipped:
                    skipped.append(agent_name)
            else:
                if agent_name not in completed:
                    completed.append(agent_name)

            # ── Evidence vector tracking ──────────────────────────────────────
            active  = list(state.get("active_vectors",  []))
            missing = list(state.get("missing_vectors", []))
            attribution = dict(state.get("confidence_attribution", {}))
            memory  = {
                k: list(v) for k, v in state.get("investigation_memory", {
                    "unresolved_issues": [],
                    "resolved_issues":   [],
                    "missing_evidence":  []
                }).items()
            }

            env_ents  = list(state.get("environmental_entities",    []))
            kg_ents   = list(state.get("knowledge_graph_entities", []))
            kg_growth = list(state.get("knowledge_graph_growth",   []))

            # ── Hypothesis evolution ──────────────────────────────────────────
            hypo = dict(state.get("hypotheses", {
                "Authentic Media Record":   0.50,
                "Synthetic AI Fabrication": 0.50
            }))

            output = agent_res.get("output", {})

            if agent_name == "ENFPhysicsAgent":
                if output.get("is_enf_available"):
                    active.append("ENF Power Spectrum (50Hz Grid)")
                    attribution["ENF Physics"] = 40.0
                    if output.get("is_authentic"):
                        hypo["Authentic Media Record"]   = min(0.95, hypo["Authentic Media Record"] + 0.35)
                        hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    else:
                        hypo["Synthetic AI Fabrication"] = min(0.95, hypo["Synthetic AI Fabrication"] + 0.40)
                        hypo["Authentic Media Record"]   = max(0.05, 1.0 - hypo["Synthetic AI Fabrication"])
                    memory["resolved_issues"].append("ENF 50Hz Grid Physics")
                    ctx.add_reasoning(agent.name.upper(), f"ENF ratio: {output.get('enf_ratio', 0):.2f}. Authentic: {output.get('is_authentic')}.")
                else:
                    missing.append("ENF Power Spectrum")
                    memory["missing_evidence"].append(f"ENF Power Spectrum: {output.get('reason', 'Unavailable')}")
                    ctx.add_reasoning(agent.name.upper(), f"ENF unavailable: {output.get('reason', 'N/A')}")

            elif agent_name == "CornealTopologyAgent":
                if output.get("is_quality_sufficient"):
                    active.append("Corneal Specular Topology")
                    attribution["Corneal Topology"] = 30.0
                    if output.get("is_authentic"):
                        hypo["Authentic Media Record"]   = min(0.95, hypo["Authentic Media Record"] + 0.25)
                        hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    else:
                        hypo["Synthetic AI Fabrication"] = min(0.95, hypo["Synthetic AI Fabrication"] + 0.35)
                        hypo["Authentic Media Record"]   = max(0.05, 1.0 - hypo["Synthetic AI Fabrication"])
                    memory["resolved_issues"].append("Corneal Reflection Symmetry")
                    ctx.add_reasoning(agent.name.upper(), f"Symmetry: {output.get('symmetry_score', 0):.1f}%. Authentic: {output.get('is_authentic')}.")
                else:
                    missing.append("Corneal Specular Topology")
                    memory["missing_evidence"].append(f"Corneal: {output.get('quality_reason', 'Insufficient quality')}")
                    ctx.add_reasoning(agent.name.upper(), f"Corneal insufficient quality: {output.get('quality_reason', 'N/A')}")

            elif agent_name == "VisionIntelligenceAgent":
                objs = output.get("environmental_objects", [])
                if objs:
                    attribution["Vision VLM"] = 15.0
                    hypo["Authentic Media Record"]   = min(0.95, hypo["Authentic Media Record"] + 0.12)
                    hypo["Synthetic AI Fabrication"] = max(0.05, 1.0 - hypo["Authentic Media Record"])
                    memory["resolved_issues"].append("Room Background Anchors")
                    # Add entity names to shared state
                    for o in objs:
                        name = o.get("entity") if isinstance(o, dict) else str(o)
                        if name not in env_ents:
                            env_ents.append(name)
                    ctx.add_reasoning(agent.name.upper(), f"Extracted {len(objs)} entities: {', '.join(env_ents[:5])}.")
                else:
                    vlm_status = output.get("status", "offline")
                    memory["missing_evidence"].append(f"Vision entities: {output.get('error', 'None found')}")
                    ctx.add_reasoning(agent.name.upper(), f"Vision status: {vlm_status}. Zero entities found.")

            elif agent_name == "KnowledgeGraphAgent":
                nodes = output.get("nodes", 0)
                edges = output.get("edges", 0)
                mapped = output.get("entities_mapped", [])
                kg_ents.extend([e for e in mapped if e not in kg_ents])
                kg_step = {
                    "step":      len(kg_growth) + 1,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "nodes":     nodes,
                    "edges":     edges,
                    "entities":  list(mapped)
                }
                kg_growth.append(kg_step)
                ctx.emit("graph_update", kg_step)
                ctx.add_reasoning(agent.name.upper(), f"Graph: {nodes} nodes, {edges} edges. Entities: {', '.join(mapped[:5])}.")

            elif agent_name == "EvidenceGapAgent":
                gap = output
                current_conf = gap.get("current_confidence", 50.0)
                estimated    = gap.get("estimated_confidence_after", 50.0)
                human_req    = gap.get("human_review_required", False)
                ctx.add_reasoning(
                    agent.name.upper(),
                    f"Confidence: {current_conf:.1f}%. Achievable: {estimated:.1f}%. "
                    f"Active vectors: {len(gap.get('available_vectors', []))}. "
                    f"Missing: {len(gap.get('missing_vectors', []))}."
                    f"{' ⚠ HUMAN REVIEW REQUIRED.' if human_req else ''}"
                )

            # ── Confidence Evolution History ──────────────────────────────────
            conf_evo = list(state.get("confidence_evolution", []))
            new_conf_point = {
                "step":           len(conf_evo) + 1,
                "timestamp":      datetime.now().strftime("%H:%M:%S"),
                "agent":          agent_name,
                "agent_label":    agent.name,
                "authentic_prob": round(hypo["Authentic Media Record"],   3),
                "synthetic_prob": round(hypo["Synthetic AI Fabrication"], 3),
                "attribution":    dict(attribution)
            }
            conf_evo.append(new_conf_point)
            # Emit live hypothesis update
            ctx.emit("hypothesis", new_conf_point)

            # ── Recommendation Graph ──────────────────────────────────────────
            recs_graph = list(state.get("agent_recommendation_graph", []))
            if agent_res.get("recommend_next"):
                recs_graph.append({
                    "from_agent":       agent_name,
                    "recommended_next": agent_res["recommend_next"],
                    "reasoning":        agent_res.get("reasoning", [])[:2]
                })

            # ── Timeline ──────────────────────────────────────────────────────
            timeline = list(state.get("investigation_timeline", []))
            verdict_text = (output.get("verdict_text") or
                            output.get("verdict_badge") or
                            f"{agent_name} completed")
            timeline.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "agent":     agent_name,
                "label":     agent.name,
                "status":    status,
                "event":     f"{agent.name} — {verdict_text}"
            })

            # ── Goals progression ─────────────────────────────────────────────
            goals = [dict(g) for g in state.get("goals", [])]
            curr_goal_idx = state.get("current_goal_idx", 0)

            # Goal 1: Authenticate Media
            if agent_name in ["EvidenceIntakeAgent", "ENFPhysicsAgent", "CornealTopologyAgent"]:
                goals[0]["progress"] = min(100, goals[0].get("progress", 0) + 40)
                if goals[0]["progress"] >= 100:
                    goals[0]["status"] = "COMPLETED"
                    curr_goal_idx = max(curr_goal_idx, 1)
                else:
                    goals[0]["status"] = "IN_PROGRESS"
            # Goal 2: Protect Investigator
            if agent_name == "PrivacyShieldAgent":
                goals[1]["progress"] = 100
                goals[1]["status"]   = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 2)
            # Goal 3: Extract Environmental Intelligence
            if agent_name == "VisionIntelligenceAgent":
                goals[2]["progress"] = 100
                goals[2]["status"]   = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 3)
            # Goal 4: Correlate Evidence
            if agent_name == "KnowledgeGraphAgent":
                goals[3]["progress"] = 100
                goals[3]["status"]   = "COMPLETED"
                curr_goal_idx = max(curr_goal_idx, 4)
            # Goal 5: Assess Risk
            if agent_name in ["RiskAssessmentAgent", "IntelligenceFusionAgent", "EvidenceGapAgent"]:
                goals[4]["progress"] = min(100, goals[4].get("progress", 0) + 40)
                if goals[4]["progress"] >= 100:
                    goals[4]["status"] = "COMPLETED"
                    curr_goal_idx = max(curr_goal_idx, 5)
            # Goal 6: Generate Legal Report
            if agent_name == "LegalReasoningAgent":
                goals[5]["progress"] = 100
                goals[5]["status"]   = "COMPLETED"

            court_ready = state.get("court_ready", False)
            if agent_name == "LegalReasoningAgent" and status == "completed":
                court_ready = True

            return {
                **state,
                "goals":                     goals,
                "current_goal_idx":          curr_goal_idx,
                "hypotheses":                hypo,
                "confidence_evolution":      conf_evo,
                "confidence_attribution":    attribution,
                "investigation_memory":      memory,
                "agent_recommendation_graph": recs_graph,
                "investigation_timeline":    timeline,
                "completed_agents":          completed,
                "skipped_agents":            skipped,
                "active_vectors":            active,
                "missing_vectors":           missing,
                "environmental_entities":    env_ents,
                "knowledge_graph_entities":  kg_ents,
                "knowledge_graph_growth":    kg_growth,
                "court_ready":               court_ready,
            }

        return node_fn

    # ── Graph Builder ─────────────────────────────────────────────────────────

    def build_graph(self):
        """Builds and compiles the LangGraph StateGraph."""
        builder = StateGraph(InvestigationState)
        builder.add_node("supervisor", self._planner_node)

        for agent_name in self.agents_map:
            builder.add_node(agent_name, self._make_agent_node(agent_name))

        builder.set_entry_point("supervisor")

        def router_edge(state: InvestigationState) -> str:
            next_ag = state.get("next_agent", "FINISH")
            if state.get("court_ready") or next_ag == "FINISH":
                return END
            if next_ag == "HUMAN_REVIEW":
                return END    # Pause for human input
            if next_ag in self.agents_map:
                return next_ag
            return END

        builder.add_conditional_edges("supervisor", router_edge)

        for agent_name in self.agents_map:
            builder.add_edge(agent_name, "supervisor")

        return builder.compile()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, context: InvestigationContext) -> Dict[str, Any]:
        """Runs the LangGraph engine to completion."""
        default_goals = [
            {"goal": "Authenticate Media",                  "progress": 0,  "status": "IN_PROGRESS"},
            {"goal": "Protect Investigator",                "progress": 0,  "status": "PENDING"},
            {"goal": "Extract Environmental Intelligence",  "progress": 0,  "status": "PENDING"},
            {"goal": "Correlate Evidence",                  "progress": 0,  "status": "PENDING"},
            {"goal": "Assess Investigative Risk",           "progress": 0,  "status": "PENDING"},
            {"goal": "Generate Legal Report",               "progress": 0,  "status": "PENDING"},
        ]

        initial_state: InvestigationState = {
            "case_id":               context.case_id,
            "media_type":            "VIDEO" if context.is_video else "IMAGE",
            "is_video":              context.is_video,
            "goals":                 default_goals,
            "current_goal_idx":      0,
            "hypotheses":            {
                "Authentic Media Record":   0.50,
                "Synthetic AI Fabrication": 0.50
            },
            "confidence_evolution":  [],
            "confidence_attribution": {},
            "investigation_memory":  {
                "unresolved_issues": ["Authenticity unverified", "Room environment unknown"],
                "resolved_issues":   [],
                "missing_evidence":  []
            },
            "agent_recommendation_graph": [],
            "investigation_timeline": [{
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "agent":     "System",
                "label":     "A.E.G.I.S.",
                "status":    "completed",
                "event":     f"Case {context.case_id} registered. Media type: {'VIDEO' if context.is_video else 'IMAGE'}."
            }],
            "completed_agents":        [],
            "skipped_agents":          [],
            "active_vectors":          [],
            "missing_vectors":         [],
            "environmental_entities":  [],
            "knowledge_graph_entities": [],
            "knowledge_graph_growth":  [],
            "planner_reasoning":       [],
            "court_ready":             False,
            "human_review_required":   False,
            "next_agent":              "EvidenceIntakeAgent",
            "context":                 context,
        }

        graph = self.build_graph()
        final_state = graph.invoke(initial_state)
        return final_state
