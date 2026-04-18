# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

import ee
import streamlit as st

from services.gee_catalog import SATELLITE_COLLECTIONS, ee_geometry_from_geojson


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
