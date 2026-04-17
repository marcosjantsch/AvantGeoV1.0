# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from services.coordinate_service import CAPTURE_MODE_LABEL, format_dd
from tabs.sidebar.entrada import render_sidebar_entrada
from tabs.sidebar.exportar import render_sidebar_exportar
from tabs.sidebar.imagens import render_sidebar_imagens
from tabs.sidebar.processamento_sentinel import (
    render_sidebar_processamento_sentinel,
)


def _render_capture_summary():
    captured = st.session_state.get("captured_coordinate")
    hover = st.session_state.get("map_hover_coordinate")

    st.markdown("### Captura no mapa")
    st.caption(
        "Abra a aba de mapa, mova o mouse para visualizar a posição atual e clique para definir ou substituir a coordenada."
    )

    if hover and hover.get("latitude") is not None and hover.get("longitude") is not None:
        st.markdown(
            f"**Mouse no mapa:** {format_dd(hover.get('latitude'))}, {format_dd(hover.get('longitude'))}"
        )

    if captured:
        st.success("Coordenada capturada no mapa.")
        st.markdown(f"**DD:** {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))}")
        st.markdown(
            f"**DMS:** {captured.get('latitude_dms', '-') } | {captured.get('longitude_dms', '-') }"
        )
    else:
        st.info("Nenhuma coordenada capturada ainda.")


def render_sidebar(gdf_full, available_images=None):
    if available_images is None:
        available_images = []

    with st.sidebar:
        st.markdown(
            '<div style="font-size:16px; font-weight:600; margin-bottom:-6px;">Selecione as opções</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        tab_entrada, tab_imagens, tab_exportar, tab_proc_sentinel = st.tabs(
            ["Entrada", "Imagens", "Exportar", "Processamento Sentinel"]
        )

        with tab_entrada:
            entrada_data = render_sidebar_entrada(gdf_full)
            if entrada_data.get("modo_entrada") == CAPTURE_MODE_LABEL:
                st.markdown("---")
                _render_capture_summary()

        with tab_imagens:
            imagens_data = render_sidebar_imagens(available_images)

        with tab_exportar:
            export_data = render_sidebar_exportar(available_images)

        with tab_proc_sentinel:
            proc_data = render_sidebar_processamento_sentinel()

    result = {}
    result.update(entrada_data)
    result.update(imagens_data)
    result.update(export_data)
    result.update(proc_data)

    result.setdefault("tipo_dado", "Dados Empresa/Fazenda")
    result.setdefault("selected_uf", None)
    result.setdefault("selected_municipio", None)
    result.setdefault("log_container", None)

    return result
