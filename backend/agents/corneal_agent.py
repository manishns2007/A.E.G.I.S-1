"""
Agent 5: Corneal Topology Agent
Wraps corneal_analyzer.py. Analyzes facial corneal specular highlights, eye ROI symmetry, and 8 independent forensic glint indicators.
"""
import time
import os
import sys
import cv2
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import corneal_analyzer

class CornealTopologyAgent(BaseAgent):
    name = "Corneal Specular Topology Agent"
    description = "Evaluates corneal specular reflections, eye symmetry, and multi-signal physical camera glint consistency."
    capabilities = ["Classical CV Eye ROI Extraction", "Specular Light Glint Contour Analysis", "8-Indicator Multi-Signal Evaluation", "Facial Pose Quality Filtering"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            img_to_analyze = context.img_bgr if context.img_bgr is not None else cv2.imread(context.file_path)
            if img_to_analyze is None:
                raise ValueError("Could not read image buffer for corneal analysis.")

            findings = corneal_analyzer.analyze_corneal_specular_topology(img_to_analyze, file_path=context.file_path)

            is_quality_valid = findings.get("is_quality_sufficient", False)
            quality_reason = findings.get("quality_reason", "Processed")
            symmetry = findings.get("symmetry_score", 50.0)
            confidence = findings.get("confidence", 50.0)
            is_authentic = findings.get("is_authentic", False)

            reasoning.append(f"Face & Eye ROI Detection: {quality_reason}")

            if is_quality_valid:
                l_cnt = findings.get("l_count", 0)
                r_cnt = findings.get("r_count", 0)
                reasoning.append(f"Isolated corneal glints: Left eye = {l_cnt}, Right eye = {r_cnt}.")
                reasoning.append(f"Multi-signal specular reflection symmetry score: {symmetry:.1f}%.")
                if is_authentic:
                    reasoning.append("VERIFIED: Symmetric corneal specular geometry consistent with physical camera sensor capture.")
                else:
                    reasoning.append("ANOMALY: Asymmetric corneal specular light highlights characteristic of generative AI diffusion.")
                status = "completed"
            else:
                reasoning.append("Corneal topology analysis suspended: Image background canvas does not contain an isolated frontal facial pose.")
                status = "warning"

            context.add_reasoning(self.name, f"Corneal analysis completed ({findings.get('verdict_text', 'Processed')}).")

            # Remove non-serializable OpenCV image matrices
            safe_output = {
                k: v for k, v in findings.items()
                if k not in ("l_crop", "r_crop", "l_mask", "r_mask", "img_bgr")
            }

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"is_video": context.is_video},
                output_data=safe_output,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Corneal topology analysis failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"file_path": context.file_path},
                output_data={"is_quality_sufficient": False, "symmetry_score": 50.0},
                reasoning=reasoning,
                error=err_msg
            )
