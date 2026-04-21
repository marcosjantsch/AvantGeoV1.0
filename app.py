# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

import streamlit as st

from app_core.auth import resolve_authenticated_user
from app_core.header_config import build_header_config
from app_core.query_actions import handle_export, infer_default_product_name, run_query
from app_core.runtime import (
    ensure_ee_initialized,
    get_gdf_full_lazy,
    reset_export_state,
    sanitize_available_images_state,
)
from components.header import render_header
from components.sidebar import render_sidebar
from core.settings import APP_ICON, APP_TITLE, AUTH_ENABLED, LAYOUT, LOGO_PATH, SIDEBAR_STATE
from core.styles import apply_styles
from services.coordinate_interaction_service import sync_coordinate_payload
from services.geometry_service import filter_gdf
from services.session_service import ensure_session_state
from tabs.tab_dados_satelite import render_tab_dados_satelite
from tabs.tab_mapa import render_tab_mapa


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)
apply_styles()


def _sync_page_state(modo_entrada, sidebar_data):
    parsed_coordinates = sidebar_data.get("parsed_coordinates")
    if modo_entrada == "Coordenada":
        parsed_coordinates = st.session_state.get("captured_coordinate")

    selected_scene_id = sidebar_data.get("selected_scene_id")
    selected_product_name = sidebar_data.get("selected_product_name")

    st.session_state["modo_entrada"] = modo_entrada
    st.session_state["_last_ui_mode"] = modo_entrada

    if selected_scene_id is not None:
        st.session_state["selected_scene_id"] = selected_scene_id

    if selected_product_name is not None:
        st.session_state["selected_product_name"] = selected_product_name

    if not st.session_state.get("selected_product_name") and st.session_state.get("selected_scene_id"):
        imgs_mem = st.session_state.get("available_images", [])
        if imgs_mem:
            st.session_state["selected_product_name"] = infer_default_product_name(imgs_mem)

    return parsed_coordinates


def _render_main_tabs(modo_entrada, sidebar_data):
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "ℹ️ Info", "🛰️ Dados Satélite"])

    with tab1:
        filtro_aplicado = st.session_state.get("filtro_aplicado", {}) or {}
        applied_mode = filtro_aplicado.get("modo_entrada")
        has_active_query_for_current_mode = applied_mode == modo_entrada

        filtro_shape = {
            "modo_entrada": modo_entrada,
            "selected_empresa": sidebar_data.get("selected_empresa"),
            "selected_fazenda": sidebar_data.get("selected_fazenda"),
            "start_date": sidebar_data.get("start_date"),
            "end_date": sidebar_data.get("end_date"),
            "selected_satellites": sidebar_data.get("selected_satellites", []),
            "buffer_m": sidebar_data.get("buffer_m", 200),
            "cloud_pct": sidebar_data.get("cloud_pct", 25),
        }

        if filtro_aplicado:
            filtro_shape["filtro_aplicado"] = filtro_aplicado

        gdf_full = st.session_state.get("_gdf_full_cache")
        query_gdf = st.session_state.get("query_gdf") if has_active_query_for_current_mode else None
        roi_geojson = st.session_state.get("roi_geojson") if has_active_query_for_current_mode else None
        available_images = st.session_state.get("available_images", []) if has_active_query_for_current_mode else []
        selected_scene_id = (
            sidebar_data.get("selected_scene_id") or st.session_state.get("selected_scene_id")
            if has_active_query_for_current_mode
            else None
        )
        selected_product_name = (
            sidebar_data.get("selected_product_name") or st.session_state.get("selected_product_name")
            if has_active_query_for_current_mode
            else None
        )

        gdf_filtered = None
        if (
            has_active_query_for_current_mode
            and query_gdf is not None
            and not getattr(query_gdf, "empty", True)
            and gdf_full is not None
            and not getattr(gdf_full, "empty", True)
            and applied_mode == "Empresa / Fazenda"
        ):
            gdf_filtered = filter_gdf(
                gdf_full,
                filtro_aplicado.get("selected_empresa"),
                filtro_aplicado.get("selected_fazenda"),
            )

        render_tab_mapa(
            gdf_full=gdf_full,
            gdf_filtered=gdf_filtered,
            filtro=filtro_shape,
            query_gdf=query_gdf,
            roi_geojson=roi_geojson,
            available_images=available_images,
            selected_scene_id=selected_scene_id,
            selected_product_name=selected_product_name,
        )

    with tab2:
        st.subheader("Informações da consulta")
        st.write(st.session_state.get("filtro_aplicado", {}))
        st.write(
            {
                "gdf_cache_loaded": st.session_state.get("_gdf_full_cache") is not None,
                "selected_scene_id": st.session_state.get("selected_scene_id"),
                "selected_product_name": st.session_state.get("selected_product_name"),
                "export_filename": sidebar_data.get("export_filename", "").strip(),
                "available_images_count": len(st.session_state.get("available_images", [])),
                "export_result": {
                    "png_name": (
                        st.session_state.get("export_result", {}).get("png_name")
                        if st.session_state.get("export_result")
                        else None
                    ),
                    "tif_name": (
                        st.session_state.get("export_result", {}).get("tif_name")
                        if st.session_state.get("export_result")
                        else None
                    ),
                },
                "captured_coordinate": st.session_state.get("captured_coordinate"),
                "roi_geojson_ok": bool(st.session_state.get("roi_geojson")),
                "roi_ready_for_export": st.session_state.get("roi_ready_for_export", False),
                "export_in_progress": st.session_state.get("export_in_progress", False),
                "last_export_error": st.session_state.get("last_export_error"),
            }
        )

    with tab3:
        render_tab_dados_satelite(logo_path=LOGO_PATH)


def main():
    ensure_session_state()
    sync_coordinate_payload(st.session_state.get("coordinate_editor_leaflet"))
    sanitize_available_images_state()

    authenticator, name, role, username = resolve_authenticated_user(AUTH_ENABLED)
    gdf_full_cached = get_gdf_full_lazy()

    sidebar_data = render_sidebar(
        gdf_full=gdf_full_cached,
        available_images=st.session_state.get("available_images", []),
    )

    modo_entrada = st.session_state.get("sb_modo_entrada", sidebar_data.get("modo_entrada"))

    header_cfg = build_header_config(
        modo_entrada=modo_entrada,
        selected_empresa=sidebar_data.get("selected_empresa"),
        selected_fazenda=sidebar_data.get("selected_fazenda"),
        parsed_coordinates=sidebar_data.get("parsed_coordinates"),
        uploaded_kml=sidebar_data.get("uploaded_kml"),
    )

    render_header(
        logo_path=LOGO_PATH,
        app_name=header_cfg["app_name"],
        version="V1.0",
        user=name,
        role=role,
        current_mode=header_cfg["mode_badge"],
        username=username,
        authenticator=authenticator,
        subtitle=header_cfg["subtitle"],
    )

    ok_ee, msg_ee = ensure_ee_initialized()
    if not ok_ee:
        st.error(msg_ee)
        st.stop()

    parsed_coordinates = _sync_page_state(modo_entrada, sidebar_data)

    if sidebar_data.get("apply", False):
        try:
            gdf_full = get_gdf_full_lazy()

            if gdf_full is None or getattr(gdf_full, "empty", True):
                raise ValueError("Erro ao carregar shapefile.")

            reset_export_state()

            run_query(
                gdf_full=gdf_full,
                modo_entrada=modo_entrada,
                selected_empresa=sidebar_data.get("selected_empresa"),
                selected_fazenda=sidebar_data.get("selected_fazenda"),
                parsed_coordinates=parsed_coordinates,
                uploaded_kml=sidebar_data.get("uploaded_kml"),
                buffer_m=sidebar_data.get("buffer_m", 200),
                selected_satellites=sidebar_data.get("selected_satellites", []),
                start_date=sidebar_data.get("start_date"),
                end_date=sidebar_data.get("end_date"),
                cloud_pct=sidebar_data.get("cloud_pct", 25),
            )

            st.session_state["roi_ready_for_export"] = bool(st.session_state.get("roi_geojson"))

            if not st.session_state.get("selected_product_name") and st.session_state.get("available_images"):
                st.session_state["selected_product_name"] = infer_default_product_name(
                    st.session_state.get("available_images", [])
                )

            if not st.session_state.get("_refresh_after_apply_done", False):
                st.session_state["_refresh_after_apply_done"] = True
                st.rerun()

        except Exception as e:
            st.session_state["_refresh_after_apply_done"] = False
            st.error(f"Erro ao aplicar consulta: {e}")
    else:
        st.session_state["_refresh_after_apply_done"] = False

    if sidebar_data.get("export_requested", False):
        handle_export(
            gdf_full=st.session_state.get("_gdf_full_cache"),
            modo_entrada=modo_entrada,
            selected_empresa=sidebar_data.get("selected_empresa"),
            selected_fazenda=sidebar_data.get("selected_fazenda"),
            parsed_coordinates=parsed_coordinates,
            uploaded_kml=sidebar_data.get("uploaded_kml"),
            buffer_m=sidebar_data.get("buffer_m", 200),
            export_filename=sidebar_data.get("export_filename", "").strip(),
            include_boundary_png=sidebar_data.get("include_boundary_png", True),
        )

        if not st.session_state.get("_refresh_after_export_done", False):
            st.session_state["_refresh_after_export_done"] = True
            st.rerun()
    else:
        st.session_state["_refresh_after_export_done"] = False

    _render_main_tabs(modo_entrada, sidebar_data)


if __name__ == "__main__":
    main()
