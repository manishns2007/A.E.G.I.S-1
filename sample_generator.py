"""
Sample Asset Generator for Project A.E.G.I.S.
Generates authentic vs synthetic test videos and images with mathematically exact physics.
- ENF Video: Real 50 Hz AC grid luminance modulation vs Synthetic AI video without 50Hz physics.
- Corneal Image: Physically consistent specular highlights vs Asymmetric AI diffusion glints.
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
    Synthetic video has no 50 Hz signal (flat/random noise).
    """
    ensure_sample_dir()
    width, height = 480, 360
    total_frames = int(duration_sec * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    base_background = np.full((height, width, 3), 120, dtype=np.uint8)
    cv2.rectangle(base_background, (50, 200), (430, 340), (80, 60, 50), -1) # bed
    cv2.circle(base_background, (240, 60), 30, (40, 40, 40), -1) # ceiling fan
    cv2.rectangle(base_background, (380, 100), (410, 140), (160, 160, 160), -1) # socket
    
    for i in range(total_frames):
        t = i / fps
        frame = base_background.copy()
        
        if is_authentic:
            flicker = 8.0 * np.sin(2 * np.pi * 50.0 * t) + 3.0 * np.sin(2 * np.pi * 100.0 * t)
        else:
            flicker = np.random.normal(0, 1.5)
            
        frame_float = frame.astype(np.float32) + flicker
        frame_clipped = np.clip(frame_float, 0, 255).astype(np.uint8)
        out.write(frame_clipped)
        
    out.release()
    return output_path

def generate_corneal_image(is_authentic: bool, output_path: str):
    """
    Generates a high-resolution face portrait image with eyes.
    Authentic: Specular light reflections (glints) in left and right corneal regions match geometry.
    Synthetic: Mismatched shape, angle, and position of light reflections (AI diffusion artifact).
    """
    ensure_sample_dir()
    img = np.full((600, 600, 3), (200, 210, 220), dtype=np.uint8)
    
    # Background
    cv2.rectangle(img, (0, 0), (600, 600), (180, 190, 200), -1)
    for y in range(0, 600, 40):
        cv2.line(img, (0, y), (600, y), (170, 180, 190), 1)
        
    # Face shape
    cv2.ellipse(img, (300, 300), (160, 210), 0, 0, 360, (140, 170, 210), -1)
    
    left_eye_center = (210, 270)
    right_eye_center = (390, 270)
    
    # Sclera
    cv2.ellipse(img, left_eye_center, (45, 25), 0, 0, 360, (245, 245, 245), -1)
    cv2.ellipse(img, right_eye_center, (45, 25), 0, 0, 360, (245, 245, 245), -1)
    cv2.ellipse(img, left_eye_center, (45, 25), 0, 0, 360, (50, 50, 50), 2)
    cv2.ellipse(img, right_eye_center, (45, 25), 0, 0, 360, (50, 50, 50), 2)
    
    # Iris
    cv2.circle(img, left_eye_center, 18, (120, 60, 30), -1)
    cv2.circle(img, right_eye_center, 18, (120, 60, 30), -1)
    
    # Pupil
    cv2.circle(img, left_eye_center, 8, (10, 10, 10), -1)
    cv2.circle(img, right_eye_center, 8, (10, 10, 10), -1)
    
    # Specular Glints
    if is_authentic:
        # Authentic: Symmetric circular top-left glints in both eyes
        cv2.circle(img, (left_eye_center[0] - 5, left_eye_center[1] - 5), 5, (255, 255, 255), -1)
        cv2.circle(img, (right_eye_center[0] - 5, right_eye_center[1] - 5), 5, (255, 255, 255), -1)
    else:
        # Synthetic AI Diffusion Artifact:
        # Left eye: Single small circle glint top-left
        cv2.circle(img, (left_eye_center[0] - 5, left_eye_center[1] - 5), 4, (255, 255, 255), -1)
        # Right eye: Multi-glint artifact with large elongated diagonal ellipse bottom-right + phantom glint
        cv2.ellipse(img, (right_eye_center[0] + 6, right_eye_center[1] + 6), (12, 4), 45, 0, 360, (255, 255, 255), -1)
        cv2.circle(img, (right_eye_center[0] - 8, right_eye_center[1] + 4), 5, (255, 255, 255), -1)

    # Nose & Mouth
    cv2.line(img, (300, 270), (295, 330), (100, 130, 170), 2)
    cv2.ellipse(img, (300, 370), (40, 10), 0, 0, 180, (80, 80, 160), 2)

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
