"""
Sample Asset Generator for Project A.E.G.I.S.
Generates authentic vs synthetic test videos and images with mathematically exact multi-signal physics.
- ENF Video: Real 50 Hz AC grid luminance modulation vs Synthetic AI video without 50Hz physics.
- Corneal Image: Physically consistent camera photo vs Asymmetric AI diffusion portrait (1024x1024, clean noise, over-saturated HSV).
"""

import os
import cv2
import numpy as np

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "samples")

def ensure_sample_dir():
    os.makedirs(SAMPLE_DIR, exist_ok=True)

def generate_enf_video(is_authentic: bool, output_path: str, duration_sec: float = 3.0, fps: float = 30.0):
    """
    Generates a sample video for ENF testing.
    Authentic video has a 50 Hz luminance signal embedded in the frame sequence.
    Synthetic video has no 50 Hz grid signal (flat/constant lighting).
    """
    ensure_sample_dir()
    width, height = 480, 360
    total_frames = int(duration_sec * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    base_background = np.full((height, width, 3), 120, dtype=np.uint8)
    cv2.rectangle(base_background, (50, 200), (430, 340), (80, 60, 50), -1)
    cv2.circle(base_background, (240, 60), 30, (40, 40, 40), -1)
    cv2.rectangle(base_background, (380, 100), (410, 140), (160, 160, 160), -1)
    
    for i in range(total_frames):
        t = i / fps
        frame = base_background.copy()
        
        if is_authentic:
            # 50 Hz AC power grid flicker modulation
            flicker = 8.0 * np.sin(2 * np.pi * 50.0 * t) + 3.0 * np.sin(2 * np.pi * 100.0 * t)
        else:
            # AI Generated video: Constant lighting without 50Hz grid physics
            flicker = 0.0
            
        frame_float = frame.astype(np.float32) + flicker
        frame_clipped = np.clip(frame_float, 0, 255).astype(np.uint8)
        out.write(frame_clipped)
        
    out.release()
    return output_path

def generate_corneal_image(is_authentic: bool, output_path: str):
    """
    Generates high-resolution portrait images.
    Authentic: Standard 800x600 camera photo, natural ISO sensor noise, symmetric eye glints.
    Synthetic: 1024x1024 AI canvas, zero-noise hyper-clean surface, over-saturated HSV colors, asymmetric glints.
    """
    ensure_sample_dir()
    
    if is_authentic:
        w_img, h_img = 800, 600
        img = np.full((h_img, w_img, 3), (200, 210, 220), dtype=np.uint8)
        cv2.rectangle(img, (0, 0), (w_img, h_img), (180, 190, 200), -1)
        for y in range(0, h_img, 40):
            cv2.line(img, (0, y), (w_img, y), (170, 180, 190), 1)
            
        cv2.ellipse(img, (400, 300), (180, 220), 0, 0, 360, (140, 170, 210), -1)
        left_eye_center = (290, 270)
        right_eye_center = (510, 270)
        
        cv2.ellipse(img, left_eye_center, (50, 26), 0, 0, 360, (245, 245, 245), -1)
        cv2.ellipse(img, right_eye_center, (50, 26), 0, 0, 360, (245, 245, 245), -1)
        
        cv2.circle(img, left_eye_center, 20, (120, 60, 30), -1)
        cv2.circle(img, right_eye_center, 20, (120, 60, 30), -1)
        cv2.circle(img, left_eye_center, 9, (10, 10, 10), -1)
        cv2.circle(img, right_eye_center, 9, (10, 10, 10), -1)
        
        cv2.circle(img, (left_eye_center[0] - 6, left_eye_center[1] - 6), 5, (255, 255, 255), -1)
        cv2.circle(img, (right_eye_center[0] - 6, right_eye_center[1] - 6), 5, (255, 255, 255), -1)
        
        cv2.line(img, (400, 270), (395, 340), (100, 130, 170), 2)
        cv2.ellipse(img, (400, 380), (45, 12), 0, 0, 180, (80, 80, 160), 2)
        
        noise = np.random.normal(0, 4.0, img.shape).astype(np.float32)
        img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        
    else:
        # Synthetic AI Canvas (1024x1024, hyper-smooth, over-saturated)
        w_img, h_img = 1024, 1024
        
        hsv_bg = np.full((h_img, w_img, 3), (110, 220, 210), dtype=np.uint8)
        img = cv2.cvtColor(hsv_bg, cv2.COLOR_HSV2BGR)
        
        cv2.ellipse(img, (512, 512), (280, 340), 0, 0, 360, (140, 170, 235), -1)
        left_eye_center = (350, 460)
        right_eye_center = (670, 460)
        
        cv2.ellipse(img, left_eye_center, (75, 38), 0, 0, 360, (245, 245, 245), -1)
        cv2.ellipse(img, right_eye_center, (75, 38), 0, 0, 360, (245, 245, 245), -1)
        
        cv2.circle(img, left_eye_center, 30, (140, 60, 30), -1)
        cv2.circle(img, right_eye_center, 30, (140, 60, 30), -1)
        cv2.circle(img, left_eye_center, 14, (10, 10, 10), -1)
        cv2.circle(img, right_eye_center, 14, (10, 10, 10), -1)
        
        cv2.circle(img, (left_eye_center[0] - 8, left_eye_center[1] - 8), 6, (255, 255, 255), -1)
        cv2.ellipse(img, (right_eye_center[0] + 10, right_eye_center[1] + 10), (18, 5), 45, 0, 360, (255, 255, 255), -1)
        cv2.circle(img, (right_eye_center[0] - 12, right_eye_center[1] + 6), 7, (255, 255, 255), -1)
        
        cv2.line(img, (512, 460), (505, 570), (100, 130, 170), 3)
        cv2.ellipse(img, (512, 640), (70, 18), 0, 0, 180, (80, 80, 160), 3)

    cv2.imwrite(output_path, img)
    return output_path

def generate_all_samples(overwrite: bool = True):
    """Generates all standard sample assets for live judging."""
    ensure_sample_dir()
    auth_video = os.path.join(SAMPLE_DIR, "authentic_video_50hz.mp4")
    synth_video = os.path.join(SAMPLE_DIR, "synthetic_ai_video.mp4")
    auth_image = os.path.join(SAMPLE_DIR, "authentic_portrait.jpg")
    synth_image = os.path.join(SAMPLE_DIR, "synthetic_ai_portrait.jpg")
    
    if overwrite or not os.path.exists(auth_video):
        generate_enf_video(True, auth_video)
    if overwrite or not os.path.exists(synth_video):
        generate_enf_video(False, synth_video)
    if overwrite or not os.path.exists(auth_image):
        generate_corneal_image(True, auth_image)
    if overwrite or not os.path.exists(synth_image):
        generate_corneal_image(False, synth_image)
        
    return {
        "auth_video": auth_video,
        "synth_video": synth_video,
        "auth_image": auth_image,
        "synth_image": synth_image
    }

if __name__ == "__main__":
    paths = generate_all_samples(overwrite=True)
    print("Generated test sample assets successfully:")
    for k, v in paths.items():
        print(f"  - {k}: {v}")
