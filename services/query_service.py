# -*- coding: utf-8 -*-
from __future__ import annotations

from services.coordinate_service import CAPTURE_MODE_LABEL
from services.file_service import read_kml_or_kmz_to_gdf
from services.geometry_service import (
    build_gdf_from_point_dd,
    build_gdf_from_point_utm,
    filter_gdf,
    gdf_to_roi_geojson,
)


def _prepare_kml_geometry_for_query(gdf, buffer_m: float):
    if gdf is None or gdf.empty:
        raise ValueError("O arquivo KML/KMZ não possui geometria válida.")

    gdf_work = gdf.copy()

    if gdf_work.crs is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")

    if str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")

    roi_geojson = gdf_to_roi_geojson(gdf_work, buffer_m=buffer_m)
    return gdf_work, roi_geojson


def get_query_gdf_and_roi_geojson(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
):
    if modo_entrada == "Empresa / Fazenda":
        query_gdf = filter_gdf(gdf_full, selected_empresa, selected_fazenda)
        if query_gdf is None or query_gdf.empty:
            raise ValueError("Nenhuma geometria encontrada para a empresa/fazenda selecionada.")

        roi_geojson = gdf_to_roi_geojson(query_gdf, buffer_m=buffer_m)
        return query_gdf, roi_geojson

    if modo_entrada in ["Coordenada", CAPTURE_MODE_LABEL]:
        if not parsed_coordinates:
            raise ValueError("Coordenadas não informadas.")

        if parsed_coordinates.get("coord_system") in [
            "Graus, minutos e segundos (DMS)",
            "Graus decimais (DD)",
        ]:
            lat = parsed_coordinates.get("latitude")
            lon = parsed_coordinates.get("longitude")

            if lat is None or lon is None:
                raise ValueError("Latitude/Longitude inválidas.")

            query_gdf = build_gdf_from_point_dd(lat, lon)
        elif parsed_coordinates.get("coord_system") == "UTM":
            easting = parsed_coordinates.get("utm_easting")
            northing = parsed_coordinates.get("utm_northing")
            zone = parsed_coordinates.get("utm_zone")
            hemisphere = parsed_coordinates.get("utm_hemisphere")

            if None in [easting, northing] or not zone or not hemisphere:
                raise ValueError("Coordenadas UTM inválidas.")

            query_gdf = build_gdf_from_point_utm(
                easting,
                northing,
                zone,
                hemisphere,
            )
        else:
            raise ValueError("Sistema de coordenadas inválido.")

        roi_geojson = gdf_to_roi_geojson(query_gdf, buffer_m=buffer_m)
        return query_gdf, roi_geojson

    if modo_entrada == "Arquivo KML/KMZ":
        query_gdf = read_kml_or_kmz_to_gdf(uploaded_kml)
        if query_gdf is None or query_gdf.empty:
            raise ValueError("Não foi possível obter geometria do KML/KMZ.")

        query_gdf, roi_geojson = _prepare_kml_geometry_for_query(query_gdf, buffer_m=buffer_m)
        return query_gdf, roi_geojson

    raise ValueError("Modo de entrada inválido.")
