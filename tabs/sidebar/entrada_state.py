# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from services.coordinate_service import (
    DEFAULT_CAPTURE_LATITUDE,
    DEFAULT_CAPTURE_LONGITUDE,
    build_capture_payload,
)


MODO_EMPRESA_FAZENDA = "Empresa / Fazenda"
MODO_COORDENADA = "Coordenada"
MODO_KML = "Arquivo KML/KMZ"


def ensure_capture_coordinate_initialized():
    if st.session_state.get("captured_coordinate") is None:
        st.session_state["captured_coordinate"] = build_capture_payload(
            latitude=DEFAULT_CAPTURE_LATITUDE,
            longitude=DEFAULT_CAPTURE_LONGITUDE,
            source="default_city_center",
        )


def apply_mode_state(modo_entrada: str):
    st.session_state["modo_entrada"] = modo_entrada
    st.session_state["_last_ui_mode"] = modo_entrada
    st.session_state["_sidebar_mode_nonce"] = int(st.session_state.get("_sidebar_mode_nonce", 0)) + 1

    if modo_entrada == MODO_COORDENADA:
        captured = st.session_state.get("captured_coordinate")
        if captured and captured.get("latitude") is not None and captured.get("longitude") is not None:
            st.session_state["capture_map_center"] = [
                float(captured["latitude"]),
                float(captured["longitude"]),
            ]

    st.session_state["aplicar"] = False
    st.session_state["filtro_aplicado"] = {}
    st.session_state["query_gdf"] = None
    st.session_state["roi_geojson"] = None
    st.session_state["available_images"] = []
    st.session_state["selected_scene_id"] = None
    st.session_state["selected_product_name"] = None
    st.session_state["uploaded_kml_name"] = None
    st.session_state["roi_ready_for_export"] = False
    st.session_state["export_result"] = None
    st.session_state["export_in_progress"] = False
    st.session_state["last_export_error"] = None
    st.session_state["sb_selected_scene_label"] = None
    st.session_state["sb_selected_product_name"] = None
    st.session_state["uploaded_kml_name"] = None
    st.session_state["uploaded_kml_file"] = None
    st.session_state["map_hover_coordinate"] = None
    st.session_state["capture_marker_active"] = False
    st.session_state["capture_last_marker_click"] = None
    st.session_state["capture_last_map_click"] = None
    st.session_state["coordinate_editor_leaflet"] = None


def handle_mode_change():
    modo_entrada = st.session_state.get("sb_modo_entrada", MODO_EMPRESA_FAZENDA)
    apply_mode_state(modo_entrada)
