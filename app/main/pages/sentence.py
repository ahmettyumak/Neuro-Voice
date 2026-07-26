import streamlit as st
import time
from style.appstyle_css import app_css

st.set_page_config(page_title="Neurovoice AI - English (Sentence)", page_icon="🧠", layout="wide")

if 'theme' not in st.session_state: st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

if st.session_state.theme == "dark":
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#0B1117", "#F8FAFC", "#111820", "rgba(255, 255, 255, 0.15)", "#1A222C", "☀️", "#1A222C", "#F8FAFC", "none"
else:
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#F8FAFC", "#0F172A", "#FFFFFF", "rgba(0, 0, 0, 0.25)", "#E2E8F0", "🌙", "#FFFFFF", "#000000", "4px groove white"

upload_hint = "WAV or MP3 format • Min 1 Min, Max 20 Mins"
css_code = app_css(bg, text, card_bg, border, input_bg, browse_bg, browse_text, layout_border, upload_hint)
st.markdown(css_code, unsafe_allow_html=True)

st.button(icon, type="tertiary", on_click=toggle_theme)

st.markdown("<div class='main-title'>NEUROVOICE AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>AI-POWERED NEUROLOGICAL ANALYSIS SYSTEM (ENGLISH)</div>", unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1], gap="large")

with col_right:
    with st.container(border=True):
        st.markdown("<h5 style='font-size:0.9rem; color:#14b8a6;'>🌍 TARGET LANGUAGE MODELS</h5>", unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1:
            st.button("🇺🇸 English", type="primary", use_container_width=True)
            if st.button("🇰🇷 Korean", type="secondary", use_container_width=True): st.switch_page("pages/korean.py")
        with l2:
            if st.button("🇪🇸 Spanish", type="secondary", use_container_width=True): st.switch_page("pages/spanish.py")
            if st.button("🇨🇳 Mandarin", type="secondary", use_container_width=True): st.switch_page("pages/mandarin.py")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h5 style='font-size:0.9rem; color:#14b8a6;'>📚 ENGLISH MODULES</h5>", unsafe_allow_html=True)
        if st.button("🖼️ Cookie (Picture)", type="secondary", use_container_width=True): st.switch_page("app.py")
        if st.button("⏱️ Fluency (Words)", type="secondary", use_container_width=True): st.switch_page("pages/fluency.py")
        if st.button("📖 Recall (Story)", type="secondary", use_container_width=True): st.switch_page("pages/recall.py")
        st.button("🧩 Sentence (Syntax)", type="primary", use_container_width=True) # Aktif Sayfa

with col_left:
    with st.container(border=True):
        st.markdown("<h5 style='font-size:0.9rem; color:#14b8a6;'>⚙️ Patient Data</h5>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: hasta_yas = st.number_input("Patient Age", min_value=20, max_value=100, value=65, step=1)
        with c2: hasta_cinsiyet = st.selectbox("Gender", ["Female", "Male", "Other"])

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Sentence Task**")
        st.caption("Instructions: Read the provided sentences aloud clearly, or construct a meaningful sentence using a given set of words. Target: Tests grammatical structure, syntactic complexity, and articulation clarity.")
        st.markdown("<hr>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["☁️ Upload Audio", "🎤 Record Live"])

        audio_file = None
        with tab1:
            uploaded = st.file_uploader("Upload Patient's Voice", type=['wav', 'mp3'], label_visibility="visible")
            if uploaded: audio_file = uploaded

        with tab2:
            recorded = st.audio_input("Record Patient's Voice (Min 1 Min - Max 20 Mins)", label_visibility="visible")
            if recorded: audio_file = recorded

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        initiate = st.button("⚡ INITIATE ANALYSIS", type="primary", use_container_width=True)

        if initiate:
            if audio_file is None:
                st.error("⚠️ Please upload or record an audio file first.")
            else:
                st.session_state.audio_bytes = audio_file.getvalue()
                dosya_adi = getattr(audio_file, "name", "recorded.wav")
                st.session_state.audio_ext = ".wav" if dosya_adi.endswith('.wav') else ".mp3"
                st.session_state.patient_age = hasta_yas
                st.session_state.patient_gender = hasta_cinsiyet

                # SENTENCE yükleme ekranına gidiyor!
                st.switch_page("pages/loading_sentence.py")