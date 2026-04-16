import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        /* =========================================================
           AJUSTES GERAIS DA PÁGINA
        ========================================================= */
        .block-container {
            padding-top: 0.35rem !important;
            padding-bottom: 1rem !important;
        }

        header[data-testid="stHeader"] {
            height: 0rem !important;
        }

        section.main > div {
            padding-top: 0rem !important;
        }

        /* =========================================================
           TÍTULO PRINCIPAL
        ========================================================= */
        .main-title {
            font-size: 24px !important;
            font-weight: 600 !important;
            margin-top: -6px !important;
            margin-bottom: 8px !important;
            line-height: 1.2 !important;
        }

        /* =========================================================
           TÍTULOS DE SEÇÃO
        ========================================================= */
        .section-title {
            font-size: 14px !important;
            font-weight: 600 !important;
            margin-top: 2px !important;
            margin-bottom: 6px !important;
            opacity: 0.95 !important;
            line-height: 1.2 !important;
        }

        /* =========================================================
           USERBAR
        ========================================================= */
        .userbar {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            margin-top: -4px;
            margin-bottom: 4px;
            white-space: nowrap;
        }

        .userbar .pill {
            padding: 2px 8px;
            border: 1px solid rgba(49, 51, 63, 0.25);
            border-radius: 999px;
            background-color: rgba(240, 240, 240, 0.6);
        }

        /* =========================================================
           BOTÕES
        ========================================================= */
        div[data-testid="stButton"] > button {
            padding: 0.25rem 0.6rem !important;
            font-size: 11px !important;
            min-height: 30px !important;
            border-radius: 8px !important;
        }

        /* =========================================================
           SIDEBAR
        ========================================================= */
        section[data-testid="stSidebar"] {
            padding-top: 0.4rem !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 0.2rem !important;
            padding-bottom: 0.3rem !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
            margin-bottom: 0.02rem !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            margin-top: 0.15rem !important;
            margin-bottom: 0.35rem !important;
            line-height: 1.2 !important;
        }

        section[data-testid="stSidebar"] h1 {
            font-size: 18px !important;
        }

        section[data-testid="stSidebar"] h2 {
            font-size: 16px !important;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 14px !important;
        }

        section[data-testid="stSidebar"] label {
            margin-bottom: 2px !important;
            font-size: 12px !important;
        }

        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] .stDateInput,
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stNumberInput,
        section[data-testid="stSidebar"] .stMultiselect {
            margin-bottom: 0.2rem !important;
        }

        section[data-testid="stSidebar"] hr {
            margin: 0.45rem 0 !important;
        }

        /* IMPORTANTE: não mexer em img da sidebar */

        /* =========================================================
           TABS
        ========================================================= */
        button[role="tab"] {
            font-size: 13px !important;
            padding: 6px 10px !important;
        }

        /* =========================================================
           MÉTRICAS
        ========================================================= */
        div[data-testid="stMetric"] {
            padding: 6px !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 12px !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 20px !important;
        }

        /* =========================================================
           DATAFRAMES
        ========================================================= */
        div[data-testid="stDataFrame"] {
            border-radius: 8px !important;
        }

        /* =========================================================
           ALERTAS
        ========================================================= */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }

 
        
        </style>
        """,
        unsafe_allow_html=True,
    )