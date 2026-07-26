# =============================================================================
# 1. KÜTÜPHANELER VE İÇE AKTARMALAR
# =============================================================================
import os
import re
import site
import sys
import logging
import warnings
import gc
from collections import Counter

import numpy as np
import pandas as pd
import joblib
import librosa
import parselmouth
import spacy
import onnxruntime as rt
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
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
    global whisper_model, nlp_model, bert_model

    if whisper_model is not None:
        del whisper_model
        whisper_model = None

    if 'nlp_model' in globals() and nlp_model is not None:
        del nlp_model
        nlp_model = None

    if 'bert_model' in globals() and bert_model is not None:
        del bert_model
        bert_model = None

    gc.collect()

    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except ImportError:
        pass

    logger.info("🧹 AI Modelleri hafızadan silindi ve VRAM tamamen temizlendi!")


# =============================================================================
# 3. SABİTLER VE YAPAY ZEKA MODELLERİ
# =============================================================================
ONNX_MODEL_FILE = "alzheimer_real_xgboost.onnx"
SCALER_FILE = "alzheimer_real_scaler.pkl"
PCA_FILE = "alzheimer_real_pca.pkl"
COLUMNS_FILE = "alzheimer_real_columns.pkl"

SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 1200

VALIDATION_KEYWORDS = [
    "cookie", "cookies", "jar", "mother", "mom", "woman", "lady", "boy", "kid", "son",
    "girl", "sister", "daughter", "stool", "chair", "sink", "water", "spill", "overflow",
    "wash", "dish", "dishes", "plate", "kitchen", "window", "curtain", "cupboard",
    "cabinet", "fall", "falling", "reach", "hand", "dry", "floor", "picture", "see", "action"
]

SEARCH_TERMS = {
    "Dolgu_Kelimeleri": ["um", "uh", "er", "ah", "like", "you know", "hmm", "well"],
    "Bos_Kelimeler": ["thing", "stuff", "something", "anything", "that", "it", "they", "there"],
}

KEY_CONCEPTS = [
    ["boy", "brother", "son", "kid"], ["girl", "sister", "daughter"],
    ["woman", "mother", "lady", "mom"], ["cookie", "cookies"],
    ["jar", "container", "pot"], ["stool", "chair", "ladder", "step"],
    ["sink", "basin", "faucet", "tap"], ["water", "spill", "overflow", "running", "puddle"],
    ["dish", "plate", "wash", "dry", "wipe"], ["fall", "tip", "over", "tumble"],
    ["reach", "hand", "give", "steal"]
]

whisper_model = bert_model = nlp_model = None


def load_ai_models():
    global whisper_model, bert_model, nlp_model
    if whisper_model is None:
        logger.info("🧠 Whisper GPU (English) starting...")
        try:
            whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
        except:
            whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

    if bert_model is None:
        logger.info("📊 BERT Model loading...")
        bert_model = SentenceTransformer('all-MiniLM-L6-v2')

    if nlp_model is None:
        logger.info("📚 Spacy NLP loading...")
        nlp_model = spacy.load("en_core_web_sm")


# =============================================================================
# 4. YARDIMCI FONKSİYONLAR (NLP & SES)
# =============================================================================
def isolate_and_analyze_speakers(segments_list, y, sr):
    patient_segments, doctor_segments, doc_texts, pat_texts = [], [], [], []
    doc_keywords = ["tell me", "everything you see", "happening in that picture", "anything else", "what else",
                    "going on", "thank you", "take a look", "all the action", "start now"]

    for seg in segments_list:
        raw_text = " ".join([w.word.strip().lower() for w in seg.words]).strip()
        text = re.sub(r'\s+', ' ', raw_text)
        is_doctor = False
        word_count = len(text.split())

        if "?" in text and word_count <= 15: is_doctor = True
        if any(keyword in text for keyword in doc_keywords) and word_count <= 35: is_doctor = True
        if word_count <= 4 and any(
            k in text for k in ["okay", "good", "alright", "yeah", "yes", "mhm", "fine", "right"]): is_doctor = True

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

    return patient_segments, patient_y, doc_dur, pat_dur, " ".join(doc_texts), " ".join(pat_texts)


def walk_tree(node, depth):
    if node.n_lefts + node.n_rights > 0: return max(walk_tree(child, depth + 1) for child in node.children)
    return depth


# =============================================================================
# 5. ÖZELLİK ÇIKARIMI (FEATURE EXTRACTION)
# =============================================================================
def extract_test_features(file_path):
    load_ai_models()
    features = {}

    y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=MAX_AUDIO_DURATION)
    segments, _ = whisper_model.transcribe(file_path, beam_size=1, vad_filter=True, word_timestamps=True, language="en")
    patient_segments, patient_y, doc_dur, pat_dur, doc_text, pat_text = isolate_and_analyze_speakers(list(segments), y,
                                                                                                     sr)

    words_data = [word for segment in patient_segments for word in segment.words]
    full_text_list = []

    for i in range(len(words_data)):
        word_str = words_data[i].word.strip().lower()
        if i < len(words_data) - 1:
            if (words_data[i + 1].start - words_data[i].end) > 0.8: word_str += "."
        full_text_list.append(word_str)

    full_text = " ".join(full_text_list)
    clean_words = [re.sub(r'[^\w\s]', '', w) for w in full_text_list if re.sub(r'[^\w\s]', '', w)]
    word_count = len(clean_words)
    speech_duration = sum([w.end - w.start for w in words_data]) if words_data else 0

    if word_count < 10 or speech_duration < 10:
        return None, "AUDIO TOO SHORT: Audio is too short or patient didn't speak enough."

    match_count = sum(1 for w in clean_words if w in VALIDATION_KEYWORDS)
    if match_count < 2:
        return None, "INVALID TASK DETECTED: Audio does NOT match 'Cookie Theft' description."

    embeddings = bert_model.encode(full_text)
    for i, val in enumerate(embeddings): features[f"BERT_Dim_{i}"] = val

    doc = nlp_model(full_text)
    sentences = list(doc.sents)
    num_sentences = len(sentences)
    features["Ortalama_Cumle_Uzunlugu"] = word_count / num_sentences if num_sentences > 0 else 0
    tree_depths = [walk_tree(sent.root, 0) for sent in sentences]
    features["Ortalama_Agac_Derinligi"] = sum(tree_depths) / len(tree_depths) if tree_depths else 0
    clauses = [token for token in doc if token.dep_ in ('advcl', 'relcl', 'ccomp', 'xcomp')]
    features["Yan_Cumlecik_Orani"] = len(clauses) / num_sentences if num_sentences > 0 else 0

    kavram_sayisi = sum(1 for cg in KEY_CONCEPTS if any(re.search(r'\b' + re.escape(w) + r'\b', full_text) for w in cg))
    features["Kavram_Skoru"] = kavram_sayisi
    features["Bilgi_Yogunlugu"] = kavram_sayisi / word_count if word_count > 0 else 0
    features["TTR_Orani"] = len(set(clean_words)) / word_count if word_count > 0 else 0

    noun_count = sum(1 for token in doc if token.pos_ in ["NOUN", "PROPN"])
    pronoun_count = sum(1 for token in doc if token.pos_ == "PRON")
    features["Zamir_Isim_Orani"] = pronoun_count / noun_count if noun_count > 0 else pronoun_count

    for category, keywords in SEARCH_TERMS.items():
        total_count = sum(len(re.findall(r'\b' + re.escape(k) + r'\b', full_text)) for k in keywords)
        features[f"Oran_{category}"] = total_count / word_count if word_count > 0 else 0

    duraksama_sayisi = kisa_takilma_sayisi = tekrar_sayisi = uzatilan_kelime = 0
    uzun_duraksama_yerleri, kekelenen_kelimeler, kullanilan_dolgular = [], [], []

    if words_data:
        for i in range(1, len(words_data)):
            bosluk = words_data[i].start - words_data[i - 1].end
            if bosluk >= 0.5:
                duraksama_sayisi += 1
                onceki_kelime = re.sub(r'[^\w\s]', '', words_data[i - 1].word.strip())
                uzun_duraksama_yerleri.append(f"'{onceki_kelime}' ({bosluk:.1f} sn)")
            elif 0.2 <= bosluk < 0.5:
                kisa_takilma_sayisi += 1

            current_clean = re.sub(r'[^\w\s]', '', words_data[i].word.strip().lower())
            prev_clean = re.sub(r'[^\w\s]', '', words_data[i - 1].word.strip().lower())
            if current_clean == prev_clean and len(current_clean) > 0:
                tekrar_sayisi += 1
                kekelenen_kelimeler.append(current_clean)

            if current_clean in SEARCH_TERMS["Dolgu_Kelimeleri"]:
                kullanilan_dolgular.append(current_clean)

        for w in words_data:
            if (w.end - w.start) > 0.8: uzatilan_kelime += 1

    features["Kisa_Takilma"] = kisa_takilma_sayisi
    features["Kelime_Tekrari"] = tekrar_sayisi
    features["Uzatilan_Kelime"] = uzatilan_kelime
    features["Artikulasyon_Hizi"] = word_count / speech_duration if speech_duration > 0 else 0
    features["Duraksama_Orani"] = duraksama_sayisi / word_count if word_count > 0 else 0

    try:
        sound = parselmouth.Sound(np.array([patient_y]), sampling_frequency=sr)
        pitch = sound.to_pitch()
        pulses = call([sound, pitch], "To PointProcess (cc)")
        features["Jitter_Local"] = call(pulses, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3) * 100
        features["Shimmer_Local"] = call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
        features["HNR"] = call(call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0), "Get mean", 0, 0)
    except:
        features["Jitter_Local"] = features["Shimmer_Local"] = features["HNR"] = 0

    rapor_detaylari = {
        "doktor_metni": doc_text if doc_text else "[Seste doktor konuşması bulunamadı]",
        "hasta_metni": pat_text if pat_text else "[Hasta konuşması bulunamadı]",
        "doktor_sure": doc_dur,
        "hasta_sure": pat_dur,
        "toplam_kelime": word_count,
        "duraksama": duraksama_sayisi,
        "kisa_takilma": kisa_takilma_sayisi,
        "gramer": features["Ortalama_Agac_Derinligi"],
        "anomi": features["Zamir_Isim_Orani"],
        "kavram": kavram_sayisi,
        "hata_yerleri": uzun_duraksama_yerleri[:5],
        "kekelemeler": list(set(kekelenen_kelimeler)),
        "dolgular": dict(Counter(kullanilan_dolgular))
    }

    return features, rapor_detaylari


# =============================================================================
# 6. YAPAY ZEKA TAHMİNİ VE STREAMLIT ÇIKTISI
# =============================================================================
def analyze_for_streamlit(audio_path):
    """Streamlit web arayüzü için analiz sonuçlarını JSON/Dict formatında döndürür."""
    result = extract_test_features(audio_path)

    # Hata yakalama
    if result is None or isinstance(result[0], type(None)):
        return {"status": "error", "message": result[1] if result else "Bilinmeyen Hata"}

    features, rapor_detaylari = result
    df_patient = pd.DataFrame([features]).fillna(0)

    try:
        pca = joblib.load(PCA_FILE)
        scaler = joblib.load(SCALER_FILE)
        expected_columns = joblib.load(COLUMNS_FILE)
        sess = rt.InferenceSession(ONNX_MODEL_FILE, providers=['CPUExecutionProvider'])
    except Exception as e:
        return {"status": "error", "message": f"Model files missing or error loading: {e}"}

    bert_cols = [c for c in df_patient.columns if c.startswith('BERT_Dim_')]
    clinical_cols = [c for c in df_patient.columns if not c.startswith('BERT_Dim_')]

    patient_bert_pca = pca.transform(df_patient[bert_cols])
    pca_cols = [f"BERT_PCA_{i}" for i in range(patient_bert_pca.shape[1])]
    df_patient_pca = pd.DataFrame(patient_bert_pca, columns=pca_cols, index=df_patient.index)

    df_final = pd.concat([df_patient[clinical_cols].reset_index(drop=True), df_patient_pca], axis=1)

    for col in expected_columns:
        if col not in df_final.columns: df_final[col] = 0.0
    df_final = df_final[expected_columns]

    X_scaled = scaler.transform(df_final).astype(np.float32)

    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    prob_name = sess.get_outputs()[1].name if len(sess.get_outputs()) > 1 else None

    pred_onx = sess.run([label_name, prob_name], {input_name: X_scaled})

    prob_dict = pred_onx[1][0]
    prob_hasta = prob_dict.get(1, 0.0) * 100 if isinstance(prob_dict, dict) else prob_dict[1] * 100
    prob_saglikli = prob_dict.get(0, 1.0) * 100 if isinstance(prob_dict, dict) else prob_dict[0] * 100

    if prob_hasta < 40.0:
        teshis, risk_level = "HEALTHY (Normal Cognitive Function)", "low"
    elif 40.0 <= prob_hasta < 70.0:
        teshis, risk_level = "AT RISK (Mild Cognitive Impairment - MCI)", "medium"
    else:
        teshis, risk_level = "HIGH RISK (Alzheimer's / Dementia)", "high"

    # 🚀 İŞTE EKSİK OLAN O KRİTİK KOD: HAFIZAYI BOŞALT!
    clear_ai_memory()

    return {
        "status": "success",
        "diagnosis": teshis,
        "risk_level": risk_level,
        "prob_hasta": round(prob_hasta, 1),
        "prob_saglikli": round(prob_saglikli, 1),
        "details": rapor_detaylari
    }