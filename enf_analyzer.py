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
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_lum = float(np.mean(gray))
        luminance_signal.append(mean_lum)
        frame_count += 1
        
    cap.release()
    
    N = len(luminance_signal)
    if N < 15:
        return {"error": "Video duration too short for ENF FFT analysis"}
        
    time_stamps = [i / fps for i in range(N)]
    
    signal_detrended = signal.detrend(luminance_signal)
    window = np.hanning(N)
    windowed_signal = signal_detrended * window
    
    fft_vals = fftpack.fft(windowed_signal)
    fft_freqs = fftpack.fftfreq(N, d=1.0/fps)
    
    pos_mask = fft_freqs >= 0
    freqs = fft_freqs[pos_mask]
    spectrum = np.abs(fft_vals[pos_mask])
    
    nyquist = fps / 2.0
    
    effective_target = target_freq
    if target_freq >= nyquist:
        effective_target = np.abs(target_freq - round(target_freq / fps) * fps)
        if effective_target == 0:
            effective_target = np.abs(100.0 - round(100.0 / fps) * fps)
            
    band_mask = (freqs >= max(0.5, effective_target - tolerance_hz)) & (freqs <= min(nyquist, effective_target + tolerance_hz))
    noise_mask = (freqs >= 1.0) & (freqs <= nyquist) & (~band_mask)
    
    if np.any(band_mask) and np.any(noise_mask):
        peak_50hz_power = float(np.max(spectrum[band_mask]))
        background_power = float(np.mean(spectrum[noise_mask])) + 1e-6
        enf_ratio = peak_50hz_power / background_power
    else:
        peak_50hz_power = 0.0
        background_power = 1.0
        enf_ratio = 1.0
        
    nperseg = min(N // 2, 32) if N >= 32 else N
    stft_freqs, stft_times, Sxx = signal.spectrogram(np.array(signal_detrended), fs=fps, nperseg=nperseg)
    
    # Authentic 50Hz grid physics criteria: Peak ratio >= 5.0 AND absolute peak power >= 0.5
    is_authentic = (enf_ratio >= 5.0) and (peak_50hz_power >= 0.5)
    confidence = min(99.4, max(45.0, (enf_ratio / 10.0) * 100.0)) if is_authentic else min(98.8, max(60.0, (1.0 - enf_ratio / 5.0) * 100.0))
    
    verdict_text = "AUTHENTIC REAL-WORLD CAPTURE (50 Hz Grid Hum Verified)" if is_authentic else "SYNTHETIC AI FABRICATION (50 Hz Grid Signal Missing)"
    
    return {
        "fps": fps,
        "total_frames": N,
        "duration_sec": N / fps,
        "time_stamps": time_stamps,
        "luminance_signal": luminance_signal,
        "detrended_signal": [float(x) for x in signal_detrended],
        "freqs": [float(x) for x in freqs],
        "spectrum": [float(x) for x in spectrum],
        "stft_freqs": [float(x) for x in stft_freqs],
        "stft_times": [float(x) for x in stft_times],
        "stft_matrix": Sxx.tolist(),
        "target_freq": target_freq,
        "effective_target_freq": float(effective_target),
        "tolerance_hz": float(tolerance_hz),
        "peak_50hz_power": peak_50hz_power,
        "background_power": background_power,
        "enf_ratio": float(enf_ratio),
        "is_authentic": is_authentic,
        "confidence": float(confidence),
        "verdict_text": verdict_text
    }
