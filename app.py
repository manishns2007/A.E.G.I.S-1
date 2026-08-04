"""
Project A.E.G.I.S. (Agentic Environmental Graphing & Intelligence System)
Kerala Police Cyberdome Hackathon Hac'KP 2026 - ACPIA Track
Main Interactive Streamlit Dashboard Application
"""

import os
import cv2
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# Import Core System Modules
import sample_generator
import privacy_shield
import enf_analyzer
import corneal_analyzer
import vlm_extractor
import knowledge_graph
import legal_docket

# Page Configuration
st.set_page_config(
    page_title="Project A.E.G.I.S. | Cyberdome ACPIA 2026",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom Tactical CSS
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Generate Sample Test Assets on First Run
sample_paths = sample_generator.generate_all_samples()

# Tactical Header Banner
st.markdown("""
<div class="tactical-header">
    <div class="tactical-title">
        <span>🛡️ PROJECT A.E.G.I.S.</span>
    </div>
    <div class="tactical-subtitle">
        Agentic Environmental Graphing & Intelligence System | Kerala Police Cyberdome ACPIA 2026
    </div>
    <p style="color: #cbd5e1; font-size: 0.95rem; margin-top: 10px; margin-bottom: 0;">
        Shifting digital forensics away from traumatizing victim pixel-matching toward analyzing invisible environmental physics, 
        multi-signal image forensic scoring, and spatial knowledge graphs — Fully compliant with Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### 🔒 CYBERDOME COMMAND SIDEBAR")
st.sidebar.markdown("---")

input_mode = st.sidebar.radio(
    "Select Evidence Source:",
    [
        "📁 Upload Custom Evidence File (Your Video / Image)",
        "🎬 Sample Authentic Video (50 Hz Grid Hum)",
        "🤖 Sample Synthetic AI Video (No Grid Hum)",
        "📷 Sample Authentic Portrait (Symmetric Corneal Glints)",
        "🎨 Sample AI Diffusion Portrait (Asymmetric Corneal Glints)"
    ],
    index=0
)

# Handle Custom Upload in Sidebar
sidebar_uploaded_file = None
if "Upload Custom Evidence File" in input_mode:
    sidebar_uploaded_file = st.sidebar.file_uploader(
        "📥 Drag & Drop Evidence File (MP4, AVI, JPG, PNG)",
        type=["mp4", "avi", "mov", "jpg", "png", "jpeg"],
        key="sidebar_uploader"
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ CASE METADATA (BSA 2023)")
case_id = st.sidebar.text_input("Case Reference ID", "KP-2026-ACPIA-0914")
officer_id = st.sidebar.text_input("Investigating Officer ID", "INSP-CYBER-884")
district = st.sidebar.selectbox("Jurisdiction District", ["Kochi Cyber Cell", "Trivandrum Headquarters", "Kozhikode North", "Thrissur Range"])

st.sidebar.markdown("---")
gemini_key = st.sidebar.text_input("Google Gemini API Key (Optional)", type="password", help="Optional API key for Gemini Vision VLM background parsing. Local fallback engine active if blank.")

# UNIFIED EVIDENCE RESOLUTION ENGINE
uploaded_file = None
if "Upload Custom Evidence File" in input_mode:
    uploaded_file = sidebar_uploaded_file

if uploaded_file is None and "main_uploaded_file" in st.session_state and st.session_state["main_uploaded_file"] is not None:
    uploaded_file = st.session_state["main_uploaded_file"]

active_path = None
is_video = True

if uploaded_file is not None:
    save_path = os.path.join(sample_generator.SAMPLE_DIR, f"custom_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    active_path = save_path
    is_video = uploaded_file.name.lower().endswith((".mp4", ".avi", ".mov"))
elif "Authentic Video" in input_mode:
    active_path = sample_paths["auth_video"]
    is_video = True
elif "Synthetic AI Video" in input_mode:
    active_path = sample_paths["synth_video"]
    is_video = True
elif "Authentic Portrait" in input_mode:
    active_path = sample_paths["auth_image"]
    is_video = False
elif "AI Diffusion Portrait" in input_mode:
    active_path = sample_paths["synth_image"]
    is_video = False
else:
    active_path = sample_paths["auth_video"]
    is_video = True

# Read file bytes & compute real SHA-256 custody chain hash
with open(active_path, "rb") as f:
    file_bytes = f.read()
sha256_custody_hash = legal_docket.compute_sha256(file_bytes)

# Execute Core Forensic Modules in Real-Time for the resolved active evidence file
@st.cache_data(show_spinner="Executing Real-Time Multi-Signal Agentic Pipeline...")
def run_forensic_pipeline(file_path: str, is_vid: bool, gemini_api_key: str, file_mtime: float):
    results = {}
    
    # 1. Privacy Shield Execution
    if not is_vid:
        img_bgr = cv2.imread(file_path)
        shielded_bgr, face_count, bboxes = privacy_shield.apply_privacy_shield_to_image(img_bgr)
        results["privacy"] = {
            "count": face_count,
            "img_bgr": img_bgr,
            "shielded_bgr": shielded_bgr,
            "shielded_vid_path": None
        }
    else:
        out_vid = os.path.join(sample_generator.SAMPLE_DIR, f"shielded_{os.path.basename(file_path)}")
        shielded_vid, face_count = privacy_shield.apply_privacy_shield_to_video(file_path, out_vid)
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()
        shielded_bgr, _, _ = privacy_shield.apply_privacy_shield_to_image(frame)
        results["privacy"] = {
            "count": face_count,
            "img_bgr": frame,
            "shielded_bgr": shielded_bgr,
            "shielded_vid_path": out_vid
        }
        
    # 2. ENF Physics Analyzer
    if is_vid:
        results["enf"] = enf_analyzer.analyze_video_enf(file_path, target_freq=50.0)
    else:
        results["enf"] = {
            "is_enf_available": False,
            "enf_ratio": 1.0,
            "is_authentic": True,
            "verdict_text": "ENF unavailable",
            "reason": "No evidence available for ENF grid frequency estimation (Static image input)",
            "freqs": [], "spectrum": [], "luminance_signal": [], "time_stamps": []
        }
        
    # 3. Multi-Signal Corneal Specular Topology Engine with Quality Filter
    img_for_corneal = cv2.imread(file_path) if not is_vid else results["privacy"]["img_bgr"]
    results["corneal"] = corneal_analyzer.analyze_corneal_specular_topology(img_for_corneal, file_path=file_path)
    
    # 4. Visuo-Acoustic Knowledge Graphing (VLM background extraction)
    results["vlm"] = vlm_extractor.parse_background_environment(results["privacy"]["shielded_bgr"], gemini_api_key)
    
    # 5. NetworkX Knowledge Graph Compilation
    G = knowledge_graph.build_case_knowledge_graph(case_id, results["vlm"].get("environmental_objects", []))
    results["graph"] = G
    results["graph_fig"] = knowledge_graph.generate_plotly_network_figure(G)
    results["graph_correlations"] = knowledge_graph.analyze_cross_case_correlations(G, case_id)
    
    return results

file_mtime = os.path.getmtime(active_path) if os.path.exists(active_path) else 0.0
forensic_data = run_forensic_pipeline(active_path, is_video, gemini_key, file_mtime)

# Generate Dynamic BSA 2023 Legal Docket
docket_res = legal_docket.generate_bsa_legal_docket(
    case_id=case_id,
    investigator_id=officer_id,
    media_filename=os.path.basename(active_path),
    media_bytes=file_bytes,
    privacy_summary=forensic_data["privacy"],
    enf_summary=forensic_data.get("enf"),
    corneal_summary=forensic_data.get("corneal"),
    vlm_summary=forensic_data.get("vlm")
)

# Render Main Dashboard Tabs
tab_overview, tab_privacy, tab_enf, tab_corneal, tab_graph, tab_legal = st.tabs([
    "🛡️ Ingestion & Overview",
    "🙈 Agentic Privacy Shield",
    "⚡ ENF Physics Engine",
    "👁️ Multi-Signal Image Forensics",
    "🕸️ Visuo-Acoustic Knowledge Graph",
    "⚖️ BSA 2023 Legal Docket"
])

# ==================== TAB 1: OVERVIEW & INGESTION HUB ====================
with tab_overview:
    st.markdown("### 📥 EVIDENCE INGESTION HUB & REAL-TIME FORENSIC SUMMARY")
    
    with st.expander("📂 CLICK HERE TO UPLOAD NEW EVIDENCE FILE (MP4, AVI, JPG, PNG)", expanded=True):
        main_tab_uploaded_file = st.file_uploader(
            "Upload any Video (.mp4, .avi) or Image (.jpg, .png) file to process through A.E.G.I.S. real-time pipeline:",
            type=["mp4", "avi", "mov", "jpg", "png", "jpeg"],
            key="main_tab_uploader"
        )
        if main_tab_uploaded_file is not None:
            if st.session_state.get("main_uploaded_file") != main_tab_uploaded_file:
                st.session_state["main_uploaded_file"] = main_tab_uploaded_file
                st.rerun()

    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Custody Chain Status</div>
            <div class="metric-value metric-status-safe">SHA-256 SECURED</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Privacy Shield Redactions</div>
            <div class="metric-value metric-status-safe">{forensic_data['privacy']['count']} SUBJECTS</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        if not forensic_data['enf'].get('is_enf_available', True) or forensic_data['enf'].get('verdict_text') == "ENF unavailable":
            enf_val = "ENF UNAVAILABLE"
            color_cls = "metric-status-threat"
        else:
            enf_val = "50.0 Hz DETECTED" if forensic_data['enf'].get('is_authentic') else "PHYSICS ANOMALY"
            color_cls = "metric-status-safe" if forensic_data['enf'].get('is_authentic') else "metric-status-threat"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ENF Grid Hum Peak</div>
            <div class="metric-value {color_cls}">{enf_val}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        c_score = forensic_data['corneal'].get('symmetry_score', 0.0)
        c_color = "metric-status-safe" if c_score >= 55.0 else "metric-status-threat"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Multi-Signal Integrity Score</div>
            <div class="metric-value {c_color}">{c_score:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Overall Authentic vs Synthetic Banner
    if docket_res["is_authentic"]:
        st.markdown(f"""
        <div style="background-color: rgba(0, 230, 118, 0.1); border: 2px solid #00e676; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #00e676; margin: 0;">✅ VERDICT: AUTHENTIC REAL-WORLD CAPTURE</h3>
            <p style="color: #cbd5e1; margin-top: 6px;">Media exhibits consistent 50 Hz power grid hum physics, camera EXIF metadata, and multi-signal optical integrity.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: rgba(255, 75, 75, 0.1); border: 2px solid #ff4b4b; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #ff4b4b; margin: 0;">🚨 VERDICT: SYNTHETIC AI GENERATED FABRICATION</h3>
            <p style="color: #cbd5e1; margin-top: 6px;">Media exhibits multi-signal forensic anomalies (asymmetric corneal specular glints, stripped EXIF, zero sensor noise, or frequency anomalies).</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown("#### 📄 Ingested Evidence Details")
        st.code(f"""
Active File Name: {os.path.basename(active_path)}
Media Type: {'Video (MP4/AVI)' if is_video else 'Static Image (JPG/PNG)'}
File Size: {len(file_bytes) / 1024:.2f} KB
SHA-256 Hash: {sha256_custody_hash}
Jurisdiction: {district}
        """, language="yaml")
    with c_right:
        st.markdown("#### 🔬 Active Forensic Multi-Agent Vectors")
        st.markdown("""
        - **Vector 1**: Automated Privacy Shield (Mental Health Safeguard)
        - **Vector 2**: SciPy FFT Electrical Network Frequency (50 Hz AC Grid Physics)
        - **Vector 3**: Multi-Signal Image Forensic Scoring Engine (8 Independent Optical & Compression Vectors)
        - **Vector 4**: Visuo-Acoustic Knowledge Graphing (Background Feature Extraction)
        - **Vector 5**: BSA 2023 Section 63 Dynamic Legal Docket
        """)

# ==================== TAB 2: PRIVACY SHIELD ====================
with tab_privacy:
    st.markdown("### 🙈 AUTOMATED AGENTIC PRIVACY SHIELD")
    st.markdown("*Protects investigator mental health by redacting human subjects upon ingestion while keeping 100% of background evidence intact.*")
    
    col_orig, col_shield = st.columns(2)
    with col_orig:
        st.markdown("#### 📥 Original Ingested Media")
        if is_video:
            st.video(active_path)
        else:
            st.image(cv2.cvtColor(forensic_data["privacy"]["img_bgr"], cv2.COLOR_BGR2RGB), use_container_width=True)
            
    with col_shield:
        st.markdown("#### 🛡️ Redacted Environmental Evidence Stream")
        if is_video and forensic_data["privacy"].get("shielded_vid_path") and os.path.exists(forensic_data["privacy"]["shielded_vid_path"]):
            st.video(forensic_data["privacy"]["shielded_vid_path"])
        else:
            st.image(cv2.cvtColor(forensic_data["privacy"]["shielded_bgr"], cv2.COLOR_BGR2RGB), use_container_width=True)
            
    st.info(f"🛡️ **Privacy Shield Active**: Redacted {forensic_data['privacy']['count']} human subject face/body regions. Background environmental evidence preserved for knowledge graph extraction.")

# ==================== TAB 3: ENF PHYSICS ENGINE ====================
with tab_enf:
    st.markdown("### ⚡ ELECTRICAL NETWORK FREQUENCY (ENF) PHYSICS LABORATORY")
    st.markdown("*Measures frame-by-frame pixel luminance oscillations using SciPy FFT, PSD, and STFT Spectrograms to isolate the 50 Hz Indian Power Grid AC frequency hum.*")
    
    if not is_video:
        st.warning("⚠️ **ENF unavailable**: Static image input (ENF physics vector requires a video luminance stream).")
    
    st.markdown("#### 🎛️ Real-Time Interactive Physics Parameters")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        target_f = st.slider("Target Grid Frequency (Hz)", min_value=40.0, max_value=70.0, value=50.0, step=0.5, help="50 Hz standard for India/Kerala AC grid lighting.")
    with p_col2:
        tolerance_f = st.slider("Frequency Search Band Tolerance (± Hz)", min_value=0.5, max_value=5.0, value=2.5, step=0.5)
        
    if is_video:
        enf = enf_analyzer.analyze_video_enf(active_path, target_freq=target_f, tolerance_hz=tolerance_f)
    else:
        enf = forensic_data["enf"]
        
    if not enf.get("is_enf_available", True) or enf.get("verdict_text") == "ENF unavailable":
        st.warning(f"⚠️ **ENF unavailable**: {enf.get('reason', 'No evidence available for ENF grid frequency estimation.')}")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("ENF Peak Power Ratio", "N/A")
        with col_m2:
            st.metric("Effective Target Freq", f"{enf.get('effective_target_freq', 50.0):.1f} Hz")
        with col_m3:
            st.metric("Sampled FPS Rate", f"{enf.get('fps', 0.0):.1f} FPS")
        with col_m4:
            st.metric("Physics Verdict", "ENF UNAVAILABLE")
    else:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("ENF Peak Power Ratio", f"{enf.get('enf_ratio', 0.0):.2f}x", delta="Authentic >= 2.2x")
        with col_m2:
            st.metric("Effective Target Freq", f"{enf.get('effective_target_freq', 50.0):.1f} Hz")
        with col_m3:
            st.metric("Sampled FPS Rate", f"{enf.get('fps', 30.0):.1f} FPS")
        with col_m4:
            st.metric("Physics Verdict", "GRID VERIFIED" if enf.get("is_authentic") else "SYNTHETIC FLICKER MISSING")
            
        st.markdown("---")
        
        # Diagnostic Plot 1: Luminance Waveform I(t) & Detrended Signal
        if enf.get("time_stamps") and enf.get("luminance_signal"):
            st.markdown("#### 📈 1. Frame-by-Frame Pixel Luminance Waveform $I(t)$ & Detrended AC Signal")
            fig_wave = go.Figure()
            fig_wave.add_trace(go.Scatter(
                x=enf["time_stamps"], y=enf["luminance_signal"],
                mode='lines', name='Raw Mean Pixel Luminance I(t)',
                line=dict(color='#00d2ff', width=2)
            ))
            if enf.get("detrended_signal"):
                fig_wave.add_trace(go.Scatter(
                    x=enf["time_stamps"], y=enf["detrended_signal"],
                    mode='lines', name='SciPy Detrended AC Oscillations',
                    line=dict(color='#ffb703', width=1.5, dash='dot')
                ))
            fig_wave.update_layout(
                xaxis_title="Time (seconds)", yaxis_title="Mean Spatial Luminance",
                paper_bgcolor="#0a0e17", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_wave, use_container_width=True)
            
        # Diagnostic Plot 2: SciPy FFT Spectrum & Search Band
        if enf.get("freqs") and len(enf["freqs"]) > 0:
            st.markdown("#### 📉 2. SciPy Fast Fourier Transform (FFT) Magnitude Spectrum")
            fig_fft = px.line(
                x=enf["freqs"], y=enf["spectrum"],
                labels={"x": "Frequency (Hz)", "y": "FFT Spectral Magnitude"},
                title=f"Luminance Power Spectrum (Target: {target_f} Hz ± {tolerance_f} Hz)"
            )
            eff_t = enf.get("effective_target_freq", 50.0)
            fig_fft.add_vrect(
                x0=max(0, eff_t - tolerance_f), x1=min(enf["fps"]/2, eff_t + tolerance_f),
                fillcolor="#00d2ff", opacity=0.15, line_width=0,
                annotation_text=f"Grid Search Band ({eff_t:.1f} Hz)", annotation_position="top left"
            )
            fig_fft.add_vline(x=eff_t, line_dash="dash", line_color="#00e676" if enf.get("is_authentic") else "#ff4b4b")
            fig_fft.update_layout(paper_bgcolor="#0a0e17", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"))
            st.plotly_chart(fig_fft, use_container_width=True)
            
        # Diagnostic Plot 3: SciPy STFT 2D Spectrogram Heatmap
        if enf.get("stft_matrix") and len(enf["stft_matrix"]) > 0:
            st.markdown("#### 🌡️ 3. SciPy Short-Time Fourier Transform (STFT) 2D Spectrogram Heatmap")
            fig_spec = go.Figure(data=go.Heatmap(
                z=enf["stft_matrix"],
                x=enf["stft_times"],
                y=enf["stft_freqs"],
                colorscale='Viridis',
                colorbar=dict(title='Power (dB)')
            ))
            fig_spec.update_layout(
                xaxis_title="Time (seconds)", yaxis_title="Frequency (Hz)",
                paper_bgcolor="#0a0e17", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_spec, use_container_width=True)

# ==================== TAB 4: MULTI-SIGNAL IMAGE FORENSICS ====================
with tab_corneal:
    st.markdown("### 👁️ MULTI-SIGNAL IMAGE FORENSIC SCORING ENGINE")
    st.markdown("*Combines 8 independent computer vision & optical physics indicators to eliminate false positives on real photographs.*")
    
    corneal = forensic_data["corneal"]
    
    c_col1, c_col2, c_col3, c_col4 = st.columns(4)
    with c_col1:
        st.metric("Multi-Signal Anomaly Score", f"{corneal.get('anomaly_score', 20.0):.1f}%", delta="Authentic < 32%")
    with c_col2:
        st.metric("Detection Confidence", f"{corneal.get('confidence', 90.0):.1f}%")
    with c_col3:
        st.metric("Corneal Integrity Score", f"{corneal['symmetry_score']:.1f}%")
    with c_col4:
        if corneal.get("verdict_text") == "No evidence available":
            st.metric("Verdict", "NO EVIDENCE AVAILABLE")
        elif not corneal.get("is_quality_sufficient", True):
            st.metric("Verdict", "INSUFFICIENT QUALITY")
        else:
            st.metric("Verdict", "AUTHENTIC REAL PHOTO" if corneal['is_authentic'] else "SYNTHETIC AI FABRICATION")
            
    st.markdown("---")
    
    if corneal.get("verdict_text") == "No evidence available":
        st.warning("⚠️ **No evidence available**: Image file missing or unreadable.")
    elif not corneal.get("is_quality_sufficient", True):
        st.warning(f"⚠️ **Analysis Suspended**: {corneal.get('quality_reason', 'Insufficient image quality')}. Quality confidence is below threshold (< 40.0%).")
    
    # 8-Feature Contributing Breakdown Plot
    st.markdown("#### 📊 8 Independent Forensic Indicator Scores & Weighted Impacts")
    
    feats = corneal.get("contributing_features", {})
    if feats:
        feature_labels = list(feats.keys())
        scores = [feats[k]["score"] for k in feature_labels]
        impacts = [feats[k]["weighted_impact"] for k in feature_labels]
        
        fig_feats = go.Figure()
        fig_feats.add_trace(go.Bar(
            y=[f.replace("_", " ").title() for f in feature_labels],
            x=scores,
            name='Raw Indicator Anomaly Score (0-100)',
            orientation='h',
            marker=dict(color='#ffb703')
        ))
        fig_feats.add_trace(go.Bar(
            y=[f.replace("_", " ").title() for f in feature_labels],
            x=impacts,
            name='Weighted Ensemble Impact',
            orientation='h',
            marker=dict(color='#00d2ff')
        ))
        fig_feats.update_layout(
            bmode='group', title="Forensic Indicator Anomaly Vector Breakdown",
            paper_bgcolor="#0a0e17", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"),
            xaxis_title="Anomaly Score Value", yaxis_title="Forensic Indicator"
        )
        st.plotly_chart(fig_feats, use_container_width=True)
        
    st.markdown("---")
    
    # Detailed Plain-English Explanations for Every Feature
    st.markdown("#### 🔬 Plain-English Scientific Feature Explanations")
    exps = corneal.get("explanation", [])
    for exp in exps:
        st.markdown(f"- 📌 {exp}")
        
    st.markdown("---")
    
    col_l_eye, col_r_eye = st.columns(2)
    with col_l_eye:
        st.markdown("#### 👁️ Left Eye Corneal Zoom & Specular Glint Mask")
        if corneal["l_crop"] is not None and corneal["l_crop"].size > 0:
            st.image(cv2.cvtColor(corneal["l_crop"], cv2.COLOR_BGR2RGB), caption="Left Eye Region of Interest (ROI)", width=250)
            st.image(corneal["l_mask"], caption="Isolated Left Specular Light Reflection Glint", width=250)
    with col_r_eye:
        st.markdown("#### 👁️ Right Eye Corneal Zoom & Specular Glint Mask")
        if corneal["r_crop"] is not None and corneal["r_crop"].size > 0:
            st.image(cv2.cvtColor(corneal["r_crop"], cv2.COLOR_BGR2RGB), caption="Right Eye Region of Interest (ROI)", width=250)
            st.image(corneal["r_mask"], caption="Isolated Right Specular Light Reflection Glint", width=250)

# ==================== TAB 5: KNOWLEDGE GRAPH ====================
with tab_graph:
    st.markdown("### 🕸️ VISUO-ACOUSTIC KNOWLEDGE GRAPHING")
    st.markdown("*Scans redacted background environments to extract furniture, textures, and fixtures, mapping them across case files using NetworkX.*")
    
    vlm = forensic_data["vlm"]
    st.markdown(f"**Extracted Scene Environment**: `{vlm.get('scene_type', 'Indoor Scene')}` | Lighting: `{vlm.get('lighting_type', 'N/A')}`")
    
    st.markdown("#### 📦 Extracted Background Entities & Attributes")
    objs = vlm.get("environmental_objects", [])
    if len(objs) == 0:
        st.warning("⚠️ **No evidence available**: Zero environmental entities detected in active evidence background.")
    else:
        obj_cols = st.columns(3)
        for idx, obj in enumerate(objs):
            with obj_cols[idx % 3]:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: #ffb703; font-weight: 700;">📌 {obj['entity']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                        {', '.join(obj.get('attributes', []))}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
    st.markdown("---")
    st.markdown("#### 🌐 Interactive NetworkX Intelligence Correlation Graph")
    st.plotly_chart(forensic_data["graph_fig"], use_container_width=True)
    
    st.markdown("#### 🚨 Cross-Case Intelligence Correlations")
    corrs = forensic_data["graph_correlations"]
    if corrs:
        for c in corrs:
            st.error(f"⚠️ **LINK DETECTED WITH {c['case_id']}**: Shares {c['shared_count']} Environmental Entity Node(s): `{', '.join(c['shared_entities'])}`")
    else:
        st.success("Zero historical case entity matches found for current evidence.")

# ==================== TAB 6: LEGAL DOCKET ====================
with tab_legal:
    st.markdown("### ⚖️ BSA 2023 SECTION 63 LEGAL FORENSIC DOCKET")
    st.markdown("*Dynamic, plain-English court report adhering to Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.*")
    
    st.markdown(docket_res["html_content"], unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Statutory Legal Docket Certificate (HTML)",
        data=docket_res["html_content"],
        file_name=f"AEGIS_Legal_Docket_{case_id}.html",
        mime="text/html"
    )
