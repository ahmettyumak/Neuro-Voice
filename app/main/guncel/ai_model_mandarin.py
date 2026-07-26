# =============================================================================
# 1. KÜTÜPHANELER VE İÇE AKTARMALAR
# =============================================================================
import os
import site
import sys
import logging
import math
import warnings
import gc
from collections import Counter

import joblib
import numpy as np
import pandas as pd
import librosa
import parselmouth
import jieba
import jieba.posseg as pseg
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

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi! (Mandarin Modülü)")


# =============================================================================
# 3. SABİTLER VE YAPAY ZEKA MODELLERİ
# =============================================================================
ONNX_MODEL_FILE = "model_XGBOOST_ALL.onnx"
SCALER_FILE = "model_XGBOOST_ALL_scaler.pkl"
COLUMNS_FILE = "model_XGBOOST_ALL_columns.pkl"
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 1200
CHINESE_FILLERS = ["那个", "这个", "嗯", "啊", "就是", "然后", "呃", "哦"]

whisper_model = None


def load_ai_models():
    global whisper_model
    if whisper_model is None:
        logger.info("🧠 Whisper GPU (Mandarin) starting...")
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")


# =============================================================================
# 4 & 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION)
# =============================================================================
def extract_mandarin_features(file_path):
    load_ai_models()
    features = {}

    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=MAX_AUDIO_DURATION)
    segments, _ = whisper_model.transcribe(y, beam_size=1, vad_filter=True, word_timestamps=True, language="zh")

    words_data = []
    full_text_list = []
    for segment in segments:
        for word in segment.words:
            words_data.append(word)
            full_text_list.append(word.word.strip())

    full_text = "".join(full_text_list)
    if len(full_text) < 5:
        return None, "AUDIO TOO SHORT / 音频太短: Not enough Chinese speech detected."

    words = list(jieba.cut(full_text))
    word_count = len(words)
    char_count = len(full_text)

    features["Kelime_Sayisi"] = word_count
    features["TTR_Orani"] = len(set(words)) / word_count if word_count > 0 else 0

    word_counts = Counter(words)
    features["Sozcuk_Entropisi"] = sum(
        [- (count / word_count) * math.log2(count / word_count) for count in word_counts.values()])

    pos_tags = pseg.cut(full_text)
    noun_count, pronoun_count, verb_count = 0, 0, 0
    for pair in pos_tags:
        if pair.flag.startswith('n'):
            noun_count += 1
        elif pair.flag.startswith('r'):
            pronoun_count += 1
        elif pair.flag.startswith('v'):
            verb_count += 1

    features["Zamir_Isim_Orani"] = pronoun_count / noun_count if noun_count > 0 else pronoun_count
    features["Fiil_Isim_Orani"] = verb_count / noun_count if noun_count > 0 else verb_count

    filler_count = sum(full_text.count(filler) for filler in CHINESE_FILLERS)
    features["Dolgu_Kelime_Orani"] = filler_count / word_count if word_count > 0 else 0

    duraksama_sayisi, kisa_takilma_sayisi = 0, 0
    uzun_duraksama_yerleri, kullanilan_dolgular = [], []
    speech_duration = sum([w.end - w.start for w in words_data]) if len(words_data) > 0 else 0

    if len(words_data) > 0:
        for i in range(1, len(words_data)):
            bosluk = words_data[i].start - words_data[i - 1].end
            if bosluk >= 0.5:
                duraksama_sayisi += 1
                uzun_duraksama_yerleri.append(f"'{words_data[i - 1].word.strip()}' ({bosluk:.1f}s)")
            elif 0.2 <= bosluk < 0.5:
                kisa_takilma_sayisi += 1
            if words_data[i].word.strip() in CHINESE_FILLERS: kullanilan_dolgular.append(words_data[i].word.strip())

    features["Duraksama_Sayisi"] = duraksama_sayisi
    features["Duraksama_Orani"] = duraksama_sayisi / word_count if word_count > 0 else 0
    features["Karakter_Hizi_CPS"] = char_count / speech_duration if speech_duration > 0 else 0

    try:
        sound = parselmouth.Sound(np.array([y]), sampling_frequency=sr)
        pitch = sound.to_pitch()
        pulses = call([sound, pitch], "To PointProcess (cc)")
        features["Jitter_Local"] = call(pulses, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3) * 100
        features["Shimmer_Local"] = call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
        features["HNR"] = call(call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0), "Get mean", 0, 0)
        formant = call(sound, "To Formant (burg)", 0.0, 5, 5500, 0.025, 50)
        features["Tini_F1_Mean"] = call(formant, "Get mean", 1, 0, 0, "Hertz")
        features["Tini_F2_Mean"] = call(formant, "Get mean", 2, 0, 0, "Hertz")
    except:
        features["Jitter_Local"] = features["Shimmer_Local"] = features["HNR"] = 0
        features["Tini_F1_Mean"] = features["Tini_F2_Mean"] = 0

    total_duration = len(y) / sr
    features["Oran_Sessizlik"] = (total_duration - speech_duration) / total_duration if total_duration > 0 else 0

    rapor_detaylari = {
        "hasta_metni": full_text,
        "toplam_sure": total_duration,
        "kelime_sayisi": word_count,
        "karakter_sayisi": char_count,
        "duraksama": duraksama_sayisi,
        "anomi": features["Zamir_Isim_Orani"],
        "sozcuk_entropisi": features["Sozcuk_Entropisi"],
        "hata_yerleri": uzun_duraksama_yerleri[:5],
        "dolgular": dict(Counter(kullanilan_dolgular))
    }
    return features, rapor_detaylari


# =============================================================================
# 6. YAPAY ZEKA TAHMİNİ VE STREAMLIT ÇIKTISI
# =============================================================================
def analyze_mandarin_for_streamlit(audio_path):
    result = extract_mandarin_features(audio_path)

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
        return {"status": "error", "message": f"Mandarin Model files missing: {e}"}

    for col in expected_columns:
        if col not in df_patient.columns: df_patient[col] = 0.0
    df_patient = df_patient[expected_columns]

    X_scaled = scaler.transform(df_patient).astype(np.float32)
    label_name = sess.get_outputs()[0].name
    prob_name = sess.get_outputs()[1].name if len(sess.get_outputs()) > 1 else None

    pred_onx = sess.run([label_name, prob_name], {input_name: X_scaled})

    prob_dict = pred_onx[1][0]
    if isinstance(prob_dict, dict):
        prob_mci = prob_dict.get(1, 0.0) * 100
        prob_hc = prob_dict.get(0, 1.0) * 100
    else:
        prob_mci = prob_dict[1] * 100
        prob_hc = prob_dict[0] * 100

    if prob_mci < 40.0:
        teshis, teshis_zh, risk_level = "HEALTHY (Normal Cognitive Function)", "健康 (认知功能正常)", "low"
    elif 40.0 <= prob_mci < 60.0:
        teshis, teshis_zh, risk_level = "SUSPECTED MCI (Borderline Decline)", "疑似 MCI (边缘性衰退)", "medium"
    else:
        teshis, teshis_zh, risk_level = "MCI DETECTED (Mild Cognitive Impairment)", "检测到 MCI (轻度认知障碍)", "high"

    # 🚀 HAFIZAYI BOŞALT!
    clear_ai_memory()

    return {
        "status": "success",
        "diagnosis_en": teshis,
        "diagnosis_zh": teshis_zh,
        "risk_level": risk_level,
        "prob_hc": round(prob_hc, 1),
        "prob_mci": round(prob_mci, 1),
        "details": rapor_detaylari
    }