# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

import ee
import streamlit as st

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

def _apply_cloud_filter(
    collection: ee.ImageCollection,
    satellite: str,
    cloud_pct: float,
):
    if satellite == "Sentinel-2":
        return collection.filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
    return collection.filter(ee.Filter.lte("CLOUD_COVER", cloud_pct))


def _build_sentinel_collection(
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    col = (
        ee.ImageCollection(SATELLITE_COLLECTIONS["Sentinel-2"])
        .filterBounds(geom)
        .filterDate(start_date, end_date)
    )
    return _apply_cloud_filter(col, "Sentinel-2", cloud_pct)


def _build_landsat_collection(
    collection_id: str,
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    col = (
        ee.ImageCollection(collection_id)
        .filterBounds(geom)
        .filterDate(start_date, end_date)
    )

    sat_name = [k for k, v in SATELLITE_COLLECTIONS.items() if v == collection_id][0]
    return _apply_cloud_filter(col, sat_name, cloud_pct)


def _collection_for_satellite(
    satellite: str,
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    if satellite == "Sentinel-2":
        return _build_sentinel_collection(geom, start_date, end_date, cloud_pct)
    if satellite == "Landsat 5":
        return _build_landsat_collection(
            SATELLITE_COLLECTIONS["Landsat 5"], geom, start_date, end_date, cloud_pct
        )
    if satellite == "Landsat 7":
        return _build_landsat_collection(
            SATELLITE_COLLECTIONS["Landsat 7"], geom, start_date, end_date, cloud_pct
        )
    if satellite == "Landsat 8":
        return _build_landsat_collection(
            SATELLITE_COLLECTIONS["Landsat 8"], geom, start_date, end_date, cloud_pct
        )
    if satellite == "Landsat 9":
        return _build_landsat_collection(
            SATELLITE_COLLECTIONS["Landsat 9"], geom, start_date, end_date, cloud_pct
        )
    return None


def _image_feature(img: ee.Image, satellite: str) -> ee.Feature:
    date_str = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")
    system_index = ee.String(img.get("system:index"))
    collection_id = ee.String(SATELLITE_COLLECTIONS[satellite])

    cloud_prop = ee.Algorithms.If(
        ee.Algorithms.IsEqual(img.get("CLOUDY_PIXEL_PERCENTAGE"), None),
        img.get("CLOUD_COVER"),
        img.get("CLOUDY_PIXEL_PERCENTAGE"),
    )

    return ee.Feature(
        None,
        {
            "id": system_index,
            "system_index": system_index,
            "collection_id": collection_id,
            "asset_id": collection_id.cat("/").cat(system_index),
            "date": date_str,
            "satellite": satellite,
            "cloud": cloud_prop,
        },
    )


@st.cache_data(show_spinner=False)
def list_available_images(
    roi_geojson: dict,
    satellites: List[str],
    start_date: str,
    end_date: str,
    cloud_pct: float = 25,
    max_per_satellite: int = 20,
) -> List[Dict]:
    geom = ee_geometry_from_geojson(roi_geojson)
    rows: List[Dict] = []

    for sat in satellites:
        collection = _collection_for_satellite(
            sat,
            geom,
            start_date,
            end_date,
            cloud_pct,
        )
        if collection is None:
            continue

        fc = ee.FeatureCollection(
            collection.sort("system:time_start", False)
            .limit(max_per_satellite)
            .map(lambda img: _image_feature(ee.Image(img), sat))
        )

        info = fc.getInfo()
        features = info.get("features", [])

        for ft in features:
            props = ft.get("properties", {})
            image_id = props.get("id")
            asset_id = props.get("asset_id")
            collection_id = props.get("collection_id")
            date_str = props.get("date")
            cloud = props.get("cloud")

            cloud_txt = "-" if cloud is None else f"{float(cloud):.1f}%"
            label = f"{sat} | {date_str} | nuvens: {cloud_txt}"

            rows.append(
                {
                    "id": image_id,
                    "asset_id": asset_id,
                    "collection_id": collection_id,
                    "label": label,
                    "satellite": sat,
                    "date": date_str,
                    "cloud": cloud,
                }
            )

    rows.sort(
        key=lambda x: (str(x.get("date", "")), str(x.get("satellite", ""))),
        reverse=True,
    )
    return rows


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
                raise ValueError(
                    "satellite/collection_id inválido para reconstruir o asset."
                )
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
            {
                "NIR": img.select("B8"),
                "RED": img.select("B4"),
                "BLUE": img.select("B2"),
            },
        ).rename("EVI")

    if product_name == "SAVI":
        return img.expression(
            "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
            {
                "NIR": img.select("B8"),
                "RED": img.select("B4"),
                "L": 0.5,
            },
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
            return {
                "bands": ["B4", "B3", "B2"],
                "min": 0,
                "max": 3500,
                "gamma": 1.3,
            }

        if product_name == "Imagem Sentinel RGB Ajustada":
            return {
                "bands": ["B4", "B3", "B2"],
                "min": 150,
                "max": 2500,
                "gamma": 1.05,
            }

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
    """
    Classificação simplificada de Corte Raso baseada no script legado.
    Classes:
      1 = não analisado / baixo
      2 = madeira em pé
      3 = corte raso

    Faixas derivadas do código antigo:
      0.0–0.7   = baixo / não analisado
      0.7–1.0   = madeira em pé
      1.0–2.0   = corte raso
    """
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

    classificacao = (
        ee.Image(0)
        .where(baixa, 1)
        .where(media, 2)
        .where(alta, 3)
        .rename("corte_raso")
        .selfMask()
    )

    return classificacao


def get_corte_raso_vis() -> Dict:
    return {
        "min": 1,
        "max": 3,
        "palette": ["green", "orange", "red"],
    }