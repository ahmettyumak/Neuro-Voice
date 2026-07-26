import logging
import math
import os
import re
import site
import sys
import warnings
from collections import Counter
import gc
import joblib
import librosa
import numpy as np
import onnxruntime as rt
import pandas as pd
import spacy
from faster_whisper import WhisperModel


# =============================================================================
# HAFIZA TEMİZLEME (VRAM KORUMASI)
# =============================================================================
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

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi! (Recall)")


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
logger = logging.getLogger(__name__)

# =============================================================================
# SABİTLER VE MODELLER
# =============================================================================
ONNX_MODEL_FILE = "model_recall_isoforest.onnx"
SCALER_FILE = "model_recall_scaler.pkl"
COLUMNS_FILE = "model_recall_columns.pkl"
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 1200  # 20 Dakika sınırı

VALIDATION_KEYWORDS = [
    "remember", "forget", "forgot", "think", "story", "picture", "saw", "told",
    "anna", "thompson", "boston", "robbed", "money", "police", "children",
    "tell me", "what else", "anything else", "guess", "cookie", "boy", "girl"
]

SEARCH_TERMS = {
    "Dolgu_Kelimeleri": ["um", "uh", "er", "ah", "like", "you know", "hmm", "well"],
    "Bos_Kelimeler": ["thing", "stuff", "something", "anything", "that", "it", "they"],
}
FORGET_PHRASES = ["i don't remember", "i cant remember", "i forgot", "i don't know", "that's all", "i think"]

whisper_model = nlp_model = None


def load_ai_models():
    global whisper_model, nlp_model
    if whisper_model is None:
        # ÇÖKMEYİ ÖNLEMEK İÇİN large-v3 YERİNE medium KULLANILIYOR
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

    if nlp_model is None:
        nlp_model = spacy.load("en_core_web_sm")


def clean_word(word): return re.sub(r'[^\w\s]', '', word.lower().strip())


def isolate_patient_audio(segments_list, y, sr):
    if len(segments_list) < 2: return segments_list, y, " ".join(
        [w.word for s in segments_list for w in s.words]).strip(), "", 0, 0
    patient_segments, doctor_segments, doc_texts, pat_texts = [], [], [], []
    doc_phrases = ["tell me", "remember", "story", "okay", "good", "ready", "let's try", "how many", "what do you",
                   "can you", "what is", "alright", "question", "picture", "read", "everything", "what else", "guess"]

    for seg in segments_list:
        text = seg.text.lower().strip()
        words = [clean_word(w.word) for w in seg.words if clean_word(w.word)]
        if len(words) == 0: continue
        is_doctor = False
        if "?" in text and len(words) < 25: is_doctor = True
        if sum(1 for p in doc_phrases if p in text) > 0 and len(words) < 25: is_doctor = True
        if len(words) <= 3 and any(
                w in text for w in ["okay", "good", "alright", "yes", "right", "fine"]): is_doctor = True

        display_text = seg.text.strip()
        if is_doctor:
            doctor_segments.append(seg)
            doc_texts.append(display_text)
        else:
            patient_segments.append(seg)
            pat_texts.append(display_text)

    patient_text = " ".join([word.word for seg in patient_segments for word in seg.words]).strip()
    doc_text = " ".join([word.word for seg in doctor_segments for word in seg.words]).strip()
    patient_audio_slices = [y[int(seg.start * sr):int(seg.end * sr)] for seg in patient_segments]
    patient_y = np.concatenate(patient_audio_slices) if patient_audio_slices else y

    doc_dur = sum([seg.end - seg.start for seg in doctor_segments])
    pat_dur = sum([seg.end - seg.start for seg in patient_segments])
    return patient_segments, patient_y, patient_text, doc_text, pat_dur, doc_dur


# =============================================================================
# 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION) - GÜVENLİ 20 DAKİKA MODU
# =============================================================================
def extract_test_features(file_path):
    # 🚀 GÜVENLİK KONTROLÜ: Dosya 20 dakikadan uzunsa kullanıcıya uyarı ver (RAM patlamasın)
    try:
        duration_check = librosa.get_duration(path=file_path)
        if duration_check > 1200:  # 1200 Saniye = 20 Dakika
            return None, f"AUDIO TOO LONG: File is {duration_check / 60:.1f} minutes. Maximum allowed for local processing is 20 minutes. System crash prevented."
    except Exception:
        pass

    load_ai_models()
    features = {}

    # 1. Sesi RAM'e yükle (Sadece ilk 20 dakikayı al)
    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=1200)

    # 2. 🚨 Whispera dosya yolunu değil, RAM'deki KIRPILMIŞ SESİ (y) veriyoruz!
    # Bu satır Connection Error hatasını kökten çözen satırdır.
    segments, _ = whisper_model.transcribe(y, beam_size=1, vad_filter=True, word_timestamps=True, language="en")

    patient_segments, patient_y, patient_text, doctor_text, pat_dur, doc_dur = isolate_patient_audio(list(segments), y,
                                                                                                     sr)

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
        return None, "AUDIO TOO SHORT: The audio is too short or the patient did not speak enough."

    match_count = sum(1 for w in full_text_list if w in VALIDATION_KEYWORDS)
    doc_match_count = sum(1 for w in [clean_word(w) for w in doctor_text.split()] if w in VALIDATION_KEYWORDS)

    if (match_count + doc_match_count) < 1:
        return None, "INVALID TASK DETECTED: This is NOT a 'Recall' or 'Memory' task!"

    # --- ÖZELLİK HESAPLAMALARI ---
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
    features["Artikulasyon_Hizi"] = word_count / speech_duration if speech_duration > 0 else 0

    forget_count = sum(1 for phrase in FORGET_PHRASES if phrase in patient_text.lower())

    rapor_detaylari = {
        "doktor_metni": doctor_text if doctor_text else "[No doctor prompts detected]",
        "hasta_metni": patient_text if patient_text else "[No patient speech detected]",
        "doktor_sure": doc_dur,
        "hasta_sure": pat_dur,
        "toplam_kelime": word_count,
        "duraksama": duraksama_sayisi,
        "kisa_takilma": kisa_takilma_sayisi,
        "anomi": features["Zamir_Isim_Orani"],
        "unutma_ifadeleri": forget_count,
        "hata_yerleri": uzun_duraksama_yerleri[:6],
        "kekelemeler": list(set(kekelenen_kelimeler)),
        "dolgular": dict(Counter(kullanilan_dolgular))
    }
    return features, rapor_detaylari

def analyze_recall_for_streamlit(audio_path):
    result = extract_test_features(audio_path)

    # Yeni Güvenlik Duvarı mesajını Streamlit'e iletme kontrolü
    if result is None or isinstance(result[0], type(None)):
        return {"status": "error", "message": result[1]}

    features, rapor_detaylari = result
    df_patient = pd.DataFrame([features]).fillna(0)

    try:
        scaler = joblib.load(SCALER_FILE)
        expected_columns = joblib.load(COLUMNS_FILE)
        sess = rt.InferenceSession(ONNX_MODEL_FILE, providers=['CPUExecutionProvider'])
        input_name = sess.get_inputs()[0].name
    except Exception as e:
        return {"status": "error", "message": f"Recall Model files missing: {e}"}

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
        teshis, risk_level = "HIGH RISK (Dementia / Memory Loss Detected)", "high"
    elif 40.0 <= disease_percent < 60.0:
        teshis, risk_level = "AT RISK (Mild Cognitive Impairment - MCI)", "medium"
    else:
        teshis, risk_level = "HEALTHY (Normal Memory Function)", "low"

    # 🚀 ÇÖKMEYİ ÖNLEYEN SON DOKUNUŞ: VRAM'İ BOŞALT
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