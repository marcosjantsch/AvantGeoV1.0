# -*- coding: utf-8 -*-
import re
import streamlit as st

from services.dialog_service import select_output_directory


def _sanitize_filename(text: str) -> str:
    text = str(text or "").strip()
    text = text.replace(" ", "_")
    text = text.replace("%", "pct")
    text = re.sub(r"[^\w\-.]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def _build_source_label() -> str:
    modo = st.session_state.get("modo_entrada")

    if modo == "Empresa / Fazenda":
        filtro = st.session_state.get("filtro_aplicado", {})
        empresa = filtro.get("selected_empresa") or ""
        fazenda = filtro.get("selected_fazenda") or ""
        parts = [p for p in [empresa, fazenda] if p]
        return "_".join(parts) if parts else "Empresa_Fazenda"

    if modo == "Coordenada":
        return "Coordenada"

    if modo == "Arquivo KML/KMZ":
        nome = st.session_state.get("uploaded_kml_name") or "Arquivo_KML_KMZ"
        nome = nome.rsplit(".", 1)[0]
        return nome

    return "Consulta"


def render_sidebar_exportar(available_images=None):
    if available_images is None:
        available_images = []

    # ---------------------------------------------------------
    # Inicialização
    # ---------------------------------------------------------
    if "sb_export_output_dir" not in st.session_state:
        st.session_state["sb_export_output_dir"] = ""

    if "sb_export_filename" not in st.session_state:
        st.session_state["sb_export_filename"] = ""

    # aplica valor pendente ANTES de criar widgets
    pending_dir = st.session_state.pop("_pending_export_output_dir", None)
    if pending_dir is not None:
        st.session_state["sb_export_output_dir"] = pending_dir

    selected_scene_id_mem = st.session_state.get("selected_scene_id")
    selected_product_mem = st.session_state.get("selected_product_name")

    st.markdown("### Exportação")

    # ---------------------------------------------------------
    # Caminho de saída
    # ---------------------------------------------------------
    c1, c2 = st.columns([0.72, 0.28])

    with c1:
        st.text_input(
            "Caminho de saída",
            key="sb_export_output_dir",
            placeholder=r"C:\Saidas\Mapas",
        )

    with c2:
        st.write("")
        st.write("")
        if st.button("📂 Procurar pasta", use_container_width=True, key="sb_pick_folder"):
            picked = select_output_directory(st.session_state.get("sb_export_output_dir", ""))
            if picked:
                st.session_state["_pending_export_output_dir"] = picked
                st.rerun()

    # ---------------------------------------------------------
    # Nome sugerido
    # ---------------------------------------------------------
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
                p for p in [
                    source_label,
                    sat_name,
                    scene_date,
                    cloud_txt,
                    product_name_export,
                ] if p
            ]
        )
    )

    last_auto = st.session_state.get("_last_auto_export_filename", "")
    current_name = st.session_state.get("sb_export_filename", "")

    if not current_name or current_name == last_auto:
        st.session_state["sb_export_filename"] = suggested_filename

    st.session_state["_last_auto_export_filename"] = suggested_filename

    st.text_input(
        "Nome base do arquivo",
        key="sb_export_filename",
    )

    st.caption("Serão gerados dois arquivos: .jpg e .tif georreferenciado")

    export_requested = st.button(
        "📦 Exportar imagem selecionada",
        use_container_width=True,
        key="sb_export_requested",
    )

    return {
        "export_output_dir": st.session_state.get("sb_export_output_dir", ""),
        "export_filename": st.session_state.get("sb_export_filename", ""),
        "export_requested": export_requested,
    }