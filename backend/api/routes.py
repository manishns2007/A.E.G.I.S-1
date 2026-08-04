import os
import uuid
import hashlib
import time
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from .schemas import UploadResponse, AnalyzeRequest, AnalyzeResponse, StandardResult
import sys

# Ensure backend root is in path so we can import legacy modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pipeline_orchestrator
import legal_docket

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
SAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'samples'))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store for case tracking (for hackathon MVP purposes)
CASES = {}

# Resolve Gemini API key from environment — never exposed to the frontend
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

def get_file_extension(filename: str) -> str:
    if not filename:
        return ".bin"
    return os.path.splitext(filename)[1].lower()

def _run_pipeline_and_build_response(case_id: str) -> AnalyzeResponse:
    """Shared pipeline execution logic used by both /analyze and /investigation/start."""
    case_data = CASES[case_id]

    raw_results = pipeline_orchestrator.run_pipeline(
        file_path=case_data["file_path"],
        is_vid=case_data["is_video"],
        gemini_api_key=GEMINI_API_KEY,
        case_id=case_id
    )

    docket_start = time.time()
    docket_res = legal_docket.generate_bsa_legal_docket(
        case_id=case_id,
        investigator_id="AEGIS-ORCHESTRATOR",
        media_filename=case_data["original_filename"],
        media_bytes=case_data["file_bytes"],
        privacy_summary=raw_results["privacy"]["findings"],
        enf_summary=raw_results["enf"]["findings"],
        corneal_summary=raw_results["corneal"]["findings"],
        vlm_summary=raw_results["vlm"]["findings"]
    )
    docket_time = time.time() - docket_start

    case_data["results"] = raw_results
    case_data["docket"] = docket_res

    def map_standard(raw: dict) -> StandardResult:
        findings = raw.get("findings", {})
        safe_findings = {}
        for k, v in findings.items():
            if type(v).__name__ == 'ndarray':
                continue
            if k in ['freqs', 'spectrum', 'luminance_signal', 'time_stamps', 'img_bgr', 'shielded_bgr']:
                continue
            safe_findings[k] = v
        return StandardResult(
            status=raw.get("status", "unknown"),
            processing_time=raw.get("processing_time", 0.0),
            confidence=raw.get("confidence"),
            findings=safe_findings,
            error_message=raw.get("error_message")
        )

    graph_findings = raw_results["graph"]["findings"].copy()
    if "graph_fig" in graph_findings:
        graph_findings.pop("graph_fig")

    legal_report = StandardResult(
        status="success",
        processing_time=docket_time,
        confidence=100.0,
        findings={"is_authentic": docket_res["is_authentic"], "verdict_badge": docket_res["verdict_badge"]},
        error_message=None
    )

    return AnalyzeResponse(
        pipeline_status={"completed": True, "case_id": case_id},
        privacy=map_standard(raw_results["privacy"]),
        enf=map_standard(raw_results["enf"]),
        corneal=map_standard(raw_results["corneal"]),
        gemini=map_standard(raw_results["vlm"]),
        knowledge_graph=StandardResult(
            status=raw_results["graph"]["status"],
            processing_time=raw_results["graph"]["processing_time"],
            findings=graph_findings,
            error_message=raw_results["graph"].get("error_message")
        ),
        legal_report=legal_report
    )


# ─────────────────────────────────────────────────────────
#  EXISTING ENDPOINTS (preserved for compatibility)
# ─────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_evidence(file: UploadFile = File(...)):
    case_id = f"KP-{uuid.uuid4().hex[:8].upper()}"
    ext = get_file_extension(file.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{case_id}{ext}")

    file_bytes = await file.read()

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    is_video = ext in ['.mp4', '.avi', '.mov']
    metadata = {
        "filename": file.filename,
        "size_bytes": len(file_bytes),
        "is_video": is_video,
        "mime_type": file.content_type
    }

    CASES[case_id] = {
        "file_path": file_path,
        "is_video": is_video,
        "metadata": metadata,
        "sha256": sha256_hash,
        "original_filename": file.filename,
        "file_bytes": file_bytes,
        "results": None,
        "docket": None,
        "registered_at": datetime.now().isoformat()
    }

    return UploadResponse(case_id=case_id, sha256=sha256_hash, metadata=metadata)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_evidence(req: AnalyzeRequest):
    if req.case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case ID not found")
    try:
        return _run_pipeline_and_build_response(req.case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/report/{case_id}")
async def get_report(case_id: str):
    if case_id not in CASES or not CASES[case_id]["docket"]:
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(content=CASES[case_id]["docket"]["html_content"])


@router.get("/graph/{case_id}")
async def get_graph(case_id: str):
    if case_id not in CASES or not CASES[case_id]["results"]:
        raise HTTPException(status_code=404, detail="Graph not found")

    raw_results = CASES[case_id]["results"]
    vlm_entities = raw_results["vlm"]["findings"].get("environmental_objects", [])

    nodes = [{"id": case_id, "label": f"TARGET: {case_id}", "type": "case"}]
    edges = []

    for ent in vlm_entities:
        ent_name = ent.get("entity", "Unknown") if isinstance(ent, dict) else str(ent)
        nodes.append({"id": ent_name, "label": ent_name, "type": "environmental_entity"})
        edges.append({"source": case_id, "target": ent_name})

    return JSONResponse(content={"nodes": nodes, "edges": edges})


# ─────────────────────────────────────────────────────────
#  NEW ENDPOINTS: Investigation Workspace
# ─────────────────────────────────────────────────────────

@router.get("/locker")
async def get_evidence_locker():
    """Return a forensic evidence repository listing from the samples/ directory."""
    if not os.path.isdir(SAMPLES_DIR):
        return JSONResponse(content={"items": []})

    VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv'}
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    SKIP_PREFIXES = ('shielded_', 'temp')

    items = []
    for fname in sorted(os.listdir(SAMPLES_DIR)):
        if fname.startswith(SKIP_PREFIXES):
            continue
        fpath = os.path.join(SAMPLES_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in VIDEO_EXTS and ext not in IMAGE_EXTS:
            continue

        stat = os.stat(fpath)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        file_type = "Video" if ext in VIDEO_EXTS else "Image"
        size_kb = round(stat.st_size / 1024, 1)

        # Derive a stable case ref from the filename
        case_ref = f"CASE-{hashlib.md5(fname.encode()).hexdigest()[:6].upper()}"

        items.append({
            "case_ref": case_ref,
            "filename": fname,
            "file_type": file_type,
            "size_kb": size_kb,
            "registered_at": mtime.strftime("%H:%M %d/%m/%Y"),
            "status": "Ready",
            "path": fpath
        })

    return JSONResponse(content={"items": items})


class InvestigationStartRequest(BaseModel):
    locker_filename: str  # filename from samples/ dir


@router.post("/investigation/start", response_model=AnalyzeResponse)
async def start_investigation(req: InvestigationStartRequest):
    """
    Start a full forensic investigation from an Evidence Locker file.
    Copies the file to uploads/, registers the case, and runs the full pipeline.
    Gemini API key is resolved from server-side environment variables only.
    """
    src_path = os.path.join(SAMPLES_DIR, req.locker_filename)
    if not os.path.isfile(src_path):
        raise HTTPException(status_code=404, detail=f"Evidence file not found in locker: {req.locker_filename}")

    case_id = f"KP-{uuid.uuid4().hex[:8].upper()}"
    ext = get_file_extension(req.locker_filename)
    dest_path = os.path.join(UPLOAD_DIR, f"{case_id}{ext}")
    shutil.copy2(src_path, dest_path)

    with open(dest_path, "rb") as f:
        file_bytes = f.read()

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    is_video = ext in ['.mp4', '.avi', '.mov']

    CASES[case_id] = {
        "file_path": dest_path,
        "is_video": is_video,
        "metadata": {
            "filename": req.locker_filename,
            "size_bytes": len(file_bytes),
            "is_video": is_video,
        },
        "sha256": sha256_hash,
        "original_filename": req.locker_filename,
        "file_bytes": file_bytes,
        "results": None,
        "docket": None,
        "registered_at": datetime.now().isoformat()
    }

    try:
        result = _run_pipeline_and_build_response(case_id)
        # Inject the case_id into pipeline_status so the frontend can navigate
        result.pipeline_status["case_id"] = case_id
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@router.get("/health")
async def system_health():
    """Returns operational status of all specialist agent subsystems."""
    gemini_status = "online" if GEMINI_API_KEY else "offline"
    return JSONResponse(content={
        "agents": [
            {"name": "Evidence Intake", "status": "online"},
            {"name": "Privacy Shield", "status": "online"},
            {"name": "ENF Physics", "status": "online"},
            {"name": "Vision Intelligence", "status": gemini_status},
            {"name": "Knowledge Graph", "status": "online"},
            {"name": "Legal Reporting", "status": "online"},
        ]
    })
