"""
Agent 3: Privacy Shield Agent
Wraps privacy_shield.py to detect human subjects, apply facial redaction, and generate investigator-safe media outputs.
"""
import time
import os
import cv2
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import privacy_shield
import sample_generator

class PrivacyShieldAgent(BaseAgent):
    name = "Privacy Shield Agent"
    purpose = "Detects human subjects and applies facial redaction masks to safeguard investigator privacy."
    inputs = ["Unredacted Image BGR Buffer", "Video Stream Path"]
    outputs = ["Shielded BGR Buffer", "Shielded Video Path", "Redacted Face Bboxes"]
    capabilities = ["Human Face Detection", "Gaussian Mask Redaction", "Investigator Safety Protection"]
    produces = ["Shielded BGR Buffer", "Shielded Video Stream", "Redacted Face Count", "Face Bounding Boxes"]
    consumes = ["Unredacted BGR Frame Buffer", "Video Stream Path"]
    dependencies = ["Evidence Intake Agent"]
    limitations = ["MediaPipe / Haar cascade face detection thresholding limitations on extreme angles."]
    typical_runtime_sec = 0.8

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            if not context.is_video:
                img_bgr = context.img_bgr if context.img_bgr is not None else cv2.imread(context.file_path)
                if img_bgr is None:
                    raise ValueError("Could not read image array for privacy processing.")

                shielded_bgr, face_count, bboxes = privacy_shield.apply_privacy_shield_to_image(img_bgr)
                context.shielded_bgr = shielded_bgr
                
                if face_count > 0:
                    reasoning.append(f"Detected {face_count} human subject(s) in static image canvas.")
                    reasoning.append("Applied Gaussian blur redaction masks over detected facial bounding boxes.")
                    rec_next = ["CornealTopologyAgent"]
                else:
                    reasoning.append("No human subjects detected in image background canvas.")
                    rec_next = ["CornealTopologyAgent", "VisionIntelligenceAgent"]
                reasoning.append("Generated investigator-safe privacy-redacted image buffer.")

                context.add_reasoning(self.name, f"Privacy Shield complete. {face_count} face(s) redacted.")

                output = {
                    "count": face_count,
                    "bboxes": bboxes,
                    "redaction_applied": face_count > 0,
                    "shielded_video_path": None,
                    "verdict_text": f"REDATION COMPLETE ({face_count} SUBJECTS)" if face_count > 0 else "NO SUBJECTS DETECTED"
                }
                confidence = 98.0 if face_count > 0 else 99.5

            else:
                os.makedirs(sample_generator.SAMPLE_DIR, exist_ok=True)
                out_vid = os.path.join(sample_generator.SAMPLE_DIR, f"shielded_{os.path.basename(context.file_path)}")
                
                shielded_vid, face_count = privacy_shield.apply_privacy_shield_to_video(context.file_path, out_vid)
                context.shielded_vid_path = out_vid

                if context.img_bgr is not None:
                    shielded_frame, _, _ = privacy_shield.apply_privacy_shield_to_image(context.img_bgr)
                    context.shielded_bgr = shielded_frame
                else:
                    cap = cv2.VideoCapture(context.file_path)
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        shielded_frame, _, _ = privacy_shield.apply_privacy_shield_to_image(frame)
                        context.shielded_bgr = shielded_frame

                reasoning.append(f"Processed video stream frame-by-frame. {face_count} human subject instance(s) redacted.")
                reasoning.append(f"Investigator-safe video rendered to: {os.path.basename(out_vid)}")

                context.add_reasoning(self.name, f"Video Privacy Shield complete. {face_count} subject(s) redacted.")

                rec_next = ["ENFPhysicsAgent"]

                output = {
                    "count": face_count,
                    "redaction_applied": face_count > 0,
                    "shielded_video_path": out_vid,
                    "verdict_text": f"VIDEO REDACTION COMPLETE ({face_count} INSTANCES)" if face_count > 0 else "NO SUBJECTS DETECTED"
                }
                confidence = 95.0

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"is_video": context.is_video},
                output_data=output,
                reasoning=reasoning,
                recommend_next=rec_next
            )

        except Exception as e:
            err_msg = f"Privacy Shield execution failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            context.shielded_bgr = context.img_bgr
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=50.0,
                input_data={"is_video": context.is_video},
                output_data={"count": 0, "redaction_applied": False},
                reasoning=reasoning,
                error=err_msg
            )
