# -*- coding: utf-8 -*-
from pathlib import Path
import tempfile
import zipfile

import geopandas as gpd
import fiona


def _enable_kml_drivers():
    try:
        fiona.drvsupport.supported_drivers["KML"] = "rw"
    except Exception:
        pass

    try:
        fiona.drvsupport.supported_drivers["LIBKML"] = "rw"
    except Exception:
        pass


def load_shapefile_full(file_path: str):
    path = Path(file_path)

    if not path.exists():
        return None

    gdf = gpd.read_file(path)

    if gdf.empty:
        return gdf

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    if str(gdf.crs).upper() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    return gdf


def read_kml_or_kmz_to_gdf(uploaded_file):
    if uploaded_file is None:
        return None

    _enable_kml_drivers()
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        tmpdir = Path(tmpdir)

        if suffix == ".kml":
            kml_path = tmpdir / "input.kml"
            kml_path.write_bytes(uploaded_file.getvalue())

        elif suffix == ".kmz":
            kmz_path = tmpdir / "input.kmz"
            kmz_path.write_bytes(uploaded_file.getvalue())

            with zipfile.ZipFile(kmz_path, "r") as zf:
                kml_names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
                if not kml_names:
                    raise ValueError("O arquivo KMZ não contém KML interno.")

                kml_data = zf.read(kml_names[0])
                kml_path = tmpdir / "doc.kml"
                kml_path.write_bytes(kml_data)
        else:
            raise ValueError("Formato inválido. Envie KML ou KMZ.")

        try:
            gdf = gpd.read_file(kml_path, driver="KML")
        except Exception:
            gdf = gpd.read_file(kml_path)

        if gdf is None or gdf.empty:
            raise ValueError("Não foi possível ler a geometria do arquivo enviado.")

        gdf = gdf[gdf.geometry.notna()].copy()
        gdf = gdf[~gdf.geometry.is_empty].copy()

        if gdf.empty:
            raise ValueError("O arquivo enviado não possui geometrias válidas.")

        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        if str(gdf.crs).upper() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        return gdf
