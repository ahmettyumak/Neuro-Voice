import streamlit as st
import plotly.graph_objects as go
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Sentence Report", page_icon="🧩", layout="wide")

if 'analysis_results_sentence' not in st.session_state or st.session_state.analysis_results_sentence is None:
    st.switch_page("pages/sentence.py")

res = st.session_state.analysis_results_sentence

if res.get("status") == "error":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(f"🛑 Analysis Rejected: {res.get('message')}")
    st.info("Tip: Ensure the patient is actively constructing or repeating sentences.")
    if st.button("⬅️ Go Back to Sentence Page", type="primary"):
        st.session_state.audio_bytes = None
        st.session_state.analysis_results_sentence = None
        st.switch_page("pages/sentence.py")
else:
    det = res["details"]
    age = st.session_state.get("patient_age", "Unknown")
    gender = st.session_state.get("patient_gender", "Unknown")
    today_date = datetime.date.today().strftime('%B %d, %Y')


    def create_sentence_pdf(fig_gauge, fig_radar):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_gauge:
            gauge_path = tmp_gauge.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_radar:
            radar_path = tmp_radar.name
        try:
            fig_gauge.write_image(gauge_path)
            fig_radar.write_image(radar_path)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 20)
            pdf.set_text_color(20, 184, 166)
            pdf.cell(0, 15, "NEUROVOICE AI - SYNTAX & SENTENCE REPORT", ln=True, align="C")
            pdf.line(10, 25, 200, 25)
            pdf.ln(8)

            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, f"Patient Demographics:", ln=True)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"Age: {age}   |   Gender: {gender}   |   Date: {today_date}", ln=True)

            pdf.ln(10)
            pdf.image(gauge_path, x=135, y=60, w=50)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"AI Decision: {res['diagnosis']}", ln=1)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"Syntactic Deficit Risk: %{res['prob_hasta']}", ln=1)
            pdf.cell(0, 8, f"Isolation Score: {res.get('isolation_score', 0)}", ln=1)

            pdf.ln(10)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Syntactic Profile Map:", ln=True)
            pdf.image(radar_path, x=110, y=115, h=70)

            pdf.ln(5)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 7, f"- Construction Pauses: {det['duraksama']}", ln=True)
            pdf.cell(0, 7, f"- Syntactic Repetitions: {det['kelime_tekrari']}", ln=True)
            pdf.cell(0, 7, f"- Pronoun/Noun Ratio: {det['anomi']:.2f}", ln=True)

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
            <div><h2 style='margin: 0; color: #F8FAFC;'>Neurovoice AI Clinical Report</h2><p style='margin: 0; color: #14b8a6; font-size: 1.1rem;'>Target: English (Sentence & Syntax)</p></div>
            <div style='text-align: right; color: #F8FAFC;'><p style='margin: 0;'><b>Patient:</b> {age} y/o, {gender}</p><p style='margin: 0;'><b>Date:</b> {today_date}</p></div>
        </div>
    """, unsafe_allow_html=True)

    col_radar, col_verdict = st.columns([1.2, 1], gap="large")

    with col_verdict:
        st.markdown("<h4 style='color: #F8FAFC;'>🧠 Final AI Decision (IsoForest)</h4>", unsafe_allow_html=True)
        if res["risk_level"] == "low":
            gauge_color = "#22c55e"
        elif res["risk_level"] == "medium":
            gauge_color = "#f59e0b"
        else:
            gauge_color = "#ef4444"

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=res['prob_hasta'],
            number={'suffix': "%", 'font': {'size': 40, 'color': gauge_color}},
            title={'text': "Syntactic Deficit Risk", 'font': {'size': 18}},
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
        st.markdown("<h4 style='color: #F8FAFC;'>🕸️ Syntactic Profile Map</h4>", unsafe_allow_html=True)
        # Sentence Modülüne Özel Map
        norm_complexity = min(det['toplam_kelime'] * 3, 100)
        norm_anomia = max(100 - (det['anomi'] * 80), 0)
        norm_pauses = max(100 - (det['duraksama'] * 5), 0)
        norm_rep = max(100 - (det['kelime_tekrari'] * 15), 0)  # Fazla tekrar = düşük puan

        fig_radar = go.Figure(go.Scatterpolar(
            r=[norm_complexity, norm_anomia, norm_pauses, norm_rep],
            theta=['Sentence Length', 'Noun Usage', 'Construction Flow', 'Repetition Control'],
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
        st.markdown("#### 📊 Syntactic Biomarkers")
        with st.container(border=True):
            st.write(f"**🗣️ Syntactic Repetitions:** {det['kelime_tekrari']} times")
            st.write(f"**🔤 Pronoun/Noun Ratio:** {det['anomi']:.2f}")
            st.write(f"**📉 Isolation Score:** {res['isolation_score']:.3f}")

    with col_anom:
        st.markdown("#### ⚠️ Sentence Construction Issues")
        with st.container(border=True):
            st.write(f"**⏸️ Construction Pauses:** {det['duraksama']}")
            if det['hata_yerleri']:
                st.error(f"**Long Pauses:** {', '.join(det['hata_yerleri'])}")
            else:
                st.success("✔️ No major frozen pauses detected.")

    with st.expander("📝 View Transcription"):
        st.markdown(f"**🧑‍⚕️ DOCTOR:**\n> {det['doktor_metni']}")
        st.markdown(f"**🎯 PATIENT:**\n> {det['hasta_metni']}")

    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    with b1:
        pdf_bytes = create_sentence_pdf(fig_gauge, fig_radar)
        if pdf_bytes:
            st.download_button(label="📄 Download PDF Report", data=pdf_bytes, file_name=f"Sentence_Report_{age}.pdf",
                               mime="application/pdf", use_container_width=True)

    with b2:
        if st.button("💡 View Clinical Recommendations", type="secondary", use_container_width=True):
            st.session_state.source_page = "sentence"
            st.switch_page("pages/recommendations.py")

    with b3:
        if st.button("🔄 Start New Sentence Analysis", type="primary", use_container_width=True):
            st.session_state.audio_bytes = None
            st.session_state.analysis_results_sentence = None
            st.switch_page("pages/sentence.py")