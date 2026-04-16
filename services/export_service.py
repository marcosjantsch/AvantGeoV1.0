# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

import requests
import rasterio
from rasterio.transform import Affine
from PIL import Image
import numpy as np
import ee

from services.gee_service import (
    build_display_image,
    get_product_vis_params,
    ee_geometry_from_geojson,
)


def _find_selected_spec(available_images, selected_scene_id):
    selected_spec = next(
        (img for img in available_images if img.get("id") == selected_scene_id),
        None,
    )
    if not selected_spec:
        raise ValueError("Cena selecionada não encontrada.")
    return selected_spec


def _download_ee_bytes(url: str) -> bytes:
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.content


def _export_rgb_jpeg(ee_img, roi_geojson, out_jpg: Path, satellite: str, product_name: str):
    region = ee_geometry_from_geojson(roi_geojson)

    # Para JPEG usamos visualização renderizada
    vis = get_product_vis_params(satellite, product_name)
    rendered = ee.Image(ee_img).visualize(**vis)

    url = rendered.getThumbURL({
        "region": region,
        "dimensions": 2048,
        "format": "jpg",
    })

    content = _download_ee_bytes(url)
    out_jpg.write_bytes(content)


def _export_geotiff(ee_img, roi_geojson, out_tif: Path, satellite: str, product_name: str):
    region = ee_geometry_from_geojson(roi_geojson)

    # Para GeoTIFF exportamos a imagem numérica
    # Se for índice de 1 banda, sai 1 banda georreferenciada
    # Se for RGB, saem 3 bandas
    url = ee.Image(ee_img).getDownloadURL({
        "region": region,
        "scale": 10 if satellite == "Sentinel-2" else 30,
        "format": "GEO_TIFF",
        "crs": "EPSG:4326",
    })

    content = _download_ee_bytes(url)
    out_tif.write_bytes(content)


def export_selected_image(
    available_images,
    selected_scene_id,
    selected_product_name,
    roi_geojson,
    output_dir,
    base_filename,
):
    if not selected_scene_id:
        raise ValueError("Nenhuma cena selecionada.")

    if not selected_product_name:
        raise ValueError("Nenhum tipo de imagem selecionado.")

    if not output_dir:
        raise ValueError("Caminho de saída não informado.")

    if not roi_geojson:
        raise ValueError("ROI não definida para exportação.")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

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

    out_tif = out_dir / f"{base_filename}.tif"
    out_jpg = out_dir / f"{base_filename}.jpg"

    _export_geotiff(
        ee_img=ee_img,
        roi_geojson=roi_geojson,
        out_tif=out_tif,
        satellite=satellite,
        product_name=selected_product_name,
    )

    _export_rgb_jpeg(
        ee_img=ee_img,
        roi_geojson=roi_geojson,
        out_jpg=out_jpg,
        satellite=satellite,
        product_name=selected_product_name,
    )

    return {
        "tif": str(out_tif),
        "jpg": str(out_jpg),
    }