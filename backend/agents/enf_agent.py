"""
Agent 4: Electrical Network Frequency (ENF) Physics Agent
Wraps enf_analyzer.py. Analyzes video luminance time-series using SciPy FFT/STFT
to detect 50 Hz Indian Power Grid Frequency hum signature.
"""
import time
import os
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import enf_analyzer

class ENFPhysicsAgent(BaseAgent):
    name = "ENF Physics Agent"
    purpose = "Verifies video physical authenticity using SciPy FFT/STFT electrical network frequency 50Hz grid hum analysis."
    inputs = ["Video Stream Path"]
    outputs = ["ENF Spectrum Data", "50Hz Grid Peak Ratio", "Authenticity Flag", "STFT Spectrogram"]
    capabilities = ["SciPy FFT Spectrum Analysis", "STFT 2D Spectrogram", "50Hz Power Grid Hum Detection", "Nyquist Aliasing Correction"]
    produces = ["ENF Grid Hum Authenticity Flag", "Luminance Spectrum", "50Hz Peak Ratio", "STFT Spectrogram Matrix"]
    consumes = ["Video File Stream"]
    dependencies = ["Evidence Intake Agent"]
    limitations = ["Inapplicable for static images", "Requires minimum 1.5s duration and >12 FPS"]
    typical_runtime_sec = 0.4

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            if not context.is_video:
                reasoning.append("Input evidence is a static image canvas. ENF electro-grid frequency hum analysis is skipped.")
                context.add_reasoning(self.name, "ENF analysis skipped (Static image input).")
                
                output = {
                    "is_enf_available": False,
                    "is_authentic": True,
                    "verdict_text": "Skipped (Static Image)",
                    "reason": "Static image evidence has zero temporal luminance frames.",
                    "enf_ratio": 1.0,
                    "confidence": 0.0
                }
                return self.format_response(
                    status="skipped",
                    processing_time=time.time() - start,
                    confidence=0.0,
                    input_data={"is_video": False},
                    output_data=output,
                    reasoning=reasoning,
                    recommend_next=["VisionIntelligenceAgent"]
                )

            reasoning.append("Extracting per-frame mean spatial luminance time-series from video stream...")
            
            enf_res = enf_analyzer.analyze_video_enf(context.file_path)
            
            is_avail = enf_res.get("is_enf_available", False)
            
            if is_avail:
                is_auth = enf_res.get("is_authentic", False)
                enf_ratio = enf_res.get("enf_ratio", 1.0)
                fps = enf_res.get("fps", 30.0)
                frames = enf_res.get("total_frames", 0)

                reasoning.append(f"Analyzed {frames} luminance frames at {fps:.1f} FPS.")
                reasoning.append(f"SciPy FFT spectrum isolated peak power ratio: {enf_ratio:.2f} relative to noise floor.")
                
                if is_auth:
                    reasoning.append("VERIFIED: 50 Hz power grid frequency hum signature detected in luminance temporal spectrum.")
                    reasoning.append("Evidence aligns with physical camera sensor capture under AC electrical grid illumination.")
                else:
                    reasoning.append("ANOMALY: 50 Hz grid hum frequency peak is MISSING from video luminance spectrum.")
                    reasoning.append("High probability of AI video diffusion model generation (e.g., Sora, Runway, Pika).")

                context.add_reasoning(self.name, f"ENF Physics analysis completed ({enf_res.get('verdict_text')}).")
                status = "completed"
                confidence = enf_res.get("confidence", 90.0)
            else:
                reason = enf_res.get("reason", "Video unreadable or too short")
                reasoning.append(f"ENF Quality Rejection: {reason}")
                context.add_reasoning(self.name, f"ENF Quality Rejection: {reason}")
                status = "warning"
                confidence = 0.0

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"is_video": True, "file_name": context.original_filename},
                output_data=enf_res,
                reasoning=reasoning,
                recommend_next=["VisionIntelligenceAgent"]
            )

        except Exception as e:
            err_msg = f"ENF Physics execution failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"is_video": True},
                output_data={"is_enf_available": False, "is_authentic": True, "verdict_text": "ENF Error"},
                reasoning=reasoning,
                error=err_msg
            )
