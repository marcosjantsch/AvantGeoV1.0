# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from components.header_helpers import render_logo_or_fallback, sanitize_header_inputs
from components.header_styles import build_header_styles


def render_header(
    logo_path: str,
    app_name: str,
    version: str,
    user: str,
    role: str,
    current_mode: str = "",
    username=None,
    authenticator=None,
    subtitle: str = "",
):
    values = sanitize_header_inputs(app_name, version, user, role, current_mode, subtitle, username)

    with st.container():
        st.markdown(
            build_header_styles(),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="ag-header-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="ag-header-card">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([0.07, 0.55, 0.38], vertical_alignment="center")

        with col1:
            render_logo_or_fallback(logo_path)

        with col2:
            st.markdown(
                f"""
                <div class="ag-header-left">
                    <div>
                        <div class="ag-header-title-row">
                            <div class="ag-header-title">{values["app_name"]}</div>
                            <div class="ag-header-version">{values["version"]}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            inner1, inner2 = st.columns([0.80, 0.20], vertical_alignment="center")

            with inner1:
                st.markdown(
                    f"""
                    <div class="ag-header-user-row">
                        <div class="ag-header-user-inline">
                            <strong>Sessão atual</strong> |
                            <strong>Usuário:</strong> {values["user"]} |
                            <strong>Perfil:</strong> {values["role"]} |
                            <strong>Login:</strong> {values["username"]}
                        </div>
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
        st.markdown("</div>", unsafe_allow_html=True)
