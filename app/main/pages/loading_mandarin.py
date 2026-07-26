import streamlit as st
import time
import tempfile
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_model_mandarin import analyze_mandarin_for_streamlit

st.set_page_config(page_title="Analyzing Mandarin...", page_icon="🇨🇳", layout="centered")

if 'audio_bytes' not in st.session_state or st.session_state.audio_bytes is None:
    st.switch_page("pages/mandarin.py")

lang = st.session_state.get("page_lang", "zh")
def t(zh, en): return zh if lang == "zh" else en

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;}
    .title-container { text-align: center; margin-top: 10px; margin-bottom: 50px; }
    .gradient-text { font-size: 3.5rem; font-weight: 800; background: linear-gradient(90deg, #14b8a6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .subtitle { color: #94a3b8; font-size: 1.1rem; margin-top: -5px; }
    .pulse-box { position: relative; width: 160px; height: 160px; margin: 20px auto 40px auto; display: flex; align-items: center; justify-content: center; }
    .ring { position: absolute; width: 100%; height: 100%; border-radius: 50%; border: 2px solid #14b8a6; animation: ripple 2s infinite ease-out; box-shadow: 0 0 15px rgba(20, 184, 166, 0.3); }
    .ring:nth-child(2) { animation-delay: 0.6s; } .ring:nth-child(3) { animation-delay: 1.2s; }
    .core-icon { font-size: 65px; z-index: 10; animation: float 3s ease-in-out infinite; filter: drop-shadow(0px 0px 20px rgba(20,184,166,0.6)); }
    @keyframes ripple { 0% { transform: scale(0.5); opacity: 1; } 100% { transform: scale(1.6); opacity: 0; } }
    @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-15px); } }
    .status-text { text-align: center; color: #F8FAFC; font-size: 1.4rem; font-weight: 500; margin-top: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="title-container">
        <h1 class="gradient-text">NeuroVoice AI</h1>
        <p class="subtitle">{t("中文分析模块 (Jieba NLP)", "Mandarin Analysis Module (Jieba NLP)")}</p>
    </div>
    <div class="pulse-box"><div class="ring"></div><div class="ring"></div><div class="ring"></div><div class="core-icon">🇨🇳</div></div>
""", unsafe_allow_html=True)

progress_bar = st.progress(0)
status_text = st.empty()

def update_status(text_zh, text_en, percent):
    status_text.markdown(f"<div class='status-text'>{t(text_zh, text_en)}</div>", unsafe_allow_html=True)
    progress_bar.progress(percent)

update_status("📡 提取 Jieba 语言特征...", "📡 Extracting Jieba NLP Biomarkers...", 15)
audio_ext = st.session_state.get("audio_ext", ".wav")
with tempfile.NamedTemporaryFile(delete=False, suffix=audio_ext) as tmp_file:
    tmp_file.write(st.session_state.audio_bytes)
    tmp_path = tmp_file.name
time.sleep(0.5)

update_status("🧬 运行 XGBoost AI 模型...", "🧬 Running Master XGBoost Model...", 45)
results = analyze_mandarin_for_streamlit(tmp_path)

update_status("⚖️ 计算阿尔茨海默症概率...", "⚖️ Calculating Alzheimer's Probabilities...", 85)
time.sleep(0.5)
os.remove(tmp_path)

st.session_state.analysis_results_mandarin = results
st.switch_page("pages/results_mandarin.py")