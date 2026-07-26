# =============================================================================
# 1. KÜTÜPHANELER VE İÇE AKTARMALAR
# =============================================================================
import os
import re
import site
import sys
import logging
import math
import warnings
import gc
from collections import Counter

import joblib
import librosa
import numpy as np
import pandas as pd
import parselmouth
import onnxruntime as rt
from faster_whisper import WhisperModel
from parselmouth.praat import call


# =============================================================================
# 2. HAFIZA YÖNETİMİ VE NVIDIA AYARLARI
# =============================================================================
def force_load_nvidia_dlls():
    paths = getattr(site, 'getsitepackages', lambda: [])()
    paths.append(site.getusersitepackages())
    paths.extend(sys.path)
    for p in set(paths):
        cublas_path = os.path.join(p, "nvidia", "cublas", "bin")
        cudnn_path = os.path.join(p, "nvidia", "cudnn", "bin")
        if os.path.exists(cublas_path):
            try:
                os.add_dll_directory(cublas_path)
            except:
                pass
            os.environ["PATH"] = cublas_path + os.pathsep + os.environ.get("PATH", "")
        if os.path.exists(cudnn_path):
            try:
                os.add_dll_directory(cudnn_path)
            except:
                pass
            os.environ["PATH"] = cudnn_path + os.pathsep + os.environ.get("PATH", "")


force_load_nvidia_dlls()
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def clear_ai_memory():
    global whisper_model

    if whisper_model is not None:
        del whisper_model
        whisper_model = None

    gc.collect()

    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except ImportError:
        pass

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi! (Spanish Modülü)")


# =============================================================================
# 3. SABİTLER VE YAPAY ZEKA MODELLERİ
# =============================================================================
ONNX_MODEL_FILE = "alzheimer_es_xgboost_model.onnx"
SCALER_FILE = "alzheimer_es_scaler.pkl"
COLUMNS_FILE = "alzheimer_es_columns.pkl"
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 600

SEARCH_TERMS = {
    "Dolgu_Kelimeleri": ["eh", "este", "pues", "bueno", "mhm", "ah", "mmm", "o sea", "sabes", "digamos", "vale",
                         "a ver", "digo", "tipo", "claro", "nada"],
    "Bos_Kelimeler": ["cosa", "cosas", "algo", "eso", "esto", "aquello", "asunto", "tema", "cuestión", "chisme",
                      "cacharro", "trasto", "aparato"],
}

VALIDATION_KEYWORDS = [
    "niño", "niña", "mujer", "madre", "agua", "galleta", "cayendo", "cocina",
    "ventana", "foto", "imagen", "historia", "recordar", "memoria", "hola",
    "buenos", "días", "gracias", "bien", "mal", "sí", "no", "quijote", "mancha", "lugar"
]

whisper_model = None


def load_ai_models():
    global whisper_model
    if whisper_model is None:
        logger.info("🧠 Whisper GPU (Spanish Task) starting...")
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")


# =============================================================================
# 4 & 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION)
# =============================================================================
def extract_test_features(file_path):
    load_ai_models()
    features = {}

    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=MAX_AUDIO_DURATION)
    if len(y) == 0: return None, "AUDIO EMPTY / AUDIO VACÍO: The audio file is empty."

    segments, info = whisper_model.transcribe(y, beam_size=1, vad_filter=True, word_timestamps=True, language="es")
    words_data, full_text_list = [], []

    for segment in segments:
        for word in segment.words:
            words_data.append(word)
            full_text_list.append(re.sub(r'[^\w\s]', '', word.word.lower().strip()))

    full_text = " ".join(full_text_list).strip()
    word_count = len(words_data)

    if word_count < 5:
        return None, "AUDIO TOO SHORT / AUDIO DEMASIADO CORTO: Not enough Spanish speech detected."

    match_count = sum(1 for keyword in VALIDATION_KEYWORDS if keyword in full_text)
    filler_match = sum(1 for filler in SEARCH_TERMS["Dolgu_Kelimeleri"] if filler in full_text)

    # Güvenlik kapısı
    if (match_count + filler_match) < 0:
        return None, "INVALID TASK / TAREA INVÁLIDA: This does not appear to be a clinical interview in Spanish."

    features["Kelime_Sayisi"] = word_count
    features["TTR_Orani"] = len(set(full_text_list)) / word_count if word_count > 0 else 0

    word_counts = Counter(full_text_list)
    features["Sozcuk_Entropisi"] = sum(
        [- (count / word_count) * math.log2(count / word_count) for count in word_counts.values()])

    kullanilan_dolgular, kullanilan_bos_kelimeler = [], []
    for category, keywords in SEARCH_TERMS.items():
        total_count = 0
        for w in full_text_list:
            if w in keywords:
                total_count += 1
                if category == "Dolgu_Kelimeleri": kullanilan_dolgular.append(w)
                if category == "Bos_Kelimeler": kullanilan_bos_kelimeler.append(w)
        features[f"Sayi_{category}"] = total_count
        features[f"Oran_{category}"] = total_count / word_count if word_count > 0 else 0

    duraksama_sayisi = 0
    uzun_duraksama_yerleri = []
    speech_duration = 0.0

    if word_count > 0:
        speech_duration = sum([w.end - w.start for w in words_data])
        for i in range(1, word_count):
            gap = words_data[i].start - words_data[i - 1].end
            if gap >= 0.5:
                duraksama_sayisi += 1
                onceki_kelime = re.sub(r'[^\w\s]', '', words_data[i - 1].word.strip())
                uzun_duraksama_yerleri.append(f"'{onceki_kelime}' ({gap:.1f}s)")

    features["Duraksama_Sayisi"] = duraksama_sayisi
    features["Duraksama_Orani"] = duraksama_sayisi / word_count if word_count > 0 else 0
    features["Sure_Konusma"] = speech_duration
    features["Konusma_Hizi"] = word_count / speech_duration if speech_duration > 0 else 0

    try:
        sound = parselmouth.Sound(np.array([y]), sampling_frequency=sr)
        pitch = sound.to_pitch()
        pulses = call([sound, pitch], "To PointProcess (cc)")
        features["Jitter_Local"] = call(pulses, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3) * 100
        features["Shimmer_Local"] = call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
        features["HNR"] = call(call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0), "Get mean", 0, 0)
    except:
        features["Jitter_Local"] = features["Shimmer_Local"] = features["HNR"] = 0

    total_duration = librosa.get_duration(y=y, sr=sr)
    features["Sure_Toplam"] = total_duration
    features["Oran_Sessizlik"] = (total_duration - speech_duration) / total_duration if total_duration > 0 else 0
    features["RMS_Enerji"] = float(np.mean(librosa.feature.rms(y=y)))

    f0, _, _ = librosa.pyin(y, fmin=50, fmax=500)
    f0 = f0[~np.isnan(f0)]
    features["Pitch_Mean"] = float(np.mean(f0)) if len(f0) > 0 else 0
    features["Pitch_Std"] = float(np.std(f0)) if len(f0) > 0 else 0

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i, val in enumerate(np.mean(mfcc, axis=1)): features[f"MFCC_Mean_{i + 1}"] = float(val)
    for i, val in enumerate(np.std(mfcc, axis=1)): features[f"MFCC_Std_{i + 1}"] = float(val)

    rapor_detaylari = {
        "hasta_metni": full_text,
        "toplam_sure": total_duration,
        "kelime_sayisi": word_count,
        "duraksama": duraksama_sayisi,
        "sozcuk_entropisi": features["Sozcuk_Entropisi"],
        "hata_yerleri": uzun_duraksama_yerleri[:5],
        "dolgular": dict(Counter(kullanilan_dolgular)),
        "bos_kelimeler": dict(Counter(kullanilan_bos_kelimeler))
    }

    return features, rapor_detaylari


# =============================================================================
# 6. YAPAY ZEKA TAHMİNİ VE STREAMLIT ÇIKTISI
# =============================================================================
def analyze_spanish_for_streamlit(audio_path):
    result = extract_test_features(audio_path)

    # Hata yakalama
    if result is None or isinstance(result[0], type(None)):
        return {"status": "error", "message": result[1] if result else "Bilinmeyen Hata"}

    features, rapor_detaylari = result
    df_patient = pd.DataFrame([features]).fillna(0)

    try:
        scaler = joblib.load(SCALER_FILE)
        expected_columns = joblib.load(COLUMNS_FILE)
        sess = rt.InferenceSession(ONNX_MODEL_FILE, providers=['CPUExecutionProvider'])
        input_name = sess.get_inputs()[0].name
    except Exception as e:
        return {"status": "error", "message": f"Spanish Model files missing: {e}"}

    for col in expected_columns:
        if col not in df_patient.columns: df_patient[col] = 0.0
    df_patient = df_patient[expected_columns]

    X_scaled = scaler.transform(df_patient).astype(np.float32)
    label_name = sess.get_outputs()[0].name
    prob_name = sess.get_outputs()[1].name if len(sess.get_outputs()) > 1 else None

    pred_onx = sess.run([label_name, prob_name], {input_name: X_scaled})

    prob_dict = pred_onx[1][0]
    if isinstance(prob_dict, dict):
        prob_hc = prob_dict.get(0, 0.0) * 100
        prob_mci = prob_dict.get(1, 0.0) * 100
        prob_ad = prob_dict.get(2, 0.0) * 100
    else:
        prob_hc = prob_dict[0] * 100
        prob_mci = prob_dict[1] * 100
        prob_ad = prob_dict[2] * 100

    final_pred = int(np.argmax([prob_hc, prob_mci, prob_ad]))

    if final_pred == 0:
        teshis, teshis_es, risk_level = "HEALTHY (Normal Cognitive Function)", "SANO (Función Cognitiva Normal)", "low"
    elif final_pred == 1:
        teshis, teshis_es, risk_level = "AT RISK (Mild Cognitive Impairment)", "RIESGO (Deterioro Cognitivo Leve)", "medium"
    else:
        teshis, teshis_es, risk_level = "HIGH RISK (Alzheimer's Disease)", "ALTO RIESGO (Enfermedad de Alzheimer)", "high"

    # 🚀 HAFIZAYI BOŞALT!
    clear_ai_memory()

    return {
        "status": "success",
        "diagnosis_en": teshis,
        "diagnosis_es": teshis_es,
        "risk_level": risk_level,
        "prob_hc": round(prob_hc, 1),
        "prob_mci": round(prob_mci, 1),
        "prob_ad": round(prob_ad, 1),
        "details": rapor_detaylari
    }