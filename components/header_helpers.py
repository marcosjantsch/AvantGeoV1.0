# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st


def mode_colors(current_mode: str) -> tuple[str, str, str]:
    mode = (current_mode or "").strip().lower()

    if "empresa" in mode and "fazenda" in mode:
        return ("rgba(14, 116, 144, 0.12)", "rgba(14, 116, 144, 0.28)", "#0f766e")
    if "captur" in mode:
        return ("rgba(220, 38, 38, 0.10)", "rgba(220, 38, 38, 0.30)", "#dc2626")
    if "coordenada" in mode:
        return ("rgba(37, 99, 235, 0.10)", "rgba(37, 99, 235, 0.28)", "#2563eb")
    if "kml" in mode or "kmz" in mode or "arquivo" in mode:
        return ("rgba(124, 58, 237, 0.10)", "rgba(124, 58, 237, 0.28)", "#7c3aed")
    return ("rgba(75, 85, 99, 0.10)", "rgba(75, 85, 99, 0.22)", "#374151")


def sanitize_header_inputs(app_name, version, user, role, current_mode, subtitle, username):
    return {
        "app_name": escape(app_name or "Avant GEO"),
        "version": escape(version or ""),
        "user": escape(user or "-"),
        "role": escape(role or "-"),
        "current_mode": escape(current_mode or "-"),
        "subtitle": escape(subtitle or ""),
        "username": escape(username or "-"),
    }


def render_logo_or_fallback(logo_path: str):
    logo_ok = False

    if logo_path:
        path = Path(logo_path).resolve()
        if path.exists():
            try:
                st.image(str(path), width=58)
                logo_ok = True
            except Exception:
                logo_ok = False

    if not logo_ok:
        st.markdown(
            """
            <div class="ag-header-logo-fallback">
                AG
            </div>
            """,
            unsafe_allow_html=True,
        )
