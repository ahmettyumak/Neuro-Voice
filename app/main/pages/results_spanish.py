import streamlit as st
import plotly.graph_objects as go
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Spanish Report", page_icon="🌍", layout="wide")

if 'analysis_results_spanish' not in st.session_state or st.session_state.analysis_results_spanish is None:
    st.switch_page("pages/spanish.py")

res = st.session_state.analysis_results_spanish
lang = st.session_state.get("page_lang", "es")


def t(es, en): return es if lang == "es" else en


def toggle_lang(): st.session_state.page_lang = "en" if lang == "es" else "es"


top_col1, top_col2 = st.columns([8, 1])
with top_col2:
    if st.button("🇬🇧 EN" if lang == "es" else "🇪🇸 ES", type="primary", use_container_width=True):
        toggle_lang()
        st.rerun()

if res.get("status") == "error":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(f"🛑 {t('Análisis Rechazado:', 'Analysis Rejected:')} {res.get('message')}")
    if st.button("⬅️ " + t("Volver a la página principal", "Go Back"), type="primary"):
        st.session_state.audio_bytes = None
        st.session_state.analysis_results_spanish = None
        st.switch_page("pages/spanish.py")
else:
    det = res["details"]
    age = st.session_state.get("patient_age", "Unknown")
    gender = st.session_state.get("patient_gender", "Unknown")
    gender_display = "Mujer" if gender == "Female" and lang == "es" else "Hombre" if gender == "Male" and lang == "es" else gender
    today_date = datetime.date.today().strftime('%B %d, %Y')


    # =========================================================
    # PDF OLUŞTURMA FONKSİYONU (ÇİFT DİLLİ)
    # =========================================================
    def create_spanish_pdf(fig_gauge, fig_radar):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_gauge:
            gauge_path = tmp_gauge.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_radar:
            radar_path = tmp_radar.name
        try:
            fig_gauge.write_image(gauge_path)
            fig_radar.write_image(radar_path)

            pdf = FPDF()
            pdf.add_page()

            # Başlık
            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(20, 184, 166)
            pdf.cell(0, 15, "NEUROVOICE AI - REPORTE CLINICO (ESPANOL)", ln=True, align="C")
            pdf.line(10, 25, 200, 25)
            pdf.ln(8)

            # Hasta Bilgileri
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, t("Datos del Paciente:", "Patient Demographics:"), ln=True)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8,
                     f"{t('Edad', 'Age')}: {age}   |   {t('Genero', 'Gender')}: {gender_display}   |   {t('Fecha', 'Date')}: {today_date}",
                     ln=True)

            pdf.ln(10)
            pdf.image(gauge_path, x=135, y=60, w=50)

            # Teşhis
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"{t('Decision de la IA', 'AI Decision')}:", ln=1)
            pdf.set_font("helvetica", "", 12)

            if res["risk_level"] == "high":
                pdf.set_text_color(239, 68, 68)
            elif res["risk_level"] == "medium":
                pdf.set_text_color(245, 158, 11)
            else:
                pdf.set_text_color(34, 197, 94)

            diag_text = res['diagnosis_es'] if lang == "es" else res['diagnosis_en']

            # Latin-1 formatına uygun string encode
            safe_diag = diag_text.encode('ascii', 'ignore').decode('ascii')
            pdf.cell(0, 8, safe_diag, ln=1)

            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, f"{t('Prob. Alzheimer', 'Alzheimer Prob.')}: %{res['prob_ad']}", ln=1)
            pdf.cell(0, 8, f"{t('Prob. Riesgo Leve', 'MCI Prob.')}: %{res['prob_mci']}", ln=1)
            pdf.cell(0, 8, f"{t('Prob. Sano', 'Healthy Prob.')}: %{res['prob_hc']}", ln=1)

            pdf.ln(15)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, t("Mapa de Perfil Cognitivo:", "Cognitive Profile Map:"), ln=True)
            pdf.image(radar_path, x=110, y=125, h=70)

            pdf.ln(5)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 7, f"- {t('Palabras Totales', 'Total Words')}: {det['kelime_sayisi']}", ln=True)
            pdf.cell(0, 7, f"- {t('Pausas', 'Pauses')}: {det['duraksama']}", ln=True)
            pdf.cell(0, 7, f"- {t('Riqueza Lexica', 'Lexical Richness')}: {det['sozcuk_entropisi']:.2f}", ln=True)

            pdf.set_y(-20)
            pdf.set_font("helvetica", "I", 8)
            pdf.cell(0, 10, t("Aviso: Herramienta de cribado unicamente.", "Disclaimer: Screening tool only."),
                     align="C")

            return bytes(pdf.output())
        except Exception as e:
            st.error(f"PDF Error: {e}")
            return None
        finally:
            if os.path.exists(gauge_path): os.remove(gauge_path)
            if os.path.exists(radar_path): os.remove(radar_path)


    # =========================================================
    # ARAYÜZ TASARIMI
    # =========================================================
    st.markdown(f"""
        <div style='background: linear-gradient(90deg, #0B1117 0%, #1A222C 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #14b8a6; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h2 style='margin: 0; color: #F8FAFC;'>Neurovoice AI Clinical Report</h2>
                <p style='margin: 0; color: #14b8a6; font-size: 1.1rem;'>{t('Objetivo: Módulo Español (XGBoost)', 'Target: Spanish Module (XGBoost)')}</p>
            </div>
            <div style='text-align: right; color: #F8FAFC;'>
                <p style='margin: 0;'><b>{t('Paciente', 'Patient')}:</b> {age} {t('años', 'y/o')}, {gender_display}</p>
                <p style='margin: 0;'><b>{t('Fecha', 'Date')}:</b> {today_date}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_radar, col_verdict = st.columns([1.2, 1], gap="large")

    with col_verdict:
        st.markdown(f"<h4 style='color: #F8FAFC;'>🧠 {t('Decisión Final de la IA', 'Final AI Decision')}</h4>",
                    unsafe_allow_html=True)
        if res["risk_level"] == "low":
            gauge_color = "#22c55e"
        elif res["risk_level"] == "medium":
            gauge_color = "#f59e0b"
        else:
            gauge_color = "#ef4444"

        # Risk Skoru: En yüksek hastalık oranını gösterir
        display_prob = res['prob_ad'] if res['risk_level'] == "high" else res['prob_mci'] if res[
                                                                                                 'risk_level'] == "medium" else 100 - \
                                                                                                                                res[
                                                                                                                                    'prob_hc']

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=display_prob,
            number={'suffix': "%", 'font': {'size': 40, 'color': gauge_color}},
            title={'text': t("Puntuación de Riesgo Cognitivo", "Cognitive Risk Score"), 'font': {'size': 18}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1}, 'bar': {'color': gauge_color, 'thickness': 0.75},
                'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#1A222C",
                'steps': [{'range': [0, 40], 'color': "rgba(34, 197, 94, 0.1)"},
                          {'range': [40, 70], 'color': "rgba(245, 158, 11, 0.1)"},
                          {'range': [70, 100], 'color': "rgba(239, 68, 68, 0.1)"}],
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_radar:
        st.markdown(f"<h4 style='color: #F8FAFC;'>🕸️ {t('Mapa de Perfil Cognitivo', 'Cognitive Profile Map')}</h4>",
                    unsafe_allow_html=True)

        # Spanish Modülüne Özel Radar Haritası
        norm_words = min(det['kelime_sayisi'] * 2, 100)
        norm_entropy = min(det['sozcuk_entropisi'] * 15, 100)
        norm_pauses = max(100 - (det['duraksama'] * 5), 0)

        fillers = sum(det['dolgular'].values()) if det['dolgular'] else 0
        norm_fillers = max(100 - (fillers * 10), 0)

        r_labels = [t('Palabras Generadas', 'Word Output'), t('Riqueza Léxica', 'Lexical Richness'),
                    t('Flujo de Habla', 'Speech Flow'), t('Control de Muletillas', 'Filler Control')]

        fig_radar = go.Figure(go.Scatterpolar(
            r=[norm_words, norm_entropy, norm_pauses, norm_fillers],
            theta=r_labels,
            fill='toself', fillcolor='rgba(20, 184, 166, 0.3)', line=dict(color='#14b8a6', width=2)
        ))
        fig_radar.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)',
                                           radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                                                           gridcolor="rgba(255,255,255,0.1)"),
                                           angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#F8FAFC")),
                                showlegend=False, height=320, margin=dict(l=40, r=40, t=30, b=40),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    col_raw, col_anom = st.columns(2, gap="large")

    with col_raw:
        st.markdown(f"#### 📊 {t('Biomarcadores Lingüísticos', 'Linguistic Biomarkers')}")
        with st.container(border=True):
            st.write(f"**🗣️ {t('Palabras Generadas', 'Words Generated')}:** {det['kelime_sayisi']}")
            st.write(f"**🔤 {t('Riqueza Léxica (Entropía)', 'Lexical Richness')}:** {det['sozcuk_entropisi']:.2f}")
            st.write(f"**⏱️ {t('Duración Total', 'Total Duration')}:** {det['toplam_sure']:.1f} sec")

            # Probabilities alt kısıma eklendi
            st.markdown(f"**🔬 {t('Análisis XGBoost', 'XGBoost Analysis')}:**")
            st.caption(
                f"Sano (Healthy): %{res['prob_hc']} | DCL (MCI): %{res['prob_mci']} | Alzheimer: %{res['prob_ad']}")

    with col_anom:
        st.markdown(f"#### ⚠️ {t('Problemas de Habla', 'Speech Issues')}")
        with st.container(border=True):
            st.write(f"**⏸️ {t('Pausas Totales', 'Total Pauses')}:** {det['duraksama']}")

            filler_text = ", ".join([f"'{k}': {v}x" for k, v in det['dolgular'].items()]) if det['dolgular'] else t(
                "Ninguno", "None")
            empty_text = ", ".join([f"'{k}': {v}x" for k, v in det['bos_kelimeler'].items()]) if det[
                'bos_kelimeler'] else t("Ninguno", "None")

            st.write(f"**🗣️ {t('Muletillas', 'Fillers')}:** {filler_text}")
            st.write(f"**📉 {t('Palabras Vacías', 'Empty Words')}:** {empty_text}")

    with st.expander(f"📝 {t('Ver Transcripción', 'View Transcription')}"):
        st.markdown(f"> {det['hasta_metni']}")

    # =========================================================
    # AKSİYON BUTONLARI
    # =========================================================
    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    with b1:
        pdf_bytes = create_spanish_pdf(fig_gauge, fig_radar)
        if pdf_bytes:
            st.download_button(
                label=t("📄 Descargar PDF", "📄 Download PDF Report"),
                data=pdf_bytes,
                file_name=f"Spanish_Report_{age}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with b2:
        if st.button(t("💡 Ver Recomendaciones Clínicas", "💡 View Clinical Recommendations"), type="secondary",
                     use_container_width=True):
            st.session_state.source_page = "spanish"
            st.switch_page("pages/recommendations.py")

    with b3:
        if st.button(t("🔄 Iniciar Nuevo Análisis", "🔄 Start New Analysis"), type="primary", use_container_width=True):
            st.session_state.audio_bytes = None
            st.session_state.analysis_results_spanish = None
            st.switch_page("pages/spanish.py")