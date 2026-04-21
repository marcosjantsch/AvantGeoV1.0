# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from app_core.runtime import get_gdf_full_lazy
from services.export_service import export_selected_image
from services.gee_service import list_available_images
from services.query_service import get_query_gdf_and_roi_geojson


def infer_default_product_name(imgs):
    if not imgs:
        return None
    satellite = imgs[0].get("satellite")
    if satellite == "Sentinel-2":
        return "Imagem Sentinel RGB Ajustada"
    if satellite == "HLS (Harmonized Landsat Sentinel)":
        return "HLS RGB"
    if satellite in ["NASADEM", "SRTM"]:
        return "Hillshade"
    if satellite == "HydroSHEDS":
        return "Hillshade + curvas 5 m"
    if satellite == "MERIT Hydro":
        return "Largura de Rio"
    if satellite in ["Sentinel-1 (10 m radar)", "Sentinel-1 SAR GRD (C-band)"]:
        return "Radar VV/VH"
    return None


def store_query_results(
    modo_entrada,
    query_gdf,
    roi_geojson,
    selected_empresa,
    selected_fazenda,
    selected_satellites,
    start_date,
    end_date,
    buffer_m,
    cloud_pct,
    uploaded_kml,
):
    st.session_state["aplicar"] = True
    st.session_state["modo_entrada"] = modo_entrada
    st.session_state["query_gdf"] = query_gdf
    st.session_state["roi_geojson"] = roi_geojson
    st.session_state["buffer_m"] = buffer_m
    st.session_state["cloud_pct"] = cloud_pct
    st.session_state["uploaded_kml_name"] = uploaded_kml.name if uploaded_kml else None
    st.session_state["roi_ready_for_export"] = bool(roi_geojson)
    st.session_state["query_result_nonce"] = int(st.session_state.get("query_result_nonce", 0)) + 1
    st.session_state["selected_scene_id"] = None
    st.session_state["selected_product_name"] = None

    st.session_state["filtro_aplicado"] = {
        "modo_entrada": modo_entrada,
        "selected_empresa": selected_empresa,
        "selected_fazenda": selected_fazenda,
        "start_date": start_date,
        "end_date": end_date,
        "selected_satellites": selected_satellites,
        "buffer_m": buffer_m,
        "cloud_pct": cloud_pct,
    }


def run_query(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
    selected_satellites,
    start_date,
    end_date,
    cloud_pct,
):
    query_gdf, roi_geojson = get_query_gdf_and_roi_geojson(
        gdf_full,
        modo_entrada,
        selected_empresa,
        selected_fazenda,
        parsed_coordinates,
        uploaded_kml,
        buffer_m,
    )

    if query_gdf is None or getattr(query_gdf, "empty", True):
        raise ValueError("Não foi possível gerar a geometria da consulta.")

    if not roi_geojson:
        raise ValueError("Não foi possível gerar a ROI da consulta.")

    store_query_results(
        modo_entrada=modo_entrada,
        query_gdf=query_gdf,
        roi_geojson=roi_geojson,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_satellites=selected_satellites,
        start_date=start_date,
        end_date=end_date,
        buffer_m=buffer_m,
        cloud_pct=cloud_pct,
        uploaded_kml=uploaded_kml,
    )

    with st.spinner("Consultando imagens..."):
        imgs = list_available_images(
            roi_geojson,
            selected_satellites,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            cloud_pct,
            cache_version="asset_ids_v4_20260421",
        )

    st.session_state["available_images"] = imgs

    if imgs:
        current_scene = st.session_state.get("selected_scene_id")
        if not current_scene or not any(
            img.get("id") == current_scene or img.get("asset_id") == current_scene for img in imgs
        ):
            st.session_state["selected_scene_id"] = imgs[0]["id"]

        if not st.session_state.get("selected_product_name"):
            st.session_state["selected_product_name"] = infer_default_product_name(imgs)
    else:
        st.session_state["selected_scene_id"] = None
        st.session_state["selected_product_name"] = None


def ensure_roi_ready_for_export(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
):
    roi_geojson = st.session_state.get("roi_geojson")
    query_gdf = st.session_state.get("query_gdf")

    if roi_geojson:
        st.session_state["roi_ready_for_export"] = True
        return query_gdf, roi_geojson

    if modo_entrada == "Coordenada":
        parsed_coordinates = st.session_state.get("captured_coordinate")

    if modo_entrada == "Coordenada" and not parsed_coordinates:
        raise ValueError("Informe uma coordenada válida antes de exportar.")

    if gdf_full is None:
        gdf_full = get_gdf_full_lazy()

    if gdf_full is None or getattr(gdf_full, "empty", True):
        raise ValueError("Erro ao carregar shapefile para exportação.")

    query_gdf, roi_geojson = get_query_gdf_and_roi_geojson(
        gdf_full,
        modo_entrada,
        selected_empresa,
        selected_fazenda,
        parsed_coordinates,
        uploaded_kml,
        buffer_m,
    )

    if query_gdf is None or getattr(query_gdf, "empty", True):
        raise ValueError("Não foi possível gerar a geometria da consulta para exportação.")

    if not roi_geojson:
        raise ValueError("Não foi possível gerar a ROI para exportação.")

    st.session_state["query_gdf"] = query_gdf
    st.session_state["roi_geojson"] = roi_geojson
    st.session_state["roi_ready_for_export"] = True

    return query_gdf, roi_geojson


def handle_export(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
    export_filename: str,
    include_boundary_png: bool = True,
):
    try:
        available_images_exp = st.session_state.get("available_images")
        selected_scene_id_exp = st.session_state.get("selected_scene_id")
        selected_product_name_exp = st.session_state.get("selected_product_name")

        query_gdf_exp, roi_geojson_exp = ensure_roi_ready_for_export(
            gdf_full=gdf_full,
            modo_entrada=modo_entrada,
            selected_empresa=selected_empresa,
            selected_fazenda=selected_fazenda,
            parsed_coordinates=parsed_coordinates,
            uploaded_kml=uploaded_kml,
            buffer_m=buffer_m,
        )

        if not available_images_exp:
            raise ValueError("Sem imagens disponíveis.")
        if not selected_scene_id_exp:
            raise ValueError("Nenhuma imagem selecionada.")
        if not selected_product_name_exp:
            raise ValueError("Selecione o tipo de imagem.")
        if not roi_geojson_exp:
            raise ValueError("ROI não definida.")
        if not export_filename:
            export_filename = "exportacao_imagem"

        st.session_state["export_in_progress"] = True
        st.session_state["export_result"] = None
        st.session_state["last_export_error"] = None

        with st.spinner("Gerando arquivos em memória para download..."):
            st.session_state["export_result"] = export_selected_image(
                available_images=available_images_exp,
                selected_scene_id=selected_scene_id_exp,
                selected_product_name=selected_product_name_exp,
                roi_geojson=roi_geojson_exp,
                query_gdf=query_gdf_exp,
                include_boundary_png=include_boundary_png,
                base_filename=export_filename,
            )

    except Exception as e:
        st.session_state["export_result"] = None
        st.session_state["last_export_error"] = f"Erro ao exportar: {e}"
        st.error(st.session_state["last_export_error"])

    finally:
        st.session_state["export_in_progress"] = False
