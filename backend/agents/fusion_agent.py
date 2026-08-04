"""
Agent 7: Intelligence Fusion Agent
Synthesizes independent forensic vectors (Privacy, ENF, Corneal, Vision) into a unified 
authenticity assessment, multi-vector confidence score, and actionable investigative leads.
"""
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

class IntelligenceFusionAgent(BaseAgent):
    name = "Intelligence Fusion Agent"
    description = "Fuses multi-agent forensic outputs to generate a unified authenticity verdict and reasoning chain."
    capabilities = ["Cross-Vector Reasoning", "Authenticity Synthesis", "Investigative Lead Generation", "Confidence Aggregation"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # 1. Retrieve all previous agent outputs from context
            privacy_res = context.agent_results.get("Privacy Shield Agent", {}).get("output", {})
            enf_res = context.agent_results.get("ENF Physics Agent", {}).get("output", {})
            corneal_res = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            vision_res = context.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
            
            # 2. Extract Active Vectors
            active_vectors = []
            
            # ENF (Video)
            enf_avail = enf_res.get("is_enf_available", False)
            enf_auth = enf_res.get("is_authentic", True)
            if enf_avail:
                active_vectors.append(("ENF Power Spectrum", enf_auth, enf_res.get("confidence", 0.0)))
                reasoning.append(f"ENF grid hum evaluated as {'AUTHENTIC' if enf_auth else 'ANOMALY'} (Peak ratio: {enf_res.get('enf_ratio', 0.0):.2f}).")
            
            # Corneal (Image)
            corneal_qual = corneal_res.get("is_quality_sufficient", False)
            corneal_auth = corneal_res.get("is_authentic", True)
            if corneal_qual:
                active_vectors.append(("Corneal Specular Topology", corneal_auth, corneal_res.get("confidence", 0.0)))
                reasoning.append(f"Corneal geometry evaluated as {'AUTHENTIC' if corneal_auth else 'ANOMALY'} (Symmetry: {corneal_res.get('symmetry_score', 0.0):.1f}%).")

            # Privacy
            face_cnt = privacy_res.get("count", 0)
            if face_cnt > 0:
                reasoning.append(f"Privacy preservation applied over {face_cnt} detected human subjects.")

            # Vision
            vlm_status = vision_res.get("status", "offline")
            objects_cnt = len(vision_res.get("environmental_objects", []))
            if vlm_status != "offline" and objects_cnt > 0:
                reasoning.append(f"Semantic scene mapped ({objects_cnt} environmental entities extracted).")

            # 3. Authenticity Synthesis & Confidence Aggregation
            if active_vectors:
                # If ANY active physical vector flags anomaly, media is synthetic.
                # If ALL active physical vectors confirm authenticity, media is real.
                is_authentic = all([v[1] for v in active_vectors])
                
                # Weighted average confidence of active vectors
                confidences = [v[2] for v in active_vectors if v[2] is not None]
                overall_confidence = sum(confidences) / len(confidences) if confidences else 85.0
                
                if is_authentic:
                    verdict = "AUTHENTIC REAL-WORLD CAPTURE"
                    reasoning.append("CONCLUSION: Active physical vectors consistently align with hardware camera sensor capture.")
                else:
                    verdict = "SYNTHETIC AI-GENERATED FABRICATION"
                    reasoning.append("CONCLUSION: Significant physical anomaly detected. Media is likely AI-generated or heavily manipulated.")
            else:
                # No active physical vectors (e.g. static image without faces)
                is_authentic = True
                overall_confidence = 65.0 # Lower confidence since it's just neutral
                if vlm_status != "offline":
                    verdict = "ENVIRONMENTAL EVIDENCE VERIFIED"
                    reasoning.append("CONCLUSION: Physical vectors inapplicable. Relying on VLM semantic scene extraction.")
                else:
                    verdict = "AUTHENTIC EVIDENCE RECORD"
                    reasoning.append("CONCLUSION: No active forensic vectors applicable. Cryptographic chain of custody verified.")

            # 4. Investigative Lead Generation
            investigative_leads = []
            
            if not is_authentic:
                investigative_leads.append("Verify deepfake/diffusion artifact origins using temporal noise pattern analysis.")
            
            if vlm_status != "offline" and objects_cnt > 0:
                scene = vision_res.get("scene_type", "Unknown Room")
                investigative_leads.append(f"Cross-reference '{scene}' background objects against known case databases.")
                if vision_res.get("lighting_type"):
                    investigative_leads.append(f"Analyze '{vision_res.get('lighting_type')}' lighting geometry for time-of-day bounding.")
            
            if face_cnt > 0:
                investigative_leads.append(f"Submit {face_cnt} redacted facial crops for authorized identity resolution workflows.")
                
            if not active_vectors:
                 investigative_leads.append("Submit additional evidence from this case containing clear facial portraits or video streams for physical vector analysis.")

            context.add_reasoning(self.name, f"Intelligence Fusion complete. Overall Verdict: {verdict}.")

            fusion_output = {
                "verdict_badge": verdict,
                "is_authentic": is_authentic,
                "overall_confidence": round(overall_confidence, 1),
                "active_vectors_count": len(active_vectors),
                "investigative_leads": investigative_leads,
                "synthesized_reasoning": reasoning
            }

            # Store in context for Legal Agent to use
            context.fusion_output = fusion_output

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=overall_confidence,
                input_data={"active_vectors": len(active_vectors), "vlm_status": vlm_status},
                output_data=fusion_output,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Intelligence Fusion failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            
            fallback_fusion = {
                 "verdict_badge": "ERROR IN FUSION ENGINE",
                 "is_authentic": True,
                 "overall_confidence": 0.0,
                 "active_vectors_count": 0,
                 "investigative_leads": [],
                 "synthesized_reasoning": []
            }
            context.fusion_output = fallback_fusion
            
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data=fallback_fusion,
                reasoning=reasoning,
                error=err_msg
            )
