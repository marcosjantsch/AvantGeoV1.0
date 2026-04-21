# -*- coding: utf-8 -*-
import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #020617 0%, #030712 100%);
            color: #e5fff3;
        }
        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(2,6,23,0.96) 0%, rgba(3,12,10,0.98) 100%);
            border-right: 1px solid rgba(16,185,129,0.20);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.0rem;
        }
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.85);
            color: #d1fae5;
            border: 1px solid rgba(16, 185, 129, 0.16);
            border-radius: 10px 10px 0 0;
        }
        [data-testid="stSidebar"] .stTabs [aria-selected="true"] {
            background: rgba(5, 150, 105, 0.18);
            color: #a7f3d0;
            border-color: rgba(52, 211, 153, 0.35);
        }
        .stButton > button,
        .stDownloadButton > button {
            background: linear-gradient(180deg, #052e1f 0%, #064e3b 100%);
            color: #ecfdf5;
            border: 1px solid rgba(52, 211, 153, 0.35);
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(110, 231, 183, 0.55);
            color: #bbf7d0;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        .stDateInput > div,
        .stTextInput > div > div,
        .stNumberInput > div > div {
            background: rgba(3, 7, 18, 0.92) !important;
            color: #ecfdf5 !important;
            border: 1px solid rgba(16, 185, 129, 0.24) !important;
        }
        .stMultiSelect label,
        .stDateInput label,
        .stTextInput label,
        .stNumberInput label,
        .stSlider label,
        .stRadio label,
        .stMarkdown,
        .stCaption,
        .stSubheader {
            color: #d1fae5 !important;
        }
        [data-baseweb="tag"] {
            background: rgba(5, 150, 105, 0.18) !important;
            color: #a7f3d0 !important;
        }
        div[data-testid="stMetric"] {
            background: rgba(3, 7, 18, 0.86);
            border: 1px solid rgba(16, 185, 129, 0.18);
            border-radius: 18px;
            padding: 10px 14px;
        }
        [data-testid="stInfo"],
        [data-testid="stSuccess"],
        [data-testid="stWarning"],
        [data-testid="stError"] {
            background: rgba(3, 7, 18, 0.90);
            color: #ecfdf5;
            border: 1px solid rgba(52, 211, 153, 0.24);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
