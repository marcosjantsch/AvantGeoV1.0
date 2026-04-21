# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from services.coordinate_service import get_default_capture_payload


def ensure_session_state():
    defaults = {
        "aplicar": False,
        "modo_entrada": "Empresa / Fazenda",
        "filtro_aplicado": {},
        "selected_satellites": [],
        "coord_system": None,
        "parsed_coordinates": None,
        "uploaded_kml_name": None,
        "uploaded_kml_file": None,
        "query_gdf": None,
        "roi_geojson": None,
        "available_images": [],
        "selected_image_ids": [],
        "buffer_m": 200,
        "cloud_pct": 25,
        "captured_coordinate": get_default_capture_payload(),
        "map_hover_coordinate": None,
        "export_result": None,
        "export_in_progress": False,
        "last_export_error": None,
        "sb_export_include_boundary_png": True,
        "capture_initialized": True,
        "capture_marker_active": False,
        "capture_last_marker_click": None,
        "capture_last_map_click": None,
        "capture_map_center": [
            get_default_capture_payload()["latitude"],
            get_default_capture_payload()["longitude"],
        ],
        "coordinate_component_signature": None,
        "image_selection_nonce": 0,
        "query_result_nonce": 0,
        "sb_modo_entrada": "Empresa / Fazenda",
        "_last_ui_mode": "Empresa / Fazenda",
        "_sidebar_mode_nonce": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
