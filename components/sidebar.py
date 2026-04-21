# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from services.coordinate_service import (
    DEFAULT_CAPTURE_CITY_NAME,
    format_dd,
)
from tabs.sidebar.entrada import render_sidebar_entrada
from tabs.sidebar.exportar import render_sidebar_exportar
from tabs.sidebar.imagens import render_sidebar_imagens


def _render_mode_summary():
    modo_entrada = st.session_state.get("sb_modo_entrada") or st.session_state.get("modo_entrada") or "-"
    mode_styles = {
        "Empresa / Fazenda": {
            "bg": "rgba(22, 163, 74, 0.14)",
            "border": "rgba(22, 163, 74, 0.28)",
            "text": "#166534",
        },
        "Coordenada": {
            "bg": "rgba(37, 99, 235, 0.14)",
            "border": "rgba(37, 99, 235, 0.28)",
            "text": "#1d4ed8",
        },
        "Arquivo KML/KMZ": {
            "bg": "rgba(217, 119, 6, 0.14)",
            "border": "rgba(217, 119, 6, 0.28)",
            "text": "#b45309",
        },
    }
    style = mode_styles.get(
        modo_entrada,
        {"bg": "rgba(120,120,120,0.10)", "border": "rgba(120,120,120,0.18)", "text": "#4b5563"},
    )

    st.markdown(
        f"""
        <div style="
            margin: 3px 0 4px 0;
            padding: 7px 10px;
            border-radius: 12px;
            border: 1px solid rgba(120,120,120,0.18);
            background: rgba(255,255,255,0.03);
        ">
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                <div style="font-size:11px; font-weight:700; opacity:0.75; text-transform:uppercase;">
                    Modo Ativo
                </div>
                <div style="
                    padding: 3px 9px;
                    border-radius: 999px;
                    font-size: 11px;
                    font-weight: 700;
                    background: {style["bg"]};
                    border: 1px solid {style["border"]};
                    color: {style["text"]};
                ">
                    {modo_entrada}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_capture_summary():
    captured = st.session_state.get("captured_coordinate")

    st.markdown("### Coordenada atual")
    st.caption(
        "O ponto inicia em Jaguariaiva, Parana. Voce pode editar no campo de coordenada ou mover o marcador no mapa segurando CTRL."
    )

    if captured:
        source = captured.get("source")
        if source == "default_city_center":
            st.info(f"Ponto inicial carregado em {DEFAULT_CAPTURE_CITY_NAME}.")
        else:
            st.success("Ponto atualmente definido no mapa.")

        st.markdown(f"**DD:** {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))}")
        st.markdown(
            f"**DMS:** {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')}"
        )
    else:
        st.info("Nenhum ponto disponivel.")


def render_sidebar(gdf_full, available_images=None):
    if available_images is None:
        available_images = []

    with st.sidebar:
        st.markdown(
            '<div style="font-size:15px; font-weight:600; margin-bottom:-8px;">Selecione as opcoes</div>',
            unsafe_allow_html=True,
        )
        _render_mode_summary()

        tab_entrada, tab_imagens, tab_exportar = st.tabs(["Entrada", "Imagens", "Exportar"])

        with tab_entrada:
            st.session_state.get("_sidebar_mode_nonce", 0)
            entrada_data = render_sidebar_entrada(gdf_full)
            if entrada_data.get("modo_entrada") == "Coordenada":
                st.markdown("---")
                _render_capture_summary()

        with tab_imagens:
            imagens_data = render_sidebar_imagens(available_images)

        with tab_exportar:
            export_data = render_sidebar_exportar(available_images)

    result = {}
    result.update(entrada_data)
    result.update(imagens_data)
    result.update(export_data)

    result.setdefault("tipo_dado", "Dados Empresa/Fazenda")
    result.setdefault("selected_uf", None)
    result.setdefault("selected_municipio", None)
    result.setdefault("log_container", None)

    return result
