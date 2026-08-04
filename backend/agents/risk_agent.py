"""
Agent 8: Risk Assessment Agent
Evaluates multi-vector findings to assign an overall threat level,
detailing supporting evidence, missing evidence, and recommended collection steps.
"""
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

class RiskAssessmentAgent(BaseAgent):
    name = "Risk Assessment Agent"
    description = "Evaluates findings from all forensic vectors to assign an evidence-grounded threat assessment."
    capabilities = ["Risk Scoring", "Threat Assessment", "Evidence Gap Identification", "Actionable Next Steps"]
    produces = ["Risk Level", "Threat Assessment Summary", "Evidence Gaps", "Recommended Collection Steps"]
    consumes = ["Privacy Shield Output", "ENF Physics Output", "Corneal Topology Output"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []
        
        try:
            privacy_res = context.agent_results.get("Privacy Shield Agent", {}).get("output", {})
            enf_res = context.agent_results.get("ENF Physics Agent", {}).get("output", {})
            corneal_res = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            
            supporting_evidence: List[str] = []
            missing_evidence: List[str] = []
            immediate_actions: List[str] = []
            collection_steps: List[str] = []
            
            # 1. PII Risk
            faces = privacy_res.get("count", 0)
            if faces > 0:
                supporting_evidence.append(f"Privacy Shield detected {faces} human subject(s) requiring PII masking.")
                immediate_actions.append("Verify Gaussian blur masks cover all human subject bounding boxes.")
            else:
                supporting_evidence.append("No human subjects detected; zero PII exposure risk.")

            # 2. ENF Grid Anomaly Risk
            enf_avail = enf_res.get("is_enf_available", False)
            enf_auth = enf_res.get("is_authentic", True)
            if enf_avail:
                if not enf_auth:
                    supporting_evidence.append(f"ENF Physics detected missing 50 Hz power grid hum (Peak ratio: {enf_res.get('enf_ratio', 0.0):.2f}).")
                    immediate_actions.append("Initiate deepfake diffusion origin tracing on video luminance frames.")
                else:
                    supporting_evidence.append("ENF Physics verified 50 Hz power grid hum frequency spectrum.")
            else:
                missing_evidence.append("ENF Power Spectrum Analysis (Unavailable for static image inputs or short clips).")
                collection_steps.append("Request original continuous video stream (> 1.5s, > 12 FPS) to perform ENF analysis.")

            # 3. Corneal Reflection Anomaly Risk
            corneal_qual = corneal_res.get("is_quality_sufficient", False)
            corneal_auth = corneal_res.get("is_authentic", True)
            if corneal_qual:
                if not corneal_auth:
                    supporting_evidence.append(f"Corneal Topology detected severe reflection glint asymmetry (Symmetry: {corneal_res.get('symmetry_score', 0.0):.1f}%).")
                    immediate_actions.append("Flag facial portrait for high-probability AI synthesis / deepfake inspection.")
                else:
                    supporting_evidence.append("Corneal Topology verified specular reflection symmetry across eye contours.")
            else:
                missing_evidence.append("Corneal Specular Topology (Insufficient image resolution or face glints obscured).")
                collection_steps.append("Request high-resolution uncompressed portrait image with direct eyes-facing lighting.")

            # Determine Risk Level & Threat Narrative
            has_synthesis_risk = (enf_avail and not enf_auth) or (corneal_qual and not corneal_auth)
            
            if has_synthesis_risk:
                risk_level = "CRITICAL"
                current_threat = "High probability of AI-generated synthetic manipulation or deepfake fabrication."
                why = "At least one active physical forensic vector (ENF physics or Corneal topology) failed authenticity verification."
                confidence = 95.0
            elif faces > 0:
                risk_level = "MEDIUM"
                current_threat = "Human subject PII exposure risk in unredacted evidence files."
                why = "Human subjects present in media required active privacy masking."
                confidence = 85.0
            else:
                risk_level = "LOW"
                current_threat = "No active physical anomalies or PII exposure risks detected."
                why = "All active forensic checks passed without flagging synthetic anomalies."
                confidence = 90.0

            reasoning.append(f"Threat Assessment complete. Assigned Risk Level: {risk_level}")
            reasoning.append(f"Threat: {current_threat}")

            context.add_reasoning(self.name, f"Assigned Threat Risk Level: {risk_level}.")

            output = {
                "risk_level": risk_level,
                "current_threat": current_threat,
                "why": why,
                "evidence_supporting_assessment": supporting_evidence,
                "missing_evidence": missing_evidence,
                "immediate_investigative_actions": immediate_actions,
                "recommended_next_collection_steps": collection_steps,
                "risk_factors": supporting_evidence
            }

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"faces": faces, "enf_available": enf_avail, "corneal_quality": corneal_qual},
                output_data=output,
                reasoning=reasoning,
                limitations=missing_evidence,
                recommend_next=["IntelligenceFusionAgent"],
                required_followup=collection_steps
            )

        except Exception as e:
            err_msg = f"Risk Assessment failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data={"risk_level": "UNKNOWN", "current_threat": "Assessment Failed", "why": str(e)},
                reasoning=reasoning,
                error=err_msg
            )
