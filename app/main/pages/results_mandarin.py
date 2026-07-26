import streamlit as st
import plotly.graph_objects as go
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Mandarin Report", page_icon="🇨🇳", layout="wide")

if 'analysis_results_mandarin' not in st.session_state or st.session_state.analysis_results_mandarin is None:
    st.switch_page("pages/mandarin.py")

res = st.session_state.analysis_results_mandarin
lang = st.session_state.get("page_lang", "zh")


def t(zh, en): return zh if lang == "zh" else en


def toggle_lang(): st.session_state.page_lang = "en" if lang == "zh" else "zh"


top_col1, top_col2 = st.columns([8, 1])
with top_col2:
    if st.button("🇬🇧 EN" if lang == "zh" else "🇨🇳 中文", type="primary", use_container_width=True):
        toggle_lang()
        st.rerun()

if res.get("status") == "error":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(f"🛑 {t('分析被拒绝:', 'Analysis Rejected:')} {res.get('message')}")
    if st.button("⬅️ " + t("返回首页", "Go Back"), type="primary"):
        st.session_state.audio_bytes = None
        st.session_state.analysis_results_mandarin = None
        st.switch_page("pages/mandarin.py")
else:
    det = res["details"]
    age = st.session_state.get("patient_age", "Unknown")
    gender = st.session_state.get("patient_gender", "Unknown")
    gender_display = "女性" if gender == "Female" and lang == "zh" else "男性" if gender == "Male" and lang == "zh" else gender
    today_date = datetime.date.today().strftime('%B %d, %Y')


    def create_mandarin_pdf(fig_gauge, fig_radar):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_gauge:
            gauge_path = tmp_gauge.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_radar:
            radar_path = tmp_radar.name
        try:
            fig_gauge.write_image(gauge_path)
            fig_radar.write_image(radar_path)

            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(20, 184, 166)
            pdf.cell(0, 15, "NEUROVOICE AI - CLINICAL REPORT (MANDARIN)", ln=True, align="C")
            pdf.line(10, 25, 200, 25)
            pdf.ln(8)

            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "Patient Demographics:", ln=True)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"Age: {age}   |   Gender: {gender}   |   Date: {today_date}", ln=True)

            pdf.ln(10)
            pdf.image(gauge_path, x=135, y=60, w=50)

            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "AI Decision:", ln=1)
            pdf.set_font("helvetica", "", 12)

            if res["risk_level"] == "high":
                pdf.set_text_color(239, 68, 68)
            elif res["risk_level"] == "medium":
                pdf.set_text_color(245, 158, 11)
            else:
                pdf.set_text_color(34, 197, 94)

            safe_diag = res['diagnosis_en'].encode('ascii', 'ignore').decode('ascii')
            pdf.cell(0, 8, safe_diag, ln=1)

            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, f"MCI Probability: %{res['prob_mci']}", ln=1)
            pdf.cell(0, 8, f"Healthy Probability: %{res['prob_hc']}", ln=1)

            pdf.ln(15)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Cognitive Profile Map:", ln=True)
            pdf.image(radar_path, x=110, y=125, h=70)

            pdf.ln(5)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 7, f"- Word Output: {det['kelime_sayisi']}", ln=True)
            pdf.cell(0, 7, f"- Total Pauses: {det['duraksama']}", ln=True)
            pdf.cell(0, 7, f"- Lexical Richness: {det['sozcuk_entropisi']:.2f}", ln=True)

            pdf.set_y(-20)
            pdf.set_font("helvetica", "I", 8)
            pdf.cell(0, 10, "Disclaimer: Screening tool only.", align="C")

            return bytes(pdf.output())
        except Exception as e:
            return None
        finally:
            if os.path.exists(gauge_path): os.remove(gauge_path)
            if os.path.exists(radar_path): os.remove(radar_path)


    st.markdown(f"""
        <div style='background: linear-gradient(90deg, #0B1117 0%, #1A222C 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #14b8a6; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h2 style='margin: 0; color: #F8FAFC;'>Neurovoice AI Clinical Report</h2>
                <p style='margin: 0; color: #14b8a6; font-size: 1.1rem;'>{t('目标: 中文模块 (XGBoost)', 'Target: Mandarin Module (XGBoost)')}</p>
            </div>
            <div style='text-align: right; color: #F8FAFC;'>
                <p style='margin: 0;'><b>{t('患者', 'Patient')}:</b> {age} {t('岁', 'y/o')}, {gender_display}</p>
                <p style='margin: 0;'><b>{t('日期', 'Date')}:</b> {today_date}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_radar, col_verdict = st.columns([1.2, 1], gap="large")

    with col_verdict:
        st.markdown(f"<h4 style='color: #F8FAFC;'>🧠 {t('AI 最终决定', 'Final AI Decision')}</h4>",
                    unsafe_allow_html=True)
        if res["risk_level"] == "low":
            gauge_color = "#22c55e"
        elif res["risk_level"] == "medium":
            gauge_color = "#f59e0b"
        else:
            gauge_color = "#ef4444"

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=res['prob_mci'],
            number={'suffix': "%", 'font': {'size': 40, 'color': gauge_color}},
            title={'text': t("MCI 概率 (轻度认知障碍)", "MCI Probability"), 'font': {'size': 18}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1}, 'bar': {'color': gauge_color, 'thickness': 0.75},
                'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#1A222C",
                'steps': [{'range': [0, 40], 'color': "rgba(34, 197, 94, 0.1)"},
                          {'range': [40, 60], 'color': "rgba(245, 158, 11, 0.1)"},
                          {'range': [60, 100], 'color': "rgba(239, 68, 68, 0.1)"}],
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_radar:
        st.markdown(f"<h4 style='color: #F8FAFC;'>🕸️ {t('认知概况图', 'Cognitive Profile Map')}</h4>",
                    unsafe_allow_html=True)

        norm_words = min(det['kelime_sayisi'] * 2, 100)
        norm_entropy = min(det['sozcuk_entropisi'] * 15, 100)
        norm_pauses = max(100 - (det['duraksama'] * 5), 0)
        fillers = sum(det['dolgular'].values()) if det['dolgular'] else 0
        norm_fillers = max(100 - (fillers * 10), 0)

        r_labels = [t('词汇量', 'Word Output'), t('词汇丰富度', 'Lexical Richness'), t('语流', 'Speech Flow'),
                    t('语气词控制', 'Filler Control')]

        fig_radar = go.Figure(go.Scatterpolar(
            r=[norm_words, norm_entropy, norm_pauses, norm_fillers], theta=r_labels,
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
        st.markdown(f"#### 📊 {t('语言学特征', 'Linguistic Biomarkers')}")
        with st.container(border=True):
            st.write(f"**🗣️ {t('词数', 'Words Generated')}:** {det['kelime_sayisi']}")
            st.write(f"**🔤 {t('词汇丰富度', 'Lexical Richness')}:** {det['sozcuk_entropisi']:.2f}")
            st.write(f"**⏱️ {t('总时长', 'Total Duration')}:** {det['toplam_sure']:.1f} sec")

            st.markdown(f"**🔬 {t('XGBoost 分析', 'XGBoost Analysis')}:**")
            st.caption(f"Healthy: %{res['prob_hc']} | MCI: %{res['prob_mci']}")

    with col_anom:
        st.markdown(f"#### ⚠️ {t('语音问题', 'Speech Issues')}")
        with st.container(border=True):
            st.write(f"**⏸️ {t('总停顿次数', 'Total Pauses')}:** {det['duraksama']}")
            filler_text = ", ".join([f"'{k}': {v}x" for k, v in det['dolgular'].items()]) if det['dolgular'] else t(
                "无", "None")
            st.write(f"**🗣️ {t('语气词', 'Fillers')}:** {filler_text}")

    with st.expander(f"📝 {t('查看语音转录', 'View Transcription')}"):
        st.markdown(f"> {det['hasta_metni']}")

    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    with b1:
        pdf_bytes = create_mandarin_pdf(fig_gauge, fig_radar)
        if pdf_bytes:
            st.download_button(label=t("📄 下载 PDF 报告", "📄 Download PDF Report"), data=pdf_bytes,
                               file_name=f"Mandarin_Report_{age}.pdf", mime="application/pdf", use_container_width=True)

    with b2:
        if st.button(t("💡 查看临床建议", "💡 View Clinical Recommendations"), type="secondary",
                     use_container_width=True):
            st.session_state.source_page = "mandarin"
            st.switch_page("pages/recommendations.py")

    with b3:
        if st.button(t("🔄 开始新分析", "🔄 Start New Analysis"), type="primary", use_container_width=True):
            st.session_state.audio_bytes = None
            st.session_state.analysis_results_mandarin = None
            st.switch_page("pages/mandarin.py")