"""
A.E.G.I.S. FastAPI Routes
Supports both legacy single-file analysis and the new Case-Based Investigation workflow.
Includes Server-Sent Events (SSE) streaming endpoint for real-time investigation demo.
"""
import os
import uuid
import hashlib
import time
import shutil
import zipfile
import json
import asyncio
import queue
import threading
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, AsyncIterator

from .schemas import (
    UploadResponse, AnalyzeRequest, MultiAgentInvestigationResponse,
    EvidenceInventory, CaseRegistrationResponse, CaseLockerEntry,
    InvestigationStartRequest, StreamStartRequest
)
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import legal_docket

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
SAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'samples'))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store
CASES: dict = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

# ── File categorisation ───────────────────────────────────────────────────────

IMAGE_EXTS  = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
VIDEO_EXTS  = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v'}
AUDIO_EXTS  = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.opus'}
DOC_EXTS    = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.csv', '.pptx'}
CHAT_EXTS   = {'.json', '.xml', '.html', '.htm', '.db', '.sqlite'}
SKIP_DIRS   = {'__MACOSX', '.DS_Store', '__pycache__'}


def categorise_file(ext: str) -> str:
    ext = ext.lower()
    if ext in IMAGE_EXTS:  return 'images'
    if ext in VIDEO_EXTS:  return 'videos'
    if ext in AUDIO_EXTS:  return 'audio'
    if ext in DOC_EXTS:    return 'documents'
    if ext in CHAT_EXTS:   return 'chats'
    return 'unknown'


def scan_directory(base_dir: str) -> dict:
    inventory: dict = {'images': [], 'videos': [], 'audio': [], 'documents': [], 'chats': [], 'unknown': []}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname.startswith('.') or fname.startswith('__'):
                continue
            ext = Path(fname).suffix.lower()
            cat = categorise_file(ext)
            inventory[cat].append(os.path.join(root, fname))
    return inventory


def pick_primary(inventory: dict) -> Optional[str]:
    for cat in ('videos', 'images', 'audio', 'documents'):
        if inventory[cat]:
            return inventory[cat][0]
    for cat in ('chats', 'unknown'):
        if inventory[cat]:
            return inventory[cat][0]
    return None


def inventory_to_schema(inv: dict) -> EvidenceInventory:
    return EvidenceInventory(
        images=len(inv.get('images', [])),
        videos=len(inv.get('videos', [])),
        audio=len(inv.get('audio', [])),
        documents=len(inv.get('documents', [])),
        chats=len(inv.get('chats', [])),
        unknown=len(inv.get('unknown', [])),
    )


def get_file_extension(filename: str) -> str:
    if not filename:
        return '.bin'
    return Path(filename).suffix.lower()


# ── Shared pipeline execution ─────────────────────────────────────────────────

from backend.agents import InvestigationContext, InvestigationOrchestratorAgent


def _run_pipeline_and_build_response(case_id: str, event_queue=None) -> MultiAgentInvestigationResponse:
    case_data = CASES[case_id]

    context = InvestigationContext(
        case_id=case_id,
        file_path=case_data['file_path'],
        is_video=case_data['is_video'],
        original_filename=case_data['original_filename'],
        file_bytes=case_data['file_bytes'],
        event_queue=event_queue,
    )

    orchestrator = InvestigationOrchestratorAgent()
    orchestrator_output = orchestrator.execute(context)

    result_dict = orchestrator_output['output']
    case_data['results'] = result_dict
    case_data['docket'] = result_dict.get('legal_report', {}).get('output', {})

    return MultiAgentInvestigationResponse(**result_dict)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE-BASED INVESTIGATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post('/case/register', response_model=CaseRegistrationResponse)
async def register_case(file: UploadFile = File(...)):
    """Register a new investigation case from a ZIP archive or single media file."""
    case_id = f'CASE-{datetime.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    file_bytes = await file.read()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    ext = get_file_extension(file.filename or '')
    case_name = file.filename or 'unknown'
    registered_at = datetime.now().strftime('%H:%M %d/%m/%Y')

    if ext == '.zip':
        zip_path = os.path.join(case_dir, 'package.zip')
        with open(zip_path, 'wb') as f:
            f.write(file_bytes)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(case_dir)
            os.remove(zip_path)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail='Invalid ZIP file')
        inventory = scan_directory(case_dir)
    else:
        dest = os.path.join(case_dir, file.filename or f'evidence{ext}')
        with open(dest, 'wb') as f:
            f.write(file_bytes)
        inventory = scan_directory(case_dir)

    primary = pick_primary(inventory)
    if not primary:
        raise HTTPException(status_code=422, detail='No usable evidence files found in the case package.')

    is_video = get_file_extension(primary) in VIDEO_EXTS
    inv_schema = inventory_to_schema(inventory)
    total = inv_schema.images + inv_schema.videos + inv_schema.audio + inv_schema.documents + inv_schema.chats + inv_schema.unknown

    with open(primary, 'rb') as f:
        primary_bytes = f.read()

    CASES[case_id] = {
        'file_path':         primary,
        'is_video':          is_video,
        'original_filename': os.path.basename(primary),
        'file_bytes':        primary_bytes,
        'sha256':            sha256_hash,
        'metadata':          {'filename': case_name, 'size_bytes': len(file_bytes), 'is_video': is_video},
        'results':           None,
        'docket':            None,
        'registered_at':     registered_at,
        'case_name':         case_name,
        'case_dir':          case_dir,
        'inventory':         inventory,
        'inventory_schema':  inv_schema.model_dump(),
        'total_files':       total,
        'status':            'Ready',
    }

    return CaseRegistrationResponse(
        case_id=case_id,
        name=case_name,
        sha256=sha256_hash,
        registered_at=registered_at,
        inventory=inv_schema,
        total_files=total,
        primary_evidence=primary,
        primary_filename=os.path.basename(primary),
    )


@router.get('/locker')
async def get_evidence_locker():
    """Return all registered investigation cases plus auto-generated sample entries."""
    entries: list[dict] = []

    for case_id, data in CASES.items():
        inv = data.get('inventory_schema') or {}
        total = data.get('total_files', 1)
        if not total and data.get('inventory_schema'):
            total = sum(inv.values())
        status = 'Complete' if data.get('docket') else ('Processing' if data.get('results') else 'Ready')
        entries.append({
            'case_id':      case_id,
            'name':         data.get('case_name', data.get('original_filename', 'Unknown')),
            'registered_at': data.get('registered_at', '—'),
            'total_files':  total,
            'inventory':    inv,
            'status':       status,
        })

    # Auto-generate entries from samples/
    if os.path.isdir(SAMPLES_DIR):
        SKIP_PREFIXES = ('shielded_', 'temp')
        registered_primaries = {d.get('original_filename') for d in CASES.values()}
        for fname in sorted(os.listdir(SAMPLES_DIR)):
            if fname.startswith(SKIP_PREFIXES) or fname.startswith('.'):
                continue
            fpath = os.path.join(SAMPLES_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            ext = Path(fname).suffix.lower()
            if ext not in IMAGE_EXTS | VIDEO_EXTS:
                continue
            if fname in registered_primaries:
                continue
            stat = os.stat(fpath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            cat = 'videos' if ext in VIDEO_EXTS else 'images'
            inv_dict = {'images': 0, 'videos': 0, 'audio': 0, 'documents': 0, 'chats': 0, 'unknown': 0}
            inv_dict[cat] = 1
            sample_case_id = f'SAMPLE-{hashlib.md5(fname.encode()).hexdigest()[:8].upper()}'
            entries.append({
                'case_id':      sample_case_id,
                'name':         fname,
                'registered_at': mtime.strftime('%H:%M %d/%m/%Y'),
                'total_files':  1,
                'inventory':    inv_dict,
                'status':       'Ready',
                '_locker_file':     fpath,
                '_locker_filename': fname,
            })

    return JSONResponse(content={'cases': entries})


@router.post('/investigation/start', response_model=MultiAgentInvestigationResponse)
async def start_investigation(req: InvestigationStartRequest):
    """Start full multi-agent investigation for a registered or sample case."""
    case_id = req.case_id

    if case_id not in CASES:
        locker_data = await get_evidence_locker()
        import json as _json
        locker_json = _json.loads(locker_data.body)
        sample_entry = next((c for c in locker_json['cases'] if c['case_id'] == case_id), None)

        if not sample_entry or '_locker_file' not in sample_entry:
            raise HTTPException(status_code=404, detail=f'Case not found: {case_id}')

        src_path = sample_entry['_locker_file']
        fname    = sample_entry['_locker_filename']
        ext      = get_file_extension(fname)
        dest_dir = os.path.join(UPLOAD_DIR, case_id)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, fname)
        shutil.copy2(src_path, dest)

        with open(dest, 'rb') as f:
            file_bytes = f.read()

        is_video = ext in VIDEO_EXTS
        cat = 'videos' if is_video else 'images'
        inv_dict = {'images': 0, 'videos': 0, 'audio': 0, 'documents': 0, 'chats': 0, 'unknown': 0}
        inv_dict[cat] = 1

        CASES[case_id] = {
            'file_path':         dest,
            'is_video':          is_video,
            'original_filename': fname,
            'file_bytes':        file_bytes,
            'sha256':            hashlib.sha256(file_bytes).hexdigest(),
            'metadata':          {'filename': fname, 'size_bytes': len(file_bytes), 'is_video': is_video},
            'results':           None,
            'docket':            None,
            'registered_at':     sample_entry['registered_at'],
            'case_name':         fname,
            'inventory':         {cat: [dest], **{k: [] for k in inv_dict if k != cat}},
            'inventory_schema':  inv_dict,
            'total_files':       1,
            'status':            'Ready',
        }

    CASES[case_id]['status'] = 'Processing'
    try:
        result = _run_pipeline_and_build_response(case_id)
        CASES[case_id]['status'] = 'Complete'
        return result
    except Exception as e:
        CASES[case_id]['status'] = 'Error'
        raise HTTPException(status_code=500, detail=f'Investigation failed: {str(e)}')


# ── SSE Streaming Investigation ───────────────────────────────────────────────

@router.post('/investigation/stream')
async def stream_investigation(req: StreamStartRequest):
    """
    Server-Sent Events endpoint — TRUE live streaming via event queue.
    The pipeline runs in a background thread and pushes events onto a queue.Queue.
    The async generator reads from that queue in real-time and streams them to the browser.

    Events emitted:
      - {"event": "start",         "data": {"case_id": "...", "timestamp": "..."}}
      - {"event": "planner_step",  "data": {...}}
      - {"event": "agent_start",   "data": {"agent": "...", "timestamp": "..."}}
      - {"event": "agent_done",    "data": {...agent response...}}
      - {"event": "hypothesis",    "data": {"authentic": 0.xx, "synthetic": 0.xx}}
      - {"event": "graph_update",  "data": {"nodes": N, "edges": E, "entities": [...]}}
      - {"event": "gap_analysis",  "data": {...gap output...}}
      - {"event": "complete",      "data": {...full result...}}
      - {"event": "error",         "data": {"message": "..."}}
    """
    case_id = req.case_id

    async def event_generator() -> AsyncIterator[str]:
        # Resolve / register the case
        if case_id not in CASES:
            locker_data = await get_evidence_locker()
            locker_json = json.loads(locker_data.body)
            sample_entry = next((c for c in locker_json['cases'] if c['case_id'] == case_id), None)

            if not sample_entry or '_locker_file' not in sample_entry:
                yield f"data: {json.dumps({'event': 'error', 'data': {'message': f'Case not found: {case_id}'}})}\n\n"
                return

            src_path = sample_entry['_locker_file']
            fname    = sample_entry['_locker_filename']
            ext      = get_file_extension(fname)
            dest_dir = os.path.join(UPLOAD_DIR, case_id)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, fname)
            shutil.copy2(src_path, dest)

            with open(dest, 'rb') as f:
                file_bytes = f.read()

            is_video = ext in VIDEO_EXTS
            cat = 'videos' if is_video else 'images'
            inv_dict = {'images': 0, 'videos': 0, 'audio': 0, 'documents': 0, 'chats': 0, 'unknown': 0}
            inv_dict[cat] = 1

            CASES[case_id] = {
                'file_path': dest, 'is_video': is_video,
                'original_filename': fname, 'file_bytes': file_bytes,
                'sha256': hashlib.sha256(file_bytes).hexdigest(),
                'metadata': {'filename': fname, 'size_bytes': len(file_bytes), 'is_video': is_video},
                'results': None, 'docket': None,
                'registered_at': sample_entry['registered_at'],
                'case_name': fname,
                'inventory': {cat: [dest], **{k: [] for k in inv_dict if k != cat}},
                'inventory_schema': inv_dict, 'total_files': 1, 'status': 'Ready',
            }

        CASES[case_id]['status'] = 'Processing'

        # ── Live event queue: agents push events here during execution ────────
        ev_queue: queue.Queue = queue.Queue()
        loop = asyncio.get_event_loop()
        result_holder: dict = {}
        error_holder:  dict = {}
        _SENTINEL = object()

        def _run_pipeline_thread():
            """Runs the blocking pipeline in a thread, pushing live events to ev_queue."""
            try:
                r = _run_pipeline_and_build_response(case_id, event_queue=ev_queue)
                result_holder['result'] = r
                CASES[case_id]['status'] = 'Complete'
            except Exception as exc:
                error_holder['error'] = str(exc)
                CASES[case_id]['status'] = 'Error'
            finally:
                ev_queue.put(_SENTINEL)  # signal completion

        # Emit start event immediately
        yield f"data: {json.dumps({'event': 'start', 'data': {'case_id': case_id, 'timestamp': datetime.now().strftime('%H:%M:%S')}})}\n\n"

        # Start pipeline in background thread
        t = threading.Thread(target=_run_pipeline_thread, daemon=True)
        t.start()

        # Stream events from the queue in real-time as they arrive
        while True:
            try:
                # Non-blocking poll so we can yield keepalives and stay async-friendly
                item = await loop.run_in_executor(None, ev_queue.get, True, 0.25)
            except Exception:
                # Timeout — yield a keepalive comment and loop
                yield ": keepalive\n\n"
                continue

            if item is _SENTINEL:
                break

            # Serialize and forward the live event
            try:
                yield f"data: {json.dumps(item)}\n\n"
            except (TypeError, ValueError):
                pass  # skip non-serialisable events

        # Pipeline finished — emit error or complete
        if error_holder:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': error_holder['error']}})}\n\n"
            return

        result = result_holder.get('result')
        if not result:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'Pipeline returned no result'}})}\n\n"
            return

        result_dict = result.model_dump()

        # Emit gap analysis as a dedicated event if not already streamed
        gap_data = result_dict.get('evidence_gap', {}).get('output', {})
        if gap_data:
            yield f"data: {json.dumps({'event': 'gap_analysis', 'data': gap_data})}\n\n"
            await asyncio.sleep(0.02)

        # Final complete event with full result payload
        yield f"data: {json.dumps({'event': 'complete', 'data': result_dict})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY ENDPOINTS (preserved for backwards compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post('/upload', response_model=UploadResponse)
async def upload_evidence(file: UploadFile = File(...)):
    case_id = f'KP-{uuid.uuid4().hex[:8].upper()}'
    ext = get_file_extension(file.filename or '')
    file_path = os.path.join(UPLOAD_DIR, f'{case_id}{ext}')

    file_bytes = await file.read()
    with open(file_path, 'wb') as f:
        f.write(file_bytes)

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    is_video = ext in VIDEO_EXTS
    cat = 'videos' if is_video else 'images'
    inv_dict = {'images': 0, 'videos': 0, 'audio': 0, 'documents': 0, 'chats': 0, 'unknown': 0}
    inv_dict[cat] = 1

    metadata = {'filename': file.filename, 'size_bytes': len(file_bytes), 'is_video': is_video, 'mime_type': file.content_type}

    CASES[case_id] = {
        'file_path':         file_path,
        'is_video':          is_video,
        'metadata':          metadata,
        'sha256':            sha256_hash,
        'original_filename': file.filename,
        'file_bytes':        file_bytes,
        'results':           None,
        'docket':            None,
        'registered_at':     datetime.now().strftime('%H:%M %d/%m/%Y'),
        'case_name':         file.filename,
        'inventory':         {cat: [file_path], **{k: [] for k in inv_dict if k != cat}},
        'inventory_schema':  inv_dict,
        'total_files':       1,
        'status':            'Ready',
    }

    return UploadResponse(case_id=case_id, sha256=sha256_hash, metadata=metadata)


@router.post('/analyze', response_model=MultiAgentInvestigationResponse)
async def analyze_evidence(req: AnalyzeRequest):
    if req.case_id not in CASES:
        raise HTTPException(status_code=404, detail='Case ID not found')
    try:
        return _run_pipeline_and_build_response(req.case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Pipeline execution failed: {str(e)}')


@router.get('/report/{case_id}')
async def get_report(case_id: str):
    if case_id not in CASES or not CASES[case_id].get('docket'):
        raise HTTPException(status_code=404, detail='Report not found')
    return HTMLResponse(content=CASES[case_id]['docket']['html_content'])


@router.get('/graph/{case_id}')
async def get_graph(case_id: str):
    if case_id not in CASES or not CASES[case_id].get('results'):
        raise HTTPException(status_code=404, detail='Graph not found')

    vision_res  = CASES[case_id]['results'].get('vision', {}).get('output', {})
    vlm_entities = vision_res.get('environmental_objects', [])
    nodes = [{'id': case_id, 'label': f'TARGET: {case_id}', 'type': 'case'}]
    edges = []
    for ent in vlm_entities:
        name = ent.get('entity', 'Unknown') if isinstance(ent, dict) else str(ent)
        nodes.append({'id': name, 'label': name, 'type': 'environmental_entity'})
        edges.append({'source': case_id, 'target': name})

    return JSONResponse(content={'nodes': nodes, 'edges': edges})


@router.get('/')
async def api_root():
    return JSONResponse(content={
        'status': 'online',
        'system': 'Project A.E.G.I.S. API',
        'version': '2.0.0',
        'health': '/api/health'
    })


@router.get('/health')
async def system_health():
    gemini_status = 'online' if GEMINI_API_KEY else 'offline'
    groq_status   = 'online' if os.getenv('GROQ_API_KEY') else 'offline'
    return JSONResponse(content={
        'agents': [
            {'name': 'Investigation Orchestrator', 'status': 'online'},
            {'name': 'Evidence Intake',            'status': 'online'},
            {'name': 'Privacy Shield',             'status': 'online'},
            {'name': 'ENF Physics',                'status': 'online'},
            {'name': 'Corneal Topology',           'status': 'online'},
            {'name': 'Vision Intelligence',        'status': gemini_status},
            {'name': 'Intelligence Fusion',        'status': 'online'},
            {'name': 'Knowledge Graph',            'status': 'online'},
            {'name': 'Risk Assessment',            'status': 'online'},
            {'name': 'Evidence Gap Agent',         'status': 'online'},
            {'name': 'Legal Reasoning',            'status': 'online'},
        ],
        'providers': {
            'groq':   groq_status,
            'gemini': gemini_status,
        }
    })

@router.get('/files/{case_id}/{filename}')
async def get_case_file(case_id: str, filename: str):
    """Serve media files (like shielded images) from a case directory."""
    # First check UPLOAD_DIR
    file_path = os.path.join(UPLOAD_DIR, case_id, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Check SAMPLES_DIR (for sample cases)
    file_path = os.path.join(SAMPLES_DIR, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    raise HTTPException(status_code=404, detail='File not found')
