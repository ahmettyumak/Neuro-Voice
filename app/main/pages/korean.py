import streamlit as st
import time

# 🌟 KORECE ÖZEL CSS FONKSİYONUMUZU İÇERİ AKTARIYORUZ
from style.k_css import korean_class_css

st.set_page_config(page_title="Neurovoice AI - Korean", page_icon="🇰🇷", layout="wide")

# ==========================================
# 🌗 STATE HAFIZASI (TEMA VE DİL)
# ==========================================
if 'theme' not in st.session_state: st.session_state.theme = "dark"
if 'page_lang' not in st.session_state: st.session_state.page_lang = "ko"  # Varsayılan dil Korece


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


def toggle_lang():
    st.session_state.page_lang = "en" if st.session_state.page_lang == "ko" else "ko"


# Çeviri Yardımcısı (Translation Helper)
def t(ko_text, en_text):
    return ko_text if st.session_state.page_lang == "ko" else en_text


# Tema Renklerini Kesin Olarak Belirle
if st.session_state.theme == "dark":
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#0B1117", "#F8FAFC", "#111820", "rgba(255, 255, 255, 0.15)", "#1A222C", "☀️", "#1A222C", "#F8FAFC", "none"
else:
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#F8FAFC", "#0F172A", "#FFFFFF", "rgba(0, 0, 0, 0.25)", "#E2E8F0", "🌙", "#FFFFFF", "#000000", "4px groove white"

# ==========================================
# 🎯 DİNAMİK UPLOAD METNİ
# ==========================================
upload_hint = t("WAV 또는 MP3 형식 • 최소 1분, 최대 20분", "WAV or MP3 format • Min 1 Min, Max 20 Mins")

# ==========================================
# 🚀 CSS'İ ÇAĞIR VE UYGULA
# ==========================================
css_code = korean_class_css(bg, text, card_bg, border, input_bg, browse_bg, browse_text, layout_border, upload_hint)
st.markdown(css_code, unsafe_allow_html=True)

# Yüzen Tema Butonu
st.button(icon, type="tertiary", on_click=toggle_theme)

# ==========================================
# 🌟 ÜST BAR: GERİ DÖN VE DİL DEĞİŞTİR BUTONLARI
# ==========================================
top_col1, top_col2, top_col3 = st.columns([1.5, 5, 1.5])
with top_col1:
    if st.button("⬅️ " + t("홈으로 돌아가기", "Back to Home"), type="secondary", use_container_width=True):
        st.switch_page("app.py")
with top_col3:
    if st.button("🇬🇧 English" if st.session_state.page_lang == "ko" else "🇰🇷 한국어", type="primary",
                 use_container_width=True):
        toggle_lang()
        st.rerun()

# ==========================================
# 🧠 ANA İÇERİK (DİNAMİK ÇEVİRİ İLE)
# ==========================================
st.markdown("<div class='main-title'>NEUROVOICE AI</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='sub-title'>{t('AI 기반 신경 분석 시스템 (한국어)', 'AI-POWERED NEUROLOGICAL ANALYSIS SYSTEM (KOREAN)')}</div>",
    unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1], gap="large")

with col_right:
    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>🌍 {t('대상 언어 모델', 'TARGET LANGUAGE MODELS')}</h5>",
                    unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1:
            if st.button("🇺🇸 English", type="secondary", use_container_width=True): st.switch_page("app.py")
            st.button("🇰🇷 Korean", type="primary", use_container_width=True)  # Aktif Sayfa
        with l2:
            if st.button("🇪🇸 Spanish", type="secondary", use_container_width=True): st.switch_page("pages/spanish.py")
            if st.button("🇨🇳 Mandarin", type="secondary", use_container_width=True): st.switch_page("pages/mandarin.py")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>📋 {t('분석 작업 세부정보', 'Analysis Task Details')}</h5>",
                    unsafe_allow_html=True)
        st.markdown(t("**한국어 마스터 AI 모델**", "**Korean Master AI Model**"))

        st.caption(t("깊은 언어적, NLP 및 음향 마커를 사용하여 전반적인 인지 저하를 평가합니다.",
                     "Evaluates overall cognitive decline using deep linguistic, NLP, and acoustic markers."))

        st.info(
            t("🗣️ **과제 지시사항:** 최근 재미있게 본 드라마나 책, 오늘 하루의 일과, 또는 과거의 중요한 기억에 대해 편안하고 자연스럽게 이야기해 주세요. \n\n*평가 목표: 자연스러운 발화 흐름, 기억 인출 및 일상적인 의사소통 능력을 평가합니다.*",
              "🗣️ **Task Instructions:** Please talk comfortably and naturally about a recent drama or book, your daily routine, or an important past memory. \n\n*Target: Evaluates natural speech flow, memory retrieval, and daily communication skills.*"))

with col_left:
    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>⚙️ {t('환자 데이터', 'Patient Data')}</h5>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            hasta_yas = st.number_input(t("환자 나이", "Patient Age"), min_value=20, max_value=100, value=65, step=1)
        with c2:
            gender_options = ["여성", "남성", "기타"] if st.session_state.page_lang == "ko" else ["Female", "Male", "Other"]
            hasta_cinsiyet = st.selectbox(t("성별", "Gender"), gender_options)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(t("**임상 녹음**", "**Clinical Recording**"))
        st.markdown("<hr>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("☁️ 파일 업로드", "☁️ Upload File"), t("🎤 음성 녹음", "🎤 Record Audio")])

        audio_file = None
        with tab1:
            uploaded = st.file_uploader(t("환자의 목소리를 업로드하세요", "Upload Patient's Voice"), type=['wav', 'mp3'],
                                        label_visibility="visible")
            if uploaded: audio_file = uploaded

        with tab2:
            recorded = st.audio_input(
                t("환자의 목소리를 녹음하세요 (최소 1분 - 최대 20분)", "Record Patient's Voice (Min 1 Min - Max 20 Mins)"),
                label_visibility="visible")
            if recorded: audio_file = recorded

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="btn-initiate">', unsafe_allow_html=True)
        initiate = st.button(t("⚡ 분석 시작 (INITIATE ANALYSIS)", "⚡ INITIATE ANALYSIS"), type="primary",
                             use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if initiate:
            if audio_file is None:
                st.error(t("⚠️ 먼저 오디오 파일을 업로드하거나 녹음해주세요.", "⚠️ Please upload or record an audio file first."))
            else:
                # 🎯 AKTİF DOSYA BOYUTU/SÜRE DENETİMİ
                file_size = getattr(audio_file, "size", len(audio_file.getvalue()))
                MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

                if file_size > MAX_SIZE_BYTES:
                    st.error(t("🛑 주의: 녹음 파일이 너무 깁니다! 최대 20분의 녹음 파일을 업로드해주세요.",
                               "🛑 ATTENTION: File too large! Please upload a max 20-minute (25MB) recording."))
                else:
                    st.session_state.audio_bytes = audio_file.getvalue()
                    dosya_adi = getattr(audio_file, "name", "recorded.wav")
                    st.session_state.audio_ext = ".wav" if dosya_adi.endswith('.wav') else ".mp3"

                    st.session_state.patient_age = hasta_yas

                    # Koreceden İngilizceye cinsiyet çevirisi (Backend hatasız çalışsın diye)
                    if hasta_cinsiyet in ["여성", "Female"]:
                        st.session_state.patient_gender = "Female"
                    elif hasta_cinsiyet in ["남성", "Male"]:
                        st.session_state.patient_gender = "Male"
                    else:
                        st.session_state.patient_gender = "Other"

                    st.switch_page("pages/loading_korean.py")