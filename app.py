# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

import streamlit as st

from auth import get_user_role, setup_authentication
from components.header import render_header
from components.sidebar import render_sidebar
from core.ee_init import init_ee
from core.settings import (
    APP_ICON,
    APP_TITLE,
    AUTH_ENABLED,
    GEO_PATH,
    LAYOUT,
    LOGO_PATH,
    SIDEBAR_STATE,
)
from core.styles import apply_styles
from services.coordinate_service import CAPTURE_MODE_LABEL
from services.export_service import export_selected_image
from services.file_service import load_shapefile_full
from services.gee_service import list_available_images
from services.geometry_service import filter_gdf
from services.log_service import add_log
from services.query_service import get_query_gdf_and_roi_geojson
from services.session_service import ensure_session_state
from tabs.tab_dados_satelite import render_tab_dados_satelite
from tabs.tab_mapa import render_tab_mapa


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)
apply_styles()


def log_auth_login(user: str, role: str, status: str, username: str = ""):
    add_log(
        level="INFO" if status == "SUCCESS" else "ERROR",
        source="auth_login_log",
        message="Login realizado" if status == "SUCCESS" else "Falha no login",
        details={"user": user, "username": username, "role": role, "status": status},
    )


def _reset_export_state():
    st.session_state["export_result"] = None
    st.session_state["last_export_error"] = None
    st.session_state["export_in_progress"] = False
    st.session_state["roi_ready_for_export"] = False


def _store_query_results(
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


def _infer_default_product_name(imgs):
    if not imgs:
        return None
    # fallback robusto para cloud/local
    return "RGB"


def _run_query(
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

    _store_query_results(
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
        )

    st.session_state["available_images"] = imgs

    if imgs:
        current_scene = st.session_state.get("selected_scene_id")
        if not current_scene or not any(img.get("id") == current_scene for img in imgs):
            st.session_state["selected_scene_id"] = imgs[0]["id"]

        # fallback para Cloud Run/Coldroot: garantir tipo de imagem persistido
        if not st.session_state.get("selected_product_name"):
            st.session_state["selected_product_name"] = _infer_default_product_name(imgs)
    else:
        st.session_state["selected_scene_id"] = None
        st.session_state["selected_product_name"] = None


def _ensure_roi_ready_for_export(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
):
    """
    Garante que query_gdf e roi_geojson existam antes da exportação.
    No modo Capturar Coordenada, a ROI gerada a partir do ponto capturado
    deve ser aceita normalmente como ROI válida para exportação.
    """
    roi_geojson = st.session_state.get("roi_geojson")
    query_gdf = st.session_state.get("query_gdf")

    if roi_geojson:
        st.session_state["roi_ready_for_export"] = True
        return query_gdf, roi_geojson

    if modo_entrada == CAPTURE_MODE_LABEL:
        parsed_coordinates = st.session_state.get("captured_coordinate")

    if modo_entrada == CAPTURE_MODE_LABEL and not parsed_coordinates:
        raise ValueError("Capture uma coordenada válida antes de exportar.")

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


def _handle_export(
    gdf_full,
    modo_entrada,
    selected_empresa,
    selected_fazenda,
    parsed_coordinates,
    uploaded_kml,
    buffer_m,
    export_filename: str,
):
    try:
        available_images_exp = st.session_state.get("available_images")
        selected_scene_id_exp = st.session_state.get("selected_scene_id")
        selected_product_name_exp = st.session_state.get("selected_product_name")

        _, roi_geojson_exp = _ensure_roi_ready_for_export(
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
                base_filename=export_filename,
            )

    except Exception as e:
        st.session_state["export_result"] = None
        st.session_state["last_export_error"] = f"Erro ao exportar: {e}"
        st.error(st.session_state["last_export_error"])

    finally:
        st.session_state["export_in_progress"] = False


def main():
    ensure_session_state()

    # blindagem extra de estados críticos
    st.session_state.setdefault("available_images", [])
    st.session_state.setdefault("selected_scene_id", None)
    st.session_state.setdefault("selected_product_name", None)
    st.session_state.setdefault("query_gdf", None)
    st.session_state.setdefault("roi_geojson", None)
    st.session_state.setdefault("roi_ready_for_export", False)
    st.session_state.setdefault("export_result", None)
    st.session_state.setdefault("export_in_progress", False)
    st.session_state.setdefault("last_export_error", None)

    name = "Usuário"
    username = None
    role = "Acesso local"
    authenticator = None

    if AUTH_ENABLED:
        authenticator, name, authentication_status, username = setup_authentication()

        if authentication_status is False:
            if not st.session_state.get("auth_login_logged_fail", False):
                log_auth_login(
                    user=username or "unknown",
                    username=username or "",
                    role="unknown",
                    status="FAIL",
                )
                st.session_state["auth_login_logged_fail"] = True
            st.error("❌ Usuário ou senha incorretos.")
            st.stop()

        if authentication_status is None:
            st.warning("⚠️ Informe suas credenciais.")
            st.stop()

        role = get_user_role()

        if not st.session_state.get("auth_login_logged_success", False):
            log_auth_login(
                user=name or "unknown",
                username=username or "",
                role=role or "unknown",
                status="SUCCESS",
            )
            st.session_state["auth_login_logged_success"] = True

    render_header(
        logo_path=LOGO_PATH,
        app_name="Avant GEO",
        version="V1.0",
        user=name,
        role=role,
        username=username,
        authenticator=authenticator,
        subtitle="Visualização de Fazendas e Imagens Earth Engine",
    )

    ok_ee, msg_ee = init_ee()
    if not ok_ee:
        st.error(msg_ee)
        st.stop()

    gdf_full = load_shapefile_full(GEO_PATH)
    st.session_state["_gdf_full_cache"] = gdf_full

    if gdf_full is None or gdf_full.empty:
        st.error("Erro ao carregar shapefile.")
        st.stop()

    sidebar_data = render_sidebar(
        gdf_full=gdf_full,
        available_images=st.session_state.get("available_images", []),
    )

    modo_entrada = sidebar_data.get("modo_entrada")
    selected_empresa = sidebar_data.get("selected_empresa")
    selected_fazenda = sidebar_data.get("selected_fazenda")
    selected_satellites = sidebar_data.get("selected_satellites", [])
    start_date = sidebar_data.get("start_date")
    end_date = sidebar_data.get("end_date")
    buffer_m = sidebar_data.get("buffer_m", 200)
    cloud_pct = sidebar_data.get("cloud_pct", 25)
    apply = sidebar_data.get("apply", False)
    parsed_coordinates = sidebar_data.get("parsed_coordinates")
    uploaded_kml = sidebar_data.get("uploaded_kml")
    selected_scene_id = sidebar_data.get("selected_scene_id")
    selected_product_name = sidebar_data.get("selected_product_name")
    export_filename = sidebar_data.get("export_filename", "").strip()
    export_requested = sidebar_data.get("export_requested", False)

    if modo_entrada == CAPTURE_MODE_LABEL:
        parsed_coordinates = st.session_state.get("captured_coordinate")

    if selected_scene_id is not None:
        st.session_state["selected_scene_id"] = selected_scene_id

    if selected_product_name is not None:
        st.session_state["selected_product_name"] = selected_product_name

    # fallback adicional para cenários cloud em que o produto some no rerun
    if not st.session_state.get("selected_product_name") and st.session_state.get("selected_scene_id"):
        imgs_mem = st.session_state.get("available_images", [])
        if imgs_mem:
            st.session_state["selected_product_name"] = _infer_default_product_name(imgs_mem)

    # -----------------------------
    # APLICAR CONSULTA
    # -----------------------------
    if apply:
        try:
            if modo_entrada == CAPTURE_MODE_LABEL:
                parsed_coordinates = st.session_state.get("captured_coordinate")

            # ao aplicar novamente, invalida export anterior
            _reset_export_state()

            _run_query(
                gdf_full=gdf_full,
                modo_entrada=modo_entrada,
                selected_empresa=selected_empresa,
                selected_fazenda=selected_fazenda,
                parsed_coordinates=parsed_coordinates,
                uploaded_kml=uploaded_kml,
                buffer_m=buffer_m,
                selected_satellites=selected_satellites,
                start_date=start_date,
                end_date=end_date,
                cloud_pct=cloud_pct,
            )

            # blindagem final: garantir persistência após a consulta
            st.session_state["roi_ready_for_export"] = bool(st.session_state.get("roi_geojson"))
            if not st.session_state.get("selected_product_name") and st.session_state.get("available_images"):
                st.session_state["selected_product_name"] = _infer_default_product_name(
                    st.session_state.get("available_images", [])
                )

            # IMPORTANTE:
            # não usar st.rerun() aqui; o clique do botão já reroda o script
            # e o rerun extra pode quebrar a persistência no Cloud Run

        except Exception as e:
            st.error(f"Erro ao aplicar consulta: {e}")

    # -----------------------------
    # EXPORTAR DOWNLOADS
    # -----------------------------
    if export_requested:
        _handle_export(
            gdf_full=gdf_full,
            modo_entrada=modo_entrada,
            selected_empresa=selected_empresa,
            selected_fazenda=selected_fazenda,
            parsed_coordinates=parsed_coordinates,
            uploaded_kml=uploaded_kml,
            buffer_m=buffer_m,
            export_filename=export_filename,
        )
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "ℹ️ Info", "🛰️ Dados Satélite"])

    with tab1:
        filtro_shape = st.session_state.get("filtro_aplicado", {}).copy()
        if not filtro_shape:
            filtro_shape = {
                "modo_entrada": modo_entrada,
                "selected_empresa": selected_empresa,
                "selected_fazenda": selected_fazenda,
                "start_date": start_date,
                "end_date": end_date,
                "selected_satellites": selected_satellites,
                "buffer_m": buffer_m,
                "cloud_pct": cloud_pct,
            }

        query_gdf = st.session_state.get("query_gdf")
        roi_geojson = st.session_state.get("roi_geojson")
        available_images = st.session_state.get("available_images", [])
        selected_scene_id = st.session_state.get("selected_scene_id")
        selected_product_name = st.session_state.get("selected_product_name")

        gdf_filtered = gdf_full.copy()
        if st.session_state.get("modo_entrada") == "Empresa / Fazenda":
            gdf_filtered = filter_gdf(
                gdf_full,
                filtro_shape.get("selected_empresa"),
                filtro_shape.get("selected_fazenda"),
            )

        render_tab_mapa(
            gdf_full=gdf_full,
            gdf_filtered=gdf_filtered,
            filtro=filtro_shape,
            query_gdf=query_gdf,
            roi_geojson=roi_geojson,
            available_images=available_images,
            selected_scene_id=selected_scene_id,
            selected_product_name=selected_product_name,
        )

    with tab2:
        st.subheader("Informações da consulta")
        st.write(st.session_state.get("filtro_aplicado", {}))
        st.write(
            {
                "selected_scene_id": st.session_state.get("selected_scene_id"),
                "selected_product_name": st.session_state.get("selected_product_name"),
                "export_filename": export_filename,
                "available_images_count": len(st.session_state.get("available_images", [])),
                "export_result": {
                    "png_name": (
                        st.session_state.get("export_result", {}).get("png_name")
                        if st.session_state.get("export_result")
                        else None
                    ),
                    "tif_name": (
                        st.session_state.get("export_result", {}).get("tif_name")
                        if st.session_state.get("export_result")
                        else None
                    ),
                },
                "captured_coordinate": st.session_state.get("captured_coordinate"),
                "roi_geojson_ok": bool(st.session_state.get("roi_geojson")),
                "roi_ready_for_export": st.session_state.get("roi_ready_for_export", False),
                "export_in_progress": st.session_state.get("export_in_progress", False),
                "last_export_error": st.session_state.get("last_export_error"),
            }
        )

    with tab3:
        render_tab_dados_satelite(logo_path=LOGO_PATH)


if __name__ == "__main__":
    main()
