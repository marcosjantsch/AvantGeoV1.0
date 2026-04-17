# -*- coding: utf-8 -*-
from pathlib import Path
import streamlit as st


def render_header(
    logo_path: str,
    app_name: str,
    version: str,
    user: str,
    role: str,
    username=None,
    authenticator=None,
    subtitle: str = "",
):
    """
    Header compacto:
    - sem linha superior destacada
    - logout ao lado do bloco usuário/perfil
    - layout mais alto e alinhado na mesma linha
    """

    with st.container():
        st.markdown(
            """
            <style>
            .header-card {
                border: none;
                border-radius: 0;
                padding: 2px 4px 8px 4px;
                margin: 0 0 6px 0;
                background: transparent;
                box-shadow: none;
            }

            .header-title {
                font-size: 22px;
                font-weight: 700;
                line-height: 1.0;
                margin: 0;
                padding: 0;
            }

            .header-version {
                font-size: 11px;
                font-weight: 600;
                opacity: 0.65;
                margin-left: 6px;
            }

            .header-subtitle {
                font-size: 12px;
                opacity: 0.75;
                margin-top: 2px;
                line-height: 1.1;
            }

            .header-user-wrap {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 14px;
                width: 100%;
                margin-top: 2px;
            }

            .header-user {
                font-size: 13px;
                line-height: 1.25;
                text-align: right;
                white-space: nowrap;
            }

            div[data-testid="stButton"] > button[kind="secondary"] {
                min-height: 34px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="header-card">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([0.08, 0.60, 0.32], vertical_alignment="center")

        with col1:
            logo_ok = False
            if logo_path:
                path = Path(logo_path).resolve()
                if path.exists():
                    try:
                        st.image(str(path), width=56)
                        logo_ok = True
                    except Exception:
                        logo_ok = False

            if not logo_ok:
                st.markdown(
                    """
                    <div style="
                        width:56px;
                        height:56px;
                        border-radius:50%;
                        background:linear-gradient(135deg, #0f766e, #1d4ed8);
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        color:white;
                        font-size:18px;
                        font-weight:700;
                        margin:auto;
                    ">
                        AG
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown(
                f"""
                <div class="header-title">
                    {app_name}
                    <span class="header-version">{version}</span>
                </div>
                <div class="header-subtitle">{subtitle}</div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            inner1, inner2 = st.columns([0.72, 0.28], vertical_alignment="center")

            with inner1:
                st.markdown(
                    f"""
                    <div class="header-user">
                        <div><strong>Usuário:</strong> {user}</div>
                        <div><strong>Perfil:</strong> {role}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with inner2:
                if authenticator is not None:
                    try:
                        authenticator.logout("Logout", "main")
                    except Exception:
                        pass

        st.markdown("</div>", unsafe_allow_html=True)
