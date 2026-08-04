"""
Corneal Specular Topology Analyzer for Project A.E.G.I.S.
Zooms into human eyes in static images/portraits to map and compare corneal light reflection (glint)
geometries between the left and right eyes, flagging asymmetric/contradictory reflections as AI fabrications.
"""

import os
import cv2
import numpy as np

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
    
    # Try OpenCV Eye Cascade safely
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
        
    # Geometric crop fallback: divide upper middle region into left and right eye areas
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
    
    # 1. Isolate the central Iris/Pupil zone (middle 60% of crop) to exclude sclera edges
    margin_x = int(w_c * 0.20)
    margin_y = int(h_c * 0.20)
    iris_roi = gray[margin_y:h_c-margin_y, margin_x:w_c-margin_x]
    
    if iris_roi.size == 0:
        iris_roi = gray
        margin_x, margin_y = 0, 0
        
    # 2. Specular glints are white pixels (RGB > 240) surrounded by dark pupil/iris
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

def analyze_corneal_specular_topology(img_bgr):
    """
    Main function for Corneal Specular Topology analysis on an image.
    Calculates reflection symmetry between left and right eyes.
    """
    l_crop, r_crop, l_box, r_box = extract_eye_rois(img_bgr)
    
    l_mask, l_count, l_feat = analyze_corneal_glints(l_crop)
    r_mask, r_count, r_feat = analyze_corneal_glints(r_crop)
    
    # 1. Count dissimilarity (Mismatched glint counts = strong AI signature)
    count_diff = abs(l_count - r_count)
    count_penalty = 0.45 if count_diff > 0 else 0.0
    
    # 2. Area dissimilarity
    max_area = max(l_feat["area"], r_feat["area"]) + 1e-5
    area_diff = abs(l_feat["area"] - r_feat["area"]) / max_area
    
    # 3. Shape & aspect ratio dissimilarity
    aspect_diff = abs(l_feat["aspect"] - r_feat["aspect"]) / (max(l_feat["aspect"], r_feat["aspect"]) + 1e-5)
    circ_diff = abs(l_feat["circularity"] - r_feat["circularity"])
    
    # Combined dissimilarity index
    dissimilarity = count_penalty + (0.30 * area_diff) + (0.25 * aspect_diff) + (0.15 * circ_diff)
    
    symmetry_score = float(np.clip((1.0 - dissimilarity) * 100.0, 10.0, 98.5))
    
    # Authenticity threshold: Symmetry score >= 75.0%
    is_authentic = (symmetry_score >= 75.0)
    
    verdict_text = "AUTHENTIC LIGHT REFLECTION (Corneal Specular Symmetry Verified)" if is_authentic else "SYNTHETIC DIFFUSION FABRICATION (Asymmetric Corneal Reflections Detected)"
    
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
        "dissimilarity": float(dissimilarity),
        "is_authentic": is_authentic,
        "verdict_text": verdict_text
    }
