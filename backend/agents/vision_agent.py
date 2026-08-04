"""
Agent 6: Vision Intelligence Agent (Gemini Vision VLM)
Wraps vlm_extractor.py. Analyzes privacy-redacted background scene environments using Gemini Vision AI.
Extracts environmental objects, room types, spatial layout, lighting, and architectural features.
"""
import time
import os
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import vlm_extractor

class VisionIntelligenceAgent(BaseAgent):
    name = "Vision Intelligence Agent"
    description = "Uses Gemini Vision AI to perform semantic background scene analysis and extract environmental entities."
    capabilities = ["Gemini Vision VLM", "Background Scene Understanding", "Environmental Object Extraction", "Spatial Layout Analysis"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # Always pass privacy-shielded BGR buffer to preserve human subject privacy
            target_bgr = context.shielded_bgr if context.shielded_bgr is not None else context.img_bgr
            
            if target_bgr is None:
                raise ValueError("No unredacted or redacted image buffer available for Vision Agent.")

            reasoning.append("Submitting privacy-redacted background canvas to Gemini Vision Intelligence engine...")
            
            # Key resolution is handled inside vlm_extractor from env (GEMINI_API_KEY)
            vlm_res = vlm_extractor.parse_background_environment(target_bgr)
            
            vlm_status = vlm_res.get("status", "offline")
            
            if vlm_status != "offline":
                scene_type = vlm_res.get("scene_type") or "Indoor Scene"
                objects = vlm_res.get("environmental_objects", [])
                spatial = vlm_res.get("spatial_layout") or "Standard layout"
                lighting = vlm_res.get("lighting_type") or "Ambient lighting"

                reasoning.append(f"Identified scene classification: '{scene_type}'.")
                reasoning.append(f"Extracted {len(objects)} environmental background entity node(s).")
                if objects:
                    entity_names = [o.get("entity") if isinstance(o, dict) else str(o) for o in objects[:4]]
                    reasoning.append(f"Key entities: {', '.join(entity_names)}{'...' if len(objects) > 4 else ''}.")
                reasoning.append(f"Spatial framing: {spatial} | Lighting signature: {lighting}.")

                context.add_reasoning(self.name, f"Vision extraction completed ({len(objects)} entities identified).")
                status = "completed"
                confidence = 92.0
            else:
                err_details = vlm_res.get("error", "API key missing or offline")
                reasoning.append(f"Gemini Vision offline: {err_details}")
                context.add_reasoning(self.name, f"Vision Agent offline: {err_details}")
                status = "warning"
                confidence = 0.0

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"shielded_buffer_used": context.shielded_bgr is not None},
                output_data=vlm_res,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Vision Agent execution failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"shielded_buffer_used": False},
                output_data={"status": "offline", "environmental_objects": []},
                reasoning=reasoning,
                error=err_msg
            )
