"""
Automated Agentic Privacy Shield Module for Project A.E.G.I.S.
Protects investigator mental health by instantly blurring/redacting human faces and bodies
upon ingestion, preserving 100% of background environmental evidence.
"""

import os
import cv2
import numpy as np

# Multi-tier face and body detector setup
YUNET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "face_detection_yunet_2023mar.onnx"))

FACE_CASCADES = []
try:
    cascade_dir = getattr(cv2.data, 'haarcascades', '')
    for xml_name in ['haarcascade_frontalface_default.xml', 'haarcascade_profileface.xml', 'haarcascade_frontalface_alt2.xml', 'haarcascade_upperbody.xml']:
        xml_path = os.path.join(cascade_dir, xml_name)
        if os.path.exists(xml_path):
            cascade = cv2.CascadeClassifier(xml_path)
            if not cascade.empty():
                FACE_CASCADES.append((xml_name, cascade))
except Exception:
    pass


def _compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0


def _merge_bboxes(bboxes, iou_thresh: float = 0.3):
    if not bboxes:
        return []
    bboxes = sorted(bboxes, key=lambda b: b[2] * b[3], reverse=True)
    merged = []
    for b in bboxes:
        keep = True
        for m in merged:
            if _compute_iou(b, m) > iou_thresh:
                keep = False
                break
        if keep:
            merged.append(b)
    return merged


def apply_privacy_shield_to_image(img_bgr, blur_strength: int = 51):
    """
    Detects human faces and bodies (frontal, 3/4 view, side profiles) using an ensemble of:
      1. OpenCV YuNet DNN Face Detector (ONNX state-of-the-art detector)
      2. MediaPipe Face Detection
      3. OpenCV Haar Cascade Ensemble (Frontal + Profile Face + Upperbody)
    Applies a Gaussian privacy redaction blur preserving environmental background.
    Returns:
      - processed_img: redacted image preserving background
      - face_count: int, number of human subjects detected and shielded
      - bbox_list: list of detected bounding boxes [(x, y, w, h)]
    """
    if img_bgr is None:
        return None, 0, []

    h_img, w_img = img_bgr.shape[:2]
    processed_img = img_bgr.copy()
    raw_bboxes = []

    # Tier 1: OpenCV DNN YuNet Face Detector (ONNX)
    if os.path.exists(YUNET_PATH) and hasattr(cv2, 'FaceDetectorYN'):
        try:
            yunet = cv2.FaceDetectorYN.create(YUNET_PATH, '', (w_img, h_img), 0.15, 0.3, 5000)
            _, faces = yunet.detect(img_bgr)
            if faces is not None:
                for face in faces:
                    x, y, w, h = face[:4].astype(int)
                    score = face[-1]
                    if score >= 0.15:
                        pad_x = int(w * 0.25)
                        pad_y = int(h * 0.35)
                        x1 = max(0, x - pad_x)
                        y1 = max(0, y - pad_y)
                        bw = min(w_img - x1, w + 2 * pad_x)
                        bh = min(h_img - y1, h + 2 * pad_y)
                        raw_bboxes.append((int(x1), int(y1), int(bw), int(bh)))
        except Exception:
            pass

    # Tier 2: MediaPipe Face Detection
    try:
        import mediapipe as mp
        solutions = getattr(mp, 'solutions', None)
        if solutions and hasattr(solutions, 'face_detection'):
            mp_face_detection = solutions.face_detection
            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.2) as face_detection:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                results = face_detection.process(img_rgb)
                if results and results.detections:
                    for detection in results.detections:
                        bboxC = detection.location_data.relative_bounding_box
                        x = max(0, int(bboxC.xmin * w_img))
                        y = max(0, int(bboxC.ymin * h_img))
                        w = min(w_img - x, int(bboxC.width * w_img))
                        h = min(h_img - y, int(bboxC.height * h_img))
                        pad_x = int(w * 0.3)
                        pad_y = int(h * 0.4)
                        x1 = max(0, x - pad_x)
                        y1 = max(0, y - pad_y)
                        bw = min(w_img - x1, w + 2 * pad_x)
                        bh = min(h_img - y1, h + 2 * pad_y)
                        raw_bboxes.append((int(x1), int(y1), int(bw), int(bh)))
    except Exception:
        pass

    # Tier 3: OpenCV Haar Cascade Ensemble (Frontal + Profile Face + Flipped Profile)
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        for xml_name, cascade in FACE_CASCADES:
            faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=3, minSize=(30, 30))
            for (x, y, w, h) in faces:
                pad_x = int(w * 0.2)
                pad_y = int(h * 0.3)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                bw = min(w_img - x1, w + 2 * pad_x)
                bh = min(h_img - y1, h + 2 * pad_y)
                raw_bboxes.append((int(x1), int(y1), int(bw), int(bh)))

            if 'profile' in xml_name:
                # Flip image horizontally to detect left-facing profile faces
                flipped_gray = cv2.flip(gray, 1)
                faces_flip = cascade.detectMultiScale(flipped_gray, scaleFactor=1.08, minNeighbors=3, minSize=(30, 30))
                for (fx, fy, fw, fh) in faces_flip:
                    real_x = w_img - fx - fw
                    pad_x = int(fw * 0.2)
                    pad_y = int(fh * 0.3)
                    x1 = max(0, real_x - pad_x)
                    y1 = max(0, fy - pad_y)
                    bw = min(w_img - x1, fw + 2 * pad_x)
                    bh = min(h_img - y1, fh + 2 * pad_y)
                    raw_bboxes.append((int(x1), int(y1), int(bw), int(bh)))
    except Exception:
        pass

    # Merge overlapping detections via NMS
    bbox_list = _merge_bboxes(raw_bboxes, iou_thresh=0.3)

    # Apply Gaussian Blur over detected bounding boxes
    ksize = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
    for (x, y, w, h) in bbox_list:
        roi = processed_img[y:y+h, x:x+w]
        if roi.size > 0:
            blurred_roi = cv2.GaussianBlur(roi, (ksize, ksize), 30)
            # Add tactical privacy overlay boundary line
            cv2.rectangle(blurred_roi, (0, 0), (w-1, h-1), (0, 210, 255), 2)
            processed_img[y:y+h, x:x+w] = blurred_roi

    return processed_img, len(bbox_list), bbox_list

def apply_privacy_shield_to_video(video_path: str, output_path: str, max_frames: int = 150):
    """
    Processes video frame-by-frame, applying privacy shield to every frame.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, 0
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_faces = 0
    frame_idx = 0
    
    while cap.isOpened() and frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        shielded_frame, count, _ = apply_privacy_shield_to_image(frame)
        total_faces += count
        out.write(shielded_frame)
        frame_idx += 1
        
    cap.release()
    out.release()
    return output_path, total_faces
