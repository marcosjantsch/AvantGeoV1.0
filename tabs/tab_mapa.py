# -*- coding: utf-8 -*-
from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
import ee
from folium.plugins import MousePosition
from shapely.geometry import shape
from streamlit_folium import st_folium

from services.coordinate_service import CAPTURE_MODE_LABEL, build_capture_payload, format_dd
from services.gee_service import build_display_image, get_product_vis_params


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
            gdf_map[col] = gdf_map[col].apply(
                lambda x: str(x) if isinstance(x, pd.Timestamp) else x
            )

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
    tooltip_fields = [
        c for c in ["EMPRESA", "FAZENDA", "UF", "MUNICIPIO", "AREA_T", "AREA_PRODU"]
        if c in gdf_map.columns
    ]

    if not tooltip_fields:
        return None

    tooltip_aliases = [f"{c}: " for c in tooltip_fields]

    return folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=tooltip_aliases,
        sticky=True,
    )


def _get_base_reference_gdf(gdf_full, gdf_filtered=None, query_gdf=None):
    if query_gdf is not None and hasattr(query_gdf, "empty") and not query_gdf.empty:
        return query_gdf
    if gdf_filtered is not None and hasattr(gdf_filtered, "empty") and not gdf_filtered.empty:
        return gdf_filtered
    if gdf_full is not None and hasattr(gdf_full, "empty") and not gdf_full.empty:
        return gdf_full
    return None


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
    folium.Marker(
        location=[lat, lon],
        popup=popup_text,
        tooltip="Coordenada capturada",
    ).add_to(m)


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

    gdf_ref = _get_base_reference_gdf(gdf_full, gdf_filtered=gdf_filtered, query_gdf=query_gdf)
    if gdf_ref is None or gdf_ref.empty:
        st.warning("Nenhuma geometria encontrada para exibição.")
        return

    try:
        gdf_map = _prepare_gdf_for_map(gdf_ref)

        centroid = gdf_map.geometry.unary_union.centroid
        lat, lon = centroid.y, centroid.x

        m = folium.Map(
            location=[lat, lon],
            zoom_start=12,
            control_scale=True,
            tiles="OpenStreetMap",
        )

        folium.TileLayer("CartoDB Voyager", name="CartoDB Voyager").add_to(m)
        folium.TileLayer("Esri.WorldImagery", name="Esri World Imagery").add_to(m)
        MousePosition(position="bottomright", separator=" | ", num_digits=6).add_to(m)

        selected_spec = None
        if selected_scene_id:
            selected_spec = next(
                (img for img in available_images if img.get("id") == selected_scene_id),
                None,
            )

        if selected_spec and roi_geojson:
            image_id = selected_spec.get("id")
            asset_id = selected_spec.get("asset_id")
            collection_id = selected_spec.get("collection_id")
            sat = selected_spec.get("satellite")
            date_str = selected_spec.get("date")

            ee_img = build_display_image(
                image_id=image_id,
                satellite=sat,
                roi_geojson=roi_geojson,
                asset_id=asset_id,
                collection_id=collection_id,
                product_name=selected_product_name,
            )

            product_label = selected_product_name or (
                "Imagem Sentinel RGB" if sat == "Sentinel-2" else "RGB Landsat"
            )

            vis = get_product_vis_params(sat, product_label)
            layer_name = f"{sat} | {date_str} | {product_label}"

            _add_ee_layer(
                map_obj=m,
                ee_image=ee_img,
                vis_params=vis,
                name=layer_name,
                shown=True,
                opacity=1.0,
            )

        folium.GeoJson(
            gdf_map,
            name="Área de consulta",
            style_function=lambda x: {
                "color": "#FF0000",
                "weight": 2,
                "fillOpacity": 0.05,
            },
            tooltip=_build_tooltip(gdf_map),
        ).add_to(m)

        buffer_m = (filtro or {}).get("buffer_m", 0)

        if roi_geojson:
            try:
                roi_shape = shape(roi_geojson)
                gdf_buffer = gpd.GeoDataFrame(
                    {"name": ["roi"]},
                    geometry=[roi_shape],
                    crs="EPSG:4326",
                )

                folium.GeoJson(
                    gdf_buffer,
                    name=f"ROI por extremos ({buffer_m} m)",
                    style_function=lambda x: {
                        "color": "#0000FF",
                        "weight": 2,
                        "fillOpacity": 0.03,
                        "dashArray": "5, 5",
                    },
                ).add_to(m)
            except Exception:
                pass

        if capture_mode:
            st.info(
                "Modo Capturar Coordenada: mova o mouse para visualizar a posição e clique no mapa para definir ou substituir a coordenada."
            )
            _add_capture_marker(m)

        _fit_map_to_gdf(m, gdf_map if roi_geojson is None else gdf_buffer)
        folium.LayerControl(collapsed=False).add_to(m)
        map_data = st_folium(m, width=None, height=MAP_HEIGHT, returned_objects=["last_clicked", "last_mouse_position"])

        if capture_mode:
            _update_capture_state(map_data)
            captured = st.session_state.get("captured_coordinate")
            if captured:
                st.caption(
                    f"Coordenada capturada: DD {format_dd(captured.get('latitude'))}, {format_dd(captured.get('longitude'))} | "
                    f"DMS {captured.get('latitude_dms', '-')} | {captured.get('longitude_dms', '-')}"
                )

    except Exception as e:
        st.error(f"Erro ao gerar mapa: {e}")
        return

    st.markdown("---")

    with st.expander("📊 Estatísticas", expanded=False):
        st.write(f"Total original: {len(gdf_full) if gdf_full is not None else 0}")
        st.write(f"Total exibido: {len(gdf_ref) if gdf_ref is not None else 0}")

        if gdf_ref is not None and "AREA_T" in gdf_ref.columns:
            area_total = pd.to_numeric(gdf_ref["AREA_T"], errors="coerce").fillna(0).sum()
            st.write(
                f"Área total (ha): "
                f"{area_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        if gdf_ref is not None and "AREA_PRODU" in gdf_ref.columns:
            area_prod = pd.to_numeric(gdf_ref["AREA_PRODU"], errors="coerce").fillna(0).sum()
            st.write(
                f"Área produtiva (ha): "
                f"{area_prod:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        st.write(f"Cena selecionada: {selected_scene_id or '-'}")
        st.write(f"Produto selecionado: {selected_product_name or '-'}")

    with st.expander("🔍 Detalhes do filtro", expanded=False):
        st.json(
            {
                "modo_entrada": (filtro or {}).get("modo_entrada"),
                "tipo_dado": (filtro or {}).get("tipo_dado"),
                "selected_empresa": (filtro or {}).get("selected_empresa"),
                "selected_fazenda": (filtro or {}).get("selected_fazenda"),
                "start_date": str((filtro or {}).get("start_date")),
                "end_date": str((filtro or {}).get("end_date")),
                "selected_satellites": (filtro or {}).get("selected_satellites"),
                "buffer_m": (filtro or {}).get("buffer_m"),
                "cloud_pct": (filtro or {}).get("cloud_pct"),
                "selected_scene_id": selected_scene_id,
                "selected_product_name": selected_product_name,
                "captured_coordinate": st.session_state.get("captured_coordinate"),
            }
        )
