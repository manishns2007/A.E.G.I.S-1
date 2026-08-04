"""
Pipeline Orchestrator for Project A.E.G.I.S.
Coordinates independent forensic modules, ensures graceful failure, and standardizes outputs.
"""
import time
import traceback
import cv2
import os

import privacy_shield
import enf_analyzer
import corneal_analyzer
import vlm_extractor
import knowledge_graph
import legal_docket
import sample_generator

def standardize_result(status="success", processing_time=0.0, confidence=None, findings=None, error_message=None):
    return {
        "status": status,
        "processing_time": processing_time,
        "confidence": confidence,
        "findings": findings if findings is not None else {},
        "error_message": error_message
    }

def run_pipeline(file_path: str, is_vid: bool, gemini_api_key: str, case_id: str):
    """
    Executes the forensic pipeline sequentially, capturing execution times and handling failures gracefully.
    """
    results = {}
    unified_feature_store = {
        "file_path": file_path,
        "is_video": is_vid,
        "shielded_bgr": None,
        "shielded_vid_path": None,
        "img_bgr": None,
        "case_id": case_id
    }

    # 1. Privacy Shield Execution
    start_time = time.time()
    try:
        if not is_vid:
            img_bgr = cv2.imread(file_path)
            unified_feature_store["img_bgr"] = img_bgr
            shielded_bgr, face_count, bboxes = privacy_shield.apply_privacy_shield_to_image(img_bgr)
            unified_feature_store["shielded_bgr"] = shielded_bgr
            results["privacy"] = standardize_result(
                status="success",
                processing_time=time.time() - start_time,
                findings={
                    "count": face_count,
                    "img_bgr": img_bgr,
                    "shielded_bgr": shielded_bgr,
                    "shielded_vid_path": None
                }
            )
        else:
            out_vid = os.path.join(sample_generator.SAMPLE_DIR, f"shielded_{os.path.basename(file_path)}")
            shielded_vid, face_count = privacy_shield.apply_privacy_shield_to_video(file_path, out_vid)
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            unified_feature_store["img_bgr"] = frame
            shielded_bgr, _, _ = privacy_shield.apply_privacy_shield_to_image(frame)
            unified_feature_store["shielded_bgr"] = shielded_bgr
            unified_feature_store["shielded_vid_path"] = out_vid
            results["privacy"] = standardize_result(
                status="success",
                processing_time=time.time() - start_time,
                findings={
                    "count": face_count,
                    "img_bgr": frame,
                    "shielded_bgr": shielded_bgr,
                    "shielded_vid_path": out_vid
                }
            )
    except Exception as e:
        results["privacy"] = standardize_result(status="failed", processing_time=time.time() - start_time, error_message=str(e))
        # Provide fallback so pipeline continues
        img_bgr = cv2.imread(file_path) if not is_vid else cv2.VideoCapture(file_path).read()[1]
        unified_feature_store["img_bgr"] = img_bgr
        unified_feature_store["shielded_bgr"] = img_bgr
        results["privacy"]["findings"] = {"count": 0, "img_bgr": img_bgr, "shielded_bgr": img_bgr, "shielded_vid_path": file_path if is_vid else None}

    # 2. ENF Physics Analyzer
    start_time = time.time()
    try:
        if is_vid:
            enf_findings = enf_analyzer.analyze_video_enf(file_path, target_freq=50.0)
            status = "success" if enf_findings.get("is_enf_available") else "warning"
            results["enf"] = standardize_result(status=status, processing_time=time.time() - start_time, confidence=enf_findings.get("confidence"), findings=enf_findings)
        else:
            enf_findings = {
                "is_enf_available": False,
                "enf_ratio": 1.0,
                "is_authentic": True,
                "verdict_text": "Unavailable",
                "reason": "Unavailable (Static image input)",
                "freqs": [], "spectrum": [], "luminance_signal": [], "time_stamps": []
            }
            results["enf"] = standardize_result(status="warning", processing_time=time.time() - start_time, findings=enf_findings, error_message="Not applicable for static images")
    except Exception as e:
        results["enf"] = standardize_result(status="failed", processing_time=time.time() - start_time, error_message=str(e), findings={"is_authentic": True, "verdict_text": "Error computing ENF", "is_enf_available": False})

    # 3. Multi-Signal Corneal Specular Topology Engine
    start_time = time.time()
    try:
        img_for_corneal = unified_feature_store["img_bgr"]
        corneal_findings = corneal_analyzer.analyze_corneal_specular_topology(img_for_corneal, file_path=file_path)
        status = "success" if corneal_findings.get("is_quality_sufficient") else "warning"
        results["corneal"] = standardize_result(status=status, processing_time=time.time() - start_time, confidence=corneal_findings.get("confidence"), findings=corneal_findings)
    except Exception as e:
        results["corneal"] = standardize_result(status="failed", processing_time=time.time() - start_time, error_message=str(e), findings={"is_authentic": True, "verdict_text": "Error computing Corneal analysis", "is_quality_sufficient": False, "symmetry_score": 0.0})

    # 4. Visuo-Acoustic Knowledge Graphing (VLM)
    start_time = time.time()
    try:
        vlm_findings = vlm_extractor.parse_background_environment(unified_feature_store["shielded_bgr"], gemini_api_key)
        status = "success" if vlm_findings.get("status") != "offline" else "warning"
        results["vlm"] = standardize_result(status=status, processing_time=time.time() - start_time, findings=vlm_findings)
    except Exception as e:
        results["vlm"] = standardize_result(status="failed", processing_time=time.time() - start_time, error_message=str(e), findings={"status": "offline", "environmental_objects": []})

    # 5. NetworkX Knowledge Graph Compilation
    start_time = time.time()
    try:
        G = knowledge_graph.build_case_knowledge_graph(
            case_id,
            results["vlm"]["findings"].get("environmental_objects", []),
            None # strictly NO historical cases
        )
        graph_fig = knowledge_graph.generate_plotly_network_figure(G)
        graph_correlations = knowledge_graph.analyze_cross_case_correlations(G, case_id, False)
        
        results["graph"] = standardize_result(status="success", processing_time=time.time() - start_time, findings={
            "graph_fig": graph_fig,
            "graph_correlations": graph_correlations,
            "historical_db_connected": False
        })
    except Exception as e:
        results["graph"] = standardize_result(status="failed", processing_time=time.time() - start_time, error_message=str(e), findings={"historical_db_connected": False})

    return results
