# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from services.coordinate_service import (
    CAPTURE_MODE_LABEL,
    DEFAULT_CAPTURE_CITY_NAME,
    DEFAULT_CAPTURE_LATITUDE,
    DEFAULT_CAPTURE_LONGITUDE,
    build_capture_payload,
    parse_coordinates_text,
)


MODO_EMPRESA_FAZENDA = "Empresa / Fazenda"
MODO_COORDENADA = "Coordenada"
MODO_KML = "Arquivo KML/KMZ"

SATELLITE_OPTIONS = ["Sentinel-2", "Landsat 8", "Landsat 9", "Landsat 7", "Landsat 5"]


def _ensure_capture_coordinate_initialized():
    if st.session_state.get("captured_coordinate") is None:
        st.session_state["captured_coordinate"] = build_capture_payload(
            latitude=DEFAULT_CAPTURE_LATITUDE,
            longitude=DEFAULT_CAPTURE_LONGITUDE,
            source="default_city_center",
        )


def _safe_unique_values(gdf, column: str):
    if gdf is None or getattr(gdf, "empty", True):
        return []
    if column not in gdf.columns:
        return []
    vals = gdf[column].dropna().astype(str).str.strip()
    vals = vals[vals != ""]
    return sorted(vals.unique().tolist())


def _safe_filter_fazendas(gdf, empresa: Optional[str]):
    if gdf is None or getattr(gdf, "empty", True):
        return []
    if "FAZENDA" not in gdf.columns:
        return []

    gdf_aux = gdf.copy()
    if empresa and "EMPRESA" in gdf_aux.columns:
        gdf_aux = gdf_aux[gdf_aux["EMPRESA"].astype(str) == str(empresa)]

    vals = gdf_aux["FAZENDA"].dropna().astype(str).str.strip()
    vals = vals[vals != ""]
    return sorted(vals.unique().tolist())


def _render_empresa_fazenda(gdf_full):
    empresas = _safe_unique_values(gdf_full, "EMPRESA")

    shapefile_loaded = gdf_full is not None and not getattr(gdf_full, "empty", True)

    if not shapefile_loaded:
        st.info(
            "O shapefile ainda não foi carregado. "
            "As listas de empresa e fazenda serão carregadas após a primeira consulta aplicada."
        )

    empresa_options = [""] + empresas if empresas else [""]
    empresa_index = 0

    current_empresa = st.session_state.get("sb_selected_empresa", "")
    if current_empresa in empresa_options:
        empresa_index = empresa_options.index(current_empresa)

    selected_empresa = st.selectbox(
        "Empresa",
        options=empresa_options,
        index=empresa_index,
        key="sb_selected_empresa",
        disabled=not shapefile_loaded,
    )

    fazendas = _safe_filter_fazendas(gdf_full, selected_empresa) if shapefile_loaded else []
    fazenda_options = [""] + fazendas if fazendas else [""]
    fazenda_index = 0

    current_fazenda = st.session_state.get("sb_selected_fazenda", "")
    if current_fazenda in fazenda_options:
        fazenda_index = fazenda_options.index(current_fazenda)

    selected_fazenda = st.selectbox(
        "Fazenda",
        options=fazenda_options,
        index=fazenda_index,
        key="sb_selected_fazenda",
        disabled=not shapefile_loaded,
    )

    return selected_empresa or None, selected_fazenda or None


def _render_captura():
    _ensure_capture_coordinate_initialized()

    st.caption(
        f"Ponto inicial: {DEFAULT_CAPTURE_CITY_NAME} "
        f"({DEFAULT_CAPTURE_LATITUDE:.6f}, {DEFAULT_CAPTURE_LONGITUDE:.6f})"
    )

    captured = st.session_state.get("captured_coordinate")
    if captured:
        st.success(
            f"Coordenada atual: {captured.get('latitude'):.6f}, {captured.get('longitude'):.6f}"
        )

    return st.session_state.get("captured_coordinate")


def _render_coordenada_manual():
    coord_text = st.text_input(
        "Coordenada (ex.: -24.248421, -49.692840)",
        key="sb_coord_text",
        placeholder="-24.248421, -49.692840",
    )

    parsed_coordinates = None
    if coord_text.strip():
        try:
            parsed_coordinates = parse_coordinates_text(coord_text)
            if parsed_coordinates:
                st.success(
                    f"Coordenada válida: {parsed_coordinates.get('latitude'):.6f}, "
                    f"{parsed_coordinates.get('longitude'):.6f}"
                )
        except Exception as e:
            st.warning(f"Coordenada inválida: {e}")

    return parsed_coordinates


def _render_kml_upload():
    uploaded_kml = st.file_uploader(
        "Enviar arquivo KML/KMZ",
        type=["kml", "kmz"],
        key="sb_uploaded_kml",
    )

    if uploaded_kml is not None:
        st.success(f"Arquivo selecionado: {uploaded_kml.name}")

    return uploaded_kml


def _render_satellites():
    current = st.session_state.get("sb_selected_satellites", ["Sentinel-2"])
    if not current:
        current = ["Sentinel-2"]

    selected_satellites = st.multiselect(
        "Satélites",
        options=SATELLITE_OPTIONS,
        default=current,
        key="sb_selected_satellites",
    )

    if not selected_satellites:
        selected_satellites = ["Sentinel-2"]

    return selected_satellites


def _render_dates():
    today = date.today()
    default_start = st.session_state.get("sb_start_date", date(today.year, 1, 1))
    default_end = st.session_state.get("sb_end_date", today)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data inicial",
            value=default_start,
            key="sb_start_date",
        )
    with col2:
        end_date = st.date_input(
            "Data final",
            value=default_end,
            key="sb_end_date",
        )

    if isinstance(start_date, list):
        start_date = start_date[0]
    if isinstance(end_date, list):
        end_date = end_date[0]

    if pd.to_datetime(start_date) > pd.to_datetime(end_date):
        st.warning("A data inicial não pode ser maior que a data final.")

    return pd.to_datetime(start_date).date(), pd.to_datetime(end_date).date()


def _render_parameters():
    buffer_m = st.number_input(
        "Buffer / raio da ROI (m)",
        min_value=0,
        max_value=10000,
        value=int(st.session_state.get("sb_buffer_m", 200)),
        step=50,
        key="sb_buffer_m",
    )

    cloud_pct = st.slider(
        "Cobertura máxima de nuvem (%)",
        min_value=0,
        max_value=100,
        value=int(st.session_state.get("sb_cloud_pct", 25)),
        step=1,
        key="sb_cloud_pct",
    )

    return buffer_m, cloud_pct


def render_sidebar_entrada(gdf_full):
    _ensure_capture_coordinate_initialized()

    modo_options = [
        MODO_EMPRESA_FAZENDA,
        CAPTURE_MODE_LABEL,
        MODO_COORDENADA,
        MODO_KML,
    ]

    current_mode = st.session_state.get("sb_modo_entrada", CAPTURE_MODE_LABEL)
    if current_mode not in modo_options:
        current_mode = CAPTURE_MODE_LABEL

    modo_entrada = st.radio(
        "Modo de entrada",
        options=modo_options,
        index=modo_options.index(current_mode),
        key="sb_modo_entrada",
    )

    selected_empresa = None
    selected_fazenda = None
    parsed_coordinates = None
    uploaded_kml = None

    st.markdown("---")

    if modo_entrada == MODO_EMPRESA_FAZENDA:
        selected_empresa, selected_fazenda = _render_empresa_fazenda(gdf_full)

    elif modo_entrada == CAPTURE_MODE_LABEL:
        parsed_coordinates = _render_captura()

    elif modo_entrada == MODO_COORDENADA:
        parsed_coordinates = _render_coordenada_manual()

    elif modo_entrada == MODO_KML:
        uploaded_kml = _render_kml_upload()

    st.markdown("---")

    selected_satellites = _render_satellites()
    start_date, end_date = _render_dates()
    buffer_m, cloud_pct = _render_parameters()

    st.markdown("---")

    apply = st.button(
        "Aplicar consulta",
        use_container_width=True,
        key="sb_apply_query",
    )

    return {
        "modo_entrada": modo_entrada,
        "selected_empresa": selected_empresa,
        "selected_fazenda": selected_fazenda,
        "selected_satellites": selected_satellites,
        "start_date": start_date,
        "end_date": end_date,
        "buffer_m": buffer_m,
        "cloud_pct": cloud_pct,
        "apply": apply,
        "parsed_coordinates": parsed_coordinates,
        "uploaded_kml": uploaded_kml,
    }
