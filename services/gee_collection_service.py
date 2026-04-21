# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

import ee
import streamlit as st

from services.gee_catalog import (
    SATELLITE_COLLECTIONS,
    SENTINEL2_SR_COLLECTION,
    SENTINEL2_TOA_COLLECTION,
    ee_geometry_from_geojson,
)


SENTINEL2_TOA_START = "2015-06-27"
SENTINEL2_SR_START = "2017-03-28"


def _parse_date(date_value: str):
    return datetime.strptime(str(date_value), "%Y-%m-%d").date()


def _to_iso(date_value):
    return date_value.strftime("%Y-%m-%d")


def _inclusive_end_to_exclusive(end_date: str) -> str:
    return _to_iso(_parse_date(end_date) + timedelta(days=1))


def _date_range_span_days(start_date: str, end_date: str) -> int:
    return max((_parse_date(end_date) - _parse_date(start_date)).days + 1, 1)


def _tag_collection(
    collection: ee.ImageCollection,
    collection_id: str,
    display_source: str = None,
):
    payload = {"collection_id_override": collection_id}
    if display_source:
        payload["display_source"] = display_source
    return collection.map(lambda image: ee.Image(image).set(payload))


def _add_year_month_bucket(collection: ee.ImageCollection) -> ee.ImageCollection:
    return collection.map(
        lambda image: ee.Image(image).set(
            {"year_month": ee.Date(image.get("system:time_start")).format("YYYY-MM")}
        )
    )


def _apply_cloud_filter(
    collection: ee.ImageCollection,
    satellite: str,
    cloud_pct: float,
):
    if satellite == "Sentinel-2":
        return collection.filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        return collection.filter(ee.Filter.lte("CLOUD_COVERAGE", cloud_pct))
    if satellite in ["Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]:
        return collection
    return collection.filter(ee.Filter.lte("CLOUD_COVER", cloud_pct))


def _build_sentinel_collection(
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    start_dt = _parse_date(start_date)
    end_exclusive_dt = _parse_date(_inclusive_end_to_exclusive(end_date))
    sr_start_dt = _parse_date(SENTINEL2_SR_START)

    collections = []

    if start_dt < sr_start_dt:
        toa_end_dt = min(end_exclusive_dt, sr_start_dt)
        if start_dt < toa_end_dt:
            toa_collection = (
                ee.ImageCollection(SENTINEL2_TOA_COLLECTION)
                .filterBounds(geom)
                .filterDate(_to_iso(start_dt), _to_iso(toa_end_dt))
            )
            toa_collection = _apply_cloud_filter(toa_collection, "Sentinel-2", cloud_pct)
            collections.append(_tag_collection(toa_collection, SENTINEL2_TOA_COLLECTION, "Sentinel-2 TOA"))

    sr_start_window = max(start_dt, sr_start_dt)
    if sr_start_window < end_exclusive_dt:
        sr_collection = (
            ee.ImageCollection(SENTINEL2_SR_COLLECTION)
            .filterBounds(geom)
            .filterDate(_to_iso(sr_start_window), _to_iso(end_exclusive_dt))
        )
        sr_collection = _apply_cloud_filter(sr_collection, "Sentinel-2", cloud_pct)
        collections.append(_tag_collection(sr_collection, SENTINEL2_SR_COLLECTION, "Sentinel-2 SR"))

    if not collections:
        return (
            ee.ImageCollection(SENTINEL2_SR_COLLECTION)
            .filterBounds(geom)
            .filterDate("1900-01-01", "1900-01-02")
        )

    merged = collections[0]
    for extra_collection in collections[1:]:
        merged = merged.merge(extra_collection)
    return merged


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
        .filterDate(start_date, _inclusive_end_to_exclusive(end_date))
    )

    sat_name = [k for k, v in SATELLITE_COLLECTIONS.items() if v == collection_id][0]
    return _apply_cloud_filter(col, sat_name, cloud_pct)


def _build_sentinel1_collection(
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
):
    return (
        ee.ImageCollection(SATELLITE_COLLECTIONS["Sentinel-1 (10 m radar)"])
        .filterBounds(geom)
        .filterDate(start_date, _inclusive_end_to_exclusive(end_date))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )


def _prepare_hls_collection(
    collection_id: str,
    source_name: str,
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    return (
        ee.ImageCollection(collection_id)
        .filterBounds(geom)
        .filterDate(start_date, _inclusive_end_to_exclusive(end_date))
        .filter(ee.Filter.lte("CLOUD_COVERAGE", cloud_pct))
        .map(
            lambda image: ee.Image(image).set(
                {
                    "display_source": source_name,
                    "collection_id_override": collection_id,
                }
            )
        )
    )


def _build_hls_collection(
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    landsat = _prepare_hls_collection(
        SATELLITE_COLLECTIONS["HLS Landsat"],
        "HLSL30",
        geom,
        start_date,
        end_date,
        cloud_pct,
    )
    sentinel = _prepare_hls_collection(
        SATELLITE_COLLECTIONS["HLS Sentinel"],
        "HLSS30",
        geom,
        start_date,
        end_date,
        cloud_pct,
    )
    return landsat.merge(sentinel)


def _collection_for_satellite(
    satellite: str,
    geom: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_pct: float,
):
    if satellite == "Sentinel-2":
        return _build_sentinel_collection(geom, start_date, end_date, cloud_pct)
    if satellite in ["Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]:
        return _build_sentinel1_collection(geom, start_date, end_date)
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        return _build_hls_collection(geom, start_date, end_date, cloud_pct)
    if satellite in ["NASADEM", "SRTM"]:
        return None
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
    collection_id = ee.String(
        ee.Algorithms.If(
            ee.Algorithms.IsEqual(img.get("collection_id_override"), None),
            SATELLITE_COLLECTIONS.get(satellite, ""),
            img.get("collection_id_override"),
        )
    )
    image_asset_id = ee.String(
        ee.Algorithms.If(
            ee.Algorithms.IsEqual(img.get("system:id"), None),
            collection_id.cat("/").cat(system_index),
            img.get("system:id"),
        )
    )

    cloud_prop = ee.Algorithms.If(
        ee.Algorithms.IsEqual(img.get("CLOUDY_PIXEL_PERCENTAGE"), None),
        ee.Algorithms.If(
            ee.Algorithms.IsEqual(img.get("CLOUD_COVER"), None),
            img.get("CLOUD_COVERAGE"),
            img.get("CLOUD_COVER"),
        ),
        img.get("CLOUDY_PIXEL_PERCENTAGE"),
    )

    return ee.Feature(
        None,
        {
            "id": image_asset_id,
            "system_index": system_index,
            "collection_id": collection_id,
            "asset_id": image_asset_id,
            "date": date_str,
            "satellite": satellite,
            "cloud": cloud_prop,
            "source": img.get("display_source"),
        },
    )


def _build_static_dem_row(satellite: str) -> Dict:
    asset_id = SATELLITE_COLLECTIONS[satellite]
    return {
        "id": asset_id,
        "asset_id": asset_id,
        "collection_id": asset_id,
        "label": f"{satellite} | modelo digital de elevação | 30 m",
        "satellite": satellite,
        "date": "2000-02",
        "cloud": None,
        "source": "DEM",
    }


def _build_static_hydro_row(satellite: str, label_suffix: str) -> Dict:
    asset_id = SATELLITE_COLLECTIONS[satellite]
    return {
        "id": asset_id,
        "asset_id": asset_id,
        "collection_id": asset_id,
        "label": f"{satellite} | {label_suffix}",
        "satellite": satellite,
        "date": "estatico",
        "cloud": None,
        "source": "HYDRO",
    }


def _expand_sentinel1_sar_rows(base_row: Dict) -> List[Dict]:
    products = ["Radar VV/VH", "VV (dB)", "VH (dB)"]
    rows = []
    for product_name in products:
        expanded = dict(base_row)
        expanded["id"] = f"{base_row['id']}|{product_name}"
        expanded["label"] = (
            f"{base_row['satellite']} | {base_row.get('date')} | {product_name}"
        )
        expanded["fixed_product_name"] = product_name
        rows.append(expanded)
    return rows


@st.cache_data(show_spinner=False)
def list_available_images(
    roi_geojson: dict,
    satellites: List[str],
    start_date: str,
    end_date: str,
    cloud_pct: float = 25,
    max_per_satellite: int = 180,
    cache_version: str = "asset_ids_v2",
) -> List[Dict]:
    geom = ee_geometry_from_geojson(roi_geojson)
    rows: List[Dict] = []
    span_days = _date_range_span_days(start_date, end_date)

    for sat in satellites:
        if sat in ["NASADEM", "SRTM"]:
            rows.append(_build_static_dem_row(sat))
            continue
        if sat == "HydroSHEDS":
            rows.append(_build_static_hydro_row("HydroSHEDS", "void-filled DEM"))
            continue
        if sat == "MERIT Hydro":
            rows.append(_build_static_hydro_row("MERIT Hydro", "hidrografia global"))
            continue

        collection = _collection_for_satellite(
            sat,
            geom,
            start_date,
            end_date,
            cloud_pct,
        )
        if collection is None:
            continue

        collection = collection.sort("system:time_start", False)
        if span_days > 180:
            collection = _add_year_month_bucket(collection).distinct(["year_month"]).sort("system:time_start", False)

        fc = ee.FeatureCollection(
            collection.limit(max_per_satellite)
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
            source = props.get("source")

            cloud_txt = "-" if cloud is None else f"{float(cloud):.1f}%"
            label = f"{sat} | {date_str} | nuvens: {cloud_txt}"
            if source:
                label = f"{sat} | {source} | {date_str} | nuvens: {cloud_txt}"

            row = {
                "id": image_id,
                "asset_id": asset_id,
                "collection_id": collection_id,
                "label": label,
                "satellite": sat,
                "date": date_str,
                "cloud": cloud,
                "source": source,
            }
            if sat == "Sentinel-1 SAR GRD (C-band)":
                rows.extend(_expand_sentinel1_sar_rows(row))
            else:
                rows.append(row)

    rows.sort(
        key=lambda x: (str(x.get("date", "")), str(x.get("satellite", ""))),
        reverse=True,
    )
    return rows
