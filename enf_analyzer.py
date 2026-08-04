"""
Electrical Network Frequency (ENF) Physics Analyzer for Project A.E.G.I.S.
Extracts pixel luminance frame-by-frame from uploaded videos and applies Fast Fourier Transform (FFT),
Power Spectral Density (PSD), and Short-Time Fourier Transform (STFT) Spectrograms using SciPy 
to isolate the 50 Hz Indian Power Grid Frequency hum.

Physics Principle:
Real camera recordings under AC electrical grid lighting capture invisible 50 Hz / 100 Hz 
luminance oscillations. AI diffusion models (Sora, Runway, Pika, Flux) render frames independently 
without modeling grid electro-physics, leaving no 50 Hz power spectrum peak.
"""

import cv2
import numpy as np
from scipy import fftpack, signal

def analyze_video_enf(video_path: str, target_freq: float = 50.0, tolerance_hz: float = 2.5, max_frames: int = 300):
    """
    Performs FFT & STFT Spectrogram analysis on video luminance time-series.
    Returns 'ENF unavailable' if video is too short, low FPS, unreadable, or flat.
    """
    default_unavailable = {
        "is_enf_available": False,
        "is_authentic": False,
        "verdict_text": "ENF unavailable",
        "reason": "Video too short, low FPS (< 12), or unreadable stream.",
        "fps": 0.0, "total_frames": 0, "duration_sec": 0.0,
        "time_stamps": [], "luminance_signal": [], "detrended_signal": [],
        "freqs": [], "spectrum": [], "stft_freqs": [], "stft_times": [], "stft_matrix": [],
        "target_freq": target_freq, "effective_target_freq": target_freq, "tolerance_hz": tolerance_hz,
        "peak_50hz_power": 0.0, "background_power": 1.0, "enf_ratio": 1.0, "confidence": 0.0
    }

    if not video_path or not isinstance(video_path, str):
        return default_unavailable

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        default_unavailable["reason"] = "Could not open video stream or path."
        return default_unavailable
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0 or np.isnan(fps):
        fps = 30.0

    # 1. Low FPS Quality Filter Rejection
    if fps < 12.0:
        cap.release()
        default_unavailable["fps"] = float(fps)
        default_unavailable["reason"] = f"Low FPS rate ({fps:.1f} FPS < 12.0 FPS threshold). Temporal sampling rate insufficient for ENF grid estimation."
        return default_unavailable
        
    luminance_signal = []
    frame_count = 0
    
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_lum = float(np.mean(gray))
        luminance_signal.append(mean_lum)
        frame_count += 1
        
    cap.release()
    
    N = len(luminance_signal)

    # 2. Short Video Duration Quality Filter Rejection (N < 45 frames ~ 1.5 seconds)
    if N < 45:
        default_unavailable["fps"] = float(fps)
        default_unavailable["total_frames"] = N
        default_unavailable["duration_sec"] = N / float(fps + 1e-5)
        default_unavailable["reason"] = f"Short video length ({N} frames < 45 frame minimum). Video duration insufficient for reliable SciPy FFT spectrum estimation."
        return default_unavailable

    # 3. Flat Luminance / Heavy Compression Rejection (Signal Variance < 1e-4)
    lum_var = float(np.var(luminance_signal))
    if lum_var < 1e-4:
        default_unavailable["fps"] = float(fps)
        default_unavailable["total_frames"] = N
        default_unavailable["reason"] = f"Zero spatial luminance variation across frames (Variance {lum_var:.6f} < 0.0001). Video appears static or flat-shaded."
        return default_unavailable
        
    time_stamps = [i / float(fps) for i in range(N)]
    
    # Detrending (Removes baseline illumination drift / motion trend)
    signal_detrended = signal.detrend(luminance_signal)
    
    # Windowing (Hanning Window to suppress spectral leakage)
    window = np.hanning(N)
    windowed_signal = signal_detrended * window
    
    # Fast Fourier Transform (FFT)
    fft_vals = fftpack.fft(windowed_signal)
    fft_freqs = fftpack.fftfreq(N, d=1.0/fps)
    
    pos_mask = fft_freqs >= 0
    freqs = fft_freqs[pos_mask]
    spectrum = np.abs(fft_vals[pos_mask])
    
    nyquist = fps / 2.0
    
    # Nyquist Aliasing Calculation for target grid frequency
    effective_target = target_freq
    if target_freq >= nyquist:
        effective_target = np.abs(target_freq - round(target_freq / fps) * fps)
        if effective_target == 0:
            effective_target = np.abs(100.0 - round(100.0 / fps) * fps)
            
    band_mask = (freqs >= max(0.5, effective_target - tolerance_hz)) & (freqs <= min(nyquist, effective_target + tolerance_hz))
    noise_mask = (freqs >= 1.0) & (freqs <= nyquist) & (~band_mask)
    
    # Peak Search & Noise Floor Ratio Computation
    if np.any(band_mask) and np.any(noise_mask):
        peak_50hz_power = float(np.max(spectrum[band_mask]))
        background_power = float(np.mean(spectrum[noise_mask])) + 1e-6
        enf_ratio = peak_50hz_power / background_power
    else:
        peak_50hz_power = 0.0
        background_power = 1.0
        enf_ratio = 1.0
        
    # Short-Time Fourier Transform (STFT 2D Spectrogram)
    nperseg = min(N // 2, 32) if N >= 32 else N
    stft_freqs, stft_times, Sxx = signal.spectrogram(np.array(signal_detrended), fs=fps, nperseg=nperseg)
    
    # Authentic 50Hz grid physics criteria: Peak ratio >= 5.0 AND absolute peak power >= 0.5
    is_authentic = (enf_ratio >= 5.0) and (peak_50hz_power >= 0.5)
    confidence = min(99.4, max(45.0, (enf_ratio / 10.0) * 100.0)) if is_authentic else min(98.8, max(60.0, (1.0 - enf_ratio / 5.0) * 100.0))
    
    verdict_text = "AUTHENTIC REAL-WORLD CAPTURE (50 Hz Grid Hum Verified)" if is_authentic else "SYNTHETIC AI FABRICATION (50 Hz Grid Signal Missing)"
    
    return {
        "is_enf_available": True,
        "fps": float(fps),
        "total_frames": N,
        "duration_sec": float(N / fps),
        "time_stamps": time_stamps,
        "luminance_signal": luminance_signal,
        "detrended_signal": [float(x) for x in signal_detrended],
        "freqs": [float(x) for x in freqs],
        "spectrum": [float(x) for x in spectrum],
        "stft_freqs": [float(x) for x in stft_freqs],
        "stft_times": [float(x) for x in stft_times],
        "stft_matrix": Sxx.tolist(),
        "target_freq": float(target_freq),
        "effective_target_freq": float(effective_target),
        "tolerance_hz": float(tolerance_hz),
        "peak_50hz_power": peak_50hz_power,
        "background_power": background_power,
        "enf_ratio": float(enf_ratio),
        "is_authentic": is_authentic,
        "confidence": float(confidence),
        "verdict_text": verdict_text,
        "reason": "ENF analysis completed successfully"
    }
