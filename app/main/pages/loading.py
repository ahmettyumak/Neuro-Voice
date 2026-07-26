import streamlit as st
import time
import tempfile
import os
import sys

# Ana dizindeki ai_model.py dosyasına erişmek için yolu ekliyoruz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_model import analyze_for_streamlit

st.set_page_config(page_title="Analyzing Patient Data...", page_icon="🧠", layout="centered")

# Eğer direkt bu sayfaya girilmeye çalışılırsa ana sayfaya geri at
if 'audio_bytes' not in st.session_state or st.session_state.audio_bytes is None:
    st.switch_page("app.py")

# ==========================================
# GELİŞMİŞ CSS TASARIMI (NEURAL RADAR EFEKTİ)
# ==========================================
st.markdown("""
    <style>
    /* Streamlit varsayılan üst menüleri gizle */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}

    /* Ana Başlık (Gradient Text) */
    .title-container {
        text-align: center;
        margin-top: 10px;
        margin-bottom: 50px;
    }
    .gradient-text {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #14b8a6, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: 2px;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: -5px;
        font-weight: 300;
        letter-spacing: 1px;
    }

    /* Radar / Beyin Dalgası Animasyonu */
    .pulse-box {
        position: relative;
        width: 160px;
        height: 160px;
        margin: 20px auto 40px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid #14b8a6;
        animation: ripple 2s infinite ease-out;
        box-shadow: 0 0 15px rgba(20, 184, 166, 0.3);
    }
    /* Dalgaların sırayla çıkması için gecikmeler */
    .ring:nth-child(2) { animation-delay: 0.6s; }
    .ring:nth-child(3) { animation-delay: 1.2s; }

    .core-icon {
        font-size: 65px;
        z-index: 10;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0px 0px 20px rgba(20,184,166,0.6));
    }

    @keyframes ripple {
        0% { transform: scale(0.5); opacity: 1; }
        100% { transform: scale(1.6); opacity: 0; }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
    }

    /* Durum Metni */
    .status-text {
        text-align: center;
        color: #F8FAFC;
        font-size: 1.4rem;
        font-weight: 500;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    </style>

    <div class="title-container">
        <h1 class="gradient-text">NeuroVoice AI</h1>
        <p class="subtitle">Advanced Clinical Acoustic & Semantic Analysis</p>
    </div>

    <div class="pulse-box">
        <div class="ring"></div>
        <div class="ring"></div>
        <div class="ring"></div>
        <div class="core-icon">🧠</div>
    </div>
""", unsafe_allow_html=True)

progress_bar = st.progress(0)
status_text = st.empty()


# İşlem aşamalarını daha havalı göstermek için küçük bir fonksiyon
def update_status(text, percent):
    status_text.markdown(f"<div class='status-text'>{text}</div>", unsafe_allow_html=True)
    progress_bar.progress(percent)


# 1. Aşama
update_status("📡 Extracting Acoustic Biomarkers...", 15)

audio_ext = st.session_state.get("audio_ext", ".wav")
with tempfile.NamedTemporaryFile(delete=False, suffix=audio_ext) as tmp_file:
    tmp_file.write(st.session_state.audio_bytes)
    tmp_path = tmp_file.name

time.sleep(0.5)  # Efektin görünmesi için kısa bekleme

# 2. Aşama
update_status("🧬 Running NLP & Deep Learning Models...", 45)

# Backend fonksiyonunu çağırıyoruz
results = analyze_for_streamlit(tmp_path)

# 3. Aşama
update_status("⚖️ Calculating Dementia Risk Probabilities...", 85)
time.sleep(0.5)

update_status("✅ Finalizing Report...", 100)
time.sleep(0.5)

os.remove(tmp_path)  # Temp dosyayı sil

# Sonuçları kaydet ve Sonuç sayfasına geç
st.session_state.analysis_results = results
st.switch_page("pages/results.py")