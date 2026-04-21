# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

import ee

from services.gee_catalog import SATELLITE_COLLECTIONS, ee_geometry_from_geojson


def _is_sentinel1_family(satellite: Optional[str]) -> bool:
    return satellite in ["Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]


def _is_dem_family(satellite: Optional[str]) -> bool:
    return satellite in ["NASADEM", "SRTM", "HydroSHEDS"]


def _normalize_dem_product_name(product_name: str) -> str:
    return (product_name or "").replace(" + curvas 5 m", "")


def should_overlay_dem_contours(satellite: Optional[str], product_name: Optional[str]) -> bool:
    return bool(_is_dem_family(satellite) and product_name and "curvas 5 m" in product_name)


def _get_default_dem_product_name(satellite: Optional[str]) -> str:
    if satellite in ["NASADEM", "SRTM"]:
        return "Hillshade"
    return "Hillshade + curvas 5 m"


def get_ee_image_for_display(
    image_id: Optional[str] = None,
    satellite: Optional[str] = None,
    roi_geojson: Optional[dict] = None,
    asset_id: Optional[str] = None,
    collection_id: Optional[str] = None,
) -> ee.Image:
    if image_id and "|" in str(image_id):
        image_id = str(image_id).split("|", 1)[0]

    if asset_id:
        img = ee.Image(asset_id)
    else:
        if not image_id:
            raise ValueError("image_id nao informado.")

        if "/" in str(image_id):
            img = ee.Image(image_id)
            if roi_geojson:
                img = img.clip(ee_geometry_from_geojson(roi_geojson))
            return img

        if not collection_id:
            if not satellite or satellite not in SATELLITE_COLLECTIONS:
                raise ValueError("satellite/collection_id invalido para reconstruir o asset.")
            collection_id = SATELLITE_COLLECTIONS[satellite]

        img = ee.Image(f"{collection_id}/{image_id}")

    if roi_geojson:
        img = img.clip(ee_geometry_from_geojson(roi_geojson))

    return img


def _get_dem_elevation_band(image: ee.Image, satellite: Optional[str]) -> ee.Image:
    if satellite == "HydroSHEDS":
        return image.select("b1").rename("elevation")
    return image.select("elevation").rename("elevation")


def _apply_sentinel_product(image: ee.Image, product_name: str) -> ee.Image:
    if product_name in ["Imagem Sentinel RGB", "Imagem Sentinel RGB Ajustada"]:
        return image.select(["B4", "B3", "B2"])
    if product_name == "Solo Exposto":
        return image.expression(
            "((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))",
            {
                "SWIR1": image.select("B11"),
                "RED": image.select("B4"),
                "NIR": image.select("B8"),
                "BLUE": image.select("B2"),
            },
        ).rename("BSI")
    if product_name == "NDVI":
        return image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    if product_name == "NDWI":
        return image.normalizedDifference(["B3", "B8"]).rename("NDWI")
    if product_name == "EVI":
        return image.expression(
            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
            {"NIR": image.select("B8"), "RED": image.select("B4"), "BLUE": image.select("B2")},
        ).rename("EVI")
    if product_name == "SAVI":
        return image.expression(
            "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
            {"NIR": image.select("B8"), "RED": image.select("B4"), "L": 0.5},
        ).rename("SAVI")
    if product_name == "NBR":
        return image.normalizedDifference(["B8", "B12"]).rename("NBR")
    if product_name == "MSI":
        return image.select("B11").divide(image.select("B8")).rename("MSI")
    if product_name == "GNDVI":
        return image.normalizedDifference(["B8", "B3"]).rename("GNDVI")
    return image.select(["B4", "B3", "B2"])


def _apply_sentinel1_product(image: ee.Image, product_name: str) -> ee.Image:
    if product_name == "Angulo de Incidencia":
        return image.select(["angle"]).rename("angle")
    if product_name == "VV (dB)":
        return image.select(["VV"]).rename("VV")
    if product_name == "VH (dB)":
        return image.select(["VH"]).rename("VH")
    ratio = image.select("VV").subtract(image.select("VH")).rename("VV_minus_VH")
    return ee.Image.cat([image.select("VV").rename("VV"), image.select("VH").rename("VH"), ratio])


def _rename_hls_bands(image: ee.Image, source_name: str) -> ee.Image:
    if source_name == "HLSL30":
        return image.select(
            ["B2", "B3", "B4", "B5", "B6", "B7"],
            ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"],
        )
    return image.select(
        ["B2", "B3", "B4", "B8A", "B11", "B12"],
        ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"],
    )


def _apply_hls_product(image: ee.Image, product_name: str, source_name: str) -> ee.Image:
    img = _rename_hls_bands(image, source_name)
    if product_name == "HLS Solo Exposto":
        return img.expression(
            "((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))",
            {
                "SWIR1": img.select("SWIR1"),
                "RED": img.select("RED"),
                "NIR": img.select("NIR"),
                "BLUE": img.select("BLUE"),
            },
        ).rename("BSI")
    if product_name == "NDVI":
        return img.normalizedDifference(["NIR", "RED"]).rename("NDVI")
    if product_name == "NDWI":
        return img.normalizedDifference(["GREEN", "NIR"]).rename("NDWI")
    if product_name == "NBR":
        return img.normalizedDifference(["NIR", "SWIR2"]).rename("NBR")
    return img.select(["RED", "GREEN", "BLUE"])


def _apply_landsat_product(image: ee.Image, satellite: str) -> ee.Image:
    if satellite in ["Landsat 5", "Landsat 7"]:
        return image.select(["SR_B3", "SR_B2", "SR_B1"])
    if satellite in ["Landsat 8", "Landsat 9"]:
        return image.select(["SR_B4", "SR_B3", "SR_B2"])
    return image


def _apply_dem_product(image: ee.Image, product_name: str) -> ee.Image:
    if product_name == "Declividade":
        return ee.Terrain.slope(image).rename("slope")
    if product_name == "Hillshade":
        return ee.Terrain.hillshade(image).rename("hillshade")
    return image.rename("elevation")


def _apply_merit_hydro_product(image: ee.Image, product_name: str) -> ee.Image:
    if product_name == "Area Montante":
        return image.select("upa").rename("upa")
    if product_name == "Elevacao Hidrologica":
        return image.select("elv").rename("elv")
    if product_name == "HAND":
        return image.select("hnd").rename("hnd")
    if product_name == "Direcao de Fluxo":
        return image.select("dir").rename("dir")
    if product_name == "Agua Permanente":
        return image.select("wat").rename("wat")
    return image.select("viswth").rename("viswth")


def _get_dynamic_single_band_range(
    image: ee.Image,
    band_name: str,
    roi_geojson: Optional[dict],
    default_min: float,
    default_max: float,
    scale: int = 30,
):
    if not roi_geojson:
        return default_min, default_max
    try:
        stats = (
            image.select(band_name)
            .reduceRegion(
                reducer=ee.Reducer.percentile([2, 98]),
                geometry=ee_geometry_from_geojson(roi_geojson),
                scale=scale,
                maxPixels=1_000_000,
                bestEffort=True,
            )
            .getInfo()
        )
        min_value = stats.get(f"{band_name}_p2")
        max_value = stats.get(f"{band_name}_p98")
        if min_value is None or max_value is None or float(min_value) >= float(max_value):
            return default_min, default_max
        return float(min_value), float(max_value)
    except Exception:
        return default_min, default_max


def build_dem_contours_image(
    image_id: Optional[str] = None,
    satellite: Optional[str] = None,
    roi_geojson: Optional[dict] = None,
    asset_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    interval_m: int = 5,
) -> ee.Image:
    dem = _get_dem_elevation_band(
        get_ee_image_for_display(
            image_id=image_id,
            satellite=satellite,
            roi_geojson=roi_geojson,
            asset_id=asset_id,
            collection_id=collection_id,
        ),
        satellite,
    )
    classes = dem.divide(interval_m).floor()
    return classes.focal_max(1).neq(classes.focal_min(1)).selfMask().rename("contours")


def get_dem_contours_vis() -> Dict:
    return {"min": 0, "max": 1, "palette": ["#f8fafc"]}


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
    if _is_sentinel1_family(satellite):
        return _apply_sentinel1_product(img, product_name or "Radar VV/VH")
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        source_name = "HLSL30" if collection_id == SATELLITE_COLLECTIONS["HLS Landsat"] else "HLSS30"
        return _apply_hls_product(img, product_name or "HLS RGB", source_name)
    if _is_dem_family(satellite):
        dem_product = _normalize_dem_product_name(product_name or _get_default_dem_product_name(satellite))
        return _apply_dem_product(_get_dem_elevation_band(img, satellite), dem_product)
    if satellite == "MERIT Hydro":
        return _apply_merit_hydro_product(img, product_name or "Largura de Rio")
    return _apply_landsat_product(img, satellite or "")


def get_product_vis_params(
    satellite: str,
    product_name: str,
    ee_image: Optional[ee.Image] = None,
    roi_geojson: Optional[dict] = None,
) -> Dict:
    if satellite == "Sentinel-2":
        if product_name == "Imagem Sentinel RGB Ajustada":
            return {"bands": ["B4", "B3", "B2"], "min": 220, "max": 2400, "gamma": 0.95}
        if product_name == "Imagem Sentinel RGB":
            return {"bands": ["B4", "B3", "B2"], "min": 80, "max": 3200, "gamma": 1.15}
        if product_name == "Solo Exposto":
            return {"min": -0.3, "max": 0.45, "palette": ["#07130b", "#2f4f2f", "#8a7d52", "#d2b48c", "#f5deb3"]}
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
    if _is_sentinel1_family(satellite):
        if product_name == "Angulo de Incidencia":
            return {"min": 25, "max": 45, "palette": ["#0b1320", "#155e75", "#67e8f9", "#f0fdfa"]}
        if product_name == "VV (dB)":
            return {"min": -20, "max": 2, "palette": ["#05080a", "#7dd3fc", "#f8fafc"]}
        if product_name == "VH (dB)":
            return {"min": -28, "max": -5, "palette": ["#05080a", "#93c5fd", "#f8fafc"]}
        return {"bands": ["VV", "VH", "VV_minus_VH"], "min": [-20, -28, 1], "max": [2, -5, 15]}
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        if product_name == "HLS RGB":
            return {"bands": ["RED", "GREEN", "BLUE"], "min": 0.015, "max": 0.16, "gamma": 0.98}
        if product_name == "HLS Solo Exposto":
            return {"min": -0.3, "max": 0.45, "palette": ["#07130b", "#2f4f2f", "#8a7d52", "#d2b48c", "#f5deb3"]}
        if product_name == "NDVI":
            return {"min": -0.2, "max": 0.9, "palette": ["brown", "yellow", "green"]}
        if product_name == "NDWI":
            return {"min": -0.5, "max": 0.5, "palette": ["brown", "beige", "blue"]}
        if product_name == "NBR":
            return {"min": -1.0, "max": 1.0, "palette": ["black", "red", "yellow", "green"]}
    if _is_dem_family(satellite):
        normalized_product = _normalize_dem_product_name(product_name)
        if normalized_product == "Hillshade":
            return {"min": 70, "max": 220, "palette": ["#0a0a0a", "#415247", "#9db39a", "#f1f5e8"]}
        if normalized_product == "Declividade":
            min_value, max_value = _get_dynamic_single_band_range(
                ee_image or ee.Image.constant(0).rename("slope"),
                "slope",
                roi_geojson,
                0,
                45,
            )
            return {"min": min_value, "max": max_value, "palette": ["#0b0f0c", "#1f5135", "#6d9f72", "#dbedc8"]}
        min_value, max_value = _get_dynamic_single_band_range(
            ee_image or ee.Image.constant(0).rename("elevation"),
            "elevation",
            roi_geojson,
            0,
            1800,
        )
        return {"min": min_value, "max": max_value, "palette": ["#15211a", "#3d6540", "#7f9867", "#b6ab83", "#f0ead8"]}
    if satellite == "MERIT Hydro":
        if product_name == "Area Montante":
            return {"min": 0, "max": 5000, "palette": ["#0b1320", "#1d4ed8", "#38bdf8", "#e0f2fe"]}
        if product_name == "Elevacao Hidrologica":
            return {"min": 0, "max": 2500, "palette": ["#15211a", "#3d6540", "#7f9867", "#b6ab83", "#f0ead8"]}
        if product_name == "HAND":
            return {"min": 0, "max": 50, "palette": ["#08130b", "#14532d", "#6d9f72", "#dbedc8"]}
        if product_name == "Direcao de Fluxo":
            return {"min": -1, "max": 128, "palette": ["#0b1320", "#334155", "#f8fafc"]}
        if product_name == "Agua Permanente":
            return {"min": 0, "max": 1, "palette": ["#111827", "#3b82f6"]}
        return {"min": 0, "max": 400, "palette": ["#020617", "#1d4ed8", "#93c5fd", "#f8fafc"]}
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
    return ee.Image(0).where(baixa, 1).where(media, 2).where(alta, 3).rename("corte_raso").selfMask()


def get_corte_raso_vis() -> Dict:
    return {"min": 1, "max": 3, "palette": ["green", "orange", "red"]}
