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
import numpy as np
import pandas as pd
import librosa
import parselmouth
import spacy
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
    global whisper_model, nlp_model

    if whisper_model is not None:
        del whisper_model
        whisper_model = None

    if 'nlp_model' in globals() and nlp_model is not None:
        del nlp_model
        nlp_model = None

    gc.collect()

    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except ImportError:
        pass

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi! (Korean Modülü)")


# =============================================================================
# 3. SABİTLER VE YAPAY ZEKA MODELLERİ
# =============================================================================
ONNX_MODEL_FILE = "model_KOREAN.onnx"
SCALER_FILE = "model_KOREAN_scaler.pkl"
COLUMNS_FILE = "model_KOREAN_columns.pkl"
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 1200

KOREAN_FILLERS = ["어", "음", "그", "저", "막", "뭐랄까", "에"]
KOREAN_COGNITIVE_DELAY = ["뭐", "뭐라고", "다시", "응?", "글쎄"]

VALIDATION_KEYWORDS = [
    "최근", "과거", "즐겨", "어머니", "아버님", "시작", "네", "아니요",
    "기억", "생각", "말씀", "잘", "조금", "오늘", "지금", "이야기"
]

whisper_model = nlp_model = None


def load_ai_models():
    global whisper_model, nlp_model

    if whisper_model is None:
        logger.info("🧠 Whisper GPU (Korean) starting...")
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

    if nlp_model is None:
        logger.info("📚 Spacy Korean NLP loading...")
        try:
            nlp_model = spacy.load("ko_core_news_sm")
        except OSError:
            logger.error(
                "❌ HATA: Spacy Korece modeli bulunamadı! Lütfen terminalde 'python -m spacy download ko_core_news_sm' komutunu çalıştırın.")
            sys.exit()


# =============================================================================
# 4. YARDIMCI FONKSİYONLAR (NLP & SES İZOLASYONU)
# =============================================================================
def isolate_patient_audio_nlp(segments_list, y, sr):
    patient_segments, doctor_segments, doc_texts, pat_texts = [], [], [], []
    doc_endings = ["요?", "까?", "나요?", "세요?", "어때요?", "있으세요?"]
    doc_keywords = ["녹음", "시작하겠습니다", "시작할게요", "어머니", "아버님", "최근에", "과거에", "즐겨 보신"]

    for seg in segments_list:
        text = " ".join([w.word for w in seg.words]).strip()
        is_doctor = False
        if any(ending in text for ending in doc_endings): is_doctor = True
        if any(keyword in text for keyword in doc_keywords) and len(text) > 5: is_doctor = True

        display_text = seg.text.strip()
        if is_doctor:
            doctor_segments.append(seg)
            doc_texts.append(display_text)
        else:
            patient_segments.append(seg)
            pat_texts.append(display_text)

    doc_dur = sum([seg.end - seg.start for seg in doctor_segments])
    pat_dur = sum([seg.end - seg.start for seg in patient_segments])

    patient_audio_slices = [y[int(seg.start * sr):int(seg.end * sr)] for seg in patient_segments]
    patient_y = np.concatenate(patient_audio_slices) if patient_audio_slices else y

    return patient_segments, patient_y, " ".join(pat_texts), " ".join(doc_texts), pat_dur, doc_dur


# =============================================================================
# 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION)
# =============================================================================
def extract_korean_features(file_path):
    load_ai_models()
    features = {}

    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=MAX_AUDIO_DURATION)
    segments, _ = whisper_model.transcribe(file_path, beam_size=1, vad_filter=True, word_timestamps=True, language="ko")

    patient_segments, patient_y, patient_text, doctor_text, pat_dur, doc_dur = isolate_patient_audio_nlp(list(segments),
                                                                                                         y, sr)

    words_data = []
    for segment in patient_segments:
        for word in segment.words: words_data.append(word)

    if len(patient_text) < 5 or pat_dur < 2.0:
        return None, "AUDIO TOO SHORT / 오디오가 너무 짧습니다: Not enough Korean speech detected."

    combined_text = patient_text + " " + doctor_text
    match_count = sum(1 for keyword in VALIDATION_KEYWORDS if keyword in combined_text)

    if match_count < 1:
        return None, "INVALID TASK / 잘못된 작업: This does not appear to be a clinical interview in Korean."

    doc = nlp_model(patient_text)
    words = [token.text for token in doc if not token.is_punct]
    word_count = len(words)
    char_count = len(patient_text.replace(" ", ""))

    features["Kelime_Sayisi"] = word_count
    features["TTR_Orani"] = len(set(words)) / word_count if word_count > 0 else 0

    word_counts = Counter(words)
    features["Sozcuk_Entropisi"] = sum(
        [- (count / word_count) * math.log2(count / word_count) for count in word_counts.values()])

    noun_count = sum(1 for token in doc if token.pos_ in ["NOUN", "PROPN"])
    pronoun_count = sum(1 for token in doc if token.pos_ == "PRON")
    verb_count = sum(1 for token in doc if token.pos_ in ["VERB", "AUX"])

    features["Zamir_Isim_Orani"] = pronoun_count / noun_count if noun_count > 0 else pronoun_count
    features["Fiil_Isim_Orani"] = verb_count / noun_count if noun_count > 0 else verb_count

    filler_count = sum(patient_text.count(filler) for filler in KOREAN_FILLERS)
    features["Dolgu_Kelime_Orani"] = filler_count / word_count if word_count > 0 else 0

    delay_count = sum(patient_text.count(delay) for delay in KOREAN_COGNITIVE_DELAY)
    features["Bilisel_Gecikme_Orani"] = delay_count / word_count if word_count > 0 else 0

    duraksama_sayisi = 0
    uzun_duraksama_yerleri = []
    speech_duration = sum([w.end - w.start for w in words_data]) if len(words_data) > 0 else 0

    if len(words_data) > 0:
        for i in range(1, len(words_data)):
            bosluk = words_data[i].start - words_data[i - 1].end
            if bosluk >= 0.5:
                duraksama_sayisi += 1
                uzun_duraksama_yerleri.append(f"'{words_data[i - 1].word.strip()}' ({bosluk:.1f}s)")

    features["Duraksama_Sayisi"] = duraksama_sayisi
    features["Duraksama_Orani"] = duraksama_sayisi / word_count if word_count > 0 else 0
    features["Karakter_Hizi_CPS"] = char_count / speech_duration if speech_duration > 0 else 0

    try:
        sound = parselmouth.Sound(np.array([patient_y]), sampling_frequency=sr)
        pitch = sound.to_pitch()
        pulses = call([sound, pitch], "To PointProcess (cc)")
        features["Jitter_Local"] = call(pulses, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3) * 100
        features["Shimmer_Local"] = call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
        features["HNR"] = call(call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0), "Get mean", 0, 0)
    except:
        features["Jitter_Local"] = features["Shimmer_Local"] = features["HNR"] = 0

    patient_total_duration = len(patient_y) / sr
    features["Oran_Sessizlik"] = (
                                             patient_total_duration - speech_duration) / patient_total_duration if patient_total_duration > 0 else 0

    rapor_detaylari = {
        "doktor_metni": doctor_text if doctor_text else "[No doctor/interviewer prompts detected]",
        "hasta_metni": patient_text,
        "doktor_sure": doc_dur,
        "hasta_sure": pat_dur,
        "kelime_sayisi": word_count,
        "duraksama": duraksama_sayisi,
        "anomi": features["Zamir_Isim_Orani"],
        "gecikme": delay_count,
        "hata_yerleri": uzun_duraksama_yerleri[:5],
        "dolgular": filler_count
    }
    return features, rapor_detaylari


# =============================================================================
# 6. YAPAY ZEKA TAHMİNİ VE STREAMLIT ÇIKTISI
# =============================================================================
def analyze_korean_for_streamlit(audio_path):
    result = extract_korean_features(audio_path)

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
        return {"status": "error", "message": f"Korean Model files missing: {e}"}

    for col in expected_columns:
        if col not in df_patient.columns: df_patient[col] = 0.0
    df_patient = df_patient[expected_columns]

    X_scaled = scaler.transform(df_patient).astype(np.float32)
    label_name = sess.get_outputs()[0].name
    prob_name = sess.get_outputs()[1].name if len(sess.get_outputs()) > 1 else None

    pred_onx = sess.run([label_name, prob_name], {input_name: X_scaled})

    prob_dict = pred_onx[1][0]
    if isinstance(prob_dict, dict):
        prob_hasta = prob_dict.get(1, 0.0) * 100
        prob_saglikli = prob_dict.get(0, 1.0) * 100
    else:
        prob_hasta = prob_dict[1] * 100
        prob_saglikli = prob_dict[0] * 100

    if prob_hasta < 40.0:
        teshis, teshis_ko, risk_level = "HEALTHY (Normal Cognitive Function)", "건강 (정상 인지 기능)", "low"
    elif 40.0 <= prob_hasta < 60.0:
        teshis, teshis_ko, risk_level = "SUSPECTED MCI (Borderline Decline)", "의심 (경도 인지 장애 의심)", "medium"
    else:
        teshis, teshis_ko, risk_level = "MCI DETECTED (Mild Cognitive Impairment)", "위험 (경도 인지 장애 감지)", "high"

    # 🚀 İŞTE EKSİK OLAN O KRİTİK KOD: HAFIZAYI BOŞALT!
    clear_ai_memory()

    return {
        "status": "success",
        "diagnosis_en": teshis,
        "diagnosis_ko": teshis_ko,
        "risk_level": risk_level,
        "prob_hasta": round(prob_hasta, 1),
        "prob_saglikli": round(prob_saglikli, 1),
        "details": rapor_detaylari
    }