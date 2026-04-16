# -*- coding: utf-8 -*-
import json
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

try:
    from shapely.validation import make_valid
except Exception:
    make_valid = None


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
    if latitude is None or longitude is None:
        raise ValueError("Latitude/Longitude não informadas.")

    pt = Point(float(longitude), float(latitude))
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
    lon, lat = transformer.transform(float(easting), float(northing))

    return build_gdf_from_point_dd(latitude=lat, longitude=lon)


def _normalize_gdf_4326(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf is None or gdf.empty:
        raise ValueError("GeoDataFrame vazio.")

    gdf_work = gdf.copy()
    gdf_work = gdf_work[gdf_work.geometry.notna()].copy()
    gdf_work = gdf_work[~gdf_work.geometry.is_empty].copy()

    if gdf_work.empty:
        raise ValueError("GeoDataFrame sem geometrias válidas.")

    if gdf_work.crs is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")
    elif str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")

    return gdf_work


def _fix_geometry(geom):
    if geom is None or geom.is_empty:
        raise ValueError("Geometria vazia.")

    try:
        if make_valid is not None:
            geom = make_valid(geom)
    except Exception:
        pass

    if geom is None or geom.is_empty:
        try:
            geom = geom.buffer(0)
        except Exception:
            pass

    if geom is None or geom.is_empty:
        raise ValueError("Geometria inválida após correção topológica.")

    if geom.geom_type == "GeometryCollection":
        parts = [g for g in geom.geoms if not g.is_empty]
        if not parts:
            raise ValueError("GeometryCollection vazia após correção.")
        geom = unary_union(parts)

    if geom is None or geom.is_empty:
        raise ValueError("Geometria inválida após unificação.")

    return geom


def apply_buffer_in_meters(gdf: gpd.GeoDataFrame, buffer_m: float):
    gdf_work = _normalize_gdf_4326(gdf)

    if buffer_m is None or float(buffer_m) <= 0:
        return gdf_work.copy()

    try:
        local_crs = gdf_work.estimate_utm_crs()
    except Exception:
        local_crs = None

    if local_crs is None:
        local_crs = "EPSG:3857"

    gdf_proj = gdf_work.to_crs(local_crs).copy()
    gdf_proj["geometry"] = gdf_proj.geometry.buffer(float(buffer_m))
    gdf_proj = gdf_proj[gdf_proj.geometry.notna()].copy()
    gdf_proj = gdf_proj[~gdf_proj.geometry.is_empty].copy()

    if gdf_proj.empty:
        raise ValueError("Falha ao gerar buffer da geometria.")

    return gdf_proj.to_crs("EPSG:4326")


def _ensure_polygonal_roi(gdf_work: gpd.GeoDataFrame, buffer_m: float):
    geom = unary_union(gdf_work.geometry.tolist())

    if geom is None or geom.is_empty:
        raise ValueError("Não foi possível unificar as geometrias.")

    geom_type = geom.geom_type

    # Se for ponto/linha, precisa virar área primeiro
    if geom_type in ["Point", "MultiPoint", "LineString", "MultiLineString"]:
        buffer_value = float(buffer_m) if buffer_m and float(buffer_m) > 0 else 200.0
        gdf_tmp = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs="EPSG:4326")
        gdf_tmp = apply_buffer_in_meters(gdf_tmp, buffer_value)
        geom = unary_union(gdf_tmp.geometry.tolist())

    # Se já for polígono e houver buffer solicitado, aplica depois
    elif buffer_m and float(buffer_m) > 0:
        gdf_tmp = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs="EPSG:4326")
        gdf_tmp = apply_buffer_in_meters(gdf_tmp, float(buffer_m))
        geom = unary_union(gdf_tmp.geometry.tolist())

    geom = _fix_geometry(geom)

    if geom.geom_type not in ["Polygon", "MultiPolygon"]:
        raise ValueError(
            f"ROI final inválido. Tipo obtido: {geom.geom_type}. "
            "Aumente o buffer ou revise a geometria de entrada."
        )

    return geom


def gdf_to_roi_geojson(gdf: gpd.GeoDataFrame, buffer_m: float = 0):
    gdf_work = _normalize_gdf_4326(gdf)
    geom = _ensure_polygonal_roi(gdf_work, buffer_m)

    geojson_geom = mapping(geom)
    geojson_geom = json.loads(json.dumps(geojson_geom))

    if "type" not in geojson_geom or "coordinates" not in geojson_geom:
        raise ValueError("GeoJSON ROI inválido.")

    if geojson_geom["type"] not in ["Polygon", "MultiPolygon"]:
        raise ValueError(
            f"ROI final inválido para consulta: {geojson_geom['type']}"
        )

    return geojson_geom
