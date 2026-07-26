def app_css(bg, text, card_bg, border, input_bg, browse_bg, browse_text, layout_border, upload_hint):
    return f"""
    <style>
        /* 🚨 SORUNLU STREAMLIT SINIFLARINI DEVRE DIŞI BIRAKMA 🚨 */
        .st-ev {{ background-color: transparent !important; }}
        .st-emotion-cache-zh4rd8 {{ background-color: transparent !important; }}
        [data-testid="stAppViewContainer"] {{ background-color: {bg} !important; }}

         /* ==========================================
           🌟 DIŞ KATMANA (stLayoutWrapper) BEYAZ GROOVE ÇERÇEVE
           ========================================== */
        [data-testid="stLayoutWrapper"] {{
            border: {layout_border} !important;
            border-radius: 15px !important;
            padding: 10px !important;
            background-color: {bg} !important;
        }}

        /* 1. SİDEBAR VE ÜST MENÜYÜ KÖKÜNDEN YOK ET */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {{ display: none !important; width: 0px !important; margin: 0px !important; padding: 0px !important; visibility: hidden !important; }}
        header, [data-testid="stHeader"], .stApp > header {{ display: none !important; height: 0px !important; background: transparent !important; }}
        footer, [data-testid="stFooter"] {{ display: none !important; }}
        section.main {{ max-width: 100% !important; padding-top: 2rem !important; padding-left: 0 !important; padding-right: 0 !important; }}

        /* 2. GENEL TEMA VE YAZILAR */
        .stApp {{ background-color: {bg} !important; font-family: 'Inter', sans-serif; transition: background-color 0.4s ease; }}
        h1, h2, h3, h4, h5, h6, p, span, label {{ color: {text} !important; }}
        .main-title {{ text-align: center; font-size: 2.8rem; font-weight: 800; color: #0d9488 !important; margin-bottom: 0px; }}
        .sub-title {{ text-align: center; font-size: 0.85rem; font-weight: 600; color: {text} !important; letter-spacing: 2px; margin-top: -5px; margin-bottom: 25px; opacity: 0.7; }}

        /* 📏 BÖLÜMLER ARASI İNCE ÇİZGİLER VE SEKMELER */
        hr {{ border-top: 1px solid {border} !important; border-bottom: none !important; margin: 1.5rem 0 !important; }}
        [data-baseweb="tab-list"] {{ border-bottom: 1px solid {border} !important; }}
        [data-baseweb="tab-highlight"] {{ background-color: #0d9488 !important; }}
        [data-baseweb="tab"] {{ color: {text} !important; }}

        /* Kartlar (Container) - DIŞ ÇİZGİLER */
        [data-testid="stVerticalBlockBorderWrapper"] {{ background-color: {card_bg} !important; border: 2px groove {border} !important; border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: all 0.4s ease; }}
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{ background-color: {input_bg} !important; border: 1px solid {border} !important; border-radius: 10px; }}
        input {{ color: {text} !important; }}

        /* 🎯 GENDER SELECTBOX (AÇILIR MENÜ) */
        div[data-baseweb="select"] div, div[data-baseweb="select"] span {{ color: {text} !important; }}
        ul[data-baseweb="menu"], div[data-baseweb="popover"] > div, div[role="listbox"] {{ background-color: {input_bg} !important; border: 1px solid {border} !important; border-radius: 8px !important; }}
        li[role="option"] {{ background-color: transparent !important; color: {text} !important; }}
        li[role="option"]:hover {{ background-color: #0d9488 !important; color: #ffffff !important; }}

        /* Normal Butonlar */
        .stButton > button {{ background-color: {input_bg} !important; color: {text} !important; border: 1px solid {border} !important; border-radius: 10px; width: 100%; height: 50px; font-weight: 500; transition: all 0.3s ease; }}
        .stButton > button:hover {{ border-color: #14b8a6 !important; color: #14b8a6 !important; background-color: rgba(13, 148, 136, 0.05) !important; }}
        .stButton > button[kind="primary"] {{ background-color: rgba(20, 184, 166, 0.1) !important; border-color: #14b8a6 !important; color: #14b8a6 !important; font-weight: bold; }}

        /* ☁️ UPLOAD VE MİKROFON KUTUSU */
        [data-testid="stFileUploader"] > section {{ background-color: {input_bg} !important; border: 2px dashed #0d9488 !important; border-radius: 12px !important; padding: 15px !important; }}
        [data-testid="stFileUploadDropzone"] svg path {{ fill: #0d9488 !important; }}

        /* 🎯 DİNAMİK UPLOAD HİNT YAZISI */
        [data-testid="stFileUploaderDropzoneInstructions"] > div > span {{
            font-size: 0px !important;
            color: transparent !important;
            display: none !important;
        }}
        [data-testid="stFileUploaderDropzoneInstructions"] > div::before {{
            content: "{upload_hint}";
            font-size: 14px !important;
            color: {text} !important;
            opacity: 0.8;
            visibility: visible !important;
            display: block;
            margin-top: 5px;
            margin-bottom: 10px;
        }}

        /* Browse Files Butonu */
        [data-testid="stFileUploadDropzone"] button {{ background-color: {browse_bg} !important; border: 1px solid {border} !important; border-radius: 8px !important; padding: 5px 15px !important; transition: all 0.3s ease !important; }}
        [data-testid="stFileUploadDropzone"] button * {{ color: {browse_text} !important; font-weight: 600 !important; }}
        [data-testid="stFileUploadDropzone"] button:hover {{ background-color: #0d9488 !important; border-color: #0d9488 !important; }}
        [data-testid="stFileUploadDropzone"] button:hover * {{ color: #ffffff !important; }}

        /* Upload & Mikrofon Üst Başlıkları (Label) */
        [data-testid="stFileUploader"] label, [data-testid="stAudioInput"] label {{ color: #0d9488 !important; font-weight: bold; font-size: 1.1rem; }}
        [data-testid="stAudioInput"] {{ border: 2px solid #0d9488 !important; background-color: rgba(13, 148, 136, 0.05) !important; border-radius: 12px; padding: 15px; }}

        /* ⚡ İNİTİATE BUTONU */
        .btn-initiate > button {{ background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%) !important; color: white !important; border: none !important; font-weight: 700 !important; font-size: 1.1rem !important; height: 55px !important; border-radius: 10px !important; box-shadow: 0 4px 20px rgba(20, 184, 166, 0.3) !important; }}
        .btn-initiate > button:hover {{ transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(20, 184, 166, 0.4) !important; }}

        /* 🌗 SAĞ ALT KÖŞE YÜZEN TEMA BUTONU */
        button[kind="tertiary"] {{ position: fixed !important; bottom: 25px !important; right: 25px !important; width: 60px !important; height: 60px !important; border-radius: 50% !important; background: {card_bg} !important; border: 2px solid #0d9488 !important; font-size: 24px !important; z-index: 9999 !important; transition: all 0.3s ease !important; }}
        button[kind="tertiary"]:hover {{ transform: scale(1.1) !important; box-shadow: 0 6px 20px rgba(13, 148, 136, 0.4) !important; }}
    </style>
    """