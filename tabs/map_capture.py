# -*- coding: utf-8 -*-
from __future__ import annotations

import folium
import streamlit as st
from streamlit_folium import st_folium

from services.coordinate_service import (
    DEFAULT_CAPTURE_CITY_NAME,
    build_capture_payload,
    format_dd,
)
from tabs.map_utils import CAPTURE_ZOOM, MAP_HEIGHT, build_map_base, build_map_key


CAPTURE_MARKER_TOOLTIP = "capture-marker"


def _capture_click_signature(point):
    if not isinstance(point, dict):
        return None
    lat = point.get("lat")
    lng = point.get("lng")
    if lat is None or lng is None:
        return None
    return f"{float(lat):.6f},{float(lng):.6f}"


def get_capture_marker_location():
    captured = st.session_state.get("captured_coordinate") or {}
    lat = captured.get("latitude")
    lon = captured.get("longitude")
    if lat is None or lon is None:
        return None
    return [float(lat), float(lon)]


def get_capture_map_center(default_center):
    center = st.session_state.get("capture_map_center")
    if isinstance(center, list) and len(center) == 2:
        return [float(center[0]), float(center[1])]
    marker_location = get_capture_marker_location()
    if marker_location is not None:
        st.session_state["capture_map_center"] = marker_location
        return marker_location
    return default_center


def build_capture_idle_map(default_center):
    return build_map_base(get_capture_map_center(default_center), CAPTURE_ZOOM)


def add_capture_marker(m):
    marker_location = get_capture_marker_location()
    if marker_location is None:
        return

    captured = st.session_state.get("captured_coordinate") or {}
    is_active = bool(st.session_state.get("capture_marker_active", False))
    marker_color = "red" if is_active else "blue"
    popup_text = (
        f"DD: {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))}<br>"
        f"DMS: {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')}"
    )

    folium.Marker(
        location=marker_location,
        popup=popup_text,
        tooltip=CAPTURE_MARKER_TOOLTIP,
        icon=folium.Icon(color=marker_color, icon="map-marker", prefix="fa"),
    ).add_to(m)


def update_capture_state(map_data):
    if not map_data:
        return False

    state_changed = False

    hover = map_data.get("last_mouse_position")
    if isinstance(hover, dict) and hover.get("lat") is not None and hover.get("lng") is not None:
        st.session_state["map_hover_coordinate"] = {
            "latitude": float(hover["lat"]),
            "longitude": float(hover["lng"]),
        }

    object_tooltip = map_data.get("last_object_clicked_tooltip")
    object_click = map_data.get("last_object_clicked")
    object_signature = _capture_click_signature(object_click)

    if object_tooltip == CAPTURE_MARKER_TOOLTIP and object_signature:
        if st.session_state.get("capture_last_marker_click") != object_signature:
            st.session_state["capture_marker_active"] = True
            st.session_state["capture_last_marker_click"] = object_signature
            state_changed = True

    clicked = map_data.get("last_clicked")
    click_signature = _capture_click_signature(clicked)
    marker_signature = _capture_click_signature(object_click)
    marker_was_clicked = object_tooltip == CAPTURE_MARKER_TOOLTIP and click_signature == marker_signature

    if (
        click_signature
        and not marker_was_clicked
        and st.session_state.get("capture_last_map_click") != click_signature
    ):
        st.session_state["capture_last_map_click"] = click_signature

        if st.session_state.get("capture_marker_active", False):
            st.session_state["captured_coordinate"] = build_capture_payload(
                latitude=clicked["lat"],
                longitude=clicked["lng"],
                source="map_click",
                label="Coordenada capturada no mapa",
            )
            st.session_state["parsed_coordinates"] = st.session_state["captured_coordinate"]
            st.session_state["capture_marker_active"] = False
            st.session_state["capture_map_center"] = [float(clicked["lat"]), float(clicked["lng"])]
            state_changed = True

    return state_changed


def render_capture_map(default_center, mode_key: str = "Coordenada"):
    map_key = build_map_key(mode_key)
    st.info(
        f"Modo coordenada ativo. O ponto inicia em {DEFAULT_CAPTURE_CITY_NAME} na cor azul. "
        "Voce pode alterar a localizacao digitando a coordenada ou clicando no ponto para ativa-lo e, em seguida, clicando em outro local do mapa."
    )

    m = build_capture_idle_map(default_center)
    add_capture_marker(m)
    folium.LayerControl(collapsed=False).add_to(m)

    map_data = st_folium(
        m,
        width=None,
        height=MAP_HEIGHT,
        key=map_key,
        returned_objects=[
            "last_clicked",
            "last_mouse_position",
            "last_object_clicked",
            "last_object_clicked_tooltip",
        ],
    )

    state_changed = update_capture_state(map_data)
    captured = st.session_state.get("captured_coordinate")

    if captured:
        status = "ativo (vermelho)" if st.session_state.get("capture_marker_active", False) else "inativo (azul)"
        st.caption(
            f"Ponto atual: DD {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))} | "
            f"DMS {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')} | "
            f"Estado: {status}"
        )

    if state_changed:
        st.rerun()
