# -*- coding: utf-8 -*-
import streamlit as st


def ensure_session_state():
    defaults = {
        "aplicar": False,
        "modo_entrada": None,
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
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value