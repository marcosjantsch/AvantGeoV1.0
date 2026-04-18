# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List

import ee

from core.settings import ASSET_FAZENDAS, COL_EMPRESA, COL_FAZENDA


SATELLITE_COLLECTIONS = {
    "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
    "Landsat 5": "LANDSAT/LT05/C02/T1_L2",
    "Landsat 7": "LANDSAT/LE07/C02/T1_L2",
    "Landsat 8": "LANDSAT/LC08/C02/T1_L2",
    "Landsat 9": "LANDSAT/LC09/C02/T1_L2",
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


def get_available_visual_products(satellite: str) -> List[str]:
    if satellite == "Sentinel-2":
        return [
            "Imagem Sentinel RGB",
            "Imagem Sentinel RGB Ajustada",
            "NDVI",
            "NDWI",
            "EVI",
            "SAVI",
            "NBR",
            "MSI",
            "GNDVI",
        ]
    return ["RGB Landsat"]
