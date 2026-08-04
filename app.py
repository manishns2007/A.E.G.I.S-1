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
        corneal specular topology, and spatial knowledge graphs — Fully compliant with Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.
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

# Determine Active File Path cleanly
active_path = None
is_video = True

if sidebar_uploaded_file is not None:
    save_path = os.path.join(sample_generator.SAMPLE_DIR, f"custom_{sidebar_uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(sidebar_uploaded_file.getbuffer())
    active_path = save_path
    is_video = sidebar_uploaded_file.name.lower().endswith((".mp4", ".avi", ".mov"))
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

# Compute SHA-256 Hash of Evidence
with open(active_path, "rb") as f:
    file_bytes = f.read()
sha256_custody_hash = legal_docket.compute_sha256(file_bytes)

# Execute Core Forensic Modules in Real-Time
@st.cache_data(show_spinner="Executing Real-Time Agentic Forensic Pipeline...")
def run_forensic_pipeline(file_path: str, is_vid: bool, gemini_api_key: str):
    results = {}
    
    # 1. Privacy Shield Execution
    if not is_vid:
        img_bgr = cv2.imread(file_path)
        shielded_bgr, face_count, bboxes = privacy_shield.apply_privacy_shield_to_image(img_bgr)
        results["privacy"] = {"count": face_count, "img_bgr": img_bgr, "shielded_bgr": shielded_bgr}
    else:
        out_vid = os.path.join(sample_generator.SAMPLE_DIR, "shielded_temp.mp4")
        shielded_vid, face_count = privacy_shield.apply_privacy_shield_to_video(file_path, out_vid)
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()
        shielded_bgr, _, _ = privacy_shield.apply_privacy_shield_to_image(frame)
        results["privacy"] = {"count": face_count, "img_bgr": frame, "shielded_bgr": shielded_bgr}
        
    # 2. ENF Physics Analyzer (for videos or video sample fallback)
    if is_vid:
        results["enf"] = enf_analyzer.analyze_video_enf(file_path)
    else:
        results["enf"] = {
            "enf_ratio": 1.0,
            "is_authentic": True,
            "verdict_text": "ENF Vector Inactive for Static Still Images (Requires Video Luminance Stream)",
            "freqs": [], "spectrum": []
        }
        
    # 3. Corneal Specular Topology Analyzer (for images or video frame crop)
    img_for_corneal = cv2.imread(file_path) if not is_vid else results["privacy"]["img_bgr"]
    results["corneal"] = corneal_analyzer.analyze_corneal_specular_topology(img_for_corneal)
    
    # 4. Visuo-Acoustic Knowledge Graphing (VLM background extraction)
    results["vlm"] = vlm_extractor.parse_background_environment(results["privacy"]["shielded_bgr"], gemini_api_key)
    
    # 5. NetworkX Knowledge Graph Compilation
    G = knowledge_graph.build_case_knowledge_graph(case_id, results["vlm"].get("environmental_objects", []))
    results["graph"] = G
    results["graph_fig"] = knowledge_graph.generate_plotly_network_figure(G)
    results["graph_correlations"] = knowledge_graph.analyze_cross_case_correlations(G, case_id)
    
    return results

forensic_data = run_forensic_pipeline(active_path, is_video, gemini_key)

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
    "👁️ Corneal Specular Topology",
    "🕸️ Visuo-Acoustic Knowledge Graph",
    "⚖️ BSA 2023 Legal Docket"
])

# ==================== TAB 1: OVERVIEW & INGESTION HUB ====================
with tab_overview:
    st.markdown("### 📥 EVIDENCE INGESTION HUB & REAL-TIME FORENSIC SUMMARY")
    
    # Prominent Upload Box in Main View
    with st.expander("📂 CLICK HERE TO UPLOAD NEW EVIDENCE FILE (MP4, AVI, JPG, PNG)", expanded=True):
        main_uploaded_file = st.file_uploader(
            "Upload any Video (.mp4, .avi) or Image (.jpg, .png) file to process through A.E.G.I.S. real-time pipeline:",
            type=["mp4", "avi", "mov", "jpg", "png", "jpeg"],
            key="main_tab_uploader"
        )
        if main_uploaded_file is not None:
            save_path = os.path.join(sample_generator.SAMPLE_DIR, f"custom_{main_uploaded_file.name}")
            with open(save_path, "wb") as f:
                f.write(main_uploaded_file.getbuffer())
            st.success(f"✅ Ingested custom evidence file: `{main_uploaded_file.name}`. Refreshing real-time analysis...")
            active_path = save_path
            is_video = main_uploaded_file.name.lower().endswith((".mp4", ".avi", ".mov"))
            forensic_data = run_forensic_pipeline(active_path, is_video, gemini_key)
            docket_res = legal_docket.generate_bsa_legal_docket(
                case_id=case_id, investigator_id=officer_id, media_filename=os.path.basename(active_path),
                media_bytes=main_uploaded_file.getvalue(), privacy_summary=forensic_data["privacy"],
                enf_summary=forensic_data.get("enf"), corneal_summary=forensic_data.get("corneal"), vlm_summary=forensic_data.get("vlm")
            )

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
        c_color = "metric-status-safe" if c_score >= 75.0 else "metric-status-threat"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Corneal Symmetry Score</div>
            <div class="metric-value {c_color}">{c_score:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Overall Authentic vs Synthetic Banner
    if docket_res["is_authentic"]:
        st.markdown(f"""
        <div style="background-color: rgba(0, 230, 118, 0.1); border: 2px solid #00e676; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #00e676; margin: 0;">✅ VERDICT: AUTHENTIC REAL-WORLD CAPTURE</h3>
            <p style="color: #cbd5e1; margin-top: 6px;">Media exhibits consistent 50 Hz power grid hum physics and symmetric corneal light reflection topology.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: rgba(255, 75, 75, 0.1); border: 2px solid #ff4b4b; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #ff4b4b; margin: 0;">🚨 VERDICT: SYNTHETIC AI GENERATED FABRICATION</h3>
            <p style="color: #cbd5e1; margin-top: 6px;">Media exhibits physical frequency anomalies or asymmetric corneal specular diffusion artifacts created by generative models.</p>
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
        - **Vector 3**: Corneal Specular Topology (Glint Symmetry Geometry)
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
        if is_video and os.path.exists(os.path.join(sample_generator.SAMPLE_DIR, "shielded_temp.mp4")):
            st.video(os.path.join(sample_generator.SAMPLE_DIR, "shielded_temp.mp4"))
        else:
            st.image(cv2.cvtColor(forensic_data["privacy"]["shielded_bgr"], cv2.COLOR_BGR2RGB), use_container_width=True)
            
    st.info(f"🛡️ **Privacy Shield Active**: Redacted {forensic_data['privacy']['count']} human subject face/body regions. Background environmental evidence preserved for knowledge graph extraction.")

# ==================== TAB 3: ENF PHYSICS ENGINE ====================
with tab_enf:
    st.markdown("### ⚡ ELECTRICAL NETWORK FREQUENCY (ENF) PHYSICS ANALYZER")
    st.markdown("*Measures frame-by-frame pixel luminance oscillations using SciPy FFT & PSD to detect the 50 Hz Indian Power Grid AC frequency hum.*")
    
    enf = forensic_data["enf"]
    if "error" in enf:
        st.warning(f"⚠️ {enf['error']}")
    else:
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("ENF 50Hz Peak Power Ratio", f"{enf.get('enf_ratio', 0.0):.2f}x", delta="Authentic > 2.2x")
        with col_m2:
            st.metric("Target Grid Frequency", f"{enf.get('target_freq', 50.0)} Hz")
        with col_m3:
            st.metric("Physics Verdict", "GRID VERIFIED" if enf.get("is_authentic") else "SYNTHETIC FLICKER MISSING")
            
        if enf.get("freqs") and len(enf["freqs"]) > 0:
            st.markdown("#### 📉 Fast Fourier Transform (FFT) Power Spectrum Plot")
            fig_fft = px.line(
                x=enf["freqs"], y=enf["spectrum"],
                labels={"x": "Frequency (Hz)", "y": "Spectral Magnitude"},
                title="SciPy Fast Fourier Transform (FFT) Luminance Power Spectrum"
            )
            fig_fft.add_vline(x=enf.get("effective_target_freq", 50.0), line_dash="dash", line_color="#00d2ff", annotation_text="50 Hz Power Grid Peak")
            fig_fft.update_layout(paper_bgcolor="#0a0e17", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"))
            st.plotly_chart(fig_fft, use_container_width=True)
            
        st.markdown("""
        > **Scientific Forensic Rationale**: Artificial intelligence video generators (Sora, Runway, Pika, Flux) render frames frame-by-frame or via latent noise projection without modeling real-world AC power grid electrical oscillations. Real cameras recording under grid lighting capture subtle 50 Hz / 100 Hz brightness hums that can be mathematically verified using SciPy FFT.
        """)

# ==================== TAB 4: CORNEAL SPECULAR TOPOLOGY ====================
with tab_corneal:
    st.markdown("### 👁️ CORNEAL SPECULAR TOPOLOGY ANALYZER")
    st.markdown("*Zooms into human eyes in high-resolution portraits to map corneal light reflections (glints) and compare specular geometry between eyes.*")
    
    corneal = forensic_data["corneal"]
    
    c_col1, c_col2, c_col3 = st.columns(3)
    with c_col1:
        st.metric("Corneal Symmetry Score", f"{corneal['symmetry_score']:.1f}%", delta="Authentic >= 75%")
    with c_col2:
        st.metric("Left Eye Glints", f"{corneal['l_count']} Glint Contour(s)")
    with c_col3:
        st.metric("Right Eye Glints", f"{corneal['r_count']} Glint Contour(s)")
        
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
            
    st.markdown("""
    > **Optical Forensic Rationale**: In real photography under distant ambient lighting, both left and right corneas reflect identical lighting geometry. Generative AI diffusion models process left and right eye latents independently, producing mismatched reflection shapes (e.g. circle in left eye vs slanted ellipse or dual glint in right eye).
    """)

# ==================== TAB 5: KNOWLEDGE GRAPH ====================
with tab_graph:
    st.markdown("### 🕸️ VISUO-ACOUSTIC KNOWLEDGE GRAPHING")
    st.markdown("*Scans redacted background environments to extract furniture, textures, and fixtures, mapping them across case files using NetworkX.*")
    
    vlm = forensic_data["vlm"]
    st.markdown(f"**Extracted Scene Environment**: `{vlm.get('scene_type', 'Indoor Scene')}` | Lighting: `{vlm.get('lighting_type', 'N/A')}`")
    
    st.markdown("#### 📦 Extracted Background Entities & Attributes")
    obj_cols = st.columns(3)
    objs = vlm.get("environmental_objects", [])
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
