# -*- coding: utf-8 -*-
import streamlit as st

from tabs.sidebar.entrada import render_sidebar_entrada
from tabs.sidebar.imagens import render_sidebar_imagens
from tabs.sidebar.exportar import render_sidebar_exportar
from tabs.sidebar.processamento_sentinel import (
    render_sidebar_processamento_sentinel,
)


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