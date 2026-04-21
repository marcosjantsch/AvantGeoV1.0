# -*- coding: utf-8 -*-
from __future__ import annotations

import ee
import folium
import geopandas as gpd
import pandas as pd
from branca.element import Element
from folium.plugins import MousePosition


MAP_HEIGHT = 760
BRAZIL_CENTER = [-14.235004, -51.92528]
BRAZIL_ZOOM = 4
WORLD_CENTER = [0, 0]
WORLD_ZOOM = 2
CAPTURE_ZOOM = 12

MAP_THEME_CSS = """
<style>
.leaflet-container {
    background: #020617 !important;
    font-family: "Segoe UI", Arial, sans-serif;
}
.leaflet-control-zoom a,
.leaflet-control-layers-toggle,
.leaflet-bar a {
    background-color: #050b09 !important;
    color: #d1fae5 !important;
    border: 1px solid rgba(52, 211, 153, 0.35) !important;
}
.leaflet-bar a:hover,
.leaflet-control-zoom a:hover {
    background-color: #0b1f17 !important;
    color: #a7f3d0 !important;
}
.leaflet-control-layers {
    background: rgba(2, 6, 23, 0.92) !important;
    color: #e5fff3 !important;
    border: 1px solid rgba(16, 185, 129, 0.35) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35) !important;
}
.leaflet-control-layers-expanded label,
.leaflet-control-layers-expanded span {
    color: #d1fae5 !important;
}
.leaflet-popup-content-wrapper,
.leaflet-popup-tip {
    background: rgba(3, 7, 18, 0.96) !important;
    color: #ecfdf5 !important;
    border: 1px solid rgba(16, 185, 129, 0.40);
}
.leaflet-popup-content {
    color: #ecfdf5 !important;
}
.leaflet-tooltip {
    background: rgba(5, 11, 9, 0.94) !important;
    color: #ecfdf5 !important;
    border: 1px solid rgba(110, 231, 183, 0.45) !important;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28) !important;
}
.leaflet-control-attribution {
    background: rgba(2, 6, 23, 0.85) !important;
    color: #86efac !important;
}
.leaflet-control-attribution a {
    color: #6ee7b7 !important;
}
</style>
"""


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
        style=(
            "background-color: rgba(3,7,18,0.96); color: #ecfdf5; "
            "border: 1px solid rgba(110,231,183,0.45); border-radius: 8px; "
            "box-shadow: 0 8px 24px rgba(0,0,0,0.28);"
        ),
    )


def build_map_base(location, zoom_start):
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        control_scale=True,
        tiles=None,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap contributors &copy; CARTO",
        name="CartoDB DarkMatter",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Esri World Imagery",
        overlay=False,
        control=True,
        show=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="&copy; OpenStreetMap contributors",
        name="OpenStreetMap",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap contributors &copy; CARTO",
        name="CartoDB Voyager",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Esri World Topo",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Esri World Street",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    MousePosition(position="bottomright", separator=" | ", num_digits=6).add_to(m)
    m.get_root().header.add_child(Element(MAP_THEME_CSS))
    return m


def build_map_key(modo_entrada: str) -> str:
    safe_mode = str(modo_entrada or "padrao").lower().replace(" ", "_").replace("/", "_")
    return f"mapa_principal_{safe_mode}"
