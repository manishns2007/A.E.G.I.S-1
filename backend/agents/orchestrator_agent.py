"""
A.E.G.I.S. Investigation Orchestrator Agent
Coordinates all 10 specialist agents via LangGraph and returns the enriched
investigation state to the API layer.
"""
import time
from typing import Dict, Any

from .base_agent      import BaseAgent, InvestigationContext
from .langgraph_engine import LangGraphEngine


def _make_default_agent_res(agent_name: str) -> Dict[str, Any]:
    """Pydantic-safe default response for agents that were not executed."""
    return {
        "agent":           agent_name,
        "status":          "skipped",
        "processing_time": 0.0,
        "confidence":      0.0,
        "input":           {},
        "output":          {"verdict_text": "Not executed"},
        "reasoning":       [f"{agent_name} was not dispatched for this evidence type."],
        "error":           None,
        "limitations":     [],
        "recommend_next":  [],
        "required_followup": [],
        "new_entities":    [],
        "new_relationships": [],
        "new_hypotheses":  {},
        "resolved_hypotheses": [],
        "investigation_notes": [],
        "uncertainty":     "Not assessed",
    }


class InvestigationOrchestratorAgent(BaseAgent):
    name        = "Investigation Orchestrator"
    description = "Plans and manages 10-agent forensic investigations using LangGraph and provider-agnostic LLMs."
    capabilities = ["LangGraph State Graph", "Multi-LLM Planning", "Dynamic Replanning", "Failure Recovery"]

    def __init__(self):
        self.langgraph_engine = LangGraphEngine()

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        context.add_reasoning("Planner", f"Initializing A.E.G.I.S. Investigation Workspace for Case {context.case_id}.")
        context.add_reasoning("Planner", f"Media type: {'VIDEO' if context.is_video else 'IMAGE'}. Dispatching to LangGraph engine.")

        # Run LangGraph State Graph Engine
        final_state = self.langgraph_engine.run(context)

        # Collect evidence gap output
        gap_res   = context.agent_results.get("Evidence Gap Agent")
        gap_out   = (gap_res or {}).get("output", {})

        # Build investigation brief from real state
        brief = _build_investigation_brief(context, final_state, gap_out)

        output = {
            "case_id":     context.case_id,
            # ── 10 Agents ──────────────────────────────────────────────────────
            "intake":      context.agent_results.get("Evidence Intake Agent")           or _make_default_agent_res("Evidence Intake Agent"),
            "privacy":     context.agent_results.get("Privacy Shield Agent")            or _make_default_agent_res("Privacy Shield Agent"),
            "enf":         context.agent_results.get("ENF Physics Agent")               or _make_default_agent_res("ENF Physics Agent"),
            "corneal":     context.agent_results.get("Corneal Specular Topology Agent") or _make_default_agent_res("Corneal Specular Topology Agent"),
            "vision":      context.agent_results.get("Vision Intelligence Agent")       or _make_default_agent_res("Vision Intelligence Agent"),
            "graph":       context.agent_results.get("Knowledge Graph Agent")           or _make_default_agent_res("Knowledge Graph Agent"),
            "risk":        context.agent_results.get("Risk Assessment Agent")           or _make_default_agent_res("Risk Assessment Agent"),
            "fusion":      context.agent_results.get("Intelligence Fusion Agent")       or _make_default_agent_res("Intelligence Fusion Agent"),
            "evidence_gap": gap_res                                                     or _make_default_agent_res("Evidence Gap Agent"),
            "legal_report": context.agent_results.get("Legal Reasoning Agent")         or _make_default_agent_res("Legal Reasoning Agent"),
            # ── Investigation Memory ───────────────────────────────────────────
            "reasoning_chain":           context.reasoning_chain,
            "planner_steps":             final_state.get("planner_reasoning",      []),
            "investigation_timeline":    final_state.get("investigation_timeline", []),
            "confidence_evolution":      final_state.get("confidence_evolution",   []),
            "goals":                     final_state.get("goals",                  []),
            "hypotheses":                final_state.get("hypotheses",             {}),
            "active_vectors":            final_state.get("active_vectors",         []),
            "missing_vectors":           final_state.get("missing_vectors",        []),
            "environmental_entities":    final_state.get("environmental_entities", []),
            "knowledge_graph_growth":    final_state.get("knowledge_graph_growth", []),
            "human_review_required":     final_state.get("human_review_required", False),
            "court_ready":               final_state.get("court_ready", False),
            "investigation_brief":       brief,
        }

        return self.format_response(
            status="completed",
            processing_time=time.time() - start,
            confidence=100.0,
            input_data={"case_id": context.case_id, "is_video": context.is_video},
            output_data=output,
            reasoning=[],
        )


def _build_investigation_brief(
    context: InvestigationContext,
    final_state: Dict[str, Any],
    gap_out: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds a plain-English investigation brief from ACTUAL agent findings only.
    Never references evidence that does not exist in context.agent_results.
    """
    paragraphs = []

    intake_out   = context.agent_results.get("Evidence Intake Agent",           {}).get("output", {})
    privacy_out  = context.agent_results.get("Privacy Shield Agent",            {}).get("output", {})
    enf_out      = context.agent_results.get("ENF Physics Agent",               {}).get("output", {})
    corneal_out  = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
    vision_out   = context.agent_results.get("Vision Intelligence Agent",       {}).get("output", {})
    graph_out    = context.agent_results.get("Knowledge Graph Agent",           {}).get("output", {})
    risk_out     = context.agent_results.get("Risk Assessment Agent",           {}).get("output", {})
    fusion_out   = context.agent_results.get("Intelligence Fusion Agent",       {}).get("output", {})
    legal_out    = context.agent_results.get("Legal Reasoning Agent",           {}).get("output", {})

    # Custody summary
    sha = context.sha256 or intake_out.get("sha256", "Unavailable")
    meta = intake_out.get("metadata", {})
    res  = meta.get("resolution", "unknown")
    fps_v = meta.get("fps")
    fps_str = f" at {fps_v:.1f} FPS" if fps_v else ""
    paragraphs.append(
        f"Case {context.case_id}: Evidence file '{context.original_filename}' "
        f"({res}{fps_str}) registered and sealed under SHA-256 custody hash {sha[:24]}…"
    )

    # Privacy
    faces = privacy_out.get("count", 0)
    if privacy_out:
        paragraphs.append(
            f"Privacy Shield detected {faces} human subject(s) and applied Gaussian blur redaction "
            "to preserve investigator safety and downstream environmental analysis integrity."
        )

    # ENF
    if enf_out.get("is_enf_available"):
        enf_auth  = enf_out.get("is_authentic", True)
        enf_ratio = enf_out.get("enf_ratio", 0.0)
        verdict   = "confirmed 50Hz AC power grid electrical hum" if enf_auth else "detected ABSENT 50Hz AC grid hum"
        implication = "consistent with physical camera capture" if enf_auth else "consistent with AI-generated synthesis (no real-world grid exposure)"
        paragraphs.append(
            f"ENF Physics Agent analyzed video luminance time-series via SciPy FFT/STFT and "
            f"{verdict} (peak ratio {enf_ratio:.2f}), {implication}."
        )
    else:
        reason = enf_out.get("reason", "Static image input") if enf_out else "Not applicable for this evidence type"
        paragraphs.append(
            f"ENF Physics analysis was not performed: {reason}. "
            "To enable ENF evaluation, provide a continuous video recording (≥1.5 s, ≥12 FPS) under AC grid lighting."
        )

    # Corneal
    if corneal_out.get("is_quality_sufficient"):
        corn_auth = corneal_out.get("is_authentic", True)
        sym       = corneal_out.get("symmetry_score", 0.0)
        verdict   = "verified consistent specular symmetry" if corn_auth else "detected anomalous specular asymmetry"
        implication = "consistent with natural human eye" if corn_auth else "indicating possible AI facial synthesis"
        paragraphs.append(
            f"Corneal Specular Topology Agent {verdict} across {faces} eye region(s) "
            f"(symmetry score {sym:.1f}%), {implication}."
        )
    elif corneal_out:
        qual_r = corneal_out.get("quality_reason", corneal_out.get("verdict_text", "Quality insufficient"))
        paragraphs.append(
            f"Corneal analysis was inconclusive: {qual_r}. "
            "A high-resolution frontal portrait (≥800 px face width) is required."
        )

    # Vision
    vlm_status = vision_out.get("status", "offline")
    objs       = vision_out.get("environmental_objects", [])
    if vlm_status != "offline" and objs:
        obj_names = [o.get("entity") if isinstance(o, dict) else str(o) for o in objs[:5]]
        scene     = vision_out.get("scene_type", "Indoor environment")
        paragraphs.append(
            f"Vision Intelligence Agent extracted {len(objs)} environmental entities "
            f"({', '.join(obj_names)}) and classified scene as '{scene}', "
            "providing spatial anchors for knowledge graph construction."
        )
    elif vlm_status == "offline":
        paragraphs.append(
            f"Vision Intelligence Agent was offline (Gemini API key missing or quota exceeded). "
            "Environmental entity extraction was not performed. Set GEMINI_API_KEY to enable."
        )
    else:
        paragraphs.append("Vision Intelligence Agent ran but extracted no identifiable environmental entities from this evidence.")

    # Knowledge Graph
    g_nodes = graph_out.get("nodes", 0)
    g_edges = graph_out.get("edges", 0)
    if g_nodes > 1:
        paragraphs.append(
            f"Knowledge Graph Agent constructed a {g_nodes}-node, {g_edges}-edge relationship graph "
            "from extracted environmental entities. Cross-case historical database unavailable (no external DB connected)."
        )
    elif graph_out:
        paragraphs.append("Knowledge Graph construction was skipped: no environmental entities were available for graph nodes.")

    # Risk
    r_level = risk_out.get("risk_level", "UNKNOWN") if risk_out else "UNKNOWN"
    r_threat = risk_out.get("current_threat", "") if risk_out else ""
    if risk_out:
        paragraphs.append(f"Risk Assessment assigned threat level: {r_level}. {r_threat}")

    # Fusion verdict
    verdict_badge = fusion_out.get("verdict_badge", "") if fusion_out else ""
    fusion_conf   = fusion_out.get("overall_confidence", 0.0) if fusion_out else 0.0
    if verdict_badge:
        paragraphs.append(
            f"Intelligence Fusion consolidated all evidence vectors and issued verdict: "
            f"'{verdict_badge}' (confidence {fusion_conf:.1f}%)."
        )

    # Evidence Gap
    curr_conf = gap_out.get("current_confidence", 0.0)
    est_conf  = gap_out.get("estimated_confidence_after", 0.0)
    recs      = gap_out.get("recommendations", [])
    human_req = gap_out.get("human_review_required", False)
    if gap_out:
        paragraphs.append(
            f"Evidence Gap Agent measured investigation completeness at {curr_conf:.1f}% confidence. "
            f"With collection of missing evidence, confidence could reach {est_conf:.1f}%."
        )

    # Recommended next action
    next_action = recs[0] if recs else "No additional evidence collection required at this time."
    legal_admis = legal_out.get("verdict_badge", verdict_badge or "Pending legal review") if legal_out else "Pending legal review"

    brief = {
        "summary_paragraphs":    paragraphs,
        "recommended_next_action": next_action,
        "all_recommendations":   recs,
        "legal_admissibility":   legal_admis,
        "human_review_required": human_req,
        "current_confidence":    curr_conf,
        "estimated_confidence_after": est_conf,
        "verdict":               verdict_badge or legal_admis,
        "risk_level":            r_level,
    }
    return brief
