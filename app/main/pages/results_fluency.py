import streamlit as st
import plotly.graph_objects as go
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Fluency Report", page_icon="⏱️", layout="wide")

# Eğer sonuç yoksa ana sayfaya at
if 'analysis_results_fluency' not in st.session_state or st.session_state.analysis_results_fluency is None:
    st.switch_page("pages/fluency.py")

res = st.session_state.analysis_results_fluency

# =========================================================
# 🛑 HATA KONTROLÜ (KEYERROR: 'DETAILS' ÇÖZÜMÜ)
# =========================================================
if res.get("status") == "error":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(f"🛑 Analysis Rejected: {res.get('message')}")
    st.info("Tip: Ensure the patient is naming animals clearly and the recording is long enough.")

    if st.button("⬅️ Go Back to Fluency Page", type="primary"):
        st.session_state.audio_bytes = None
        st.session_state.analysis_results_fluency = None
        st.switch_page("pages/fluency.py")

# =========================================================
# ✅ EĞER HATA YOKSA SAYFAYI ÇİZ
# =========================================================
else:
    det = res["details"]
    age = st.session_state.get("patient_age", "Unknown")
    gender = st.session_state.get("patient_gender", "Unknown")
    today_date = datetime.date.today().strftime('%B %d, %Y')


    # PDF OLUŞTURMA FONKSİYONU
    def create_fluency_pdf(fig_gauge, fig_radar):
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
            pdf.cell(0, 15, "NEUROVOICE AI - VERBAL FLUENCY REPORT", ln=True, align="C")
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
            pdf.cell(0, 8, f"Dementia Risk: %{res['prob_hasta']}", ln=1)
            pdf.cell(0, 8, f"Isolation Score: {res.get('isolation_score', 0)}", ln=1)

            pdf.ln(10)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Fluency Profile Map:", ln=True)
            pdf.image(radar_path, x=110, y=115, h=70)

            pdf.ln(5)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 7, f"- Total Words: {det['toplam_kelime']}", ln=True)
            pdf.cell(0, 7, f"- Pauses: {det['duraksama']}", ln=True)
            pdf.cell(0, 7, f"- Micro-Stutters: {det['kisa_takilma']}", ln=True)

            pdf.set_y(-20)
            pdf.set_font("helvetica", "I", 8)
            pdf.cell(0, 10, "Disclaimer: Screening tool only.", align="C")

            return bytes(pdf.output())
        except Exception as e:
            st.error(f"PDF Error: {e}")
            return None
        finally:
            if os.path.exists(gauge_path): os.remove(gauge_path)
            if os.path.exists(radar_path): os.remove(radar_path)


    # BANNER
    st.markdown(f"""
        <div style='background: linear-gradient(90deg, #0B1117 0%, #1A222C 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #14b8a6; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;'>
            <div><h2 style='margin: 0; color: #F8FAFC;'>Neurovoice AI Clinical Report</h2><p style='margin: 0; color: #14b8a6; font-size: 1.1rem;'>Target: English (Verbal Fluency)</p></div>
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
            title={'text': "Dementia Risk Score", 'font': {'size': 18}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': gauge_color, 'thickness': 0.75},
                'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#1A222C",
                'steps': [{'range': [0, 40], 'color': "rgba(34, 197, 94, 0.1)"},
                          {'range': [40, 70], 'color': "rgba(245, 158, 11, 0.1)"},
                          {'range': [70, 100], 'color': "rgba(239, 68, 68, 0.1)"}],
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_radar:
        st.markdown("<h4 style='color: #F8FAFC;'>🕸️ Fluency Profile Map</h4>", unsafe_allow_html=True)
        norm_words = min(det['toplam_kelime'] * 4, 100)
        norm_anomia = max(100 - (det['anomi'] * 80), 0)
        norm_pauses = max(100 - (det['duraksama'] * 5), 0)
        norm_stutters = max(100 - (det['kisa_takilma'] * 10), 0)

        fig_radar = go.Figure(go.Scatterpolar(
            r=[norm_words, norm_anomia, norm_pauses, norm_stutters],
            theta=['Word Generation', 'Noun Retrieval', 'Speech Flow', 'Motor Stability'],
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
        st.markdown("#### 📊 Fluency Biomarkers")
        with st.container(border=True):
            st.write(f"**🗣️ Words Generated:** {det['toplam_kelime']}")
            st.write(f"**🔤 Pronoun/Noun Ratio:** {det['anomi']:.2f}")
            st.write(f"**📉 Isolation Score:** {res['isolation_score']:.3f}")

    with col_anom:
        st.markdown("#### ⚠️ Motor & Speech Issues")
        with st.container(border=True):
            st.write(f"**⏸️ Total Pauses:** {det['duraksama']}")
            st.write(f"**〰️ Micro-Stutters:** {det['kisa_takilma']}")
            if det['hata_yerleri']:
                st.error(f"**Long Pauses:** {', '.join(det['hata_yerleri'])}")
            else:
                st.success("✔️ No major frozen pauses detected.")

    with st.expander("📝 View Transcription"):
        st.markdown(f"**🧑‍⚕️ DOCTOR:**\n> {det['doktor_metni']}")
        st.markdown(f"**🎯 PATIENT:**\n> {det['hasta_metni']}")

        # AKSİYON BUTONLARI
        st.markdown("---")
        b1, b2, b3 = st.columns(3)

        with b1:
            # PDF oluşturma işlemini sadece indirme butonuna tıklandığında yapacak şekilde optimize edelim
            pdf_bytes = create_fluency_pdf(fig_gauge, fig_radar)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Fluency_Report_{age}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with b2:
            # Tıklandığında direkt geçiş yapması için basit yapı
            if st.button("💡 View Clinical Recommendations", type="secondary", use_container_width=True):
                st.session_state.source_page = "fluency"
                st.switch_page("pages/recommendations.py")

        with b3:
            if st.button("🔄 Start New Fluency Analysis", type="primary", use_container_width=True):
                # State temizliği
                st.session_state.audio_bytes = None
                st.session_state.analysis_results_fluency = None
                st.switch_page("pages/fluency.py")