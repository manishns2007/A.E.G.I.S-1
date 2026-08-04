"""
Agent 4: ENF Physics Agent
Wraps enf_analyzer.py. Analyzes video luminance time-series to verify 50 Hz power grid hum.
Returns status="skipped" for static image inputs without triggering UI warnings.
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
    description = "Analyzes temporal frame luminance to detect 50 Hz electrical power grid hum signatures."
    capabilities = ["Fast Fourier Transform (FFT)", "Power Spectral Density (PSD)", "50 Hz Grid Hum Verification", "Temporal Sampling Physics"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        # ── 1. Gate: Skip static image inputs cleanly ───────────────────────
        if not context.is_video:
            reasoning.append("ENF analysis skipped: Static image input.")
            reasoning.append("Physical 50 Hz power grid frequency estimation requires multi-frame video luminance temporal sampling.")
            context.add_reasoning(self.name, "ENF analysis skipped (Static image input).")

            output = {
                "is_enf_available": False,
                "is_authentic": True,
                "verdict_text": "Skipped (Static Image)",
                "reason": "Static image input — ENF grid hum is not applicable.",
                "enf_ratio": 1.0,
                "peak_50hz_power": 0.0
            }

            return self.format_response(
                status="skipped",
                processing_time=round(time.time() - start, 3),
                confidence=None,
                input_data={"media_type": "Image"},
                output_data=output,
                reasoning=reasoning
            )

        # ── 2. Video ENF Execution ──────────────────────────────────────────
        try:
            enf_findings = enf_analyzer.analyze_video_enf(context.file_path, target_freq=50.0)
            is_avail = enf_findings.get("is_enf_available", False)
            is_auth = enf_findings.get("is_authentic", False)
            confidence = enf_findings.get("confidence", 85.0)

            if is_avail:
                ratio = enf_findings.get("enf_ratio", 1.0)
                peak_pwr = enf_findings.get("peak_50hz_power", 0.0)
                reasoning.append(f"Extracted luminance signal across {enf_findings.get('total_frames', 0)} frames @ {enf_findings.get('fps', 0):.1f} FPS.")
                reasoning.append(f"SciPy FFT spectrum calculated: 50 Hz peak power ratio = {ratio:.2f} (Peak Power = {peak_pwr:.3f}).")
                if is_auth:
                    reasoning.append("VERIFIED: 50 Hz Indian Electrical Grid Frequency hum peak confirmed. Real-world physical recording.")
                else:
                    reasoning.append("ANOMALY: 50 Hz grid frequency hum absent or suppressed. Indicates AI video synthesis or synthetic rendering.")
                status = "completed"
            else:
                reason = enf_findings.get("reason", "ENF unavailable")
                reasoning.append(f"ENF signal unextractable: {reason}")
                status = "warning"

            context.add_reasoning(self.name, f"ENF Physics analysis completed ({enf_findings.get('verdict_text', 'Processed')}).")

            # Remove large numpy arrays for clean serialization
            safe_output = {k: v for k, v in enf_findings.items() if k not in ("freqs", "spectrum", "luminance_signal", "time_stamps", "stft_matrix")}

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"file_path": context.file_path, "target_freq": 50.0},
                output_data=safe_output,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"ENF analysis failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"file_path": context.file_path},
                output_data={"is_enf_available": False, "is_authentic": True, "verdict_text": "Error"},
                reasoning=reasoning,
                error=err_msg
            )
