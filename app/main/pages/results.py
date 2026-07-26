import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Neurological Report", page_icon="🧠", layout="wide")

# Eğer sonuç yoksa ana sayfaya at
if 'analysis_results' not in st.session_state or st.session_state.analysis_results is None:
    st.switch_page("app.py")

res = st.session_state.analysis_results

# =========================================================
# 🛑 HATA KONTROLÜNÜ EN BAŞA ALDIK (KEYERROR ÇÖZÜMÜ)
# =========================================================
if res.get("status") == "error":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error(f"🛑 Analysis Rejected: {res.get('message')}")
    st.info("Tip: Make sure the audio contains clear speech related to the 'Cookie Theft' picture.")

    if st.button("⬅️ Go Back to Main Page", type="primary"):
        st.session_state.audio_bytes = None
        st.session_state.analysis_results = None
        st.switch_page("app.py")

# =========================================================
# ✅ EĞER HATA YOKSA (ANALİZ BAŞARILIYSA) SAYFAYI ÇİZ
# =========================================================
else:
    # Detayları GÜVENLİ bir şekilde artık burada çekiyoruz
    det = res["details"]
    age = st.session_state.get("patient_age", "Unknown")
    gender = st.session_state.get("patient_gender", "Unknown")
    today_date = datetime.date.today().strftime('%B %d, %Y')


    # PDF OLUŞTURMA FONKSİYONU
    def create_pdf(fig_gauge, fig_radar):
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
            pdf.cell(0, 15, "NEUROVOICE AI - CLINICAL REPORT", ln=True, align="C")
            pdf.line(10, 25, 200, 25)
            pdf.ln(8)

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, f"Patient Demographics:", ln=True)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"Age: {age}   |   Gender: {gender}   |   Date: {today_date}", ln=True)
            pdf.ln(5)

            pdf.set_font("helvetica", "B", 14)
            pdf.cell(100, 10, f"FINAL AI DECISION:", ln=0)
            pdf.cell(0, 10, f"Dementia Risk Score:", ln=1)

            pdf.set_font("helvetica", "B", 12)
            if res["risk_level"] == "high":
                pdf.set_text_color(239, 68, 68)
            elif res["risk_level"] == "medium":
                pdf.set_text_color(245, 158, 11)
            else:
                pdf.set_text_color(34, 197, 94)

            pdf.cell(100, 10, res['diagnosis'], ln=0)
            pdf.image(gauge_path, x=135, y=60, w=50)

            pdf.ln(10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 11)
            pdf.cell(100, 8, f"Disease Probability: %{res['prob_hasta']}", ln=1)

            pdf.ln(10)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Cognitive Profile Map:", ln=True)
            pdf.image(radar_path, x=110, y=105, h=70)

            pdf.ln(5)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 8, f"Linguistic Data:", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 7, f"- Grammar Complexity: {det['gramer']:.2f}", ln=True)
            pdf.cell(0, 7, f"- Anomia Ratio: {det['anomi']:.2f}", ln=True)
            pdf.cell(0, 7, f"- Concept Recall: {det['kavram']} / 11", ln=True)
            pdf.cell(0, 7, f"- Total Words: {det['toplam_kelime']}", ln=True)

            pdf.ln(5)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 8, "Speech Anomalies:", ln=True)
            pdf.set_font("helvetica", "", 10)

            hata_yok = True
            if det['hata_yerleri']:
                pdf.cell(0, 7, f"- Long Pauses: {', '.join(det['hata_yerleri'])}", ln=True)
                hata_yok = False
            if det['kekelemeler']:
                pdf.cell(0, 7, f"- Stuttered Words: {', '.join(det['kekelemeler'])}", ln=True)
                hata_yok = False
            if hata_yok:
                pdf.cell(0, 7, f"- No major anomalies detected.", ln=True)

            pdf.ln(10)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Patient Transcription Summary:", ln=True)
            pdf.set_font("helvetica", "I", 10)

            safe_text = det["hasta_metni"][:1000].encode('ascii', 'ignore').decode('ascii') + "..."
            pdf.multi_cell(0, 6, f'"{safe_text}"')

            pdf.set_y(-20)
            pdf.set_font("helvetica", "I", 8)
            pdf.cell(0, 10,
                     "Disclaimer: This is an AI-powered pre-screening tool and does not replace professional clinical diagnosis.",
                     align="C")

            return bytes(pdf.output())

        except Exception as e:
            st.error(f"❌ Error during PDF generation: {e}")
            return None

        finally:
            if os.path.exists(gauge_path): os.remove(gauge_path)
            if os.path.exists(radar_path): os.remove(radar_path)


    # 1. KLİNİK BAŞLIK (BANNER)
    st.markdown(f"""
        <div style='background: linear-gradient(90deg, #0B1117 0%, #1A222C 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #14b8a6; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h2 style='margin: 0; color: #F8FAFC;'>Neurovoice AI Clinical Report</h2>
                <p style='margin: 0; color: #14b8a6; font-size: 1.1rem;'>Target: English (Cookie Task)</p>
            </div>
            <div style='text-align: right; color: #F8FAFC;'>
                <p style='margin: 0;'><b>Patient:</b> {age} y/o, {gender}</p>
                <p style='margin: 0;'><b>Date:</b> {today_date}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. ANA DASHBOARD (RADAR VE GÖSTERGE)
    col_radar, col_verdict = st.columns([1.2, 1], gap="large")

    with col_verdict:
        st.markdown("<h4 style='color: #F8FAFC;'>🧠 Final AI Decision</h4>", unsafe_allow_html=True)
        if res["risk_level"] == "low":
            st.success(f"**{res['diagnosis']}**")
            gauge_color = "#22c55e"
        elif res["risk_level"] == "medium":
            st.warning(f"**{res['diagnosis']}**")
            gauge_color = "#f59e0b"
        else:
            st.error(f"**{res['diagnosis']}**")
            gauge_color = "#ef4444"

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=res['prob_hasta'],
            number={'suffix': "%", 'font': {'size': 40, 'color': gauge_color}},
            title={'text': "Dementia Risk Score", 'font': {'size': 18}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': gauge_color, 'thickness': 0.75},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#1A222C",
                'steps': [
                    {'range': [0, 40], 'color': "rgba(34, 197, 94, 0.1)"},
                    {'range': [40, 70], 'color': "rgba(245, 158, 11, 0.1)"},
                    {'range': [70, 100], 'color': "rgba(239, 68, 68, 0.1)"}],
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_radar:
        st.markdown("<h4 style='color: #F8FAFC;'>🕸️ Cognitive Profile Map</h4>", unsafe_allow_html=True)

        norm_grammar = min(det['gramer'] * 15, 100)
        norm_concept = (det['kavram'] / 11) * 100
        norm_anomia = max(100 - (det['anomi'] * 80), 0)
        norm_fluency = max(100 - (det['duraksama'] * 5), 0)
        categories = ['Grammar Depth', 'Concept Recall', 'Lexical Focus', 'Speech Fluency']

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[norm_grammar, norm_concept, norm_anomia, norm_fluency],
            theta=categories,
            fill='toself',
            fillcolor='rgba(20, 184, 166, 0.3)',
            line=dict(color='#14b8a6', width=2),
            name='Patient Profile'
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor="rgba(255,255,255,0.1)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#F8FAFC")
            ),
            showlegend=False, height=320, margin=dict(l=40, r=40, t=30, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # 3. VERİ KARTLARI (METRİKLER VE ANOMALİLER)
    col_raw, col_anom = st.columns(2, gap="large")

    with col_raw:
        st.markdown("#### 📊 Raw Biomarker Data")
        with st.container(border=True):
            st.write(f"**🌳 Tree Depth (Syntax):** {det['gramer']:.2f}")
            st.progress(min(det['gramer'] / 7, 1.0))
            st.write(f"**🧩 Concepts Hit:** {det['kavram']} / 11")
            st.progress(det['kavram'] / 11)
            st.write(f"**🔤 Anomia Ratio:** {det['anomi']:.2f}")
            st.write(f"**🗣️ Total Words Spoken:** {det['toplam_kelime']}")

    with col_anom:
        st.markdown("#### ⚠️ Speech Anomalies")
        with st.container(border=True):
            if det['hata_yerleri']:
                st.error(f"**Frozen Pauses (>0.5s):**\n" + "\n".join([f"- {h}" for h in det['hata_yerleri']]))
            else:
                st.success("✔️ No major brain freezes detected.")

            if det['kekelemeler']:
                st.warning(f"**Stuttered Words:** {', '.join(det['kekelemeler'])}")

            if det['dolgular']:
                d_str = ", ".join([f"'{k}': {v}x" for k, v in det['dolgular'].items()])
                st.info(f"**Fillers Used:** {d_str}")
            else:
                st.write("**Fillers:** Clean speech detected.")

    # 4. TRANSKRİPSİYON GİZLİ PANELİ
    with st.expander("📝 View Doctor/Patient Transcription Separation"):
        st.markdown(f"**🧑‍⚕️ DOCTOR ({det['doktor_sure']:.1f} sec):**\n> {det['doktor_metni']}")
        st.markdown(f"**🎯 PATIENT ({det['hasta_sure']:.1f} sec):**\n> {det['hasta_metni']}")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 5. AKSİYON BUTONLARI
    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    with b1:
        pdf_bytes = create_pdf(fig_gauge, fig_radar)
        if pdf_bytes:
            st.download_button(
                label="📄 Download PDF Report (with Charts)",
                data=pdf_bytes,
                file_name=f"Neurovoice_Report_{age}_{gender}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with b2:
        if st.button("💡 AI Recommendations", type="secondary", use_container_width=True):
            st.switch_page("pages/recommendations.py")

    with b3:
        if st.button("🔄 Start New Patient Analysis", type="primary", use_container_width=True):
            st.session_state.audio_bytes = None
            st.session_state.analysis_results = None
            st.switch_page("app.py")