"""
Agent 10: Evidence Gap Agent
Operates AFTER Intelligence Fusion and BEFORE Legal Reasoning.

Reads only from InvestigationContext.agent_results (real findings from every
previous agent). Never fabricates entities, confidence numbers, or recommendations.

Responsibilities
----------------
- List which forensic vectors were active (returned findings)
- List which vectors were skipped or unavailable
- Compute a realistic potential-confidence estimate if missing evidence were collected
- Produce actionable collection recommendations based on what is actually missing
- Identify whether human review is required (confidence < 60% threshold)

Confidence Estimation Formula
------------------------------
Each vector has a known maximum contribution:
  ENF Physics       → +40%  (if video with sufficient FPS/duration)
  Corneal Topology  → +30%  (if high-resolution face with clear eyes)
  Vision VLM        → +15%  (if Gemini/OpenCV scene entities found)
  Privacy           →  +5%  (always active)
  Base              →  20%  (custody chain baseline)

Total possible = 110% (capped at 99%)
Current confidence = sum of active contribution weights
Estimated after collection = current + sum of missing max contributions (capped at 99%)
"""
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext


# Contribution weights per forensic vector (deterministic, not generated)
VECTOR_WEIGHTS: Dict[str, float] = {
    "ENF Physics":        40.0,
    "Corneal Topology":   30.0,
    "Vision VLM":         15.0,
    "Privacy Shield":      5.0,
    "Custody Chain":      20.0,
}


class EvidenceGapAgent(BaseAgent):
    name = "Evidence Gap Agent"
    purpose = (
        "Analyzes active versus unavailable forensic evidence vectors, computes "
        "achievable confidence estimates, and produces evidence-backed collection "
        "recommendations from InvestigationState findings only."
    )
    inputs = [
        "Privacy Shield Output", "ENF Physics Output", "Corneal Topology Output",
        "Vision Intelligence Output", "Knowledge Graph Output",
        "Intelligence Fusion Output"
    ]
    outputs = [
        "Available Evidence Vectors", "Missing Evidence Vectors",
        "Current Confidence Estimate", "Achievable Confidence Estimate",
        "Recommended Next Steps", "Human Review Required"
    ]
    capabilities = [
        "Forensic Vector Gap Analysis",
        "Evidence-Driven Confidence Estimation",
        "Investigation Completeness Scoring",
        "Human-in-the-Loop Signalling"
    ]
    produces = [
        "Evidence Vector Inventory", "Gap-Aware Confidence Projection",
        "Collection Priority Queue", "Investigation Completeness Report"
    ]
    consumes = ["All Previous Agent Outputs via InvestigationContext"]
    dependencies = ["Intelligence Fusion Agent"]
    limitations = [
        "Cannot request or retrieve evidence itself.",
        "Confidence projection is an upper-bound estimate, not a guarantee."
    ]
    typical_runtime_sec = 0.05

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # ── Pull real outputs from context ─────────────────────────────────
            intake_out    = context.agent_results.get("Evidence Intake Agent",         {}).get("output", {})
            privacy_out   = context.agent_results.get("Privacy Shield Agent",          {}).get("output", {})
            enf_out       = context.agent_results.get("ENF Physics Agent",             {}).get("output", {})
            corneal_out   = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            vision_out    = context.agent_results.get("Vision Intelligence Agent",     {}).get("output", {})
            graph_out     = context.agent_results.get("Knowledge Graph Agent",         {}).get("output", {})
            fusion_out    = context.agent_results.get("Intelligence Fusion Agent",     {}).get("output", {})

            reasoning.append("Reading InvestigationState to enumerate active and unavailable forensic vectors...")

            available_vectors: List[Dict[str, Any]] = []
            missing_vectors:   List[Dict[str, Any]] = []
            recommendations:   List[str] = []
            current_confidence = VECTOR_WEIGHTS["Custody Chain"]   # baseline: SHA-256 hash always done

            # ── Custody / Intake ───────────────────────────────────────────────
            sha256 = intake_out.get("sha256") or context.sha256
            if sha256:
                available_vectors.append({
                    "vector": "Custody Chain (SHA-256)",
                    "status": "active",
                    "finding": f"Evidence hash sealed: {sha256[:16]}…",
                    "contribution": VECTOR_WEIGHTS["Custody Chain"]
                })
                reasoning.append(f"Custody Chain: ACTIVE — SHA-256 hash {sha256[:16]}…")
            else:
                missing_vectors.append({
                    "vector": "Custody Chain",
                    "status": "missing",
                    "reason": "No SHA-256 hash recorded",
                    "potential_contribution": VECTOR_WEIGHTS["Custody Chain"]
                })

            # ── Privacy Shield ────────────────────────────────────────────────
            faces = privacy_out.get("count", 0)
            if privacy_out:   # any output means agent ran
                current_confidence += VECTOR_WEIGHTS["Privacy Shield"]
                available_vectors.append({
                    "vector": "Privacy Shield",
                    "status": "active",
                    "finding": f"{faces} human subject(s) detected and redacted",
                    "contribution": VECTOR_WEIGHTS["Privacy Shield"]
                })
                reasoning.append(f"Privacy Shield: ACTIVE — {faces} face(s) detected.")
            else:
                missing_vectors.append({
                    "vector": "Privacy Shield",
                    "status": "missing",
                    "reason": "Privacy Shield did not run or produced no output",
                    "potential_contribution": VECTOR_WEIGHTS["Privacy Shield"]
                })

            # ── ENF Physics ───────────────────────────────────────────────────
            enf_avail = enf_out.get("is_enf_available", False)
            if enf_avail:
                current_confidence += VECTOR_WEIGHTS["ENF Physics"]
                enf_ratio = enf_out.get("enf_ratio", 0.0)
                fps        = enf_out.get("fps", 0.0)
                available_vectors.append({
                    "vector": "ENF Physics (50Hz Grid Spectrum)",
                    "status": "active",
                    "finding": f"50Hz power grid FFT completed. ENF ratio: {enf_ratio:.2f}, FPS: {fps:.1f}",
                    "contribution": VECTOR_WEIGHTS["ENF Physics"]
                })
                reasoning.append(f"ENF Physics: ACTIVE — ENF ratio {enf_ratio:.2f}.")
            else:
                enf_reason = enf_out.get("reason", "Static image or insufficient video quality")
                missing_vectors.append({
                    "vector": "ENF Physics (50Hz Grid Spectrum)",
                    "status": "missing",
                    "reason": enf_reason,
                    "potential_contribution": VECTOR_WEIGHTS["ENF Physics"]
                })
                if context.is_video:
                    recommendations.append(
                        f"ENF missing ({enf_reason}). Provide continuous indoor video "
                        f"≥1.5 s at ≥12 FPS under artificial AC lighting to enable SciPy FFT analysis."
                    )
                else:
                    recommendations.append(
                        "ENF requires video input. Upload a continuous indoor video clip (≥1.5 s, ≥12 FPS) "
                        "recorded under artificial lighting to capture 50Hz/100Hz grid hum."
                    )
                reasoning.append(f"ENF Physics: MISSING — {enf_reason}.")

            # ── Corneal Topology ──────────────────────────────────────────────
            corneal_qual = corneal_out.get("is_quality_sufficient", False)
            if corneal_qual:
                current_confidence += VECTOR_WEIGHTS["Corneal Topology"]
                sym_score = corneal_out.get("symmetry_score", 0.0)
                available_vectors.append({
                    "vector": "Corneal Specular Topology",
                    "status": "active",
                    "finding": f"Specular eye glint analysis completed. Symmetry score: {sym_score:.1f}%",
                    "contribution": VECTOR_WEIGHTS["Corneal Topology"]
                })
                reasoning.append(f"Corneal Topology: ACTIVE — symmetry score {sym_score:.1f}%.")
            else:
                corneal_reason = corneal_out.get(
                    "quality_reason",
                    corneal_out.get("verdict_text", "Insufficient image resolution or no detectable facial eyes")
                )
                missing_vectors.append({
                    "vector": "Corneal Specular Topology",
                    "status": "missing",
                    "reason": corneal_reason,
                    "potential_contribution": VECTOR_WEIGHTS["Corneal Topology"]
                })
                recommendations.append(
                    f"Corneal topology unavailable ({corneal_reason}). "
                    "Provide a high-resolution frontal portrait (≥800×800 px) with direct lighting "
                    "so eye specular glints can be extracted by the OpenCV cascade pipeline."
                )
                reasoning.append(f"Corneal Topology: MISSING — {corneal_reason}.")

            # ── Vision VLM ────────────────────────────────────────────────────
            vlm_status = vision_out.get("status", "offline")
            vlm_objects = vision_out.get("environmental_objects", [])
            if vlm_status != "offline" and vlm_objects:
                current_confidence += VECTOR_WEIGHTS["Vision VLM"]
                entity_names = [
                    o.get("entity") if isinstance(o, dict) else str(o)
                    for o in vlm_objects[:5]
                ]
                available_vectors.append({
                    "vector": "Vision Intelligence (VLM Scene Analysis)",
                    "status": "active",
                    "finding": f"{len(vlm_objects)} entities extracted: {', '.join(entity_names)}",
                    "contribution": VECTOR_WEIGHTS["Vision VLM"]
                })
                reasoning.append(f"Vision VLM: ACTIVE — {len(vlm_objects)} entities.")
            elif vlm_status == "offline":
                missing_vectors.append({
                    "vector": "Vision Intelligence (VLM Scene Analysis)",
                    "status": "missing",
                    "reason": vision_out.get("error", "Gemini API offline or key missing"),
                    "potential_contribution": VECTOR_WEIGHTS["Vision VLM"]
                })
                recommendations.append(
                    "Gemini Vision API was offline. Set GEMINI_API_KEY environment variable "
                    "and retry to enable semantic background entity extraction."
                )
                reasoning.append("Vision VLM: MISSING — API offline.")
            else:
                # API returned but no entities found
                available_vectors.append({
                    "vector": "Vision Intelligence (VLM Scene Analysis)",
                    "status": "partial",
                    "finding": "Vision API online but returned zero environmental entities",
                    "contribution": 5.0   # partial credit for successful API call
                })
                current_confidence += 5.0
                recommendations.append(
                    "Vision Agent connected but detected no background entities. "
                    "Ensure the evidence image shows visible room context or background scene."
                )
                reasoning.append("Vision VLM: PARTIAL — API online, zero entities.")

            # ── Knowledge Graph ───────────────────────────────────────────────
            graph_nodes = graph_out.get("nodes", 0)
            graph_edges = graph_out.get("edges", 0)
            if graph_nodes > 1:  # > 1 because the case node itself counts as 1
                available_vectors.append({
                    "vector": "Knowledge Graph",
                    "status": "active",
                    "finding": f"{graph_nodes} nodes, {graph_edges} edges constructed from vision entities",
                    "contribution": 0.0   # confidence already counted via Vision
                })
                reasoning.append(f"Knowledge Graph: ACTIVE — {graph_nodes} nodes, {graph_edges} edges.")
            else:
                missing_vectors.append({
                    "vector": "Knowledge Graph",
                    "status": "missing",
                    "reason": "No environmental entities available for graph construction",
                    "potential_contribution": 0.0
                })
                reasoning.append("Knowledge Graph: EMPTY — no entities to correlate.")

            # ── Compute potential confidence after collection ──────────────────
            missing_potential = sum(
                v["potential_contribution"] for v in missing_vectors
                if v.get("potential_contribution", 0) > 0
            )
            estimated_confidence_after = min(99.0, current_confidence + missing_potential)
            current_confidence_capped  = min(99.0, current_confidence)

            # ── Human review threshold ─────────────────────────────────────────
            human_review_required = current_confidence_capped < 60.0
            if human_review_required:
                reasoning.append(
                    f"HUMAN REVIEW REQUIRED: Current confidence {current_confidence_capped:.1f}% "
                    f"is below the 60% threshold. Critical evidence missing: "
                    f"{', '.join(v['vector'] for v in missing_vectors if v.get('potential_contribution', 0) >= 20)}."
                )
                recommendations.insert(0,
                    "⚠ Confidence below threshold (60%). Manual investigator review is required "
                    "before legal proceedings. Collect missing evidence listed above first."
                )

            # ── Investigation completeness summary ────────────────────────────
            completeness_pct = round(
                (len(available_vectors) / max(1, len(available_vectors) + len(missing_vectors))) * 100, 1
            )

            reasoning.append(
                f"Evidence Gap Analysis complete. Active vectors: {len(available_vectors)}, "
                f"Missing vectors: {len(missing_vectors)}. "
                f"Current confidence: {current_confidence_capped:.1f}%. "
                f"Achievable confidence: {estimated_confidence_after:.1f}%."
            )

            context.add_reasoning(
                self.name,
                f"Gap analysis complete. Confidence {current_confidence_capped:.1f}% → "
                f"up to {estimated_confidence_after:.1f}% after evidence collection."
            )

            output = {
                "available_vectors":           available_vectors,
                "missing_vectors":             missing_vectors,
                "current_confidence":          round(current_confidence_capped, 1),
                "estimated_confidence_after":  round(estimated_confidence_after, 1),
                "recommendations":             recommendations,
                "human_review_required":       human_review_required,
                "investigation_completeness":  completeness_pct,
                "faces_detected":              faces,
                "graph_nodes":                 graph_nodes,
                "graph_edges":                 graph_edges,
                "vlm_entity_count":            len(vlm_objects),
                "fusion_verdict":              fusion_out.get("verdict_badge", "PENDING"),
            }

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=current_confidence_capped,
                input_data={
                    "agents_consulted": list(context.agent_results.keys()),
                    "is_video": context.is_video
                },
                output_data=output,
                reasoning=reasoning,
                limitations=[
                    "Confidence projection is an estimate based on maximum vector contributions.",
                    "Cannot guarantee same findings with new evidence — depends on actual file content."
                ],
                recommend_next=["LegalReasoningAgent"],
                required_followup=recommendations
            )

        except Exception as e:
            err_msg = f"Evidence Gap Agent failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data={
                    "available_vectors": [],
                    "missing_vectors": [],
                    "current_confidence": 0.0,
                    "estimated_confidence_after": 0.0,
                    "recommendations": ["Evidence Gap Analysis failed. Manual review required."],
                    "human_review_required": True,
                },
                reasoning=reasoning,
                error=err_msg
            )
