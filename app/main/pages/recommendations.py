import streamlit as st

st.set_page_config(page_title="AI Recommendations", page_icon="💡", layout="wide")

# =========================================================
# 🛠️ AKILLI VERİ YÖNETİMİ (TÜM MODÜLLER ENTEGRE)
# =========================================================

source = st.session_state.get("source_page", "cookie")

if source == "fluency":
    res = st.session_state.get("analysis_results_fluency")
    back_target = "pages/results_fluency.py"
    main_page = "pages/fluency.py"
elif source == "recall":
    res = st.session_state.get("analysis_results_recall")
    back_target = "pages/results_recall.py"
    main_page = "pages/recall.py"
elif source == "sentence":
    res = st.session_state.get("analysis_results_sentence")
    back_target = "pages/results_sentence.py"
    main_page = "pages/sentence.py"
elif source == "spanish":
    res = st.session_state.get("analysis_results_spanish")
    back_target = "pages/results_spanish.py"
    main_page = "pages/spanish.py"
elif source == "mandarin":
    res = st.session_state.get("analysis_results_mandarin")
    back_target = "pages/results_mandarin.py"
    main_page = "pages/mandarin.py"
elif source == "korean":
    res = st.session_state.get("analysis_results_korean")
    back_target = "pages/results_korean.py"
    main_page = "pages/korean.py"
else:
    res = st.session_state.get("analysis_results")
    back_target = "pages/results.py"
    main_page = "app.py"

if res is None:
    st.switch_page(main_page)

# Risk seviyesini ve yaş bilgisini çekiyoruz
risk = res.get("risk_level", "low")
age = st.session_state.get("patient_age", "Unknown")

# Özel CSS
st.markdown("""
    <style>
    .recom-card { padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid; }
    .low-card { background-color: rgba(34, 197, 94, 0.05); border-color: #22c55e; }
    .med-card { background-color: rgba(245, 158, 11, 0.05); border-color: #f59e0b; }
    .high-card { background-color: rgba(239, 68, 68, 0.05); border-color: #ef4444; }
    .step-number { font-size: 1.5rem; font-weight: bold; margin-right: 10px; }
    </style>
""", unsafe_allow_html=True)

# Üst Banner
st.markdown(f"""
    <div style='background: linear-gradient(90deg, #0B1117 0%, #1A222C 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6; margin-bottom: 20px;'>
        <h2 style='margin: 0; color: #F8FAFC;'>💡 Personalized Clinical Action Plan</h2>
        <p style='margin: 0; color: #94a3b8;'>AI-Generated pathway for <b>{source.upper()}</b> task.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 🟢 SENARYO 1: DÜŞÜK RİSK (SAĞLIKLI) - TÜM DİLLER İÇİN ORTAK
# ==========================================
if risk == "low":
    st.success("### ✅ Status: Healthy Cognitive Function")
    st.write(
        "Patient exhibits strong linguistic patterns and memory recall. The focus should be on **Cognitive Maintenance & Prevention**.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class='recom-card low-card'>
                <h4>🧠 Neuro-Fitness & Plasticity</h4>
                <ul>
                    <li><b>Language Engagement:</b> Reading complex literature or learning a new language.</li>
                    <li><b>Strategic Games:</b> Chess, Sudoku, or strategy games.</li>
                    <li><b>Social Interaction:</b> High-density social conversations.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class='recom-card low-card'>
                <h4>🥗 Diet & Lifestyle</h4>
                <ul>
                    <li><b>MIND Diet:</b> Leafy greens, berries, nuts, and olive oil.</li>
                    <li><b>Exercise:</b> 150 mins of moderate aerobic exercise per week.</li>
                    <li><b>Sleep:</b> 7-8 hours for amyloid-beta clearance.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 🟠 SENARYO 2: ORTA RİSK (MCI ŞÜPHESİ) - TÜM DİLLER İÇİN ORTAK
# ==========================================
elif risk == "medium":
    st.warning("### ⚠️ Status: Suspected Mild Cognitive Impairment (MCI)")
    st.write(
        "Patient shows early signs of linguistic hesitation or cognitive delays. The focus should be on **Proactive Intervention & Monitoring**.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class='recom-card med-card'>
                <h4>🩺 Clinical Next Steps</h4>
                <ul>
                    <li><b>Assessment:</b> Schedule a MoCA or MMSE test within 4 weeks.</li>
                    <li><b>Blood Panel:</b> Check B12, TSH, and Vitamin D levels.</li>
                    <li><b>Monitoring:</b> Repeat NeuroVoice AI analysis in 6 months.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class='recom-card med-card'>
                <h4>🗣️ Cognitive Therapy</h4>
                <ul>
                    <li><b>Speech Therapy:</b> Exercises to improve word retrieval.</li>
                    <li><b>Memory Clinics:</b> Structured cognitive rehabilitation.</li>
                    <li><b>Routine:</b> Daily scheduling to reduce cognitive load.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 🔴 SENARYO 3: YÜKSEK RİSK (DİLLERE GÖRE AYRIM YAPILAN YER)
# ==========================================
else:
    # 🇨🇳 🇰🇷 EĞER ÇİNCE VEYA KORECE İSE (SADECE MCI SEVİYESİ)
    if source in ["mandarin", "korean"]:
        st.error("### 🚨 Status: Advanced Mild Cognitive Impairment (MCI) Detected")
        st.write(
            "Significant semantic degradation, cognitive delays, and acoustic pauses detected. Immediate clinical evaluation is recommended to prevent further decline.")

        st.markdown("""
            <div class='recom-card high-card'>
                <h4>🏥 Immediate Medical Pathway</h4>
                <p><span class='step-number'>1</span> <b>Detailed Neuropsychological Assessment:</b> Comprehensive cognitive testing.</p>
                <p><span class='step-number'>2</span> <b>Specialist Referral:</b> Consultation with a Neurologist for MCI staging.</p>
                <p><span class='step-number'>3</span> <b>Brain Imaging:</b> MRI scan to rule out other organic causes.</p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.info(
                "#### 🛡️ Patient Care Routine\n- Monitor daily activities and memory gaps.\n- Implement cognitive support tools (calendars, notes).\n- Review prescriptions affecting cognition.")
        with c2:
            st.info(
                "#### 🤝 Clinical Support\n- Enroll in cognitive rehabilitation programs.\n- Family counseling and planning.\n- Regular 3-month follow-ups required.")

    # 🇺🇸 🇪🇸 EĞER İNGİLİZCE VEYA İSPANYOLCA İSE (ALZHEIMER/DEMANS SEVİYESİ)
    else:
        st.error("### 🚨 Status: High Risk of Dementia / Alzheimer's")
        st.write("Severe semantic degradation, memory loss, and significant pauses detected. Urgent action required.")

        st.markdown("""
            <div class='recom-card high-card'>
                <h4>🏥 Immediate Medical Pathway</h4>
                <p><span class='step-number'>1</span> <b>Urgent MRI / PET Scan:</b> Neuroimaging for atrophy detection.</p>
                <p><span class='step-number'>2</span> <b>Specialist Referral:</b> Consultation with a Neurologist.</p>
                <p><span class='step-number'>3</span> <b>Medication Review:</b> Evaluate prescriptions affecting cognition.</p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.info("#### 🛡️ Patient Safety\n- Fall risk assessment.\n- Medication alarms.\n- GPS tracking if needed.")
        with c2:
            st.info(
                "#### 🤝 Caregiver Support\n- Alzheimer's Association contact.\n- Family psychological support.\n- Legal/Financial planning.")

# ==========================================
# ALT NAVİGASYON (DİNAMİK)
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([1, 2, 1])

with b1:
    if st.button("⬅️ Back to Results", use_container_width=True):
        st.switch_page(back_target)

with b3:
    if st.button("🏠 New Patient Analysis", type="primary", use_container_width=True):
        # TÜM MODÜLLER İÇİN STATE TEMİZLİĞİ (GÜVENLİK)
        st.session_state.audio_bytes = None
        st.session_state.analysis_results = None
        st.session_state.analysis_results_fluency = None
        st.session_state.analysis_results_recall = None
        st.session_state.analysis_results_sentence = None
        st.session_state.analysis_results_spanish = None
        st.session_state.analysis_results_mandarin = None
        st.session_state.analysis_results_korean = None
        st.switch_page(main_page)