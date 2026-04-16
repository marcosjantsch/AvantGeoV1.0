# -*- coding: utf-8 -*-
from datetime import date
import streamlit as st


def safe_unique(gdf, col):
    if gdf is None or col not in gdf.columns:
        return []
    return sorted([str(x) for x in gdf[col].dropna().unique()])


def _to_float(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return None


def dms_to_decimal(graus, minutos, segundos, hemisferio=None):
    g = _to_float(graus)
    m = _to_float(minutos)
    s = _to_float(segundos)

    if g is None or m is None or s is None:
        return None

    if m < 0 or m >= 60 or s < 0 or s >= 60:
        return None

    decimal = abs(g) + (m / 60.0) + (s / 3600.0)

    if hemisferio:
        hemisferio = str(hemisferio).strip().upper()
        if hemisferio in ["S", "W", "O"]:
            decimal *= -1

    if g < 0:
        decimal *= -1

    return decimal


def parse_coordinate_payload(coord_system, values):
    def _fail(msg):
        raise ValueError(msg)

    if coord_system == "Graus, minutos e segundos (DMS)":
        lat = dms_to_decimal(
            values.get("lat_graus"),
            values.get("lat_minutos"),
            values.get("lat_segundos"),
            values.get("lat_hemisferio"),
        )
        lon = dms_to_decimal(
            values.get("lon_graus"),
            values.get("lon_minutos"),
            values.get("lon_segundos"),
            values.get("lon_hemisferio"),
        )

        if lat is None or lon is None:
            _fail("Preencha corretamente os campos DMS.")

        if not (-90 <= lat <= 90):
            _fail("Latitude DMS fora do intervalo válido (-90 a 90).")

        if not (-180 <= lon <= 180):
            _fail("Longitude DMS fora do intervalo válido (-180 a 180).")

        return {
            "coord_system": coord_system,
            "latitude": lat,
            "longitude": lon,
            "utm_easting": None,
            "utm_northing": None,
            "utm_zone": None,
            "utm_hemisphere": None,
        }

    if coord_system == "Graus decimais (DD)":
        lat = _to_float(values.get("latitude_dd"))
        lon = _to_float(values.get("longitude_dd"))

        if lat is None or lon is None:
            _fail("Latitude/Longitude inválidas.")

        if not (-90 <= lat <= 90):
            _fail("Latitude fora do intervalo válido (-90 a 90).")

        if not (-180 <= lon <= 180):
            _fail("Longitude fora do intervalo válido (-180 a 180).")

        return {
            "coord_system": coord_system,
            "latitude": lat,
            "longitude": lon,
            "utm_easting": None,
            "utm_northing": None,
            "utm_zone": None,
            "utm_hemisphere": None,
        }

    if coord_system == "UTM":
        easting = _to_float(values.get("utm_easting"))
        northing = _to_float(values.get("utm_northing"))
        zone = values.get("utm_zone")
        hemisphere = values.get("utm_hemisphere")

        if None in [easting, northing] or not zone or not hemisphere:
            _fail("Coordenadas UTM inválidas.")

        try:
            zone_int = int(str(zone).strip())
        except Exception:
            _fail("Fuso UTM inválido.")

        if not (1 <= zone_int <= 60):
            _fail("Fuso UTM deve estar entre 1 e 60.")

        hemisphere = str(hemisphere).strip().upper()
        if hemisphere not in ["S", "N"]:
            _fail("Hemisfério UTM inválido. Use S ou N.")

        return {
            "coord_system": coord_system,
            "latitude": None,
            "longitude": None,
            "utm_easting": easting,
            "utm_northing": northing,
            "utm_zone": str(zone_int),
            "utm_hemisphere": hemisphere,
        }

    _fail("Sistema de coordenadas inválido.")


def render_sidebar_entrada(gdf_full):
    st.markdown(
        """
        <style>
        div[data-testid="stRadio"] > label,
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stTextInput"] > label,
        div[data-testid="stDateInput"] > label,
        div[data-testid="stFileUploader"] > label,
        div[data-testid="stMultiSelect"] > label,
        div[data-testid="stSlider"] > label {
            font-size: 0.88rem !important;
            margin-bottom: 0.10rem !important;
        }

        div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.20rem !important;
        }

        div[data-testid="stVerticalBlock"] > div {
            gap: 0.28rem !important;
        }

        div[data-testid="stFileUploader"] section {
            padding-top: 0.35rem !important;
            padding-bottom: 0.35rem !important;
        }

        button[kind="secondary"], button[kind="primary"] {
            padding-top: 0.35rem !important;
            padding-bottom: 0.35rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    modo_entrada = None
    selected_empresa = None
    selected_fazenda = None
    coord_system = None
    coord_payload = {}
    parsed_coordinates = None
    uploaded_kml = None

    apply = False
    apply_filters = False
    apply_coordinates = False
    apply_kml = False

    hoje = date.today()
    data_inicial_padrao = date(2026, 1, 1)

    default_sat = st.session_state.get("sb_selected_satellites_mem", ["Sentinel-2"])
    default_start = st.session_state.get("sb_start_date_mem", data_inicial_padrao)
    default_end = st.session_state.get("sb_end_date_mem", hoje)
    default_buffer_m = st.session_state.get("sb_buffer_m_mem", 200)
    default_cloud_pct = st.session_state.get("sb_cloud_pct_mem", 25)

    modo_entrada = st.radio(
        "Modo de consulta",
        [
            "Empresa / Fazenda",
            "Coordenada",
            "Arquivo KML/KMZ",
        ],
        key="sb_modo_entrada",
    )

    if modo_entrada == "Empresa / Fazenda":
        empresas = safe_unique(gdf_full, "EMPRESA")
        selected_empresa = (
            st.selectbox(
                "Empresa",
                options=empresas,
                index=0 if empresas else None,
                key="sb_selected_empresa",
            )
            if empresas
            else None
        )

        if (
            selected_empresa
            and gdf_full is not None
            and "EMPRESA" in gdf_full.columns
            and "FAZENDA" in gdf_full.columns
        ):
            gdf_emp = gdf_full[gdf_full["EMPRESA"].astype(str) == str(selected_empresa)]
            fazendas = safe_unique(gdf_emp, "FAZENDA")
            selected_fazenda = (
                st.selectbox(
                    "Fazenda",
                    options=fazendas,
                    index=0 if fazendas else None,
                    key="sb_selected_fazenda",
                )
                if fazendas
                else None
            )

    elif modo_entrada == "Coordenada":
        coord_system = st.selectbox(
            "Formato das coordenadas",
            options=[
                "Graus, minutos e segundos (DMS)",
                "Graus decimais (DD)",
                "UTM",
            ],
            index=0,
            key="sb_coord_system",
        )

        if coord_system == "Graus, minutos e segundos (DMS)":
            st.caption("Latitude")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1], gap="small")
            coord_payload["lat_graus"] = c1.text_input("Graus", key="lat_graus")
            coord_payload["lat_minutos"] = c2.text_input("Min", key="lat_minutos")
            coord_payload["lat_segundos"] = c3.text_input("Seg", key="lat_segundos")
            coord_payload["lat_hemisferio"] = c4.selectbox("Hem", ["S", "N"], key="lat_hemisferio")

            st.caption("Longitude")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1], gap="small")
            coord_payload["lon_graus"] = c1.text_input("Graus ", key="lon_graus")
            coord_payload["lon_minutos"] = c2.text_input("Min ", key="lon_minutos")
            coord_payload["lon_segundos"] = c3.text_input("Seg ", key="lon_segundos")
            coord_payload["lon_hemisferio"] = c4.selectbox("Hem ", ["W", "E"], key="lon_hemisferio")

        elif coord_system == "Graus decimais (DD)":
            c1, c2 = st.columns(2, gap="small")
            coord_payload["latitude_dd"] = c1.text_input(
                "Latitude",
                placeholder="-26.123456",
                key="latitude_dd",
            )
            coord_payload["longitude_dd"] = c2.text_input(
                "Longitude",
                placeholder="-49.123456",
                key="longitude_dd",
            )

        elif coord_system == "UTM":
            c1, c2 = st.columns(2, gap="small")
            coord_payload["utm_easting"] = c1.text_input(
                "Easting",
                placeholder="500000",
                key="utm_easting",
            )
            coord_payload["utm_northing"] = c2.text_input(
                "Northing",
                placeholder="7000000",
                key="utm_northing",
            )

            c3, c4 = st.columns(2, gap="small")
            coord_payload["utm_zone"] = c3.text_input(
                "Fuso",
                placeholder="22",
                key="utm_zone",
            )
            coord_payload["utm_hemisphere"] = c4.selectbox(
                "Hem",
                ["S", "N"],
                key="utm_hemisphere",
            )

        try:
            parsed_coordinates = parse_coordinate_payload(coord_system, coord_payload)
        except Exception as e:
            parsed_coordinates = None
            if any(str(v).strip() != "" for v in coord_payload.values() if v is not None):
                st.error(str(e))

    elif modo_entrada == "Arquivo KML/KMZ":
        uploaded_kml = st.file_uploader(
            "Arquivo KML ou KMZ",
            type=["kml", "kmz"],
            accept_multiple_files=False,
            key="sb_uploaded_kml",
        )

    st.caption("Parâmetros de imagem")

    selected_satellites = st.multiselect(
        "Satélites",
        options=[
            "Sentinel-2",
            "Landsat 5",
            "Landsat 7",
            "Landsat 8",
            "Landsat 9",
        ],
        default=default_sat,
        key="sb_selected_satellites",
    )

    start_date = st.date_input(
        "Data inicial",
        value=default_start,
        format="DD/MM/YYYY",
        key="sb_start_date",
    )

    end_date = st.date_input(
        "Data final",
        value=default_end,
        format="DD/MM/YYYY",
        key="sb_end_date",
    )

    buffer_m = st.slider(
        "Buffer (m)",
        min_value=0,
        max_value=5000,
        value=int(default_buffer_m),
        step=50,
        key="sb_buffer_m",
    )

    cloud_pct = st.slider(
        "Nuvens (%)",
        min_value=0,
        max_value=100,
        value=int(default_cloud_pct),
        step=5,
        key="sb_cloud_pct",
    )

    if start_date > end_date:
        st.error("A data inicial não pode ser maior que a data final.")

    st.session_state["sb_selected_satellites_mem"] = selected_satellites
    st.session_state["sb_start_date_mem"] = start_date
    st.session_state["sb_end_date_mem"] = end_date
    st.session_state["sb_buffer_m_mem"] = buffer_m
    st.session_state["sb_cloud_pct_mem"] = cloud_pct

    if modo_entrada == "Empresa / Fazenda":
        apply_filters = st.button(
            "Aplicar consulta",
            use_container_width=True,
            key="sb_apply_filters",
        )
        apply = apply_filters

    elif modo_entrada == "Coordenada":
        apply_coordinates = st.button(
            "Aplicar consulta",
            use_container_width=True,
            key="sb_apply_coordinates",
        )
        apply = apply_coordinates

    elif modo_entrada == "Arquivo KML/KMZ":
        apply_kml = st.button(
            "Aplicar consulta",
            use_container_width=True,
            key="sb_apply_kml",
        )
        apply = apply_kml

    return {
        "modo_entrada": modo_entrada,
        "selected_empresa": selected_empresa,
        "selected_fazenda": selected_fazenda,
        "selected_satellites": selected_satellites,
        "start_date": start_date,
        "end_date": end_date,
        "buffer_m": buffer_m,
        "cloud_pct": cloud_pct,
        "apply": apply,
        "apply_filters": apply_filters,
        "coord_system": coord_system,
        "coordinate_values": coord_payload,
        "parsed_coordinates": parsed_coordinates,
        "apply_coordinates": apply_coordinates,
        "uploaded_kml": uploaded_kml,
        "apply_kml": apply_kml,
    }
