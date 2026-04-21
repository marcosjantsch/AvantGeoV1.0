# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List

import ee

from core.settings import ASSET_FAZENDAS, COL_EMPRESA, COL_FAZENDA

SENTINEL2_SR_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
SENTINEL2_TOA_COLLECTION = "COPERNICUS/S2_HARMONIZED"

SATELLITE_COLLECTIONS = {
    "Sentinel-2": SENTINEL2_SR_COLLECTION,
    "Sentinel-1 (10 m radar)": "COPERNICUS/S1_GRD",
    "Sentinel-1 SAR GRD (C-band)": "COPERNICUS/S1_GRD",
    "HLS Landsat": "NASA/HLS/HLSL30/v002",
    "HLS Sentinel": "NASA/HLS/HLSS30/v002",
    "NASADEM": "NASA/NASADEM_HGT/001",
    "SRTM": "USGS/SRTMGL1_003",
    "HydroSHEDS": "WWF/HydroSHEDS/03VFDEM",
    "MERIT Hydro": "MERIT/Hydro/v1_0_1",
    "Landsat 5": "LANDSAT/LT05/C02/T1_L2",
    "Landsat 7": "LANDSAT/LE07/C02/T1_L2",
    "Landsat 8": "LANDSAT/LC08/C02/T1_L2",
    "Landsat 9": "LANDSAT/LC09/C02/T1_L2",
}

SATELLITE_START_DATES = {
    "Sentinel-2": "2015-06-27",
    "Sentinel-1 (10 m radar)": "2014-10-03",
    "Sentinel-1 SAR GRD (C-band)": "2014-10-03",
}


def get_farm_fc(empresa: str, fazenda: str) -> ee.FeatureCollection:
    return (
        ee.FeatureCollection(ASSET_FAZENDAS)
        .filter(ee.Filter.eq(COL_EMPRESA, empresa))
        .filter(ee.Filter.eq(COL_FAZENDA, fazenda))
    )


def get_farm_geom(empresa: str, fazenda: str) -> ee.Geometry:
    return get_farm_fc(empresa, fazenda).geometry()


def ee_geometry_from_geojson(geojson_dict: dict) -> ee.Geometry:
    return ee.Geometry(geojson_dict)


def get_satellite_start_date(satellite: str, fallback: str = "2015-06-27") -> str:
    return SATELLITE_START_DATES.get(satellite, fallback)


def get_available_visual_products(satellite: str) -> List[str]:
    if satellite == "Sentinel-2":
        return [
            "Imagem Sentinel RGB Ajustada",
            "Imagem Sentinel RGB",
            "Solo Exposto",
            "NDVI",
            "NDWI",
            "EVI",
            "SAVI",
            "NBR",
            "MSI",
            "GNDVI",
        ]
    if satellite in ["Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]:
        return [
            "Radar VV/VH",
            "VV (dB)",
            "VH (dB)",
            "Angulo de Incidencia",
        ]
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        return [
            "HLS RGB",
            "HLS Solo Exposto",
            "NDVI",
            "NDWI",
            "NBR",
        ]
    if satellite in ["NASADEM", "SRTM"]:
        return [
            "Hillshade",
            "Elevacao",
            "Declividade",
        ]
    if satellite == "HydroSHEDS":
        return [
            "Hillshade + curvas 5 m",
            "Hillshade",
            "Elevacao + curvas 5 m",
            "Elevacao",
            "Declividade + curvas 5 m",
            "Declividade",
        ]
    if satellite == "MERIT Hydro":
        return [
            "Largura de Rio",
            "Area Montante",
            "Elevacao Hidrologica",
            "HAND",
            "Direcao de Fluxo",
            "Agua Permanente",
        ]
    return ["RGB Landsat"]
