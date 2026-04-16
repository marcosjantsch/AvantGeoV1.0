# -*- coding: utf-8 -*-
import streamlit as st


def render_sidebar_exportar(available_images=None):
    if available_images is None:
        available_images = []

    st.markdown("### Exportar imagem")

    # Nome do arquivo (mantém padrão)
    export_filename = st.text_input(
        "Nome do arquivo",
        value=st.session_state.get("export_filename", "imagem_exportada"),
        key="export_filename_input",
    )

    # Botão de exportação
    export_requested = st.button(
        "📤 Exportar imagem",
        use_container_width=True,
        key="btn_exportar_imagem",
    )

    # Atualiza session_state
    st.session_state["export_filename"] = export_filename

    return {
        "export_filename": export_filename,
        "export_requested": export_requested,
    }
