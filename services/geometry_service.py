# -*- coding: utf-8 -*-
from __future__ import annotations

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point, box, mapping


MIN_ROI_SIZE_M = 500.0


def filter_gdf(gdf: gpd.GeoDataFrame, empresa: str = None, fazenda: str = None):
    gdf_filtered = gdf.copy()

    if empresa and fazenda and all(c in gdf_filtered.columns for c in ["EMPRESA", "FAZENDA"]):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["EMPRESA"].astype(str) == str(empresa))
            & (gdf_filtered["FAZENDA"].astype(str) == str(fazenda))
        ]
    elif empresa and "EMPRESA" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["EMPRESA"].astype(str) == str(empresa)]

    return gdf_filtered


def _ensure_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf is None or gdf.empty:
        raise ValueError("GeoDataFrame vazio.")

    gdf_work = gdf.copy()
    if gdf_work.crs is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")
    if str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")
    return gdf_work


def build_gdf_from_point_dd(latitude: float, longitude: float):
    pt = Point(longitude, latitude)
    return gpd.GeoDataFrame({"name": ["Ponto"]}, geometry=[pt], crs="EPSG:4326")


def build_gdf_from_point_utm(easting: float, northing: float, zone: str, hemisphere: str):
    zone_int = int(str(zone).strip())
    hemi = str(hemisphere).strip().upper()
    epsg = 32700 + zone_int if hemi == "S" else 32600 + zone_int

    transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return build_gdf_from_point_dd(latitude=lat, longitude=lon)


def build_rectangular_roi_gdf(
    gdf: gpd.GeoDataFrame,
    buffer_m: float = 0,
    min_width_m: float = MIN_ROI_SIZE_M,
    min_height_m: float = MIN_ROI_SIZE_M,
) -> gpd.GeoDataFrame:
    gdf_work = _ensure_wgs84(gdf)
    gdf_proj = gdf_work.to_crs(3857)

    minx, miny, maxx, maxy = gdf_proj.total_bounds
    buffer_value = max(float(buffer_m or 0), 0.0)

    minx -= buffer_value
    miny -= buffer_value
    maxx += buffer_value
    maxy += buffer_value

    width = maxx - minx
    height = maxy - miny

    if width < float(min_width_m):
        expand = (float(min_width_m) - width) / 2.0
        minx -= expand
        maxx += expand

    if height < float(min_height_m):
        expand = (float(min_height_m) - height) / 2.0
        miny -= expand
        maxy += expand

    rect = box(minx, miny, maxx, maxy)
    roi_gdf = gpd.GeoDataFrame(
        {
            "roi_type": ["rect_extremos"],
            "buffer_m": [buffer_value],
            "min_width_m": [float(min_width_m)],
            "min_height_m": [float(min_height_m)],
        },
        geometry=[rect],
        crs="EPSG:3857",
    ).to_crs(4326)

    return roi_gdf


def gdf_to_roi_geojson(gdf: gpd.GeoDataFrame, buffer_m: float = 0):
    roi_gdf = build_rectangular_roi_gdf(gdf, buffer_m=buffer_m)
    geom = roi_gdf.geometry.iloc[0]
    return mapping(geom)


def get_rectangular_roi_bounds(gdf: gpd.GeoDataFrame, buffer_m: float = 0):
    roi_gdf = build_rectangular_roi_gdf(gdf, buffer_m=buffer_m)
    minx, miny, maxx, maxy = roi_gdf.total_bounds
    return {
        "west": float(minx),
        "south": float(miny),
        "east": float(maxx),
        "north": float(maxy),
    }
