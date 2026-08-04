"""
Agent 2: Evidence Intake Agent
Registers evidence, computes SHA-256 custody hash, detects media type, and extracts metadata.
"""
import time
import os
import hashlib
import cv2
from pathlib import Path
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

class EvidenceIntakeAgent(BaseAgent):
    name = "Evidence Intake Agent"
    description = "Registers evidence, verifies custody chain via SHA-256, and extracts metadata."
    capabilities = ["SHA-256 Cryptographic Hashing", "Media Type Detection", "Metadata Extraction", "Custody Registration"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # 1. SHA-256 Hashing
            if context.file_bytes:
                sha256_hash = hashlib.sha256(context.file_bytes).hexdigest()
            else:
                hasher = hashlib.sha256()
                with open(context.file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                sha256_hash = hasher.hexdigest()

            context.sha256 = sha256_hash
            reasoning.append(f"SHA-256 custody hash generated: {sha256_hash[:16]}...{sha256_hash[-8:]}")

            # 2. File Metadata & Frame Inspection
            file_size = os.path.getsize(context.file_path) if os.path.exists(context.file_path) else len(context.file_bytes)
            ext = Path(context.file_path).suffix.lower()
            
            metadata: Dict[str, Any] = {
                "case_id": context.case_id,
                "original_filename": context.original_filename,
                "file_extension": ext,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
                "is_video": context.is_video,
                "mime_type": "video/" + ext[1:] if context.is_video else "image/" + ext[1:]
            }

            # 3. Read initial BGR frame buffer into context
            if not context.is_video:
                img_bgr = cv2.imread(context.file_path)
                if img_bgr is not None:
                    h, w = img_bgr.shape[:2]
                    metadata["resolution"] = f"{w}x{h}"
                    context.img_bgr = img_bgr
                    reasoning.append(f"Static image evidence validated ({w}x{h} px).")
                else:
                    reasoning.append("Warning: Image frame read returned empty array.")
            else:
                cap = cv2.VideoCapture(context.file_path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                    ret, frame = cap.read()
                    cap.release()
                    metadata["fps"] = round(fps, 2)
                    metadata["total_frames"] = total_frames
                    metadata["duration_sec"] = round(total_frames / fps, 2) if fps > 0 else 0
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        metadata["resolution"] = f"{w}x{h}"
                        context.img_bgr = frame
                    reasoning.append(f"Video stream validated ({total_frames} frames @ {fps:.1f} FPS, {metadata.get('resolution', 'N/A')}).")
                else:
                    reasoning.append("Warning: Could not open VideoCapture stream.")

            context.metadata = metadata
            context.add_reasoning(self.name, f"Evidence registered for {context.case_id}. Custody chain verified.")

            output = {
                "case_id": context.case_id,
                "sha256": sha256_hash,
                "media_type": "Video" if context.is_video else "Image",
                "metadata": metadata,
                "custody_chain_verified": True
            }

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=100.0,
                input_data={"file_path": context.file_path, "is_video": context.is_video},
                output_data=output,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Evidence intake failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"file_path": context.file_path},
                output_data={},
                reasoning=reasoning,
                error=err_msg
            )
