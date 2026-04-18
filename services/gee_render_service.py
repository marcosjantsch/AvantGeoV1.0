# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

import ee

from services.gee_catalog import SATELLITE_COLLECTIONS, ee_geometry_from_geojson


def get_ee_image_for_display(
    image_id: Optional[str] = None,
    satellite: Optional[str] = None,
    roi_geojson: Optional[dict] = None,
    asset_id: Optional[str] = None,
    collection_id: Optional[str] = None,
) -> ee.Image:
    if asset_id:
        img = ee.Image(asset_id)
    else:
        if not image_id:
            raise ValueError("image_id não informado.")

        if not collection_id:
            if not satellite or satellite not in SATELLITE_COLLECTIONS:
                raise ValueError("satellite/collection_id inválido para reconstruir o asset.")
            collection_id = SATELLITE_COLLECTIONS[satellite]

        img = ee.Image(f"{collection_id}/{image_id}")

    if roi_geojson:
        img = img.clip(ee_geometry_from_geojson(roi_geojson))

    return img


def _apply_sentinel_product(image: ee.Image, product_name: str) -> ee.Image:
    img = image

    if product_name == "Imagem Sentinel RGB":
        return img.select(["B4", "B3", "B2"])
    if product_name == "Imagem Sentinel RGB Ajustada":
        return img.select(["B4", "B3", "B2"])
    if product_name == "NDVI":
        return img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    if product_name == "NDWI":
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI")
    if product_name == "EVI":
        return img.expression(
            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
            {"NIR": img.select("B8"), "RED": img.select("B4"), "BLUE": img.select("B2")},
        ).rename("EVI")
    if product_name == "SAVI":
        return img.expression(
            "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
            {"NIR": img.select("B8"), "RED": img.select("B4"), "L": 0.5},
        ).rename("SAVI")
    if product_name == "NBR":
        return img.normalizedDifference(["B8", "B12"]).rename("NBR")
    if product_name == "MSI":
        return img.select("B11").divide(img.select("B8")).rename("MSI")
    if product_name == "GNDVI":
        return img.normalizedDifference(["B8", "B3"]).rename("GNDVI")

    return img.select(["B4", "B3", "B2"])


def _apply_landsat_product(
    image: ee.Image,
    satellite: str,
    product_name: str,
) -> ee.Image:
    if satellite in ["Landsat 5", "Landsat 7"]:
        return image.select(["SR_B3", "SR_B2", "SR_B1"])
    if satellite in ["Landsat 8", "Landsat 9"]:
        return image.select(["SR_B4", "SR_B3", "SR_B2"])
    return image


def build_display_image(
    image_id: Optional[str] = None,
    satellite: Optional[str] = None,
    roi_geojson: Optional[dict] = None,
    asset_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    product_name: Optional[str] = None,
) -> ee.Image:
    img = get_ee_image_for_display(
        image_id=image_id,
        satellite=satellite,
        roi_geojson=roi_geojson,
        asset_id=asset_id,
        collection_id=collection_id,
    )

    if satellite == "Sentinel-2":
        return _apply_sentinel_product(img, product_name or "Imagem Sentinel RGB")

    return _apply_landsat_product(img, satellite or "", product_name or "RGB Landsat")


def get_product_vis_params(satellite: str, product_name: str) -> Dict:
    if satellite == "Sentinel-2":
        if product_name == "Imagem Sentinel RGB":
            return {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3500, "gamma": 1.3}
        if product_name == "Imagem Sentinel RGB Ajustada":
            return {"bands": ["B4", "B3", "B2"], "min": 150, "max": 2500, "gamma": 1.05}
        if product_name == "NDVI":
            return {"min": -0.2, "max": 0.9, "palette": ["brown", "yellow", "green"]}
        if product_name == "NDWI":
            return {"min": -0.5, "max": 0.5, "palette": ["brown", "beige", "blue"]}
        if product_name == "EVI":
            return {"min": -0.2, "max": 1.0, "palette": ["brown", "yellow", "green"]}
        if product_name == "SAVI":
            return {"min": -0.2, "max": 1.0, "palette": ["brown", "yellow", "green"]}
        if product_name == "NBR":
            return {"min": -1.0, "max": 1.0, "palette": ["black", "red", "yellow", "green"]}
        if product_name == "MSI":
            return {"min": 0.2, "max": 2.0, "palette": ["green", "yellow", "red"]}
        if product_name == "GNDVI":
            return {"min": -0.2, "max": 0.9, "palette": ["brown", "yellow", "green"]}

    if satellite in ["Landsat 5", "Landsat 7"]:
        return {"bands": ["SR_B3", "SR_B2", "SR_B1"], "min": 7000, "max": 18000}
    if satellite in ["Landsat 8", "Landsat 9"]:
        return {"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 7000, "max": 18000}

    return {"min": 0, "max": 1}


def build_sentinel_corte_raso_image(
    image_id: Optional[str] = None,
    roi_geojson: Optional[dict] = None,
    asset_id: Optional[str] = None,
    collection_id: Optional[str] = None,
) -> ee.Image:
    img = get_ee_image_for_display(
        image_id=image_id,
        satellite="Sentinel-2",
        roi_geojson=roi_geojson,
        asset_id=asset_id,
        collection_id=collection_id,
    )

    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    kernel = ee.Kernel.square(radius=0, units="pixels", normalize=True)
    suavizacao = ndvi.convolve(kernel)

    classe_baixa = suavizacao.gte(0.0).And(suavizacao.lt(0.7))
    classe_media = suavizacao.gte(0.7).And(suavizacao.lt(1.0))
    classe_alta = suavizacao.gte(1.0).And(suavizacao.lt(2.0))

    baixa = classe_baixa.selfMask().multiply(1)
    media = classe_media.selfMask().multiply(2)
    alta = classe_alta.selfMask().multiply(3)

    return (
        ee.Image(0)
        .where(baixa, 1)
        .where(media, 2)
        .where(alta, 3)
        .rename("corte_raso")
        .selfMask()
    )


def get_corte_raso_vis() -> Dict:
    return {"min": 1, "max": 3, "palette": ["green", "orange", "red"]}
