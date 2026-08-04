"""
Electrical Network Frequency (ENF) Physics Analyzer for Project A.E.G.I.S.
Extracts pixel luminance frame-by-frame from uploaded videos and applies Fast Fourier Transform (FFT)
& Power Spectral Density (PSD) using SciPy to isolate the 50 Hz Indian Power Grid Frequency hum.

Physics Principle:
Real camera recordings under AC electrical grid lighting capture invisible 50 Hz / 100 Hz 
luminance oscillations. AI diffusion models (Sora, Runway, Pika, Flux) render frames independently 
without modeling grid electro-physics, leaving no 50 Hz power spectrum peak.
"""

import cv2
import numpy as np
from scipy import fftpack, signal

def analyze_video_enf(video_path: str, target_freq: float = 50.0, max_frames: int = 300):
    """
    Performs FFT analysis on video luminance time-series.
    
    Returns a dict with:
      - fps: sampling frequency (frames per sec)
      - time_series: list of frame mean luminance values
      - freqs: frequency axis (Hz)
      - spectrum: FFT magnitude spectrum
      - peak_50hz_power: power at target 50 Hz frequency
      - background_power: mean power in neighboring frequency band
      - enf_ratio: ratio of 50 Hz peak power to noise floor
      - is_authentic: bool verdict
      - confidence: float score (0-100%)
      - verdict_text: str
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Could not open video file"}
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0
        
    luminance_signal = []
    frame_count = 0
    
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert BGR to Grayscale for mean spatial luminance extraction
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_lum = np.mean(gray)
        luminance_signal.append(mean_lum)
        frame_count += 1
        
    cap.release()
    
    N = len(luminance_signal)
    if N < 15:
        return {"error": "Video duration too short for ENF FFT analysis"}
        
    # Detrend luminance signal to remove slow illumination shifts / camera movement
    signal_detrended = signal.detrend(luminance_signal)
    
    # Apply Hanning window to reduce spectral leakage
    window = np.hanning(N)
    windowed_signal = signal_detrended * window
    
    # Perform Fast Fourier Transform (FFT) via SciPy
    fft_vals = fftpack.fft(windowed_signal)
    fft_freqs = fftpack.fftfreq(N, d=1.0/fps)
    
    # Take positive frequencies only
    pos_mask = fft_freqs >= 0
    freqs = fft_freqs[pos_mask]
    spectrum = np.abs(fft_vals[pos_mask])
    
    # Nyquist limit check
    nyquist = fps / 2.0
    
    # Find peak near 50 Hz (or 50 Hz aliased harmonic depending on camera frame rate)
    # Note: If fps <= 50, 50 Hz aliases to |50 - fps| or harmonic |100 - fps|
    effective_target = target_freq
    if target_freq >= nyquist:
        # Calculate aliased grid frequency under Nyquist rate
        effective_target = np.abs(target_freq - round(target_freq / fps) * fps)
        if effective_target == 0:
            effective_target = np.abs(100.0 - round(100.0 / fps) * fps)
            
    # Search band +/- 2.5 Hz around target frequency
    band_mask = (freqs >= max(0.5, effective_target - 2.5)) & (freqs <= min(nyquist, effective_target + 2.5))
    noise_mask = (freqs >= 1.0) & (freqs <= nyquist) & (~band_mask)
    
    if np.any(band_mask) and np.any(noise_mask):
        peak_50hz_power = float(np.max(spectrum[band_mask]))
        background_power = float(np.mean(spectrum[noise_mask])) + 1e-6
        enf_ratio = peak_50hz_power / background_power
    else:
        peak_50hz_power = 0.0
        background_power = 1.0
        enf_ratio = 1.0
        
    # Verdict threshold: ENF peak ratio > 2.2 indicates authentic power grid modulation
    is_authentic = (enf_ratio >= 2.2)
    confidence = min(99.4, max(45.0, (enf_ratio / 3.5) * 100.0)) if is_authentic else min(98.8, max(60.0, (1.0 - enf_ratio / 2.2) * 100.0))
    
    verdict_text = "AUTHENTIC REAL-WORLD CAPTURE (50 Hz Grid Hum Verified)" if is_authentic else "SYNTHETIC AI FABRICATION (50 Hz Grid Signal Missing)"
    
    return {
        "fps": fps,
        "total_frames": N,
        "luminance_signal": [float(x) for x in luminance_signal[:100]],
        "freqs": [float(x) for x in freqs],
        "spectrum": [float(x) for x in spectrum],
        "target_freq": target_freq,
        "effective_target_freq": float(effective_target),
        "peak_50hz_power": peak_50hz_power,
        "background_power": background_power,
        "enf_ratio": float(enf_ratio),
        "is_authentic": is_authentic,
        "confidence": float(confidence),
        "verdict_text": verdict_text
    }
