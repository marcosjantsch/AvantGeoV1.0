# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from core.ee_init import init_ee
from core.settings import GEO_PATH
from services.file_service import load_shapefile_full


def reset_export_state():
    st.session_state["export_result"] = None
    st.session_state["last_export_error"] = None
    st.session_state["export_in_progress"] = False
    st.session_state["roi_ready_for_export"] = False


def reset_query_state_for_mode_change():
    st.session_state["aplicar"] = False
    st.session_state["filtro_aplicado"] = {}
    st.session_state["query_gdf"] = None
    st.session_state["roi_geojson"] = None
    st.session_state["available_images"] = []
    st.session_state["selected_scene_id"] = None
    st.session_state["selected_product_name"] = None
    st.session_state["sb_selected_scene_label"] = None
    st.session_state["sb_selected_product_name"] = None
    st.session_state["uploaded_kml_name"] = None
    st.session_state["uploaded_kml_file"] = None
    st.session_state["map_hover_coordinate"] = None
    st.session_state["capture_marker_active"] = False
    st.session_state["capture_last_marker_click"] = None
    st.session_state["capture_last_map_click"] = None
    reset_export_state()


def sanitize_available_images_state():
    available_images = st.session_state.get("available_images") or []
    if not available_images:
        return

    satellites_with_full_asset_ids = {
        "Sentinel-1 (10 m radar)",
        "HLS (Harmonized Landsat Sentinel)",
    }

    has_stale_entry = any(
        img.get("satellite") in satellites_with_full_asset_ids
        and "/" not in str(img.get("asset_id") or "")
        for img in available_images
    )

    stale_selected_scene = (
        st.session_state.get("selected_scene_id") is not None
        and "/" not in str(st.session_state.get("selected_scene_id"))
        and any(
            img.get("satellite") in satellites_with_full_asset_ids
            for img in available_images
        )
    )

    if has_stale_entry or stale_selected_scene:
        st.session_state["available_images"] = []
        st.session_state["selected_scene_id"] = None
        st.session_state["selected_product_name"] = None
        st.session_state["sb_selected_scene_label"] = None
        st.session_state["sb_selected_product_name"] = None


def ensure_ee_initialized():
    if st.session_state.get("_ee_initialized", False):
        return True, None

    ok_ee, msg_ee = init_ee()
    if ok_ee:
        st.session_state["_ee_initialized"] = True
        return True, None

    return False, msg_ee


def get_gdf_full_lazy(force_reload: bool = False):
    if not force_reload and st.session_state.get("_gdf_full_cache") is not None:
        return st.session_state["_gdf_full_cache"]

    gdf_full = load_shapefile_full(GEO_PATH)
    st.session_state["_gdf_full_cache"] = gdf_full
    return gdf_full
