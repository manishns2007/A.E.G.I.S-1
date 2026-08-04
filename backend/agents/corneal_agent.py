"""
Agent 5: Corneal Specular Topology Agent
Wraps corneal_analyzer.py. Analyzes specular reflections in corneal eye regions 
to detect AI-generated facial inconsistencies across 8 classical CV indicators.
"""
import time
import os
import cv2
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import corneal_analyzer

class CornealTopologyAgent(BaseAgent):
    name = "Corneal Specular Topology Agent"
    purpose = "Analyzes specular eye reflection geometry to detect AI facial synthesis across 8 classical CV indicators."
    inputs = ["Image BGR Buffer"]
    outputs = ["Corneal Glint Contour Maps", "Symmetry Score", "8-Indicator Anomaly Score", "Authenticity Flag"]
    capabilities = ["Haar Eye Detection", "Specular Highlight Extraction", "8-Indicator Classical CV Evaluator", "Reflection Symmetry Scoring"]
    produces = ["Corneal Specular Glint Contour Maps", "8-Indicator Anomaly Score", "Specular Symmetry Score"]
    consumes = ["Unredacted / Shielded BGR Image Frame"]
    dependencies = ["Evidence Intake Agent", "Privacy Shield Agent"]
    limitations = ["Requires clear, unblurred facial eye regions (Laplacian Var > 35)"]
    typical_runtime_sec = 0.2

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            target_bgr = context.img_bgr if context.img_bgr is not None else cv2.imread(context.file_path)
            
            if target_bgr is None:
                raise ValueError("Could not read image buffer for corneal analysis.")

            reasoning.append("Running OpenCV face & eye cascade detection for specular reflection regions...")
            
            corneal_res = corneal_analyzer.analyze_corneal_specular_topology(target_bgr, context.file_path)
            
            is_qual = corneal_res.get("is_quality_sufficient", False)
            sym_score = corneal_res.get("symmetry_score", 0.0)
            anomaly_score = corneal_res.get("anomaly_score", 0.0)
            verdict = corneal_res.get("verdict_text", "Unknown")

            if is_qual:
                is_auth = corneal_res.get("is_authentic", True)
                reasoning.append(f"Extracted corneal specular highlights. Symmetry Score: {sym_score:.1f}% | Anomaly Score: {anomaly_score:.1f}%.")
                
                explanations = corneal_res.get("explanation", [])
                for exp in explanations[:3]:
                    reasoning.append(f"Indicator: {exp}")
                    
                if is_auth:
                    reasoning.append("VERIFIED: Specular lighting reflections across eye contours are physically consistent.")
                else:
                    reasoning.append("ANOMALY DETECTED: Significant specular reflection dissimilarity across corneal regions (Deepfake indicator).")

                context.add_reasoning(self.name, f"Corneal analysis completed ({verdict}).")
                status = "completed"
                confidence = corneal_res.get("confidence", 85.0)
                rec_next = ["VisionIntelligenceAgent", "RiskAssessmentAgent"]
            else:
                reasoning.append(f"Corneal Quality Rejection: {corneal_res.get('quality_reason', 'Low quality image')}")
                reasoning.append("Physical specular reflection vectors cannot be reliably evaluated for this frame.")
                context.add_reasoning(self.name, f"Corneal analysis completed ({verdict}).")
                status = "warning"
                confidence = 15.0
                rec_next = ["VisionIntelligenceAgent"]

            output = {
                "is_quality_sufficient": is_qual,
                "is_authentic": corneal_res.get("is_authentic", True),
                "symmetry_score": float(sym_score),
                "anomaly_score": float(anomaly_score),
                "verdict_text": verdict,
                "quality_reason": corneal_res.get("quality_reason"),
                "explanation": corneal_res.get("explanation", []),
                "confidence": confidence
            }

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"is_video": context.is_video},
                output_data=output,
                reasoning=reasoning,
                recommend_next=rec_next
            )

        except Exception as e:
            err_msg = f"Corneal Topology execution failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"is_video": context.is_video},
                output_data={"is_quality_sufficient": False, "is_authentic": True, "verdict_text": "Corneal Error"},
                reasoning=reasoning,
                error=err_msg
            )
