"""
A.E.G.I.S. Enhanced LLM Provider Layer
=======================================
Supports Groq (Llama-3), Gemini, and Procedural Fallback with automatic provider
priority selection and failover.

STRICT RULES
------------
1. LLM providers ONLY handle orchestration reasoning — they NEVER generate
   forensic conclusions or alter physical vector findings.
2. The Planner MUST always observe live InvestigationState before deciding.
3. ProceduralFallbackProvider uses actual state fields (face count, FPS, ENF
   availability, Vision entity count, etc.) — it is NOT a fixed pipeline.
4. Planner output is structured: current_goal, current_uncertainty,
   current_evidence, next_agent, reason_for_selection, expected_benefit,
   updated_hypothesis.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List

# ── Valid dispatch targets ────────────────────────────────────────────────────
VALID_AGENTS = [
    "EvidenceIntakeAgent",
    "PrivacyShieldAgent",
    "ENFPhysicsAgent",
    "CornealTopologyAgent",
    "VisionIntelligenceAgent",
    "KnowledgeGraphAgent",
    "RiskAssessmentAgent",
    "IntelligenceFusionAgent",
    "EvidenceGapAgent",
    "LegalReasoningAgent",
    "FINISH",
    "HUMAN_REVIEW",
]

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Senior Investigation Supervisor (Planner) for A.E.G.I.S.,
a multi-agent forensic intelligence platform.

Your ONLY job is to PLAN. You NEVER generate forensic conclusions.
All evidence facts come from specialist agents — you only decide WHO to send next.

At each step you will receive the live InvestigationState containing:
- Media type (IMAGE / VIDEO)
- Completed agents and their findings
- Current hypotheses (Authentic vs Synthetic probabilities)
- Environmental entities discovered
- Knowledge graph size
- Pending investigation goals
- Missing evidence vectors
- Overall confidence level

THINK LIKE A SENIOR INVESTIGATION OFFICER:
1. What do I currently know?
2. What do I NOT know yet?
3. Which hypothesis is currently strongest?
4. Which specialist will reduce the most uncertainty?
5. Is confidence sufficient to proceed to legal, or do I need more evidence?
6. Should the investigation pause for human review?

AGENT DISPATCH RULES (apply dynamically based on state):
- EvidenceIntakeAgent: Always first if not completed
- PrivacyShieldAgent: Always second if not completed (protects investigators)
- ENFPhysicsAgent: Only if media_type == VIDEO AND not completed
- CornealTopologyAgent: Only if media_type == IMAGE AND not completed
- VisionIntelligenceAgent: After Privacy if not completed; provides environmental anchors
- KnowledgeGraphAgent: Only after VisionIntelligenceAgent AND vision has > 0 entities
- RiskAssessmentAgent: After physical vectors (ENF/Corneal) and Vision are complete
- IntelligenceFusionAgent: After Risk Assessment
- EvidenceGapAgent: After Fusion — identifies missing evidence BEFORE legal report
- LegalReasoningAgent: Always LAST after EvidenceGapAgent
- FINISH: After LegalReasoningAgent completes
- HUMAN_REVIEW: When confidence < 60% AND critical evidence is missing

SKIP LOGIC (adapt dynamically):
- Skip KnowledgeGraphAgent if Vision entities == 0
- Skip ENFPhysicsAgent for IMAGE inputs
- Skip CornealTopologyAgent for VIDEO inputs
- Skip KnowledgeGraphAgent if VisionIntelligenceAgent failed/offline

CHALLENGE SELF before dispatching LegalReasoningAgent:
- Is the strongest hypothesis supported by >= 2 active forensic vectors?
- Is there any counter-evidence that contradicts it?
- If confidence < 60%, return HUMAN_REVIEW instead of LegalReasoningAgent

Respond with ONLY valid JSON (no markdown, no code fences):
{
  "current_goal": "<1 sentence: what the investigation is trying to achieve right now>",
  "current_uncertainty": "<1 sentence: what is not yet known>",
  "current_evidence": "<1 sentence: what has been established so far>",
  "next_agent": "<AgentClassName or FINISH or HUMAN_REVIEW>",
  "reason_for_selection": "<1-2 sentences: WHY this agent, based on state>",
  "expected_benefit": "<1 sentence: what uncertainty this dispatch will reduce>",
  "updated_hypothesis": "<strongest hypothesis with rough probability e.g. 'Authentic 74%, Synthetic 26%'>",
  "what_i_know": ["<fact1>", "<fact2>"],
  "what_i_dont_know": ["<uncertainty1>", "<uncertainty2>"]
}
"""

# ── Abstract base ─────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract interface for LLM Orchestration Providers."""
    name: str = "BaseProvider"

    @abstractmethod
    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Returns (next_agent_name, structured_planner_output, raw_response_dict).
        structured_planner_output contains all planner reasoning fields.
        """
        pass


def _build_state_summary(state: Dict[str, Any]) -> str:
    """Build a compact, information-dense state summary for LLM context."""
    completed = state.get("completed_agents", [])
    skipped   = state.get("skipped_agents", [])
    is_video  = state.get("is_video", False)
    hypo      = state.get("hypotheses", {})
    memory    = state.get("investigation_memory", {})
    active_v  = state.get("active_vectors", [])
    missing_v = state.get("missing_vectors", [])
    env_ent   = state.get("environmental_entities", [])
    kg_nodes  = state.get("knowledge_graph_entities", [])
    goals     = state.get("goals", [])
    conf_evo  = state.get("confidence_evolution", [])
    ctx       = state.get("context")

    # Pull live data from context if available
    face_count  = 0
    fps         = 0.0
    resolution  = "unknown"
    enf_avail   = False
    enf_ratio   = 0.0
    corneal_ok  = False
    vision_ents = 0

    if ctx:
        priv_out    = ctx.agent_results.get("Privacy Shield Agent", {}).get("output", {})
        enf_out     = ctx.agent_results.get("ENF Physics Agent", {}).get("output", {})
        corneal_out = ctx.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
        vision_out  = ctx.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
        intake_out  = ctx.agent_results.get("Evidence Intake Agent", {}).get("output", {})

        face_count  = priv_out.get("count", 0)
        fps         = ctx.metadata.get("fps", 0.0) if ctx.metadata else 0.0
        resolution  = ctx.metadata.get("resolution", "unknown") if ctx.metadata else "unknown"
        enf_avail   = enf_out.get("is_enf_available", False)
        enf_ratio   = enf_out.get("enf_ratio", 0.0)
        corneal_ok  = corneal_out.get("is_quality_sufficient", False)
        vision_ents = len(vision_out.get("environmental_objects", []))

    last_conf = conf_evo[-1] if conf_evo else {}
    current_conf = last_conf.get("authentic_prob", 0.5) * 100

    summary = {
        "case_id":          state.get("case_id", "UNKNOWN"),
        "media_type":       "VIDEO" if is_video else "IMAGE",
        "resolution":       resolution,
        "fps":              fps,
        "face_count":       face_count,
        "completed_agents": completed,
        "skipped_agents":   skipped,
        "hypotheses":       hypo,
        "current_confidence_pct": round(current_conf, 1),
        "enf_available":    enf_avail,
        "enf_ratio":        enf_ratio,
        "corneal_quality_ok": corneal_ok,
        "vision_entities_found": vision_ents,
        "environmental_entities": env_ent[:6],
        "kg_nodes":         len(kg_nodes),
        "active_vectors":   active_v,
        "missing_vectors":  missing_v,
        "unresolved_issues": memory.get("unresolved_issues", []),
        "missing_evidence": memory.get("missing_evidence", []),
        "goals_pending": [g["goal"] for g in goals if g.get("status") != "COMPLETED"][:3],
        "court_ready":      state.get("court_ready", False),
    }
    return json.dumps(summary, indent=2)


# ── Groq Provider ─────────────────────────────────────────────────────────────

class GroqProvider(LLMProvider):
    """Groq LPU accelerated provider — highest throughput, preferred for live demos."""
    name = "Groq (Llama-3.3-70B)"

    def __init__(self, api_key: str):
        import groq
        self.client = groq.Groq(api_key=api_key, timeout=3.0)

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        state_summary = _build_state_summary(state)
        user_msg = f"Current Investigation State:\n{state_summary}\n\nSelect next agent. Respond ONLY with JSON."

        last_err = None
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_msg}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.05,
                    max_tokens=512,
                    timeout=3.0
                )
                text = res.choices[0].message.content.strip()
                data = json.loads(text)
                next_agent = data.get("next_agent", "FINISH")
                if next_agent not in VALID_AGENTS:
                    next_agent = "FINISH"
                return next_agent, data, data
            except Exception as e:
                last_err = e

        raise Exception(f"Groq API failed on all models: {last_err}")


# ── Gemini Provider ───────────────────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    """Gemini Provider using google-genai SDK — fallback after Groq."""
    name = "Gemini (gemini-flash-latest)"

    def __init__(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        state_summary = _build_state_summary(state)
        user_msg = (
            f"{SYSTEM_PROMPT}\n\nCurrent Investigation State:\n{state_summary}\n\n"
            "Respond ONLY with valid JSON."
        )
        last_err = None
        for model in ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash"]:
            try:
                res = self.client.models.generate_content(model=model, contents=user_msg)
                text = res.text.strip()
                # Strip markdown fences if present
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                data = json.loads(text)
                next_agent = data.get("next_agent", "FINISH")
                if next_agent not in VALID_AGENTS:
                    next_agent = "FINISH"
                return next_agent, data, data
            except Exception as e:
                last_err = e

        raise Exception(f"Gemini API failed on all models: {last_err}")


# ── Procedural Fallback Provider ──────────────────────────────────────────────

class ProceduralFallbackProvider(LLMProvider):
    """
    Deterministic state-driven fallback.

    Reads actual InvestigationState fields (media type, face count, ENF
    availability, vision entities, etc.) instead of following a hardcoded list.
    Every decision explains its reasoning from real state data.
    """
    name = "Procedural State Engine"

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        completed = set(state.get("completed_agents", []))
        skipped   = set(state.get("skipped_agents", []))
        is_video  = state.get("is_video", False)
        hypo      = state.get("hypotheses", {"Authentic Media Record": 0.50, "Synthetic AI Fabrication": 0.50})
        conf_evo  = state.get("confidence_evolution", [])
        ctx       = state.get("context")
        court_r   = state.get("court_ready", False)

        # Pull live data from context
        face_count  = 0
        fps         = 0.0
        enf_avail   = False
        corneal_ok  = False
        vision_ents = 0
        current_confidence = 50.0

        if ctx:
            priv    = ctx.agent_results.get("Privacy Shield Agent", {}).get("output", {})
            enf_o   = ctx.agent_results.get("ENF Physics Agent", {}).get("output", {})
            corn_o  = ctx.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            vis_o   = ctx.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
            face_count  = priv.get("count", 0)
            fps         = ctx.metadata.get("fps", 0.0) if ctx.metadata else 0.0
            enf_avail   = enf_o.get("is_enf_available", False)
            corneal_ok  = corn_o.get("is_quality_sufficient", False)
            vision_ents = len(vis_o.get("environmental_objects", []))

        if conf_evo:
            last = conf_evo[-1]
            current_confidence = last.get("authentic_prob", 0.5) * 100

        # ── Helper ────────────────────────────────────────────────────────
        auth_pct  = round(hypo.get("Authentic Media Record", 0.5) * 100, 1)
        synth_pct = round(hypo.get("Synthetic AI Fabrication", 0.5) * 100, 1)
        hypo_str  = f"Authentic {auth_pct}%, Synthetic {synth_pct}%"

        def _mk(agent, goal, uncertainty, evidence, reason, benefit):
            return {
                "current_goal":        goal,
                "current_uncertainty": uncertainty,
                "current_evidence":    evidence,
                "next_agent":          agent,
                "reason_for_selection": reason,
                "expected_benefit":    benefit,
                "updated_hypothesis":  hypo_str,
                "what_i_know":         [f"Media type: {'VIDEO' if is_video else 'IMAGE'}",
                                        f"Completed: {list(completed)}"],
                "what_i_dont_know":    ["Authenticity not yet established"]
            }

        # ── Decision tree driven by STATE, not a hardcoded sequence ──────

        if "EvidenceIntakeAgent" not in completed:
            return "EvidenceIntakeAgent", _mk(
                "EvidenceIntakeAgent",
                goal="Register evidence and establish custody chain",
                uncertainty="No SHA-256 hash, no media metadata. Evidence not yet catalogued.",
                evidence="No evidence processed yet.",
                reason="Intake must run first to validate file integrity and extract media metadata (type, FPS, resolution) for all downstream decisions.",
                benefit="SHA-256 custody chain sealed; media type and quality metrics become available for planner routing."
            ), {}

        if "PrivacyShieldAgent" not in completed:
            return "PrivacyShieldAgent", _mk(
                "PrivacyShieldAgent",
                goal="Protect investigators from traumatic imagery before analysis",
                uncertainty=f"Human subjects may be visible. Face count unknown. Evidence: {ctx.original_filename if ctx else 'unknown'}.",
                evidence="Custody chain established. Evidence registered.",
                reason="Privacy Shield must run before any visual analysis to redact human subjects and produce the protected canvas for downstream agents.",
                benefit="Face count established; redacted canvas ready for Vision/Corneal analysis."
            ), {}

        if is_video and "ENFPhysicsAgent" not in completed and "ENFPhysicsAgent" not in skipped:
            fps_str = f"{fps:.1f} FPS" if fps > 0 else "FPS unknown"
            return "ENFPhysicsAgent", _mk(
                "ENFPhysicsAgent",
                goal="Verify physical electrical grid signature embedded in video luminance",
                uncertainty=f"Unknown whether video was captured under AC grid lighting. FPS: {fps_str}.",
                evidence=f"Video confirmed. Privacy complete. {face_count} face(s) detected.",
                reason=f"Media is VIDEO at {fps_str}. ENF Physics can extract the 50Hz AC grid hum via SciPy FFT/STFT, which AI generators (Sora, Runway, Pika) cannot reproduce.",
                benefit="If 50Hz peak found: +40% authentic confidence. If absent: synthetic fabrication strongly suspected."
            ), {}

        if not is_video and "CornealTopologyAgent" not in completed and "CornealTopologyAgent" not in skipped:
            return "CornealTopologyAgent", _mk(
                "CornealTopologyAgent",
                goal="Analyze corneal specular reflections for lighting environment consistency",
                uncertainty=f"Image has {face_count} detected face(s). Corneal glint symmetry unknown.",
                evidence=f"Static image. Privacy complete. {face_count} face(s) detected.",
                reason=f"Media is IMAGE with {face_count} face(s). Classical CV corneal topology checks specular glint symmetry — real eyes show consistent environmental reflections; AI-generated eyes show synthetic artifacts.",
                benefit="Symmetry score establishes whether facial lighting is physically consistent with the scene."
            ), {}

        if "VisionIntelligenceAgent" not in completed and "VisionIntelligenceAgent" not in skipped:
            enf_status = "ENF confirmed 50Hz grid" if enf_avail else ("ENF skipped (image)" if not is_video else "ENF ran — insufficient signal")
            corn_status = f"Corneal {'passed' if corneal_ok else 'insufficient quality'}" if not is_video else "Corneal N/A (video)"
            return "VisionIntelligenceAgent", _mk(
                "VisionIntelligenceAgent",
                goal="Extract environmental background entities for scene grounding",
                uncertainty="Room environment unknown. No spatial anchors available for knowledge graph construction.",
                evidence=f"Physical vectors: {enf_status}; {corn_status}.",
                reason="No environmental entities extracted yet. Vision Intelligence uses Gemini VLM (or OpenCV fallback) to identify room objects, scene type, and spatial layout — required before graph construction.",
                benefit="Background entities become knowledge graph nodes; scene type informs risk assessment; entity list narrows down location context."
            ), {}

        if "KnowledgeGraphAgent" not in completed and "KnowledgeGraphAgent" not in skipped:
            if vision_ents == 0:
                # Skip graph — nothing to correlate
                return "RiskAssessmentAgent", _mk(
                    "RiskAssessmentAgent",
                    goal="Assess investigative risk from available physical vectors",
                    uncertainty=f"Vision found zero entities — graph construction not possible. Risk profile unknown.",
                    evidence=f"Physical vectors complete. Vision: 0 entities.",
                    reason="Vision returned no entities so Knowledge Graph would be empty. Skipping graph construction and proceeding directly to Risk Assessment which can reason over ENF/Corneal/Privacy findings.",
                    benefit="Risk level and synthesis narrative established for Intelligence Fusion."
                ), {}
            return "KnowledgeGraphAgent", _mk(
                "KnowledgeGraphAgent",
                goal="Construct environmental relationship graph from vision-extracted entities",
                uncertainty=f"Relationships between {vision_ents} entities not yet mapped.",
                evidence=f"Vision extracted {vision_ents} environmental entities.",
                reason=f"Vision Agent found {vision_ents} entities. Knowledge Graph Agent will construct NetworkX nodes and edges linking room objects to this case, enabling cross-case correlation.",
                benefit=f"{vision_ents} entity nodes linked to case graph; enables relationship-based reasoning in Risk and Fusion agents."
            ), {}

        if "RiskAssessmentAgent" not in completed and "RiskAssessmentAgent" not in skipped:
            return "RiskAssessmentAgent", _mk(
                "RiskAssessmentAgent",
                goal="Evaluate threat level and consolidate forensic risk posture",
                uncertainty="Risk level not yet determined. Synthesis narrative incomplete.",
                evidence=f"Physical vectors complete. Vision: {vision_ents} entities. Hypothesis: {hypo_str}.",
                reason="All physical and environmental vectors are complete. Risk Assessment synthesizes PII exposure, ENF anomalies, and corneal findings into an actionable threat level.",
                benefit="Risk level (LOW/MEDIUM/HIGH/CRITICAL) established; missing evidence gaps identified; collection steps generated."
            ), {}

        if "IntelligenceFusionAgent" not in completed and "IntelligenceFusionAgent" not in skipped:
            return "IntelligenceFusionAgent", _mk(
                "IntelligenceFusionAgent",
                goal="Synthesize all forensic vectors into a unified evidence-grounded verdict",
                uncertainty="No unified verdict produced yet. Evidence narrative disconnected.",
                evidence=f"Risk assessed. {len(completed)} agents completed. Hypothesis: {hypo_str}.",
                reason="Intelligence Fusion produces the cross-vector narrative where every sentence cites originating agents, confidence contributions, and limitations — no template reasoning.",
                benefit="Unified verdict badge and confidence score established; actionable investigative leads generated."
            ), {}

        if "EvidenceGapAgent" not in completed and "EvidenceGapAgent" not in skipped:
            return "EvidenceGapAgent", _mk(
                "EvidenceGapAgent",
                goal="Identify missing evidence vectors and estimate achievable confidence",
                uncertainty=f"Evidence gaps not yet quantified. Current confidence estimate: {current_confidence:.1f}%.",
                evidence=f"Fusion complete. Verdict available. {len(completed)} agents ran.",
                reason="Before legal report generation, Evidence Gap Agent audits what was collected vs what is missing, projects achievable confidence, and flags human review requirement if confidence < 60%.",
                benefit="Evidence completeness score; collection priority queue; human review decision; confidence projection for legal admissibility."
            ), {}

        # ── Challenge loop before legal ───────────────────────────────────
        if "LegalReasoningAgent" not in completed and not court_r:
            # Check if human review is required
            if current_confidence < 60.0:
                gap_out = {}
                if ctx:
                    gap_out = ctx.agent_results.get("Evidence Gap Agent", {}).get("output", {})
                missing_critical = [
                    v["vector"] for v in gap_out.get("missing_vectors", [])
                    if v.get("potential_contribution", 0) >= 20
                ]
                if missing_critical:
                    return "HUMAN_REVIEW", _mk(
                        "HUMAN_REVIEW",
                        goal="Obtain human investigator decision before legal submission",
                        uncertainty=f"Confidence {current_confidence:.1f}% below threshold. Critical evidence missing: {', '.join(missing_critical)}.",
                        evidence=f"Hypothesis: {hypo_str}. Gap analysis flagged {len(missing_critical)} critical missing vectors.",
                        reason=f"Confidence {current_confidence:.1f}% is below the 60% minimum threshold for autonomous legal report generation. A human investigator must review and either collect missing evidence or authorize submission.",
                        benefit="Prevents premature legal claims with insufficient forensic backing."
                    ), {}

            return "LegalReasoningAgent", _mk(
                "LegalReasoningAgent",
                goal="Generate BSA 2023 Section 63 compliant forensic certificate",
                uncertainty=f"Legal admissibility document not yet produced. Court readiness: {court_r}.",
                evidence=f"Evidence Gap analyzed. Confidence: {current_confidence:.1f}%. Hypothesis: {hypo_str}.",
                reason=f"All analysis complete with confidence {current_confidence:.1f}%. Evidence Gap Agent has catalogued active and missing vectors. Legal Reasoning Agent will compile BSA 2023 certificate referencing ONLY actual evidence collected.",
                benefit="Court-ready admissibility certificate generated with SHA-256 sealed chain of custody."
            ), {}

        return "FINISH", _mk(
            "FINISH",
            goal="Investigation complete",
            uncertainty="None — all agents have completed",
            evidence=f"Full pipeline complete. {len(completed)} agents executed. Court ready: {court_r}.",
            reason="All forensic agents have executed and Legal Reasoning has produced the BSA 2023 certificate. Investigation is complete.",
            benefit="Case closed and handed to legal review team."
        ), {}


# ── Provider Factory ──────────────────────────────────────────────────────────

class ProviderFactory:
    """
    Resolves provider priority: Groq → Gemini → Procedural Fallback.
    Groq is preferred because its higher throughput reduces rate-limit
    interruptions during live demonstrations.
    """

    @staticmethod
    def get_provider() -> LLMProvider:
        groq_key   = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if groq_key:
            try:
                return GroqProvider(groq_key)
            except Exception:
                pass

        if gemini_key:
            try:
                return GeminiProvider(gemini_key)
            except Exception:
                pass

        return ProceduralFallbackProvider()
