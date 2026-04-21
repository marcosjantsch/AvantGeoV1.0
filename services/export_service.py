# -*- coding: utf-8 -*-
from __future__ import annotations

import io
from typing import Dict

import ee
import requests
from shapely.geometry import mapping

from services.gee_service import build_display_image, ee_geometry_from_geojson, get_product_vis_params


DEFAULT_EXPORT_DIMENSIONS = 2048


def _find_selected_spec(available_images, selected_scene_id):
    selected_spec = next(
        (
            img
            for img in available_images
            if img.get("id") == selected_scene_id or img.get("asset_id") == selected_scene_id
        ),
        None,
    )
    if not selected_spec:
        raise ValueError("Cena selecionada não encontrada.")
    return selected_spec


def _download_ee_bytes(url: str) -> bytes:
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    return resp.content


def _gdf_to_ee_feature_collection(query_gdf):
    if query_gdf is None or getattr(query_gdf, "empty", True):
        return None

    gdf_work = query_gdf.copy()
    if getattr(gdf_work, "crs", None) is None:
        gdf_work = gdf_work.set_crs("EPSG:4326")
    elif str(gdf_work.crs).upper() != "EPSG:4326":
        gdf_work = gdf_work.to_crs("EPSG:4326")

    features = []
    for geom in gdf_work.geometry:
        if geom is None or getattr(geom, "is_empty", False):
            continue
        features.append(ee.Feature(ee.Geometry(mapping(geom))))

    if not features:
        return None

    return ee.FeatureCollection(features)


def _blend_query_boundary(rendered_image, query_gdf):
    query_fc = _gdf_to_ee_feature_collection(query_gdf)
    if query_fc is None:
        return rendered_image

    boundary_fill = ee.Image().byte().paint(query_fc, 1, 3).visualize(
        palette=["#f97316"],
        opacity=0.95,
    )
    boundary_outline = ee.Image().byte().paint(query_fc, 1, 1).visualize(
        palette=["#fff7ed"],
        opacity=1.0,
    )
    return ee.Image(rendered_image).blend(boundary_fill).blend(boundary_outline)


def _export_rgb_png_bytes(
    ee_img,
    roi_geojson,
    satellite: str,
    product_name: str,
    query_gdf=None,
    include_boundary_png: bool = True,
) -> bytes:
    region = ee_geometry_from_geojson(roi_geojson)
    vis = get_product_vis_params(satellite, product_name, ee_image=ee_img, roi_geojson=roi_geojson)
    rendered = ee.Image(ee_img).visualize(**vis)
    if include_boundary_png:
        rendered = _blend_query_boundary(rendered, query_gdf)
    url = rendered.getThumbURL({"region": region, "dimensions": DEFAULT_EXPORT_DIMENSIONS, "format": "png"})
    return _download_ee_bytes(url)


def _export_geotiff_bytes(ee_img, roi_geojson, satellite: str) -> bytes:
    region = ee_geometry_from_geojson(roi_geojson)
    scale = 30
    if satellite in ["Sentinel-2", "Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]:
        scale = 10
    if satellite in ["NASADEM", "SRTM"]:
        scale = 30
    if satellite in ["HydroSHEDS", "MERIT Hydro"]:
        scale = 90
    url = ee.Image(ee_img).getDownloadURL(
        {
            "region": region,
            "scale": scale,
            "format": "GEO_TIFF",
            "crs": "EPSG:4326",
        }
    )
    return _download_ee_bytes(url)


def export_selected_image(
    available_images,
    selected_scene_id,
    selected_product_name,
    roi_geojson,
    base_filename,
    query_gdf=None,
    include_boundary_png: bool = True,
) -> Dict:
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
        query_gdf=query_gdf,
        include_boundary_png=include_boundary_png,
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
