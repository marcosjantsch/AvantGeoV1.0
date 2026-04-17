# -*- coding: utf-8 -*-
from __future__ import annotations

import re

import streamlit as st

from services.coordinate_service import CAPTURE_MODE_LABEL


def _sanitize_filename(text: str) -> str:
    text = str(text or "").strip()
    text = text.replace(" ", "_")
    text = text.replace("%", "pct")
    text = re.sub(r"[^\w\-.]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def _build_source_label() -> str:
    modo = st.session_state.get("modo_entrada") or st.session_state.get("sb_modo_entrada")

    if modo == "Empresa / Fazenda":
        filtro = st.session_state.get("filtro_aplicado", {})
        empresa = filtro.get("selected_empresa") or st.session_state.get("sb_selected_empresa") or ""
        fazenda = filtro.get("selected_fazenda") or st.session_state.get("sb_selected_fazenda") or ""
        parts = [p for p in [empresa, fazenda] if p]
        return "_".join(parts) if parts else "Empresa_Fazenda"

    if modo in ["Coordenada", CAPTURE_MODE_LABEL]:
        return "Coordenada"

    if modo == "Arquivo KML/KMZ":
        nome = st.session_state.get("uploaded_kml_name") or "Arquivo_KML_KMZ"
        nome = nome.rsplit(".", 1)[0]
        return nome

    return "Consulta"


def render_sidebar_exportar(available_images=None):
    if available_images is None:
        available_images = []

    if "sb_export_filename" not in st.session_state:
        st.session_state["sb_export_filename"] = ""

    selected_scene_id_mem = st.session_state.get("selected_scene_id")
    selected_product_mem = st.session_state.get("selected_product_name")
    export_result = st.session_state.get("export_result")
    export_in_progress = st.session_state.get("export_in_progress", False)

    st.markdown("### Exportação")

    has_data = bool(st.session_state.get("available_images")) and bool(selected_scene_id_mem) and bool(selected_product_mem)

    scene_for_export = next(
        (img for img in available_images if img.get("id") == selected_scene_id_mem),
        None,
    )

    sat_name = scene_for_export.get("satellite") if scene_for_export else ""
    scene_date = scene_for_export.get("date") if scene_for_export else ""
    cloud_value = scene_for_export.get("cloud") if scene_for_export else None
    product_name_export = selected_product_mem or ""

    cloud_txt = ""
    if cloud_value is not None:
        try:
            cloud_txt = f"{float(cloud_value):.1f}pct"
        except Exception:
            cloud_txt = str(cloud_value)

    source_label = _build_source_label()

    suggested_filename = _sanitize_filename(
        "_".join(
            [
                p
                for p in [
                    source_label,
                    sat_name,
                    scene_date,
                    cloud_txt,
                    product_name_export,
                ]
                if p
            ]
        )
    ) or "exportacao_imagem"

    last_auto = st.session_state.get("_last_auto_export_filename", "")
    current_name = st.session_state.get("sb_export_filename", "")

    if not current_name or current_name == last_auto:
        st.session_state["sb_export_filename"] = suggested_filename

    st.session_state["_last_auto_export_filename"] = suggested_filename

    st.text_input(
        "Nome base do arquivo",
        key="sb_export_filename",
        disabled=not has_data,
    )

    st.caption("Serão gerados dois arquivos em memória: PNG para visualização e TIFF raster original.")

    export_requested = False

    if not has_data:
        st.info("A exportação será habilitada após existir ROI válida, imagem listada, cena selecionada e produto definido.")
    else:
        export_requested = st.button(
            "📦 Gerar arquivos para download",
            use_container_width=True,
            key="sb_export_requested",
            disabled=export_in_progress,
        )
        if export_requested:
            st.session_state["export_result"] = None
    
    if export_result:
        st.success("Arquivos prontos para download.")
        st.download_button(
            label="📥 Baixar PNG",
            data=export_result.get("png_bytes"),
            file_name=export_result.get("png_name", "imagem.png"),
            mime="image/png",
            use_container_width=True,
            key=f"download_png_{export_result.get('png_name', 'imagem.png')}",
        )
        st.download_button(
            label="📥 Baixar TIFF georreferenciado",
            data=export_result.get("tif_bytes"),
            file_name=export_result.get("tif_name", "imagem.tif"),
            mime="image/tiff",
            use_container_width=True,
            key=f"download_tif_{export_result.get('tif_name', 'imagem.tif')}",
        )

    return {
        "export_filename": st.session_state.get("sb_export_filename", ""),
        "export_requested": export_requested,
    }
