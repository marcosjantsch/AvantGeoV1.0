# -*- coding: utf-8 -*-

import logging
import streamlit as st

from auth import setup_authentication, get_user_role
from core.settings import (
    APP_TITLE,
    APP_ICON,
    LAYOUT,
    SIDEBAR_STATE,
    LOGO_PATH,
    GEO_PATH,
    AUTH_ENABLED,
)
from core.styles import apply_styles
from core.ee_init import init_ee

from components.header import render_header
from components.sidebar import render_sidebar

from tabs.tab_mapa import render_tab_mapa
from tabs.tab_dados_satelite import render_tab_dados_satelite

from services.file_service import load_shapefile_full
from services.geometry_service import filter_gdf
from services.query_service import get_query_gdf_and_roi_geojson
from services.session_service import ensure_session_state
from services.gee_service import list_available_images
from services.export_service import export_selected_image
from services.log_service import add_log


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
        details={
            "user": user,
            "username": username,
            "role": role,
            "status": status,
        },
    )


def main():
    ensure_session_state()

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

    if gdf_full is None or gdf_full.empty:
        st.error("Erro ao carregar shapefile.")
        st.stop()

    available_images_sidebar = st.session_state.get("available_images", [])

    sidebar_data = render_sidebar(
        gdf_full=gdf_full,
        available_images=available_images_sidebar,
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

    export_output_dir = sidebar_data.get("export_output_dir", "")
    export_filename = sidebar_data.get("export_filename", "")
    export_requested = sidebar_data.get("export_requested", False)

    if selected_scene_id is not None:
        st.session_state["selected_scene_id"] = selected_scene_id

    if selected_product_name is not None:
        st.session_state["selected_product_name"] = selected_product_name

    if apply:
        try:
            query_gdf, roi_geojson = get_query_gdf_and_roi_geojson(
                gdf_full,
                modo_entrada,
                selected_empresa,
                selected_fazenda,
                parsed_coordinates,
                uploaded_kml,
                buffer_m,
            )

            st.session_state["aplicar"] = True
            st.session_state["modo_entrada"] = modo_entrada
            st.session_state["query_gdf"] = query_gdf
            st.session_state["roi_geojson"] = roi_geojson
            st.session_state["buffer_m"] = buffer_m
            st.session_state["cloud_pct"] = cloud_pct
            st.session_state["uploaded_kml_name"] = uploaded_kml.name if uploaded_kml else None

            filtro_aplicado = {
                "modo_entrada": modo_entrada,
                "selected_empresa": selected_empresa,
                "selected_fazenda": selected_fazenda,
                "start_date": start_date,
                "end_date": end_date,
                "selected_satellites": selected_satellites,
                "buffer_m": buffer_m,
                "cloud_pct": cloud_pct,
            }

            st.session_state["filtro_aplicado"] = filtro_aplicado

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
            else:
                st.session_state["selected_scene_id"] = None
                st.session_state["selected_product_name"] = None

        except Exception as e:
            st.error(f"Erro ao aplicar consulta: {e}")

    if export_requested:
        try:
            available_images_exp = st.session_state.get("available_images")
            selected_scene_id_exp = st.session_state.get("selected_scene_id")
            selected_product_name_exp = st.session_state.get("selected_product_name")
            roi_geojson_exp = st.session_state.get("roi_geojson")
    
            if not available_images_exp:
                raise ValueError("Sem imagens disponíveis")
            if not selected_scene_id_exp:
                raise ValueError("Nenhuma imagem selecionada")
            if not selected_product_name_exp:
                raise ValueError("Selecione o tipo de imagem")
            if not roi_geojson_exp:
                raise ValueError("ROI não definida")
            if not export_filename:
                raise ValueError("Nome do arquivo vazio")
    
            with st.spinner("Gerando arquivos para download..."):
                result = export_selected_image(
                    available_images=available_images_exp,
                    selected_scene_id=selected_scene_id_exp,
                    selected_product_name=selected_product_name_exp,
                    roi_geojson=roi_geojson_exp,
                    output_dir="/tmp",
                    base_filename=export_filename,
                )
    
            st.success("Exportação concluída.")
    
            png_path = result["png_path"]
            tif_path = result["tif_path"]
    
            with open(png_path, "rb") as f_png:
                st.download_button(
                    label="📥 Baixar PNG",
                    data=f_png.read(),
                    file_name=result["png_name"],
                    mime="image/png",
                )
    
            with open(tif_path, "rb") as f_tif:
                st.download_button(
                    label="📥 Baixar TIFF georreferenciado",
                    data=f_tif.read(),
                    file_name=result["tif_name"],
                    mime="image/tiff",
                )
    
        except Exception as e:
            st.error(f"Erro ao exportar: {e}")

    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "ℹ️ Info", "🛰️ Dados Satélite"])

    with tab1:
        if st.session_state.get("aplicar"):
            filtro_shape = st.session_state.get("filtro_aplicado", {})
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
        else:
            st.info("Aplique uma consulta para visualizar o mapa.")

    with tab2:
        st.subheader("Informações da consulta")
        st.write(st.session_state.get("filtro_aplicado", {}))
        st.write(
            {
                "selected_scene_id": st.session_state.get("selected_scene_id"),
                "selected_product_name": st.session_state.get("selected_product_name"),
                "export_output_dir": st.session_state.get("export_output_dir", ""),
                "export_filename": st.session_state.get("export_filename", ""),
            }
        )

    with tab3:
        render_tab_dados_satelite(logo_path=LOGO_PATH)


if __name__ == "__main__":
    main()
