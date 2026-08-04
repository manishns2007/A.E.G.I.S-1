import os
import uuid
import hashlib
import json
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
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
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store for case tracking (for hackathon MVP purposes)
CASES = {}

def get_file_extension(filename: str) -> str:
    if not filename:
        return ".bin"
    return os.path.splitext(filename)[1].lower()

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
        "docket": None
    }
    
    return UploadResponse(
        case_id=case_id,
        sha256=sha256_hash,
        metadata=metadata
    )

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_evidence(req: AnalyzeRequest):
    if req.case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case ID not found")
        
    case_data = CASES[req.case_id]
    
    try:
        raw_results = pipeline_orchestrator.run_pipeline(
            file_path=case_data["file_path"],
            is_vid=case_data["is_video"],
            gemini_api_key=req.gemini_api_key or "",
            case_id=req.case_id
        )
        
        # Build standard legal docket using the outputs
        docket_start = time.time()
        docket_res = legal_docket.generate_bsa_legal_docket(
            case_id=req.case_id,
            investigator_id="API-INVESTIGATOR",
            media_filename=case_data["original_filename"],
            media_bytes=case_data["file_bytes"],
            privacy_summary=raw_results["privacy"]["findings"],
            enf_summary=raw_results["enf"]["findings"],
            corneal_summary=raw_results["corneal"]["findings"],
            vlm_summary=raw_results["vlm"]["findings"]
        )
        docket_time = time.time() - docket_start
        
        # Save results in memory for subsequent GET requests
        case_data["results"] = raw_results
        case_data["docket"] = docket_res
        
        # Format response to match required schema
        def map_standard(raw: dict) -> StandardResult:
            return StandardResult(
                status=raw.get("status", "unknown"),
                processing_time=raw.get("processing_time", 0.0),
                confidence=raw.get("confidence"),
                findings=raw.get("findings", {}),
                error_message=raw.get("error_message")
            )
            
        # For Graph, we don't pass the raw NetworkX object back in REST
        graph_findings = raw_results["graph"]["findings"].copy()
        if "graph_fig" in graph_findings:
            # We don't want to send Plotly objects over REST, we just send node/edge data or correlations
            # For MVP, we send correlations
            graph_findings.pop("graph_fig")
            
        legal_report = StandardResult(
            status="success",
            processing_time=docket_time,
            confidence=100.0,
            findings={"is_authentic": docket_res["is_authentic"], "verdict_badge": docket_res["verdict_badge"]},
            error_message=None
        )

        return AnalyzeResponse(
            pipeline_status={"completed": True, "case_id": req.case_id},
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
        
    # We will construct a JSON graph representation dynamically
    # since we skipped saving the raw NetworkX object.
    raw_results = CASES[case_id]["results"]
    vlm_entities = raw_results["vlm"]["findings"].get("environmental_objects", [])
    
    nodes = [{"id": case_id, "label": f"TARGET: {case_id}", "type": "case"}]
    edges = []
    
    for ent in vlm_entities:
        ent_name = ent.get("entity", "Unknown") if isinstance(ent, dict) else str(ent)
        nodes.append({
            "id": ent_name,
            "label": ent_name,
            "type": "environmental_entity"
        })
        edges.append({
            "source": case_id,
            "target": ent_name
        })
        
    return JSONResponse(content={"nodes": nodes, "edges": edges})
