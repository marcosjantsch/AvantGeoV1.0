# -*- coding: utf-8 -*-
from __future__ import annotations

import folium
import geopandas as gpd
from shapely.geometry import shape
from streamlit_folium import st_folium
import streamlit as st

from components.coordinate_marker_map import render_coordinate_marker_map
from services.coordinate_service import format_dd
from services.gee_service import (
    build_dem_contours_image,
    build_display_image,
    get_dem_contours_vis,
    get_product_vis_params,
    should_overlay_dem_contours,
)
from tabs.map_utils import (
    BRAZIL_CENTER,
    BRAZIL_ZOOM,
    MAP_HEIGHT,
    add_ee_layer,
    build_map_base,
    build_map_key,
    build_tooltip,
    fit_map_to_gdf,
    prepare_gdf_for_map,
)


def _build_query_map_key(modo_entrada: str, selected_scene_id, selected_product_name, buffer_m) -> str:
    def _sanitize(value):
        return str(value or "none").replace("/", "_").replace(" ", "_").replace("|", "_")

    return (
        f"{build_map_key(modo_entrada)}"
        f"_{_sanitize(selected_scene_id)}"
        f"_{_sanitize(selected_product_name)}"
        f"_{_sanitize(buffer_m)}"
        f"_{st.session_state.get('query_result_nonce', 0)}"
        f"_{st.session_state.get('image_selection_nonce', 0)}"
    )


def _build_idle_map_for_mode(modo_entrada: str):
    if modo_entrada == "Coordenada":
        return build_map_base(BRAZIL_CENTER, BRAZIL_ZOOM)
    return build_map_base(BRAZIL_CENTER, BRAZIL_ZOOM)


def _render_idle_map_for_mode(modo_entrada: str, map_key: str):
    m = _build_idle_map_for_mode(modo_entrada)
    folium.LayerControl(collapsed=False).add_to(m)

    info_messages = {
        "Empresa / Fazenda": (
            "Modo Empresa / Fazenda ativo. O mapa exibe o estado padrão desse modo enquanto a consulta ainda não foi aplicada."
        ),
        "Coordenada": (
            "Modo Coordenada ativo. O mapa exibe o ponto inicial e permite reposicionamento imediato sem aplicar a consulta."
        ),
        "Arquivo KML/KMZ": (
            "Modo Arquivo KML/KMZ ativo. O mapa exibe o estado padrão desse modo enquanto a consulta ainda não foi aplicada."
        ),
    }
    st.info(info_messages.get(modo_entrada, "Aplique uma consulta para carregar o mapa."))

    st_folium(
        m,
        width=None,
        height=MAP_HEIGHT,
        key=map_key,
        returned_objects=["last_clicked", "last_mouse_position"],
    )
COORDINATE_EDITOR_HEIGHT = 520


def _render_coordinate_editor():
    captured = st.session_state.get("captured_coordinate") or {}
    latitude = captured.get("latitude", BRAZIL_CENTER[0])
    longitude = captured.get("longitude", BRAZIL_CENTER[1])

    st.info(
        "Modo Coordenada ativo. Segure CTRL para deixar o ponto vermelho e arrastavel. "
        "Ao soltar CTRL ou encerrar o arraste, a coordenada final e enviada uma unica vez ao backend."
    )

    component_value = render_coordinate_marker_map(
        latitude=latitude,
        longitude=longitude,
        zoom=12,
        height=COORDINATE_EDITOR_HEIGHT,
        key="coordinate_editor_leaflet",
    )

    captured = st.session_state.get("captured_coordinate") or {}
    st.caption(
        f"Ponto atual: {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))}"
    )


def _resolve_map_reference(gdf_full, gdf_filtered, query_gdf):
    if query_gdf is not None and hasattr(query_gdf, "empty") and not query_gdf.empty:
        return query_gdf
    if gdf_filtered is not None and hasattr(gdf_filtered, "empty") and not gdf_filtered.empty:
        return gdf_filtered
    if gdf_full is not None and hasattr(gdf_full, "empty") and not gdf_full.empty:
        return gdf_full
    return None


def _render_query_map(
    gdf_ref,
    filtro,
    roi_geojson,
    available_images,
    selected_scene_id,
    selected_product_name,
):
    gdf_map = prepare_gdf_for_map(gdf_ref)
    centroid = gdf_map.geometry.unary_union.centroid
    lat, lon = centroid.y, centroid.x

    m = build_map_base([lat, lon], 12)

    selected_spec = None
    if selected_scene_id:
        selected_spec = next(
            (
                img
                for img in available_images
                if img.get("id") == selected_scene_id or img.get("asset_id") == selected_scene_id
            ),
            None,
        )

    if selected_spec and roi_geojson:
        ee_img = build_display_image(
            image_id=selected_spec.get("id"),
            satellite=selected_spec.get("satellite"),
            roi_geojson=roi_geojson,
            asset_id=selected_spec.get("asset_id"),
            collection_id=selected_spec.get("collection_id"),
            product_name=selected_product_name,
        )
        product_label = selected_product_name or "RGB"
        vis = get_product_vis_params(
            selected_spec.get("satellite"),
            product_label,
            ee_image=ee_img,
            roi_geojson=roi_geojson,
        )
        layer_name = f"{selected_spec.get('satellite')} | {selected_spec.get('date')} | {product_label}"
        add_ee_layer(m, ee_img, vis, layer_name, shown=True, opacity=1.0)

        if should_overlay_dem_contours(selected_spec.get("satellite"), product_label):
            contour_img = build_dem_contours_image(
                image_id=selected_spec.get("id"),
                satellite=selected_spec.get("satellite"),
                roi_geojson=roi_geojson,
                asset_id=selected_spec.get("asset_id"),
                collection_id=selected_spec.get("collection_id"),
                interval_m=5,
            )
            add_ee_layer(
                m,
                contour_img,
                get_dem_contours_vis(),
                f"{selected_spec.get('satellite')} | Curvas de nivel 5 m",
                shown=True,
                opacity=0.9,
            )

    folium.GeoJson(
        gdf_map,
        name="Área de consulta",
        style_function=lambda x: {
            "color": "#34d399",
            "weight": 2.1,
            "fillColor": "#22c55e",
            "fillOpacity": 0.07,
        },
        highlight_function=lambda x: {
            "color": "#a7f3d0",
            "weight": 2.8,
            "fillColor": "#4ade80",
            "fillOpacity": 0.12,
        },
        tooltip=build_tooltip(gdf_map),
    ).add_to(m)

    gdf_buffer = None
    if roi_geojson:
        try:
            roi_shape = shape(roi_geojson)
            gdf_buffer = gpd.GeoDataFrame({"name": ["roi"]}, geometry=[roi_shape], crs="EPSG:4326")
            folium.GeoJson(
                gdf_buffer,
                name=f"ROI ({filtro.get('buffer_m', 0)} m)",
                style_function=lambda x: {
                    "color": "#6ee7b7",
                    "weight": 1.8,
                    "fillColor": "#10b981",
                    "fillOpacity": 0.03,
                    "dashArray": "5, 5",
                },
                highlight_function=lambda x: {
                    "color": "#bbf7d0",
                    "weight": 2.2,
                    "fillColor": "#34d399",
                    "fillOpacity": 0.06,
                },
            ).add_to(m)
        except Exception:
            gdf_buffer = None

    fit_map_to_gdf(m, gdf_buffer if gdf_buffer is not None else gdf_map)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def render_tab_mapa(
    gdf_full,
    gdf_filtered,
    filtro,
    query_gdf=None,
    roi_geojson=None,
    available_images=None,
    selected_scene_id=None,
    selected_product_name=None,
):
    st.subheader("🗺️ Mapa Principal")

    available_images = available_images or []
    filtro = filtro or {}
    modo_entrada = filtro.get("modo_entrada")
    map_key = _build_query_map_key(
        modo_entrada,
        selected_scene_id,
        selected_product_name,
        filtro.get("buffer_m", 0),
    )

    if modo_entrada == "Coordenada":
        if query_gdf is None or getattr(query_gdf, "empty", True):
            _render_coordinate_editor()
            return

    if query_gdf is None or getattr(query_gdf, "empty", True):
        _render_idle_map_for_mode(modo_entrada, map_key)
        return

    gdf_ref = _resolve_map_reference(gdf_full, gdf_filtered, query_gdf)
    if gdf_ref is None or getattr(gdf_ref, "empty", True):
        _render_idle_map_for_mode(modo_entrada, map_key)
        return

    m = _render_query_map(
        gdf_ref=gdf_ref,
        filtro=filtro,
        roi_geojson=roi_geojson,
        available_images=available_images,
        selected_scene_id=selected_scene_id,
        selected_product_name=selected_product_name,
    )

    st_folium(
        m,
        width=None,
        height=MAP_HEIGHT,
        key=map_key,
        returned_objects=["last_clicked", "last_mouse_position"],
    )
