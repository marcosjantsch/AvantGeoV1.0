# -*- coding: utf-8 -*-
from __future__ import annotations

import ee
import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from folium.plugins import MousePosition
from shapely.geometry import shape
from streamlit_folium import st_folium

from services.coordinate_service import (
    CAPTURE_MODE_LABEL,
    DEFAULT_CAPTURE_CITY_NAME,
    build_capture_payload,
    format_dd,
)
from services.gee_service import build_display_image, get_product_vis_params
from services.geometry_service import build_gdf_from_point_dd


MAP_HEIGHT = 760


def _prepare_gdf_for_map(gdf):
    if gdf is None or gdf.empty:
        return gdf

    gdf_map = gdf.copy()
    for col in gdf_map.columns:
        if col == "geometry":
            continue
        if pd.api.types.is_datetime64_any_dtype(gdf_map[col]):
            gdf_map[col] = gdf_map[col].astype(str)
        else:
            gdf_map[col] = gdf_map[col].apply(lambda x: str(x) if isinstance(x, pd.Timestamp) else x)
    return gdf_map


def _add_ee_layer(map_obj, ee_image, vis_params, name, shown=True, opacity=1.0):
    map_id_dict = ee.Image(ee_image).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        show=shown,
        opacity=opacity,
    ).add_to(map_obj)


def _fit_map_to_gdf(m, gdf):
    if gdf is None or gdf.empty:
        return
    minx, miny, maxx, maxy = gdf.total_bounds
    if all(v is not None for v in [minx, miny, maxx, maxy]):
        m.fit_bounds([[miny, minx], [maxy, maxx]])


def _build_tooltip(gdf_map):
    tooltip_fields = [c for c in ["EMPRESA", "FAZENDA", "UF", "MUNICIPIO", "AREA_T", "AREA_PRODU"] if c in gdf_map.columns]
    if not tooltip_fields:
        return None
    return folium.GeoJsonTooltip(fields=tooltip_fields, aliases=[f"{c}: " for c in tooltip_fields], sticky=True)


def _get_capture_reference_gdf(captured):
    if not captured:
        return None
    lat = captured.get("latitude")
    lon = captured.get("longitude")
    if lat is None or lon is None:
        return None
    return build_gdf_from_point_dd(lat, lon)


def _get_map_reference_gdf(gdf_full, gdf_filtered=None, query_gdf=None, capture_mode=False):
    if query_gdf is not None and hasattr(query_gdf, "empty") and not query_gdf.empty:
        return query_gdf
    if capture_mode:
        captured = st.session_state.get("captured_coordinate")
        capture_gdf = _get_capture_reference_gdf(captured)
        if capture_gdf is not None and not capture_gdf.empty:
            return capture_gdf
    if gdf_filtered is not None and hasattr(gdf_filtered, "empty") and not gdf_filtered.empty:
        return gdf_filtered
    if gdf_full is not None and hasattr(gdf_full, "empty") and not gdf_full.empty:
        return gdf_full
    return None


class BindClickToRepositionCaptureMarker(MacroElement):
    def __init__(self, marker):
        super().__init__()
        self._name = "BindClickToRepositionCaptureMarker"
        self.marker = marker
        self._template = Template(
            """
            {% macro script(this, kwargs) %}
            var marker = {{ this.marker.get_name() }};
            var map = {{ this.marker._parent.get_name() }};

            var blueIcon = L.divIcon({
                className: 'custom-capture-marker-wrapper',
                html: `
                    <div style="
                        width: 18px;
                        height: 18px;
                        border-radius: 50%;
                        background: #1f77ff;
                        border: 2px solid #ffffff;
                        box-shadow: 0 0 0 2px rgba(31,119,255,0.25);
                    "></div>
                `,
                iconSize: [18, 18],
                iconAnchor: [9, 9]
            });

            var redIcon = L.divIcon({
                className: 'custom-capture-marker-wrapper',
                html: `
                    <div style="
                        width: 18px;
                        height: 18px;
                        border-radius: 50%;
                        background: #ff2b2b;
                        border: 2px solid #ffffff;
                        box-shadow: 0 0 0 2px rgba(255,43,43,0.25);
                    "></div>
                `,
                iconSize: [18, 18],
                iconAnchor: [9, 9]
            });

            marker.setIcon(blueIcon);
            marker.options.repositionArmed = false;

            function isLeftButton(evt) {
                if (!evt) return true;
                if (typeof evt.button === "number") return evt.button === 0;
                if (typeof evt.which === "number") return evt.which === 1;
                return true;
            }

            marker.on("click", function(e) {
                if (e && e.originalEvent && !isLeftButton(e.originalEvent)) {
                    return;
                }
                marker.options.repositionArmed = true;
                marker.setIcon(redIcon);
            });

            map.on("click", function(e) {
                if (!marker.options.repositionArmed) {
                    return;
                }

                if (!e || !e.latlng) {
                    return;
                }

                marker.setLatLng(e.latlng);
                marker.options.repositionArmed = false;
                marker.setIcon(blueIcon);

                map.fire("capture_marker_moved", {
                    latlng: e.latlng
                });
            });
            {% endmacro %}
            """
        )

def _add_capture_marker(m):
    captured = st.session_state.get("captured_coordinate")
    if not captured:
        return

    lat = captured.get("latitude")
    lon = captured.get("longitude")
    if lat is None or lon is None:
        return

    popup_text = (
        f"DD: {format_dd(lat)}, {format_dd(lon)}<br>"
        f"DMS: {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')}"
    )

    marker = folium.Marker(
        location=[lat, lon],
        popup=popup_text,
        tooltip="Clique no ponto para ativar o reposicionamento",
        draggable=False,
    )
    marker.add_to(m)
    marker.add_child(BindClickToRepositionCaptureMarker(marker))


def _update_capture_state(map_data):
    if not map_data:
        return

    hover = map_data.get("last_mouse_position")
    if isinstance(hover, dict) and hover.get("lat") is not None and hover.get("lng") is not None:
        st.session_state["map_hover_coordinate"] = {
            "latitude": float(hover["lat"]),
            "longitude": float(hover["lng"]),
        }

    clicked = map_data.get("last_clicked")
    if isinstance(clicked, dict) and clicked.get("lat") is not None and clicked.get("lng") is not None:
        st.session_state["captured_coordinate"] = build_capture_payload(
            latitude=clicked["lat"],
            longitude=clicked["lng"],
            source="map_click",
        )
        st.session_state["parsed_coordinates"] = st.session_state["captured_coordinate"]


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
    capture_mode = (filtro or {}).get("modo_entrada") == CAPTURE_MODE_LABEL or st.session_state.get("sb_modo_entrada") == CAPTURE_MODE_LABEL
    gdf_ref = _get_map_reference_gdf(gdf_full, gdf_filtered=gdf_filtered, query_gdf=query_gdf, capture_mode=capture_mode)
    if gdf_ref is None or gdf_ref.empty:
        st.warning("Nenhuma geometria encontrada para exibição.")
        return

    gdf_map = _prepare_gdf_for_map(gdf_ref)
    centroid = gdf_map.geometry.unary_union.centroid
    lat, lon = centroid.y, centroid.x

    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True, tiles="OpenStreetMap")
    folium.TileLayer("CartoDB Voyager", name="CartoDB Voyager").add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Esri World Imagery").add_to(m)
    MousePosition(position="bottomright", separator=" | ", num_digits=6).add_to(m)

    selected_spec = None
    if selected_scene_id:
        selected_spec = next((img for img in available_images if img.get("id") == selected_scene_id), None)

    if selected_spec and roi_geojson:
        ee_img = build_display_image(
            image_id=selected_spec.get("id"),
            satellite=selected_spec.get("satellite"),
            roi_geojson=roi_geojson,
            asset_id=selected_spec.get("asset_id"),
            collection_id=selected_spec.get("collection_id"),
            product_name=selected_product_name,
        )
        product_label = selected_product_name or ("Imagem Sentinel RGB" if selected_spec.get("satellite") == "Sentinel-2" else "RGB Landsat")
        vis = get_product_vis_params(selected_spec.get("satellite"), product_label)
        layer_name = f"{selected_spec.get('satellite')} | {selected_spec.get('date')} | {product_label}"
        _add_ee_layer(m, ee_img, vis, layer_name, shown=True, opacity=1.0)

    if capture_mode:
        st.info(
            f"Modo Capturar Coordenada: o ponto inicia em {DEFAULT_CAPTURE_CITY_NAME}. "
            f"Clique no marcador azul para ativar o reposicionamento. "
            f"Quando ele ficar vermelho, clique em outra região do mapa para mover o ponto. "
            f"Após o reposicionamento, ele volta a ficar azul. "
            f"A consulta só será atualizada quando você clicar em Aplicar consulta."
        )
        _add_capture_marker(m)
    else:
        folium.GeoJson(
            gdf_map,
            name="Área de consulta",
            style_function=lambda x: {"color": "#FF0000", "weight": 2, "fillOpacity": 0.05},
            tooltip=_build_tooltip(gdf_map),
        ).add_to(m)

    gdf_buffer = None
    if roi_geojson:
        try:
            roi_shape = shape(roi_geojson)
            gdf_buffer = gpd.GeoDataFrame({"name": ["roi"]}, geometry=[roi_shape], crs="EPSG:4326")
            folium.GeoJson(
                gdf_buffer,
                name=f"ROI por extremos ({(filtro or {}).get('buffer_m', 0)} m)",
                style_function=lambda x: {"color": "#0000FF", "weight": 2, "fillOpacity": 0.03, "dashArray": "5, 5"},
            ).add_to(m)
        except Exception:
            gdf_buffer = None

    _fit_map_to_gdf(m, gdf_buffer if gdf_buffer is not None else gdf_map)
    folium.LayerControl(collapsed=False).add_to(m)

    map_data = st_folium(
        m,
        width=None,
        height=MAP_HEIGHT,
        key="mapa_principal",
        returned_objects=["last_clicked", "last_mouse_position"],
    )

    if capture_mode:
        _update_capture_state(map_data)
        captured = st.session_state.get("captured_coordinate")
        if captured:
            st.caption(
                f"Ponto atual: DD {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))} | "
                f"DMS {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')}"
            )