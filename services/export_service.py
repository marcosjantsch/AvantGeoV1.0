# -*- coding: utf-8 -*-
from __future__ import annotations

import io
from typing import Dict

import ee
import requests

from services.gee_service import build_display_image, ee_geometry_from_geojson, get_product_vis_params


DEFAULT_EXPORT_DIMENSIONS = 2048


def _find_selected_spec(available_images, selected_scene_id):
    selected_spec = next((img for img in available_images if img.get("id") == selected_scene_id), None)
    if not selected_spec:
        raise ValueError("Cena selecionada não encontrada.")
    return selected_spec


def _download_ee_bytes(url: str) -> bytes:
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    return resp.content


def _export_rgb_png_bytes(ee_img, roi_geojson, satellite: str, product_name: str) -> bytes:
    region = ee_geometry_from_geojson(roi_geojson)
    vis = get_product_vis_params(satellite, product_name)
    rendered = ee.Image(ee_img).visualize(**vis)
    url = rendered.getThumbURL({"region": region, "dimensions": DEFAULT_EXPORT_DIMENSIONS, "format": "png"})
    return _download_ee_bytes(url)


def _export_geotiff_bytes(ee_img, roi_geojson, satellite: str) -> bytes:
    region = ee_geometry_from_geojson(roi_geojson)
    url = ee.Image(ee_img).getDownloadURL(
        {
            "region": region,
            "scale": 10 if satellite == "Sentinel-2" else 30,
            "format": "GEO_TIFF",
            "crs": "EPSG:4326",
        }
    )
    return _download_ee_bytes(url)


def export_selected_image(available_images, selected_scene_id, selected_product_name, roi_geojson, base_filename) -> Dict:
    if not selected_scene_id:
        raise ValueError("Nenhuma cena selecionada.")
    if not selected_product_name:
        raise ValueError("Nenhum tipo de imagem selecionado.")
    if not roi_geojson:
        raise ValueError("ROI não definida para exportação.")

    base_filename = (base_filename or "exportacao_imagem").strip()
    selected_spec = _find_selected_spec(available_images, selected_scene_id)

    image_id = selected_spec.get("id")
    asset_id = selected_spec.get("asset_id")
    collection_id = selected_spec.get("collection_id")
    satellite = selected_spec.get("satellite")

    ee_img = build_display_image(
        image_id=image_id,
        satellite=satellite,
        roi_geojson=roi_geojson,
        asset_id=asset_id,
        collection_id=collection_id,
        product_name=selected_product_name,
    )

    tif_bytes = _export_geotiff_bytes(ee_img=ee_img, roi_geojson=roi_geojson, satellite=satellite)
    png_bytes = _export_rgb_png_bytes(
        ee_img=ee_img,
        roi_geojson=roi_geojson,
        satellite=satellite,
        product_name=selected_product_name,
    )

    return {
        "tif_bytes": tif_bytes,
        "png_bytes": png_bytes,
        "tif_buffer": io.BytesIO(tif_bytes),
        "png_buffer": io.BytesIO(png_bytes),
        "tif_name": f"{base_filename}.tif",
        "png_name": f"{base_filename}.png",
        "scene_id": selected_scene_id,
        "product_name": selected_product_name,
    }
