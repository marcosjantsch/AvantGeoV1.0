# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional


CAPTURE_MODE_LABEL = "Capturar Coordenada"


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return None


def dms_to_decimal(graus, minutos, segundos, hemisferio=None):
    g = _to_float(graus)
    m = _to_float(minutos)
    s = _to_float(segundos)

    if g is None or m is None or s is None:
        return None

    decimal = abs(g) + (m / 60.0) + (s / 3600.0)

    if hemisferio:
        hemisferio = str(hemisferio).strip().upper()
        if hemisferio in ["S", "W", "O"]:
            decimal *= -1

    if g < 0:
        decimal *= -1

    return decimal


def decimal_to_dms(value: Optional[float], is_latitude: bool = True) -> Optional[str]:
    if value is None:
        return None

    value = float(value)
    abs_value = abs(value)
    graus = int(abs_value)
    minutos_float = (abs_value - graus) * 60.0
    minutos = int(minutos_float)
    segundos = (minutos_float - minutos) * 60.0

    if is_latitude:
        hem = "N" if value >= 0 else "S"
    else:
        hem = "E" if value >= 0 else "W"

    return f"{graus}° {minutos:02d}' {segundos:06.3f}\" {hem}"


def format_dd(value: Optional[float], digits: int = 6) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def build_capture_payload(latitude: Optional[float], longitude: Optional[float]) -> Optional[Dict[str, Any]]:
    if latitude is None or longitude is None:
        return None

    latitude = float(latitude)
    longitude = float(longitude)

    return {
        "coord_system": "Graus decimais (DD)",
        "latitude": latitude,
        "longitude": longitude,
        "utm_easting": None,
        "utm_northing": None,
        "utm_zone": None,
        "utm_hemisphere": None,
        "latitude_dd": latitude,
        "longitude_dd": longitude,
        "latitude_dms": decimal_to_dms(latitude, is_latitude=True),
        "longitude_dms": decimal_to_dms(longitude, is_latitude=False),
        "source": "map_click",
    }


def parse_coordinate_payload(coord_system, values):
    if coord_system == "Graus, minutos e segundos (DMS)":
        lat = dms_to_decimal(
            values.get("lat_graus"),
            values.get("lat_minutos"),
            values.get("lat_segundos"),
            values.get("lat_hemisferio"),
        )
        lon = dms_to_decimal(
            values.get("lon_graus"),
            values.get("lon_minutos"),
            values.get("lon_segundos"),
            values.get("lon_hemisferio"),
        )
        return {
            "coord_system": coord_system,
            "latitude": lat,
            "longitude": lon,
            "utm_easting": None,
            "utm_northing": None,
            "utm_zone": None,
            "utm_hemisphere": None,
            "latitude_dms": decimal_to_dms(lat, is_latitude=True) if lat is not None else None,
            "longitude_dms": decimal_to_dms(lon, is_latitude=False) if lon is not None else None,
        }

    if coord_system == "Graus decimais (DD)":
        lat = _to_float(values.get("latitude_dd"))
        lon = _to_float(values.get("longitude_dd"))
        return {
            "coord_system": coord_system,
            "latitude": lat,
            "longitude": lon,
            "utm_easting": None,
            "utm_northing": None,
            "utm_zone": None,
            "utm_hemisphere": None,
            "latitude_dms": decimal_to_dms(lat, is_latitude=True) if lat is not None else None,
            "longitude_dms": decimal_to_dms(lon, is_latitude=False) if lon is not None else None,
        }

    if coord_system == "UTM":
        return {
            "coord_system": coord_system,
            "latitude": None,
            "longitude": None,
            "utm_easting": _to_float(values.get("utm_easting")),
            "utm_northing": _to_float(values.get("utm_northing")),
            "utm_zone": values.get("utm_zone"),
            "utm_hemisphere": values.get("utm_hemisphere"),
            "latitude_dms": None,
            "longitude_dms": None,
        }

    return {
        "coord_system": coord_system,
        "latitude": None,
        "longitude": None,
        "utm_easting": None,
        "utm_northing": None,
        "utm_zone": None,
        "utm_hemisphere": None,
        "latitude_dms": None,
        "longitude_dms": None,
    }
