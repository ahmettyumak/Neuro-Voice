import streamlit as st
import time

# 🌟 MANDARİN (ÇİNCE) ÖZEL CSS FONKSİYONUMUZU İÇERİ AKTARIYORUZ
from style.m_css import mandarin_class_css

st.set_page_config(page_title="Neurovoice AI - Mandarin", page_icon="🇨🇳", layout="wide")

# ==========================================
# 🌗 STATE HAFIZASI (TEMA VE DİL)
# ==========================================
if 'theme' not in st.session_state: st.session_state.theme = "dark"
if 'page_lang' not in st.session_state: st.session_state.page_lang = "zh"  # Varsayılan dil Çince


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


def toggle_lang():
    st.session_state.page_lang = "en" if st.session_state.page_lang == "zh" else "zh"


# Çeviri Yardımcısı (Translation Helper)
def t(zh_text, en_text):
    return zh_text if st.session_state.page_lang == "zh" else en_text


# Tema Renklerini Kesin Olarak Belirle
if st.session_state.theme == "dark":
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#0B1117", "#F8FAFC", "#111820", "rgba(255, 255, 255, 0.15)", "#1A222C", "☀️", "#1A222C", "#F8FAFC", "none"
else:
    bg, text, card_bg, border, input_bg, icon, browse_bg, browse_text, layout_border = "#F8FAFC", "#0F172A", "#FFFFFF", "rgba(0, 0, 0, 0.25)", "#E2E8F0", "🌙", "#FFFFFF", "#000000", "4px groove white"

# ==========================================
# 🎯 DİNAMİK UPLOAD METNİ
# ==========================================
upload_hint = t("WAV 或 MP3 格式 • 至少 1 分钟，最多 20 分钟", "WAV or MP3 format • Min 1 Min, Max 20 Mins")

# ==========================================
# 🚀 CSS'İ ÇAĞIR VE UYGULA
# ==========================================
css_code = mandarin_class_css(bg, text, card_bg, border, input_bg, browse_bg, browse_text, layout_border, upload_hint)
st.markdown(css_code, unsafe_allow_html=True)

# Yüzen Tema Butonu
st.button(icon, type="tertiary", on_click=toggle_theme)

# ==========================================
# 🌟 ÜST BAR: GERİ DÖN VE DİL DEĞİŞTİR BUTONLARI
# ==========================================
top_col1, top_col2, top_col3 = st.columns([1.5, 5, 1.5])
with top_col1:
    if st.button("⬅️ " + t("返回首页", "Back to Home"), type="secondary", use_container_width=True):
        st.switch_page("app.py")
with top_col3:
    if st.button("🇬🇧 English" if st.session_state.page_lang == "zh" else "🇨🇳 中文", type="primary",
                 use_container_width=True):
        toggle_lang()
        st.rerun()

# ==========================================
# 🧠 ANA İÇERİK (DİNAMİK ÇEVİRİ İLE)
# ==========================================
st.markdown("<div class='main-title'>NEUROVOICE AI</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='sub-title'>{t('人工智能神经分析系统 (中文)', 'AI-POWERED NEUROLOGICAL ANALYSIS SYSTEM (MANDARIN)')}</div>",
    unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1], gap="large")

with col_right:
    with st.container(border=True):
        st.markdown(
            f"<h5 style='font-size:0.9rem; color:#14b8a6;'>🌍 {t('目标语言模型', 'TARGET LANGUAGE MODELS')}</h5>",
            unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1:
            if st.button("🇺🇸 English", type="secondary", use_container_width=True): st.switch_page("app.py")
            if st.button("🇰🇷 Korean", type="secondary", use_container_width=True): st.switch_page("pages/korean.py")
        with l2:
            if st.button("🇪🇸 Spanish", type="secondary", use_container_width=True): st.switch_page("pages/spanish.py")
            st.button("🇨🇳 Mandarin", type="primary", use_container_width=True)  # Aktif Sayfa

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>📋 {t('分析任务详情', 'Analysis Task Details')}</h5>",
                    unsafe_allow_html=True)
        st.markdown(t("**中文主控 AI 模型**", "**Mandarin Master AI Model**"))

        st.caption(t("评估整体认知能力下降（MCI/Alzheimer）。", "Evaluates overall cognitive decline (MCI/Alzheimer)."))

        st.info(
            t("🖼️ **看图说话任务说明:** 请观察屏幕上的图片（例如：爸爸熨衣服或公园场景）。请描述图片中发生的事情。\n\n*评估目标：测试视觉信息处理和自发性言语。*",
              "🖼️ **Task Instructions:** Please look at the picture (e.g., dad ironing or park scene). Describe the events and actions happening in the picture. \n\n*Target: Tests visual information processing and spontaneous speech.*"))

with col_left:
    with st.container(border=True):
        st.markdown(f"<h5 style='font-size:0.9rem; color:#14b8a6;'>⚙️ {t('患者数据', 'Patient Data')}</h5>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            hasta_yas = st.number_input(t("患者年龄", "Patient Age"), min_value=20, max_value=100, value=65, step=1)
        with c2:
            gender_options = ["女性", "男性", "其他"] if st.session_state.page_lang == "zh" else ["Female", "Male",
                                                                                                  "Other"]
            hasta_cinsiyet = st.selectbox(t("性别", "Gender"), gender_options)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(t("**临床录音**", "**Clinical Recording**"))
        st.markdown("<hr>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("☁️ 上传文件", "☁️ Upload File"), t("🎤 录制声音", "🎤 Record Audio")])

        audio_file = None
        with tab1:
            uploaded = st.file_uploader(t("上传患者的声音", "Upload Patient's Voice"), type=['wav', 'mp3'],
                                        label_visibility="visible")
            if uploaded: audio_file = uploaded

        with tab2:
            recorded = st.audio_input(
                t("录制患者声音 (至少 1 分钟，最多 20 分钟)", "Record Patient's Voice (Min 1 Min - Max 20 Mins)"),
                label_visibility="visible")
            if recorded: audio_file = recorded

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="btn-initiate">', unsafe_allow_html=True)
        initiate = st.button(t("⚡ 开始分析 (INITIATE ANALYSIS)", "⚡ INITIATE ANALYSIS"), type="primary",
                             use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if initiate:
            if audio_file is None:
                st.error(t("⚠️ 请先上传或录制音频。", "⚠️ Please upload or record an audio file first."))
            else:
                # 🎯 AKTİF DOSYA BOYUTU/SÜRE DENETİMİ
                file_size = getattr(audio_file, "size", len(audio_file.getvalue()))
                MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

                if file_size > MAX_SIZE_BYTES:
                    st.error(t("🛑 注意：录音文件太大！请上传最多 20 分钟（25MB）的录音。",
                               "🛑 ATTENTION: File too large! Please upload a max 20-minute (25MB) recording."))
                else:
                    st.session_state.audio_bytes = audio_file.getvalue()
                    dosya_adi = getattr(audio_file, "name", "recorded.wav")
                    st.session_state.audio_ext = ".wav" if dosya_adi.endswith('.wav') else ".mp3"

                    st.session_state.patient_age = hasta_yas

                    # Çinceden İngilizceye cinsiyet çevirisi (Backend'in hatasız çalışması için)
                    if hasta_cinsiyet in ["女性", "Female"]:
                        st.session_state.patient_gender = "Female"
                    elif hasta_cinsiyet in ["男性", "Male"]:
                        st.session_state.patient_gender = "Male"
                    else:
                        st.session_state.patient_gender = "Other"

                    st.switch_page("pages/loading_mandarin.py")