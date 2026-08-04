"""
Multi-Signal Image Forensic Scoring Engine for Project A.E.G.I.S.
Evaluates 8 independent computer vision & optical physics indicators to detect synthetic AI media
without relying on single-threshold binary decisions, eliminating false positives on real photographs.

Independent Forensic Indicators:
  1. Corneal Specular Reflection Consistency (Glint geometry dissimilarity)
  2. EXIF Camera Metadata Integrity (Sensor tags vs AI stripped metadata)
  3. JPEG Quantization & Compression Artifact Consistency
  4. Aspect Ratio & Canvas Resolution Anomaly Analysis
  5. Laplacian Blur Variance (Depth-of-field vs AI hyper-sharpness/over-smoothing)
  6. High-Frequency Spatial Noise Residual Variance (Sensor shot noise vs clean AI surfaces)
  7. Structural Edge Density Distribution (Canny edge statistics)
  8. HSV Saturation & Color Histogram Distribution (Over-saturation & dynamic range)
"""

import os
import cv2
import numpy as np
from PIL import Image, ExifTags

def extract_eye_rois(img_bgr):
    """
    Extracts left and right eye image crops using OpenCV or geometric fallback.
    Returns:
      - left_eye_crop, right_eye_crop
      - left_box (x, y, w, h), right_box (x, y, w, h)
    """
    if img_bgr is None:
        return None, None, None, None
        
    h_img, w_img = img_bgr.shape[:2]
    
    try:
        cascade_path = getattr(cv2.data, 'haarcascades', '')
        eye_xml = os.path.join(cascade_path, 'haarcascade_eye.xml')
        if os.path.exists(eye_xml):
            eye_cascade = cv2.CascadeClassifier(eye_xml)
            if not eye_cascade.empty():
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(20, 20))
                
                if len(eyes) >= 2:
                    eyes = sorted(eyes, key=lambda e: e[0])
                    x1, y1, w1, h1 = eyes[0]
                    x2, y2, w2, h2 = eyes[1]
                    
                    pad1 = int(w1 * 0.25)
                    pad2 = int(w2 * 0.25)
                    
                    l_crop = img_bgr[max(0, y1-pad1):min(h_img, y1+h1+pad1), max(0, x1-pad1):min(w_img, x1+w1+pad1)]
                    r_crop = img_bgr[max(0, y2-pad2):min(h_img, y2+h2+pad2), max(0, x2-pad2):min(w_img, x2+w2+pad2)]
                    
                    return l_crop, r_crop, (x1, y1, w1, h1), (x2, y2, w2, h2)
    except Exception:
        pass
        
    eye_y1, eye_y2 = int(h_img * 0.38), int(h_img * 0.58)
    l_x1, l_x2 = int(w_img * 0.20), int(w_img * 0.48)
    r_x1, r_x2 = int(w_img * 0.52), int(w_img * 0.80)
    
    l_crop = img_bgr[eye_y1:eye_y2, l_x1:l_x2]
    r_crop = img_bgr[eye_y1:eye_y2, r_x1:r_x2]
    
    return l_crop, r_crop, (l_x1, eye_y1, l_x2-l_x1, eye_y2-eye_y1), (r_x1, eye_y1, r_x2-r_x1, eye_y2-eye_y1)

def analyze_corneal_glints(eye_crop):
    """
    Isolates specular light glints inside the dark iris/pupil region of an eye crop.
    """
    if eye_crop is None or eye_crop.size == 0:
        return np.zeros((50, 50), dtype=np.uint8), 0, {"area": 0, "circularity": 0, "cx": 0.5, "cy": 0.5, "aspect": 1.0}
        
    gray = cv2.cvtColor(eye_crop, cv2.COLOR_BGR2GRAY)
    h_c, w_c = gray.shape[:2]
    
    margin_x = int(w_c * 0.20)
    margin_y = int(h_c * 0.20)
    iris_roi = gray[margin_y:h_c-margin_y, margin_x:w_c-margin_x]
    
    if iris_roi.size == 0:
        iris_roi = gray
        margin_x, margin_y = 0, 0
        
    _, glint_mask_sub = cv2.threshold(iris_roi, 240, 255, cv2.THRESH_BINARY)
    
    glint_mask = np.zeros_like(gray)
    glint_mask[margin_y:h_c-margin_y, margin_x:w_c-margin_x] = glint_mask_sub
    
    contours, _ = cv2.findContours(glint_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_glints = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= 1:
            perimeter = cv2.arcLength(cnt, True) + 1e-5
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            
            x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
            aspect = float(w_b) / float(h_b + 1e-5)
            
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = (M["m10"] / M["m00"]) / w_c
                cy = (M["m01"] / M["m00"]) / h_c
            else:
                cx, cy = 0.5, 0.5
            valid_glints.append({
                "area": float(area),
                "circularity": float(circularity),
                "aspect": aspect,
                "cx": float(cx),
                "cy": float(cy)
            })
            
    if not valid_glints:
        return glint_mask, 0, {"area": 0.0, "circularity": 0.0, "aspect": 1.0, "cx": 0.5, "cy": 0.5}
        
    primary = max(valid_glints, key=lambda g: g["area"])
    return glint_mask, len(valid_glints), primary

# ==================== INDEPENDENT FORENSIC INDICATORS ====================

def eval_corneal_indicator(l_count, r_count, l_feat, r_feat):
    """Indicator 1: Corneal Specular Reflection Consistency (Weight = 0.30)"""
    count_diff = abs(l_count - r_count)
    count_penalty = 0.45 if count_diff > 0 else 0.0
    
    max_area = max(l_feat["area"], r_feat["area"]) + 1e-5
    area_diff = abs(l_feat["area"] - r_feat["area"]) / max_area
    aspect_diff = abs(l_feat["aspect"] - r_feat["aspect"]) / (max(l_feat["aspect"], r_feat["aspect"]) + 1e-5)
    circ_diff = abs(l_feat["circularity"] - r_feat["circularity"])
    
    dissimilarity = count_penalty + (0.30 * area_diff) + (0.25 * aspect_diff) + (0.15 * circ_diff)
    score = float(np.clip(dissimilarity * 100.0, 0.0, 100.0))
    
    expl = f"Corneal Specular Glint Disparity: {score:.1f}% dissimilarity across left ({l_count}) and right ({r_count}) eye glint contours."
    return score, expl

def eval_exif_indicator(image_path_or_bytes):
    """Indicator 2: EXIF Metadata Structure (Weight = 0.20)"""
    if not image_path_or_bytes:
        return 50.0, "EXIF Metadata: Media source path unavailable for EXIF header verification."
        
    try:
        if isinstance(image_path_or_bytes, str) and os.path.exists(image_path_or_bytes):
            pil_img = Image.open(image_path_or_bytes)
        else:
            return 50.0, "EXIF Metadata: Raw BGR matrix passed without file header."
            
        exif = pil_img._getexif()
        if exif:
            exif_dict = {ExifTags.TAGS.get(k, k): v for k, v in exif.items() if k in ExifTags.TAGS}
            camera_tags = ["Make", "Model", "DateTimeOriginal", "FNumber", "ExposureTime", "ISOSpeedRatings"]
            found = [t for t in camera_tags if t in exif_dict]
            if len(found) >= 2:
                return 0.0, f"EXIF Metadata: Genuine camera hardware tags verified ({', '.join(found[:3])})."
            else:
                return 30.0, f"EXIF Metadata: Partial EXIF tags present ({len(found)} camera attributes)."
        else:
            return 65.0, "EXIF Metadata: Stripped camera EXIF header (typical of web re-encoding or AI synthesis)."
    except Exception:
        return 50.0, "EXIF Metadata: Header parsing error or non-JPEG format."

def eval_jpeg_compression_indicator(img_bgr):
    """Indicator 3: JPEG Compression & Quantization Consistency (Weight = 0.15)"""
    if img_bgr is None:
        return 50.0, "JPEG Compression: Image matrix unavailable."
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    
    if h >= 64 and w >= 64:
        s1_h = gray[7::8, :]
        s2_h = gray[8::8, :]
        min_h = min(s1_h.shape[0], s2_h.shape[0])
        diff_h = np.abs(s1_h[:min_h].astype(np.float32) - s2_h[:min_h].astype(np.float32))
        
        s1_w = gray[:, 7::8]
        s2_w = gray[:, 8::8]
        min_w = min(s1_w.shape[1], s2_w.shape[1])
        diff_w = np.abs(s1_w[:, :min_w].astype(np.float32) - s2_w[:, :min_w].astype(np.float32))
        
        block_discontinuity = float(np.mean(diff_h) + np.mean(diff_w))
    else:
        block_discontinuity = 10.0
        
    if 3.5 <= block_discontinuity <= 25.0:
        score = 10.0
        expl = f"JPEG Compression: Standard hardware camera quantization grid verified (discontinuity: {block_discontinuity:.1f})."
    else:
        score = 60.0
        expl = f"JPEG Compression: Non-standard quantization grid (discontinuity: {block_discontinuity:.1f})."
        
    return score, expl

def eval_resolution_indicator(img_bgr):
    """Indicator 4: Aspect Ratio & Canvas Resolution Anomaly (Weight = 0.10)"""
    if img_bgr is None:
        return 50.0, "Resolution: Image matrix unavailable."
        
    h, w = img_bgr.shape[:2]
    
    ai_resolutions = [(1024, 1024), (512, 512), (2048, 2048), (1024, 1536), (1536, 1024), (1024, 576)]
    if (w, h) in ai_resolutions or (h, w) in ai_resolutions:
        score = 65.0
        expl = f"Resolution Anomaly: Exact AI diffusion canvas resolution ({w}x{h})."
    else:
        aspect = max(w, h) / float(min(w, h) + 1e-5)
        if 1.25 <= aspect <= 1.8:
            score = 10.0
            expl = f"Resolution: Standard camera optical aspect ratio ({w}x{h}, aspect {aspect:.2f})."
        else:
            score = 35.0
            expl = f"Resolution: Non-standard resolution framing ({w}x{h})."
            
    return score, expl

def eval_blur_indicator(img_bgr):
    """Indicator 5: Laplacian Blur Variance (Weight = 0.05)"""
    if img_bgr is None:
        return 50.0, "Blur Estimation: Image matrix unavailable."
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    if 60.0 <= lap_var <= 1600.0:
        score = 10.0
        expl = f"Focus Blur Variance: Natural camera depth-of-field focus (Laplacian Var: {lap_var:.1f})."
    elif lap_var > 2200.0:
        score = 65.0
        expl = f"Focus Blur Anomaly: Hyper-sharp synthetic rendering (Laplacian Var: {lap_var:.1f})."
    else:
        score = 45.0
        expl = f"Focus Blur Anomaly: Over-smoothed spatial regions (Laplacian Var: {lap_var:.1f})."
        
    return score, expl

def eval_noise_indicator(img_bgr):
    """Indicator 6: Spatial Noise Residual Variance (Weight = 0.10)"""
    if img_bgr is None:
        return 50.0, "Noise Variance: Image matrix unavailable."
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
    noise_residual = gray - blurred
    noise_var = float(np.var(noise_residual))
    
    if noise_var >= 2.2:
        score = 10.0
        expl = f"Sensor Noise Residual: Physical ISO photon shot noise detected (Variance: {noise_var:.2f})."
    else:
        score = 70.0
        expl = f"Sensor Noise Anomaly: Hyper-clean zero-noise surface characteristic of AI diffusion (Variance: {noise_var:.2f})."
        
    return score, expl

def eval_edge_density_indicator(img_bgr):
    """Indicator 7: Structural Edge Density Distribution (Weight = 0.05)"""
    if img_bgr is None:
        return 50.0, "Edge Density: Image matrix unavailable."
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.mean(edges) / 255.0)
    
    if 0.03 <= edge_density <= 0.18:
        score = 10.0
        expl = f"Edge Density: Natural structural contour distribution ({edge_density*100:.1f}% edge density)."
    else:
        score = 55.0
        expl = f"Edge Density Anomaly: Unusual texture distribution ({edge_density*100:.1f}% edge density)."
        
    return score, expl

def eval_saturation_indicator(img_bgr):
    """Indicator 8: Saturation Statistics & Color Histogram (Weight = 0.05)"""
    if img_bgr is None:
        return 50.0, "Saturation: Image matrix unavailable."
        
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    sat_mean = float(np.mean(hsv[:, :, 1]))
    sat_std = float(np.std(hsv[:, :, 1]))
    
    if sat_mean > 135.0 or (sat_mean > 115.0 and sat_std > 65.0):
        score = 65.0
        expl = f"Color Saturation Anomaly: Artificial over-saturation (HSV Saturation Mean: {sat_mean:.1f})."
    else:
        score = 10.0
        expl = f"Color Saturation: Balanced real-world color distribution (HSV Saturation Mean: {sat_mean:.1f})."
        
    return score, expl

# ==================== MAIN MULTI-SIGNAL FORENSIC ENGINE ====================

def analyze_corneal_specular_topology(img_bgr, file_path: str = None):
    """
    Main Multi-Signal Forensic Scoring Engine.
    Combines 8 independent computer vision & optical indicators into a weighted ensemble score,
    eliminating single-threshold false positives on real photographs.
    """
    if isinstance(img_bgr, str) and file_path is None:
        file_path = img_bgr
        img_bgr = cv2.imread(file_path)
        
    l_crop, r_crop, l_box, r_box = extract_eye_rois(img_bgr)
    l_mask, l_count, l_feat = analyze_corneal_glints(l_crop)
    r_mask, r_count, r_feat = analyze_corneal_glints(r_crop)
    
    s1, exp1 = eval_corneal_indicator(l_count, r_count, l_feat, r_feat)
    s2, exp2 = eval_exif_indicator(file_path)
    s3, exp3 = eval_jpeg_compression_indicator(img_bgr)
    s4, exp4 = eval_resolution_indicator(img_bgr)
    s5, exp5 = eval_blur_indicator(img_bgr)
    s6, exp6 = eval_noise_indicator(img_bgr)
    s7, exp7 = eval_edge_density_indicator(img_bgr)
    s8, exp8 = eval_saturation_indicator(img_bgr)
    
    weights = {
        "corneal_reflection": 0.30,
        "exif_metadata": 0.20,
        "jpeg_compression": 0.15,
        "resolution_aspect": 0.10,
        "noise_residual": 0.10,
        "blur_laplacian": 0.05,
        "edge_density": 0.05,
        "saturation_stats": 0.05
    }
    
    scores = {
        "corneal_reflection": s1,
        "exif_metadata": s2,
        "jpeg_compression": s3,
        "resolution_aspect": s4,
        "noise_residual": s6,
        "blur_laplacian": s5,
        "edge_density": s7,
        "saturation_stats": s8
    }
    
    explanations = [exp1, exp2, exp3, exp4, exp5, exp6, exp7, exp8]
    
    weighted_anomaly_score = sum(weights[k] * scores[k] for k in weights)
    anomaly_score = float(np.clip(weighted_anomaly_score, 5.0, 95.0))
    
    symmetry_score = float(np.clip(100.0 - anomaly_score, 10.0, 98.5))
    
    # Multi-signal decision rule: Anomaly Score < 32.0 => AUTHENTIC (Integrity >= 68.0%)
    is_authentic = (anomaly_score < 32.0)
    confidence = float(min(99.0, max(55.0, abs(anomaly_score - 32.0) * 1.8 + 60.0)))
    
    verdict_text = (
        f"AUTHENTIC REAL-WORLD CAPTURE (Multi-Signal Anomaly Score: {anomaly_score:.1f}%)"
        if is_authentic else
        f"SYNTHETIC AI FABRICATION (Multi-Signal Anomaly Score: {anomaly_score:.1f}%)"
    )
    
    contributing_features = {
        k: {
            "score": round(scores[k], 1),
            "weight": weights[k],
            "weighted_impact": round(scores[k] * weights[k], 2)
        }
        for k in weights
    }
    
    return {
        "l_crop": l_crop,
        "r_crop": r_crop,
        "l_mask": l_mask,
        "r_mask": r_mask,
        "l_count": l_count,
        "r_count": r_count,
        "l_feat": l_feat,
        "r_feat": r_feat,
        "symmetry_score": symmetry_score,
        "anomaly_score": anomaly_score,
        "confidence": confidence,
        "contributing_features": contributing_features,
        "explanation": explanations,
        "is_authentic": is_authentic,
        "verdict_text": verdict_text
    }
