# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from services.coordinate_service import build_capture_payload


def clear_applied_query_state():
    st.session_state["filtro_aplicado"] = {}
    st.session_state["query_gdf"] = None
    st.session_state["roi_geojson"] = None
    st.session_state["roi_ready_for_export"] = False
    st.session_state["available_images"] = []
    st.session_state["selected_scene_id"] = None
    st.session_state["selected_product_name"] = None
    st.session_state["sb_selected_scene_label"] = None
    st.session_state["sb_selected_product_name"] = None
    st.session_state["export_result"] = None
    st.session_state["last_export_error"] = None


def sync_coordinate_payload(payload) -> bool:
    if not isinstance(payload, dict):
        return False

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if latitude is None or longitude is None:
        return False

    signature = f"{float(latitude):.6f},{float(longitude):.6f}"
    if st.session_state.get("coordinate_component_signature") == signature:
        return False

    current = st.session_state.get("captured_coordinate") or {}
    current_lat = current.get("latitude")
    current_lon = current.get("longitude")

    if (
        current_lat is not None
        and current_lon is not None
        and abs(float(current_lat) - float(latitude)) < 0.000001
        and abs(float(current_lon) - float(longitude)) < 0.000001
    ):
        return False

    coordinate_payload = build_capture_payload(
        latitude=latitude,
        longitude=longitude,
        source=payload.get("source", "map_update"),
        label="Coordenada ajustada no mapa",
    )
    st.session_state["captured_coordinate"] = coordinate_payload
    st.session_state["parsed_coordinates"] = coordinate_payload
    st.session_state["capture_map_center"] = [float(latitude), float(longitude)]
    st.session_state["sb_coord_text"] = f"{float(latitude):.6f}, {float(longitude):.6f}"
    st.session_state["coordinate_component_signature"] = signature
    clear_applied_query_state()
    return True
