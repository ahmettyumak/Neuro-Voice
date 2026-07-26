# =============================================================================
# 1. KÜTÜPHANELER VE İÇE AKTARMALAR
# =============================================================================
import logging
import math
import os
import re
import site
import sys
import warnings
import gc
from collections import Counter

import joblib
import librosa
import numpy as np
import onnxruntime as rt
import pandas as pd
import spacy
from faster_whisper import WhisperModel


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

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi! (Fluency Modülü)")


# =============================================================================
# 3. SABİTLER VE YAPAY ZEKA MODELLERİ
# =============================================================================
ONNX_MODEL_FILE = "model_fluency_isoforest.onnx"
SCALER_FILE = "model_fluency_scaler.pkl"
COLUMNS_FILE = "model_fluency_columns.pkl"
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 1200

VALIDATION_KEYWORDS = [
    "animal", "animals", "dog", "cat", "horse", "lion", "bear", "tiger",
    "elephant", "bird", "fish", "cow", "pig", "monkey", "deer", "snake",
    "rabbit", "fox", "giraffe", "zebra", "think of", "tell me", "name",
    "start", "minute", "ready", "ahead", "pet", "pets", "wild"
]

SEARCH_TERMS = {
    "Dolgu_Kelimeleri": ["um", "uh", "er", "ah", "like", "you know", "hmm", "well"],
    "Bos_Kelimeler": ["thing", "stuff", "something", "anything", "that", "it", "they"],
}

whisper_model = nlp_model = None


def load_ai_models():
    global whisper_model, nlp_model
    if whisper_model is None:
        logger.info("🧠 Whisper GPU (Fluency Task) starting...")
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

    if nlp_model is None:
        logger.info("📚 Spacy NLP loading...")
        nlp_model = spacy.load("en_core_web_sm")


# =============================================================================
# 4. YARDIMCI FONKSİYONLAR (NLP & SES İZOLASYONU)
# =============================================================================
def clean_word(word):
    return re.sub(r'[^\w\s]', '', word.lower().strip())


def isolate_patient_audio(segments_list, y, sr):
    if len(segments_list) < 2:
        return segments_list, y, " ".join([w.word for s in segments_list for w in s.words]).strip(), ""

    rms_values = []
    for seg in segments_list:
        if (seg.end - seg.start) > 0.5:
            audio_slice = y[int(seg.start * sr):int(seg.end * sr)]
            if len(audio_slice) > 0: rms_values.append(np.mean(librosa.feature.rms(y=audio_slice)))

    rms_threshold = np.percentile(rms_values, 90) * 0.10 if rms_values else 0
    patient_segments, doctor_segments = [], []

    for seg in segments_list:
        if (seg.end - seg.start) <= 0.5: continue
        audio_slice = y[int(seg.start * sr):int(seg.end * sr)]
        if len(audio_slice) == 0 or np.mean(librosa.feature.rms(y=audio_slice)) < rms_threshold: continue

        text = seg.text.lower()
        words = [clean_word(w.word) for w in seg.words if clean_word(w.word)]
        if len(words) == 0: continue

        doc_phrases = ["minute", "letter", "start", "begin", "ready", "ahead", "change", "directions", "stop",
                       "name for me", "tell me", "time"]
        doc_score = sum(1 for p in doc_phrases if p in text)

        doc = nlp_model(text)
        noun_count = sum(1 for token in doc if token.pos_ in ["NOUN", "PROPN"])
        noun_ratio = noun_count / len(words) if len(words) > 0 else 0

        if noun_ratio > 0.35:
            patient_segments.append(seg)
        elif doc_score > 0 and len(words) < 25:
            doctor_segments.append(seg)
        elif len(words) > 40:
            patient_segments.append(seg)
        elif doc_score >= 2:
            doctor_segments.append(seg)
        else:
            patient_segments.append(seg)

    patient_text = " ".join([word.word for seg in patient_segments for word in seg.words]).strip()
    doc_text = " ".join([word.word for seg in doctor_segments for word in seg.words]).strip()
    patient_audio_slices = [y[int(seg.start * sr):int(seg.end * sr)] for seg in patient_segments]
    patient_y = np.concatenate(patient_audio_slices) if patient_audio_slices else y

    return patient_segments, patient_y, patient_text, doc_text


# =============================================================================
# 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION)
# =============================================================================
def extract_test_features(file_path):
    load_ai_models()
    features = {}

    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=MAX_AUDIO_DURATION)
    segments, _ = whisper_model.transcribe(file_path, beam_size=1, vad_filter=True, word_timestamps=True, language="en")
    patient_segments, patient_y, patient_text, doctor_text = isolate_patient_audio(list(segments), y, sr)

    words_data = []
    full_text_list = []
    for segment in patient_segments:
        for word in segment.words:
            words_data.append(word)
            full_text_list.append(clean_word(word.word))

    full_text = " ".join(full_text_list)
    word_count = len(words_data)
    speech_duration = sum([w.end - w.start for w in words_data]) if word_count > 0 else 0

    if word_count < 5 or speech_duration < 3:
        return None, "AUDIO TOO SHORT: The audio is too short or patient did not speak enough."

    match_count = sum(1 for w in full_text_list if w in VALIDATION_KEYWORDS)
    doc_match_count = sum(1 for w in [clean_word(w) for w in doctor_text.split()] if w in VALIDATION_KEYWORDS)

    if (match_count + doc_match_count) < 2:
        return None, "INVALID TASK DETECTED: This is NOT a 'Verbal Fluency' (Animal Naming) task!"

    features["Kelime_Sayisi"] = word_count
    features["TTR_Orani"] = len(set(full_text_list)) / word_count if word_count > 0 else 0

    word_counts = Counter(full_text_list)
    features["Sozcuk_Entropisi"] = sum([- (c / word_count) * math.log2(c / word_count) for c in word_counts.values()])

    doc = nlp_model(full_text)
    pronoun_count = sum(1 for token in doc if token.pos_ == "PRON")
    noun_count = sum(1 for token in doc if token.pos_ == "NOUN")
    features["Zamir_Isim_Orani"] = pronoun_count / noun_count if noun_count > 0 else pronoun_count

    for category, keywords in SEARCH_TERMS.items():
        total_count = sum(len(re.findall(r'\b' + re.escape(k) + r'\b', full_text)) for k in keywords)
        features[f"Oran_{category}"] = total_count / word_count if word_count > 0 else 0

    duraksama_sayisi = kisa_takilma_sayisi = tekrar_sayisi = uzatilan_kelime = 0
    uzun_duraksama_yerleri, kekelenen_kelimeler, kullanilan_dolgular = [], [], []

    if word_count > 0:
        for i in range(1, word_count):
            bosluk = words_data[i].start - words_data[i - 1].end
            if bosluk >= 0.5:
                duraksama_sayisi += 1
                uzun_duraksama_yerleri.append(f"'{clean_word(words_data[i - 1].word)}' ({bosluk:.1f}s)")
            elif 0.2 <= bosluk < 0.5:
                kisa_takilma_sayisi += 1

            w1, w2 = clean_word(words_data[i - 1].word), clean_word(words_data[i].word)
            if w1 == w2 and len(w1) > 1:
                tekrar_sayisi += 1
                kekelenen_kelimeler.append(w2)
            if w2 in SEARCH_TERMS["Dolgu_Kelimeleri"]:
                kullanilan_dolgular.append(w2)

    features["Duraksama_Sayisi"] = duraksama_sayisi
    features["Kisa_Takilma"] = kisa_takilma_sayisi
    features["Kelime_Tekrari"] = tekrar_sayisi
    features["Uzatilan_Kelime"] = uzatilan_kelime
    features["Artikulasyon_Hizi"] = word_count / speech_duration if speech_duration > 0 else 0
    features["Duraksama_Orani"] = duraksama_sayisi / word_count if word_count > 0 else 0

    patient_total_duration = len(patient_y) / sr
    doc_dur = len(y) / sr - patient_total_duration

    rapor_detaylari = {
        "doktor_metni": doctor_text if doctor_text else "[No doctor prompts detected]",
        "hasta_metni": patient_text if patient_text else "[No patient speech detected]",
        "doktor_sure": doc_dur,
        "hasta_sure": patient_total_duration,
        "toplam_kelime": word_count,
        "duraksama": duraksama_sayisi,
        "kisa_takilma": kisa_takilma_sayisi,
        "anomi": features["Zamir_Isim_Orani"],
        "hata_yerleri": uzun_duraksama_yerleri[:6],
        "kekelemeler": list(set(kekelenen_kelimeler)),
        "dolgular": dict(Counter(kullanilan_dolgular))
    }
    return features, rapor_detaylari


# =============================================================================
# 6. YAPAY ZEKA TAHMİNİ VE STREAMLIT ÇIKTISI
# =============================================================================
def analyze_fluency_for_streamlit(audio_path):
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
        return {"status": "error", "message": f"Fluency Model files missing: {e}"}

    for col in expected_columns:
        if col not in df_patient.columns: df_patient[col] = 0.0
    df_patient = df_patient[expected_columns]

    X_scaled = scaler.transform(df_patient).astype(np.float32)
    pred_onx = sess.run(None, {input_name: X_scaled})
    decision_score = float(np.array(pred_onx[1]).flatten()[0])

    scaling_factor = 5.0
    healthy_prob_raw = 1 / (1 + math.exp(-decision_score * scaling_factor))
    healthy_percent = healthy_prob_raw * 100
    disease_percent = 100 - healthy_percent

    if disease_percent >= 60.0:
        teshis, risk_level = "HIGH RISK (Dementia / Anomaly Detected)", "high"
    elif 40.0 <= disease_percent < 60.0:
        teshis, risk_level = "AT RISK (Mild Cognitive Impairment - MCI)", "medium"
    else:
        teshis, risk_level = "HEALTHY (Normal Cognitive Function)", "low"

    # 🚀 İŞTE EKSİK OLAN O KRİTİK KOD: HAFIZAYI BOŞALT!
    clear_ai_memory()

    return {
        "status": "success",
        "diagnosis": teshis,
        "risk_level": risk_level,
        "prob_hasta": round(disease_percent, 1),
        "prob_saglikli": round(healthy_percent, 1),
        "isolation_score": round(decision_score, 3),
        "details": rapor_detaylari
    }