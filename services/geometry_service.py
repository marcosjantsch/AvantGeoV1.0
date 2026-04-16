# -*- coding: utf-8 -*-
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point, mapping


def filter_gdf(gdf: gpd.GeoDataFrame, empresa: str = None, fazenda: str = None):
    gdf_filtered = gdf.copy()

    if (
        empresa
        and fazenda
        and all(c in gdf_filtered.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["EMPRESA"].astype(str) == str(empresa))
            & (gdf_filtered["FAZENDA"].astype(str) == str(fazenda))
        ]
    elif empresa and "EMPRESA" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[
            gdf_filtered["EMPRESA"].astype(str) == str(empresa)
        ]

    return gdf_filtered


def build_gdf_from_point_dd(latitude: float, longitude: float):
    pt = Point(longitude, latitude)
    return gpd.GeoDataFrame({"name": ["Ponto"]}, geometry=[pt], crs="EPSG:4326")


def build_gdf_from_point_utm(
    easting: float,
    northing: float,
    zone: str,
    hemisphere: str,
):
    zone_int = int(str(zone).strip())
    hemi = str(hemisphere).strip().upper()
    epsg = 32700 + zone_int if hemi == "S" else 32600 + zone_int

    transformer = Transformer.from_crs(
        f"EPSG:{epsg}",
        "EPSG:4326",
        always_xy=True,
    )
    lon, lat = transformer.transform(easting, northing)

    return build_gdf_from_point_dd(latitude=lat, longitude=lon)


def apply_buffer_in_meters(gdf: gpd.GeoDataFrame, buffer_m: float):
    if gdf is None or gdf.empty:
        raise ValueError("GeoDataFrame vazio.")

    if buffer_m is None or float(buffer_m) <= 0:
        return gdf.copy()

    gdf_proj = gdf.to_crs(3857).copy()
    gdf_proj["geometry"] = gdf_proj.geometry.buffer(float(buffer_m))
    return gdf_proj.to_crs(4326)


def gdf_to_roi_geojson(gdf: gpd.GeoDataFrame, buffer_m: float = 0):
    if gdf is None or gdf.empty:
        raise ValueError("GeoDataFrame vazio para geração de ROI.")

    gdf_work = gdf.copy()

    if gdf_work.crs is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")

    if str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")

    geom = gdf_work.unary_union

    try:
        geom = geom.buffer(0)
    except Exception:
        pass

    if buffer_m and buffer_m > 0:
        gdf_tmp = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs="EPSG:4326")
        gdf_tmp = apply_buffer_in_meters(gdf_tmp, buffer_m)
        geom = gdf_tmp.geometry.iloc[0]

    return mapping(geom)