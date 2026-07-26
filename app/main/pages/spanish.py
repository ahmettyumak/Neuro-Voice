import streamlit as st
import time

# 🌟 İSPANYOLCA ÖZEL CSS FONKSİYONUMUZU İÇERİ AKTARIYORUZ
from style.s_css import spanish_class_css

st.set_page_config(page_title="Neurovoice AI - Spanish", page_icon="🌍", layout="wide")

# ==========================================
# 🌗 STATE HAFIZASI (TEMA VE DİL)
# ==========================================
if 'theme' not in st.session_state: st.session_state.theme = "dark"
if 'page_lang' not in st.session_state: st.session_state.page_lang = "es"  # Varsayılan dil İspanyolca


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


def toggle_lang():
    st.session_state.page_lang = "en" if st.session_state.page_lang == "es" else "es"


# Çeviri Yardımcısı (Translation Helper)
def t(es_text, en_text):
    return es_text if st.session_state.page_lang == "es" else en_text


# Tema Renklerini Kesin Olarak Belirle
if st.session_state.theme == "dark":
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#0B1117", "#F8FAFC", "#111820", "rgba(255, 255, 255, 0.15)", "#1A222C", "☀️", "#1A222C", "#F8FAFC", "none"
else:
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#F8FAFC", "#0F172A", "#FFFFFF", "rgba(0, 0, 0, 0.25)", "#E2E8F0", "🌙", "#FFFFFF", "#000000", "4px groove white"

# ==========================================
# 🎯 DİNAMİK UPLOAD METNİ
# ==========================================
upload_hint = t("Formato WAV o MP3 • Mín. 1 Min, Máx. 20 Minutos", "WAV or MP3 format • Min 1 Min, Max 20 Mins")

# ==========================================
# 🚀 CSS'İ ÇAĞIR VE UYGULA
# ==========================================
css_code = spanish_class_css(bg, text, card_bg, border, input_bg, browse_bg, browse_text, layout_border, upload_hint)
st.markdown(css_code, unsafe_allow_html=True)

# Yüzen Tema Butonu
st.button(icon, type="tertiary", on_click=toggle_theme)

# ==========================================
# 🌟 ÜST BAR: GERİ DÖN VE DİL DEĞİŞTİR BUTONLARI
# ==========================================
top_col1, top_col2, top_col3 = st.columns([1.5, 5, 1.5])
with top_col1:
    if st.button("⬅️ " + t("Volver al Inicio", "Back to Home"), type="secondary", use_container_width=True):
        st.switch_page("app.py")
with top_col3:
    if st.button("🇬🇧 English" if st.session_state.page_lang == "es" else "🇪🇸 Español", type="primary",
                 use_container_width=True):
        toggle_lang()
        st.rerun()

# ==========================================
# 🧠 ANA İÇERİK (DİNAMİK ÇEVİRİ İLE)
# ==========================================
st.markdown("<div class='main-title'>NEUROVOICE AI</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='sub-title'>{t('SISTEMA DE ANÁLISIS NEUROLÓGICO CON IA (ESPAÑOL)', 'AI-POWERED NEUROLOGICAL ANALYSIS SYSTEM (SPANISH)')}</div>",
    unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1], gap="large")

with col_right:
    with st.container(border=True):
        st.markdown(
            f"<h5 style='font-size:0.9rem; color:#14b8a6;'>🌍 {t('MODELOS DE IDIOMA DESTINO', 'TARGET LANGUAGE MODELS')}</h5>",
            unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1:
            if st.button("🇺🇸 English", type="secondary", use_container_width=True): st.switch_page("app.py")
            if st.button("🇰🇷 Korean", type="secondary", use_container_width=True): st.switch_page("pages/korean.py")
        with l2:
            st.button("🇪🇸 Spanish", type="primary", use_container_width=True)  # Aktif Sayfa
            if st.button("🇨🇳 Mandarin", type="secondary", use_container_width=True): st.switch_page("pages/mandarin.py")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            f"<h5 style='font-size:0.9rem; color:#14b8a6;'>📋 {t('Detalles de la Tarea de Análisis', 'Analysis Task Details')}</h5>",
            unsafe_allow_html=True)
        st.markdown(t("**Modelo Maestro en Español**", "**Spanish Master AI Model**"))

        st.caption(
            t("Evalúa el deterioro cognitivo general utilizando marcadores lingüísticos, procesamiento de lenguaje natural (NLP) y acústicos profundos.",
              "Evaluates overall cognitive decline using deep linguistic, NLP, and acoustic markers."))

        st.info(
            t("📖 **Instrucciones:** Lea el texto en voz alta y clara. Luego, relate la historia con sus propias palabras. \n\n*Objetivo: Evalúa la fluidez, la articulación y la memoria semántica.*",
              "📖 **Instructions:** Read the text aloud and clearly. Then, retell the story in your own words. \n\n*Target: Evaluates fluency, articulation, and semantic memory.*"))

with col_left:
    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>⚙️ {t('Datos del Paciente', 'Patient Data')}</h5>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            hasta_yas = st.number_input(t("Edad del Paciente", "Patient Age"), min_value=20, max_value=100, value=65,
                                        step=1)
        with c2:
            gender_options = ["Mujer", "Hombre", "Otro"] if st.session_state.page_lang == "es" else ["Female", "Male",
                                                                                                     "Other"]
            hasta_cinsiyet = st.selectbox(t("Género", "Gender"), gender_options)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(t("**Grabación Clínica**", "**Clinical Recording**"))
        st.markdown("<hr>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("☁️ Subir Archivo", "☁️ Upload File"), t("🎤 Grabar Voz", "🎤 Record Audio")])

        audio_file = None
        with tab1:
            uploaded = st.file_uploader(t("Sube la voz del paciente", "Upload Patient's Voice"), type=['wav', 'mp3'],
                                        label_visibility="visible")
            if uploaded: audio_file = uploaded

        with tab2:
            recorded = st.audio_input(t("Grabar voz del paciente (Mín. 1 Min - Máx. 20 Min)",
                                        "Record Patient's Voice (Min 1 Min - Max 20 Mins)"), label_visibility="visible")
            if recorded: audio_file = recorded

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="btn-initiate">', unsafe_allow_html=True)
        initiate = st.button(t("⚡ INICIAR ANÁLISIS", "⚡ INITIATE ANALYSIS"), type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if initiate:
            if audio_file is None:
                st.error(t("⚠️ Por favor, suba o grabe un archivo de audio primero.",
                           "⚠️ Please upload or record an audio file first."))
            else:
                # 🎯 AKTİF DOSYA BOYUTU/SÜRE DENETİMİ
                file_size = getattr(audio_file, "size", len(audio_file.getvalue()))
                MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

                if file_size > MAX_SIZE_BYTES:
                    st.error(
                        t("🛑 ATENCIÓN: ¡El archivo es demasiado grande! Por favor, suba una grabación de máximo 20 minutos (25MB).",
                          "🛑 ATTENTION: File too large! Please upload a max 20-minute (25MB) recording."))
                else:
                    st.session_state.audio_bytes = audio_file.getvalue()
                    dosya_adi = getattr(audio_file, "name", "recorded.wav")
                    st.session_state.audio_ext = ".wav" if dosya_adi.endswith('.wav') else ".mp3"

                    st.session_state.patient_age = hasta_yas

                    # Backend modelinin anlayacağı İngilizce standartına çekiyoruz
                    if hasta_cinsiyet in ["Mujer", "Female"]:
                        st.session_state.patient_gender = "Female"
                    elif hasta_cinsiyet in ["Hombre", "Male"]:
                        st.session_state.patient_gender = "Male"
                    else:
                        st.session_state.patient_gender = "Other"

                    st.switch_page("pages/loading_spanish.py")