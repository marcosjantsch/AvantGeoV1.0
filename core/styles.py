# -*- coding: utf-8 -*-
import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #0b1220 0%, #101828 100%);
        }
        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.04);
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.0rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 10px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
