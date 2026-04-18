# -*- coding: utf-8 -*-
from __future__ import annotations

import ee
import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import MousePosition


MAP_HEIGHT = 760
BRAZIL_CENTER = [-14.235004, -51.92528]
BRAZIL_ZOOM = 4
WORLD_CENTER = [0, 0]
WORLD_ZOOM = 2
CAPTURE_ZOOM = 12


def prepare_gdf_for_map(gdf):
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


def add_ee_layer(map_obj, ee_image, vis_params, name, shown=True, opacity=1.0):
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


def fit_map_to_gdf(m, gdf):
    if gdf is None or gdf.empty:
        return
    minx, miny, maxx, maxy = gdf.total_bounds
    if all(v is not None for v in [minx, miny, maxx, maxy]):
        m.fit_bounds([[miny, minx], [maxy, maxx]])


def build_tooltip(gdf_map):
    tooltip_fields = [
        c for c in ["EMPRESA", "FAZENDA", "UF", "MUNICIPIO", "AREA_T", "AREA_PRODU"]
        if c in gdf_map.columns
    ]
    if not tooltip_fields:
        return None
    return folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=[f"{c}: " for c in tooltip_fields],
        sticky=True,
    )


def build_map_base(location, zoom_start):
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        control_scale=True,
        tiles="OpenStreetMap",
    )
    folium.TileLayer("CartoDB Voyager", name="CartoDB Voyager").add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Esri World Imagery").add_to(m)
    MousePosition(position="bottomright", separator=" | ", num_digits=6).add_to(m)
    return m


def build_map_key(modo_entrada: str) -> str:
    safe_mode = str(modo_entrada or "padrao").lower().replace(" ", "_").replace("/", "_")
    return f"mapa_principal_{safe_mode}"
