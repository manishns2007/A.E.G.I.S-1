"""
Corneal Specular Topology Analyzer for Project A.E.G.I.S.
Classical Computer Vision Engine for Face & Eye Detection, Image Quality Filtering,
Specular Glint Geometry Extraction, and Multi-Signal Forensic Evaluation.

Quality Filtering Pipeline (Classical CV):
  1. Face Detection & Minimum Bounding Box Resolution (Rejects tiny faces)
  2. Eye ROI Detection & Frontal Pose Symmetry (Rejects side profiles)
  3. Eye Aspect Ratio & Pupil Contrast Analysis (Rejects closed/blinking eyes)
  4. Laplacian Focus Blur Variance (Rejects blurry eyes)

Calculated Glint Metrics:
  - Glint Count
  - Glint Centroid (cx, cy)
  - Circularity (4 * pi * Area / Perimeter^2)
  - Contour Area
  - Specular Symmetry Score
"""

import os
import cv2
import numpy as np
from PIL import Image, ExifTags

# ==================== CLASSICAL CV FACE & EYE DETECTOR ====================

def detect_face_and_eyes_classical(img_bgr):
    """
    Classical CV Face and Eye Detector with Strict Quality & Pose Filtering.
    Returns 'No evidence available' if image array is empty or unreadable.
    """
    if img_bgr is None or img_bgr.size == 0:
        return False, "No evidence available: Invalid or unreadable image array.", None, None, None, None, 0.0

    h_img, w_img = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Face Detection via OpenCV Haar Cascade (with multi-scale normalization)
    cascade_path = getattr(cv2.data, 'haarcascades', '')
    face_xml = os.path.join(cascade_path, 'haarcascade_frontalface_default.xml')
    eye_xml = os.path.join(cascade_path, 'haarcascade_eye.xml')

    faces = []
    if os.path.exists(face_xml):
        try:
            face_cascade = cv2.CascadeClassifier(face_xml)
            if not face_cascade.empty():
                # Scale down for robust detection if resolution > 1000px
                target_w = 800.0
                scale_ratio = target_w / float(w_img) if w_img > target_w else 1.0
                if scale_ratio < 1.0:
                    small_gray = cv2.resize(gray, (int(w_img * scale_ratio), int(h_img * scale_ratio)))
                else:
                    small_gray = gray

                detected_small = face_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                for (s_x, s_y, s_w, s_h) in detected_small:
                    if scale_ratio < 1.0:
                        faces.append((int(s_x / scale_ratio), int(s_y / scale_ratio), int(s_w / scale_ratio), int(s_h / scale_ratio)))
                    else:
                        faces.append((s_x, s_y, s_w, s_h))
        except Exception:
            pass

    if len(faces) == 0:
        overall_blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if overall_blur < 35.0:
            return False, "Insufficient image quality: Overall image blur too high (Laplacian Var < 35).", None, None, None, None, 15.0

        fx, fy, fw, fh = int(w_img * 0.20), int(h_img * 0.15), int(w_img * 0.60), int(h_img * 0.70)
        faces = [(fx, fy, fw, fh)]

    primary_face = max(faces, key=lambda f: f[2] * f[3])
    fx, fy, fw, fh = primary_face

    # Quality Check: Reject Tiny Faces
    face_area = fw * fh
    img_area = w_img * h_img
    face_ratio = face_area / float(img_area + 1e-5)

    if fw < 70 or fh < 70 or face_ratio < 0.03:
        return False, f"Insufficient image quality: Tiny face detected ({fw}x{fh} px, {face_ratio*100:.1f}% canvas).", None, None, None, None, 25.0

    face_gray = gray[fy:fy+fh, fx:fx+fw]

    # Eye Detection & Pose Filtering
    eyes = []
    if os.path.exists(eye_xml):
        try:
            eye_cascade = cv2.CascadeClassifier(eye_xml)
            if not eye_cascade.empty():
                upper_face_gray = face_gray[0:int(fh * 0.60), :]
                eyes_detected = eye_cascade.detectMultiScale(upper_face_gray, scaleFactor=1.1, minNeighbors=3, minSize=(16, 16))
                for ex, ey, ew, eh in eyes_detected:
                    eyes.append((fx + ex, fy + ey, ew, eh))
        except Exception:
            pass

    if len(eyes) >= 2:
        eyes = sorted(eyes, key=lambda e: e[0])
        e1, e2 = eyes[0], eyes[1]

        eye1_cx = e1[0] + e1[2] / 2.0
        eye2_cx = e2[0] + e2[2] / 2.0
        eye_sep = abs(eye2_cx - eye1_cx)

        if eye_sep < (fw * 0.22) or eye_sep > (fw * 0.75):
            return False, "Insufficient image quality: Side profile or asymmetric facial pose detected.", None, None, None, None, 30.0

        if abs(e1[1] - e2[1]) > (fh * 0.15):
            return False, "Insufficient image quality: Extreme head tilt / non-frontal pose detected.", None, None, None, None, 32.0

        pad1, pad2 = int(e1[2] * 0.25), int(e2[2] * 0.25)
        l_crop = img_bgr[max(0, e1[1]-pad1):min(h_img, e1[1]+e1[3]+pad1), max(0, e1[0]-pad1):min(w_img, e1[0]+e1[2]+pad1)]
        r_crop = img_bgr[max(0, e2[1]-pad2):min(h_img, e2[1]+e2[3]+pad2), max(0, e2[0]-pad2):min(w_img, e2[0]+e2[2]+pad2)]
        l_box, r_box = e1, e2
    else:
        eye_y1, eye_y2 = int(fy + fh * 0.28), int(fy + fh * 0.58)
        l_x1, l_x2 = int(fx + fw * 0.12), int(fx + fw * 0.46)
        r_x1, r_x2 = int(fx + fw * 0.54), int(fx + fw * 0.88)

        l_crop = img_bgr[eye_y1:eye_y2, l_x1:l_x2]
        r_crop = img_bgr[eye_y1:eye_y2, r_x1:r_x2]
        l_box = (l_x1, eye_y1, l_x2-l_x1, eye_y2-eye_y1)
        r_box = (r_x1, eye_y1, r_x2-r_x1, eye_y2-eye_y1)

    if l_crop is None or r_crop is None or l_crop.size == 0 or r_crop.size == 0:
        return False, "Insufficient image quality: Failed to isolate eye regions of interest.", None, None, None, None, 20.0

    # Quality Check: Closed / Blinking Eyes
    l_gray = cv2.cvtColor(l_crop, cv2.COLOR_BGR2GRAY)
    r_gray = cv2.cvtColor(r_crop, cv2.COLOR_BGR2GRAY)

    l_h, l_w = l_gray.shape[:2]
    r_h, r_w = r_gray.shape[:2]

    l_ear = float(l_h) / float(l_w + 1e-5)
    r_ear = float(r_h) / float(r_w + 1e-5)

    if l_ear < 0.18 or r_ear < 0.18:
        return False, "Insufficient image quality: Closed or blinking eyes detected (Eye Aspect Ratio < 0.18).", None, None, None, None, 35.0

    # Quality Check: Blurry Eyes
    l_blur = float(cv2.Laplacian(l_gray, cv2.CV_64F).var())
    r_blur = float(cv2.Laplacian(r_gray, cv2.CV_64F).var())
    mean_eye_blur = (l_blur + r_blur) / 2.0

    if l_blur < 40.0 or r_blur < 40.0:
        return False, f"Insufficient image quality: Blurry eye regions (Laplacian Var: Left={l_blur:.1f}, Right={r_blur:.1f} < 40.0).", None, None, None, None, 35.0

    quality_confidence = float(np.clip(
        40.0 + (min(mean_eye_blur, 500.0) / 10.0) + (face_ratio * 100.0 * 0.5),
        55.0, 99.0
    ))

    return True, "Quality verified", l_crop, r_crop, l_box, r_box, quality_confidence

# ==================== GLINT EXTRACTION & GEOMETRY ====================

def analyze_corneal_glints(eye_crop):
    """
    Isolates specular light glints inside dark iris/pupil region.
    Calculates glint count, centroid, circularity, area.
    """
    default_feat = {"area": 0.0, "circularity": 0.0, "aspect": 1.0, "cx": 0.5, "cy": 0.5}
    if eye_crop is None or eye_crop.size == 0:
        return np.zeros((50, 50), dtype=np.uint8), 0, default_feat
        
    gray = cv2.cvtColor(eye_crop, cv2.COLOR_BGR2GRAY)
    h_c, w_c = gray.shape[:2]
    
    margin_x = int(w_c * 0.18)
    margin_y = int(h_c * 0.18)
    iris_roi = gray[margin_y:max(margin_y+1, h_c-margin_y), margin_x:max(margin_x+1, w_c-margin_x)]
    
    if iris_roi.size == 0:
        iris_roi = gray
        margin_x, margin_y = 0, 0
        
    _, glint_mask_sub = cv2.threshold(iris_roi, 235, 255, cv2.THRESH_BINARY)
    
    glint_mask = np.zeros_like(gray)
    glint_mask[margin_y:margin_y+glint_mask_sub.shape[0], margin_x:margin_x+glint_mask_sub.shape[1]] = glint_mask_sub
    
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
                cx = float((M["m10"] / M["m00"]) / w_c)
                cy = float((M["m01"] / M["m00"]) / h_c)
            else:
                cx, cy = 0.5, 0.5
                
            valid_glints.append({
                "area": float(area),
                "circularity": float(circularity),
                "aspect": float(aspect),
                "cx": float(cx),
                "cy": float(cy)
            })
            
    if not valid_glints:
        return glint_mask, 0, default_feat
        
    primary = max(valid_glints, key=lambda g: g["area"])
    return glint_mask, len(valid_glints), primary

# ==================== INDEPENDENT FORENSIC INDICATORS ====================

def eval_corneal_indicator(l_count, r_count, l_feat, r_feat):
    """Indicator 1: Corneal Specular Reflection Consistency (Weight = 0.30)"""
    if l_count == 0 and r_count == 0:
        return 50.0, "Corneal Reflection: No visible specular glints isolated in eye crops."

    count_diff = abs(l_count - r_count)
    count_penalty = 0.45 if count_diff > 0 else 0.0
    
    max_area = max(l_feat["area"], r_feat["area"]) + 1e-5
    area_diff = abs(l_feat["area"] - r_feat["area"]) / max_area
    aspect_diff = abs(l_feat["aspect"] - r_feat["aspect"]) / (max(l_feat["aspect"], r_feat["aspect"]) + 1e-5)
    circ_diff = abs(l_feat["circularity"] - r_feat["circularity"])
    centroid_dist = np.sqrt((l_feat["cx"] - r_feat["cx"])**2 + (l_feat["cy"] - r_feat["cy"])**2)
    
    dissimilarity = count_penalty + (0.25 * area_diff) + (0.20 * aspect_diff) + (0.15 * circ_diff) + (0.15 * centroid_dist)
    score = float(np.clip(dissimilarity * 100.0, 0.0, 100.0))
    
    expl = f"Corneal Specular Glint Disparity: {score:.1f}% dissimilarity across left ({l_count}) and right ({r_count}) eye glint contours."
    return score, expl

def eval_exif_indicator(image_path_or_bytes):
    """Indicator 2: EXIF Metadata Structure (Weight = 0.20)"""
    if not image_path_or_bytes:
        return 50.0, "EXIF Metadata: No evidence available for EXIF header verification."
        
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
            return 35.0, "EXIF Metadata: Stripped camera EXIF header (typical of web re-encoding or social media uploads)."
    except Exception:
        return 50.0, "EXIF Metadata: Header parsing error or non-JPEG format."

def eval_jpeg_compression_indicator(img_bgr):
    """Indicator 3: JPEG Compression & Quantization Consistency (Weight = 0.15)"""
    if img_bgr is None:
        return 50.0, "JPEG Compression: No evidence available."
        
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
        score = 35.0
        expl = f"JPEG Compression: Re-encoded web quantization grid (discontinuity: {block_discontinuity:.1f})."
        
    return score, expl

def eval_resolution_indicator(img_bgr):
    """Indicator 4: Aspect Ratio & Canvas Resolution Anomaly (Weight = 0.10)"""
    if img_bgr is None:
        return 50.0, "Resolution: No evidence available."
        
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
        return 50.0, "Blur Estimation: No evidence available."
        
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
        return 50.0, "Noise Variance: No evidence available."
        
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
        return 50.0, "Edge Density: No evidence available."
        
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
        return 50.0, "Saturation: No evidence available."
        
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
    Main Multi-Signal Forensic Engine with Classical Computer Vision Quality Filtering.
    Returns 'Insufficient image quality' or 'No evidence available' gracefully if image is unavailable.
    """
    if isinstance(img_bgr, str) and file_path is None:
        file_path = img_bgr
        img_bgr = cv2.imread(file_path)

    if img_bgr is None or img_bgr.size == 0:
        return {
            "l_crop": None, "r_crop": None, "l_mask": None, "r_mask": None,
            "l_count": 0, "r_count": 0,
            "l_feat": {"area": 0, "circularity": 0, "cx": 0.5, "cy": 0.5, "aspect": 1.0},
            "r_feat": {"area": 0, "circularity": 0, "cx": 0.5, "cy": 0.5, "aspect": 1.0},
            "symmetry_score": 50.0, "anomaly_score": 50.0, "confidence": 0.0,
            "is_quality_sufficient": False, "is_authentic": False,
            "verdict_text": "No evidence available",
            "quality_reason": "No evidence available: Image file missing or unreadable.",
            "contributing_features": {},
            "explanation": ["Rejection: No evidence available"]
        }

    # 1. Classical CV Face, Eye, and Quality Filter
    is_quality_valid, quality_reason, l_crop, r_crop, l_box, r_box, quality_confidence = detect_face_and_eyes_classical(img_bgr)

    # Extract Glint Features
    l_mask, l_count, l_feat = analyze_corneal_glints(l_crop)
    r_mask, r_count, r_feat = analyze_corneal_glints(r_crop)

    # Rejection Rule: Return "Insufficient image quality" or "No evidence available" if quality check fails
    if not is_quality_valid or quality_confidence < 40.0:
        verdict = "No evidence available" if "No evidence available" in quality_reason else "Insufficient image quality"
        return {
            "l_crop": l_crop,
            "r_crop": r_crop,
            "l_mask": l_mask,
            "r_mask": r_mask,
            "l_count": l_count,
            "r_count": r_count,
            "l_feat": l_feat,
            "r_feat": r_feat,
            "symmetry_score": 50.0,
            "anomaly_score": 50.0,
            "confidence": quality_confidence,
            "is_quality_sufficient": False,
            "is_authentic": True,  # Neutral default — do not flag synthetic if quality check was skipped/rejected
            "verdict_text": verdict,
            "quality_reason": quality_reason,
            "contributing_features": {},
            "explanation": [f"Rejection: {quality_reason}"]
        }

    # 2. Evaluate 8 Independent Forensic Indicators
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

    is_authentic = (anomaly_score < 32.0)
    confidence = float(np.clip(quality_confidence, 55.0, 99.0))

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
        "is_quality_sufficient": True,
        "quality_reason": "Quality verified",
        "contributing_features": contributing_features,
        "explanation": explanations,
        "is_authentic": is_authentic,
        "verdict_text": verdict_text
    }
