# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import pandas as pd
import streamlit as st

from core.settings import DEFAULT_START_DATE
from services.coordinate_interaction_service import clear_applied_query_state
from services.coordinate_service import (
    DEFAULT_CAPTURE_CITY_NAME,
    DEFAULT_CAPTURE_LATITUDE,
    DEFAULT_CAPTURE_LONGITUDE,
    build_capture_payload,
    format_dd,
    parse_coordinates_text,
)
from services.gee_catalog import get_satellite_start_date


SATELLITE_OPTIONS = [
    "Sentinel-2",
    "Sentinel-1 SAR GRD (C-band)",
    "HLS (Harmonized Landsat Sentinel)",
    "NASADEM",
    "SRTM",
    "HydroSHEDS",
    "MERIT Hydro",
    "Landsat 8",
    "Landsat 9",
    "Landsat 7",
    "Landsat 5",
]


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


def render_empresa_fazenda(gdf_full):
    empresas = _safe_unique_values(gdf_full, "EMPRESA")
    shapefile_loaded = gdf_full is not None and not getattr(gdf_full, "empty", True)

    if not shapefile_loaded:
        st.info("Nao foi possivel carregar a base de empresas e fazendas.")

    empresa_options = [""] + empresas if empresas else [""]
    current_empresa = st.session_state.get("sb_selected_empresa", "")
    empresa_index = empresa_options.index(current_empresa) if current_empresa in empresa_options else 0

    selected_empresa = st.selectbox(
        "Empresa",
        options=empresa_options,
        index=empresa_index,
        key="sb_selected_empresa",
        disabled=not shapefile_loaded,
    )

    fazendas = _safe_filter_fazendas(gdf_full, selected_empresa) if shapefile_loaded else []
    fazenda_options = [""] + fazendas if fazendas else [""]
    current_fazenda = st.session_state.get("sb_selected_fazenda", "")
    fazenda_index = fazenda_options.index(current_fazenda) if current_fazenda in fazenda_options else 0

    selected_fazenda = st.selectbox(
        "Fazenda",
        options=fazenda_options,
        index=fazenda_index,
        key="sb_selected_fazenda",
        disabled=not shapefile_loaded,
    )

    return selected_empresa or None, selected_fazenda or None


def render_captura():
    st.caption(
        f"Ponto inicial em {DEFAULT_CAPTURE_CITY_NAME} "
        f"({DEFAULT_CAPTURE_LATITUDE:.6f}, {DEFAULT_CAPTURE_LONGITUDE:.6f})"
    )

    captured = st.session_state.get("captured_coordinate")
    if captured:
        st.success(
            f"Coordenada atual: {captured.get('latitude'):.6f}, {captured.get('longitude'):.6f}"
        )

    return st.session_state.get("captured_coordinate")


def render_coordenada_manual():
    st.session_state.setdefault(
        "sb_coord_text",
        f"{DEFAULT_CAPTURE_LATITUDE:.6f}, {DEFAULT_CAPTURE_LONGITUDE:.6f}",
    )

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
                current = st.session_state.get("captured_coordinate") or {}
                current_lat = current.get("latitude")
                current_lon = current.get("longitude")
                new_lat = parsed_coordinates.get("latitude")
                new_lon = parsed_coordinates.get("longitude")
                coordinate_changed = (
                    current_lat is None
                    or current_lon is None
                    or abs(float(current_lat) - float(new_lat)) >= 0.000001
                    or abs(float(current_lon) - float(new_lon)) >= 0.000001
                )

                st.session_state["captured_coordinate"] = build_capture_payload(
                    latitude=new_lat,
                    longitude=new_lon,
                    source="manual_input",
                    label="Coordenada informada manualmente",
                )
                st.session_state["parsed_coordinates"] = st.session_state["captured_coordinate"]
                st.session_state["capture_map_center"] = [
                    float(new_lat),
                    float(new_lon),
                ]
                st.session_state["coordinate_component_signature"] = f"{float(new_lat):.6f},{float(new_lon):.6f}"
                if coordinate_changed:
                    clear_applied_query_state()
                st.success(
                    f"Coordenada valida: {new_lat:.6f}, {new_lon:.6f}"
                )
        except Exception as e:
            st.warning(f"Coordenada invalida: {e}")

    captured = st.session_state.get("captured_coordinate")
    if captured:
        st.caption(
            f"Ponto no mapa: {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))}"
        )

    return st.session_state.get("captured_coordinate") or parsed_coordinates


def render_kml_upload():
    uploaded_kml = st.file_uploader(
        "Enviar arquivo KML/KMZ",
        type=["kml", "kmz"],
        key="sb_uploaded_kml",
    )

    if uploaded_kml is not None:
        st.success(f"Arquivo selecionado: {uploaded_kml.name}")

    return uploaded_kml


def render_satellites():
    current = st.session_state.get("sb_selected_satellites", ["Sentinel-2"])
    if not current:
        current = ["Sentinel-2"]

    selected_satellites = st.multiselect(
        "Satelites",
        options=SATELLITE_OPTIONS,
        default=current,
        key="sb_selected_satellites",
    )

    if not selected_satellites:
        selected_satellites = ["Sentinel-2"]

    return selected_satellites


def _parse_iso_date(date_str: str, fallback: date) -> date:
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return fallback


def _resolve_allowed_start_date(selected_satellites) -> date:
    satellites = selected_satellites or ["Sentinel-2"]
    candidates = [
        _parse_iso_date(get_satellite_start_date(satellite, DEFAULT_START_DATE), _parse_iso_date(DEFAULT_START_DATE, date.today()))
        for satellite in satellites
    ]
    return min(candidates) if candidates else _parse_iso_date(DEFAULT_START_DATE, date.today())


def render_dates(selected_satellites=None):
    today = date.today()
    min_start_date = _resolve_allowed_start_date(selected_satellites)
    default_start = st.session_state.get("sb_start_date", min_start_date)
    default_end = st.session_state.get("sb_end_date", today)

    if pd.to_datetime(default_start).date() < min_start_date:
        default_start = min_start_date
        st.session_state["sb_start_date"] = min_start_date

    if pd.to_datetime(default_end).date() < min_start_date:
        default_end = min_start_date
        st.session_state["sb_end_date"] = min_start_date

    if pd.to_datetime(default_end).date() > today:
        default_end = today
        st.session_state["sb_end_date"] = today

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data inicial",
            value=default_start,
            min_value=min_start_date,
            max_value=today,
            key="sb_start_date",
        )
    with col2:
        end_date = st.date_input(
            "Data final",
            value=default_end,
            min_value=min_start_date,
            max_value=today,
            key="sb_end_date",
        )

    if isinstance(start_date, list):
        start_date = start_date[0]
    if isinstance(end_date, list):
        end_date = end_date[0]

    if pd.to_datetime(start_date) > pd.to_datetime(end_date):
        st.warning("A data inicial nao pode ser maior que a data final.")

    if selected_satellites and "Sentinel-2" in selected_satellites:
        st.caption("Sentinel-2 disponivel de 27/06/2015 ate a data atual na consulta.")

    return pd.to_datetime(start_date).date(), pd.to_datetime(end_date).date()


def render_parameters():
    buffer_m = st.number_input(
        "Buffer / raio da ROI (m)",
        min_value=0,
        max_value=10000,
        value=int(st.session_state.get("sb_buffer_m", 200)),
        step=50,
        key="sb_buffer_m",
    )

    cloud_pct = st.slider(
        "Cobertura maxima de nuvem (%)",
        min_value=0,
        max_value=100,
        value=int(st.session_state.get("sb_cloud_pct", 25)),
        step=1,
        key="sb_cloud_pct",
    )

    return buffer_m, cloud_pct
