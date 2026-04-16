# -*- coding: utf-8 -*-
from services.file_service import read_kml_or_kmz_to_gdf
from services.geometry_service import (
    filter_gdf,
    build_gdf_from_point_dd,
    build_gdf_from_point_utm,
    gdf_to_roi_geojson,
    apply_buffer_in_meters,
)


def _prepare_kml_geometry_for_query(gdf, buffer_m: float):
    """
    Trata KML/KMZ conforme o tipo geométrico:
    - Polygon / MultiPolygon: usa a geometria diretamente
    - Point / MultiPoint: aplica buffer para criar área
    - LineString / MultiLineString: aplica buffer para criar área
    """
    if gdf is None or gdf.empty:
        raise ValueError("O arquivo KML/KMZ não possui geometria válida.")

    gdf_work = gdf.copy()

    if gdf_work.crs is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")

    if str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")

    geom_types = set(gdf_work.geometry.geom_type.dropna().unique().tolist())

    has_polygon = any(gt in ["Polygon", "MultiPolygon"] for gt in geom_types)
    has_line = any(gt in ["LineString", "MultiLineString"] for gt in geom_types)
    has_point = any(gt in ["Point", "MultiPoint"] for gt in geom_types)

    if has_line or has_point:
        buffer_value = float(buffer_m) if buffer_m and float(buffer_m) > 0 else 200.0
        gdf_work = apply_buffer_in_meters(gdf_work, buffer_value)
        return gdf_work

    if has_polygon:
        return gdf_work

    raise ValueError("O arquivo KML/KMZ possui um tipo de geometria não suportado.")


def _validate_parsed_coordinates(parsed_coordinates):
    if not parsed_coordinates or not isinstance(parsed_coordinates, dict):
        raise ValueError("Coordenadas não informadas ou inválidas.")

    coord_system = parsed_coordinates.get("coord_system")
    if not coord_system:
        raise ValueError("Sistema de coordenadas não informado.")

    if coord_system in ["Graus, minutos e segundos (DMS)", "Graus decimais (DD)"]:
        lat = parsed_coordinates.get("latitude")
        lon = parsed_coordinates.get("longitude")

        if lat is None or lon is None:
            raise ValueError("Latitude/Longitude não foram preenchidas corretamente.")

        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            raise ValueError("Latitude/Longitude inválidas.")

        if not (-90 <= lat <= 90):
            raise ValueError("Latitude fora do intervalo válido (-90 a 90).")

        if not (-180 <= lon <= 180):
            raise ValueError("Longitude fora do intervalo válido (-180 a 180).")

        return {
            "coord_system": coord_system,
            "latitude": lat,
            "longitude": lon,
            "utm_easting": None,
            "utm_northing": None,
            "utm_zone": None,
            "utm_hemisphere": None,
        }

    if coord_system == "UTM":
        easting = parsed_coordinates.get("utm_easting")
        northing = parsed_coordinates.get("utm_northing")
        zone = parsed_coordinates.get("utm_zone")
        hemisphere = parsed_coordinates.get("utm_hemisphere")

        if easting is None or northing is None or not zone or not hemisphere:
            raise ValueError("Coordenadas UTM incompletas ou inválidas.")

        try:
            easting = float(easting)
            northing = float(northing)
        except Exception:
            raise ValueError("Easting/Northing UTM inválidos.")

        try:
            zone_int = int(str(zone).strip())
        except Exception:
            raise ValueError("Fuso UTM inválido.")

        if not (1 <= zone_int <= 60):
            raise ValueError("Fuso UTM deve estar entre 1 e 60.")

        hemisphere = str(hemisphere).strip().upper()
        if hemisphere not in ["S", "N"]:
            raise ValueError("Hemisfério UTM inválido. Use S ou N.")

        return {
            "coord_system": coord_system,
            "latitude": None,
            "longitude": None,
            "utm_easting": easting,
            "utm_northing": northing,
            "utm_zone": str(zone_int),
            "utm_hemisphere": hemisphere,
        }

    raise ValueError("Sistema de coordenadas inválido.")


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
            raise ValueError(
                "Nenhuma geometria encontrada para a empresa/fazenda selecionada."
            )

        roi_geojson = gdf_to_roi_geojson(query_gdf, buffer_m=buffer_m)
        return query_gdf, roi_geojson

    if modo_entrada == "Coordenada":
        parsed_coordinates = _validate_parsed_coordinates(parsed_coordinates)
        coord_system = parsed_coordinates.get("coord_system")

        if coord_system in [
            "Graus, minutos e segundos (DMS)",
            "Graus decimais (DD)",
        ]:
            lat = parsed_coordinates.get("latitude")
            lon = parsed_coordinates.get("longitude")
            query_gdf = build_gdf_from_point_dd(lat, lon)

        elif coord_system == "UTM":
            easting = parsed_coordinates.get("utm_easting")
            northing = parsed_coordinates.get("utm_northing")
            zone = parsed_coordinates.get("utm_zone")
            hemisphere = parsed_coordinates.get("utm_hemisphere")

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

        query_gdf = _prepare_kml_geometry_for_query(query_gdf, buffer_m=buffer_m)
        roi_geojson = gdf_to_roi_geojson(query_gdf, buffer_m=0)

        return query_gdf, roi_geojson

    raise ValueError("Modo de entrada inválido.")
