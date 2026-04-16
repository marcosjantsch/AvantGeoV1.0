# -*- coding: utf-8 -*-
"""
app.py — Avant | Visualizador de Shapefile + Dados Climáticos
Versão V2.1
- Header SaaS
- Logo estável
- Autenticação opcional
- Mapa modularizado
- Geometria original preservada para exibição sem simplificação
- Tabs modularizadas
- Carregamento climático centralizado em services/climate_service.py
"""

import os
import logging
from typing import Optional

import geopandas as gpd
import streamlit as st

from core.styles import apply_styles
from core.stylesHEADER import apply_stylesHEADER
from core.settings import (
    APP_TITLE,
    APP_ICON,
    LAYOUT,
    SIDEBAR_STATE,
    GEO_PATH,
    LOGO_PATH,
    AUTH_ENABLED,
)
from components.header import render_header
from components.sidebar import render_sidebar

from tabs.tab_mapa import render_tab_mapa
from tabs.tab_shape import render_tab_shape
from tabs.tab_clima import render_tab_clima
from tabs.tab_analise import render_tab_analise
from tabs.tab_previsao import render_tab_previsao
from tabs.tab_tendencia_climatica import render_tab_tendencia_climatica
from services.auth_log_service import registrar_login
from services.climate_service import load_climate_data
from tabs.tab_imagens_tempo_real import render_tab_imagens_tempo_real

# =====================================================================
# LOGGING
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# =====================================================================
# CONFIG
# =====================================================================
SIMPLIFICATION_TOLERANCE = 0.001


# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

apply_styles()
apply_stylesHEADER()


# =====================================================================
# HELPERS
# =====================================================================
@st.cache_data(show_spinner=False)
def load_shapefile_full(file_path: str) -> Optional[gpd.GeoDataFrame]:
    logger.info("Carregando shapefile: %s", file_path)

    if not os.path.exists(file_path):
        logger.warning("Shapefile não encontrado: %s", file_path)
        return None

    try:
        gdf = gpd.read_file(file_path)

        if gdf.empty:
            logger.warning("Shapefile carregado, porém vazio.")
            return gdf

        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        if str(gdf.crs).upper() != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        gdf["__geometry_original__"] = gdf.geometry.copy()

        try:
            gdf["geometry"] = gdf.geometry.simplify(
                SIMPLIFICATION_TOLERANCE,
                preserve_topology=True,
            )
        except Exception as e:
            logger.warning("Falha na simplificação do shapefile: %s", e)

        return gdf

    except Exception as e:
        logger.error("Erro ao carregar shapefile: %s", e)
        return None


def filter_gdf(gdf: gpd.GeoDataFrame, filtro: dict) -> gpd.GeoDataFrame:
    gdf_filtered = gdf.copy()
    tipo = filtro["tipo_dado"]

    if (
        tipo == "Dados por Estado"
        and filtro["selected_uf"]
        and "UF" in gdf_filtered.columns
    ):
        gdf_filtered = gdf_filtered[
            gdf_filtered["UF"].astype(str) == str(filtro["selected_uf"])
        ]

    elif (
        tipo == "Dados por Empresa"
        and filtro["selected_empresa"]
        and "EMPRESA" in gdf_filtered.columns
    ):
        gdf_filtered = gdf_filtered[
            gdf_filtered["EMPRESA"].astype(str) == str(filtro["selected_empresa"])
        ]

    elif (
        tipo == "Dados Empresa/Fazenda"
        and filtro["selected_empresa"]
        and filtro["selected_fazenda"]
        and all(c in gdf_filtered.columns for c in ["EMPRESA", "FAZENDA"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["EMPRESA"].astype(str) == str(filtro["selected_empresa"]))
            & (gdf_filtered["FAZENDA"].astype(str) == str(filtro["selected_fazenda"]))
        ]

    elif (
        tipo == "Dados por Município"
        and filtro["selected_uf"]
        and filtro["selected_municipio"]
        and all(c in gdf_filtered.columns for c in ["UF", "MUNICIPIO"])
    ):
        gdf_filtered = gdf_filtered[
            (gdf_filtered["UF"].astype(str) == str(filtro["selected_uf"]))
            & (
                gdf_filtered["MUNICIPIO"].astype(str)
                == str(filtro["selected_municipio"])
            )
        ]

    return gdf_filtered


# =====================================================================
# AUTH
# =====================================================================
# AUTH
# =====================================================================
name = None
username = None
role = None
authentication_status = None
authenticator = None

auth_enabled = AUTH_ENABLED

if auth_enabled:
    try:
        from auth import setup_authentication, get_user_role

        authenticator, name, authentication_status, username = setup_authentication()

        if authentication_status is False:
            st.error("❌ Usuário/senha incorretos")
            st.stop()
        elif authentication_status is None:
            st.warning("⚠️ Informe suas credenciais")
            st.stop()

        try:
            role = get_user_role()
        except Exception:
            role = "Usuário"

    except Exception as e:
        logger.warning("Falha ao carregar autenticação: %s", e)
        auth_enabled = False
        name = "Usuário"
        role = "Sem autenticação"
else:
    name = "Usuário"
    role = "Acesso local"

# REGISTRO DE LOGIN
# =====================================================================
if authentication_status:
    if "login_registrado" not in st.session_state:
        st.session_state["login_registrado"] = False

    if not st.session_state["login_registrado"]:
        registrar_login(
            username=username,
            nome=name,
            perfil=role,
        )
        st.session_state["login_registrado"] = True


# =====================================================================
# HEADER
# =====================================================================
render_header(
    logo_path=LOGO_PATH,
    app_name="Avant - Clima",
    version="V2.1",
    user=name,
    role=role,
    username=username,
    authenticator=authenticator,
)
# =====================================================================
# DADOS BASE
# =====================================================================
gdf_full = load_shapefile_full(GEO_PATH)
if gdf_full is None:
    st.error(f"Não foi possível carregar o shapefile em: {GEO_PATH}")
    st.stop()


# =====================================================================
# SIDEBAR
# =====================================================================
sidebar_data = render_sidebar(gdf_full)

tipo_dado = sidebar_data["tipo_dado"]
selected_uf = sidebar_data["selected_uf"]
selected_empresa = sidebar_data["selected_empresa"]
selected_fazenda = sidebar_data["selected_fazenda"]
selected_municipio = sidebar_data["selected_municipio"]
start_date = sidebar_data["start_date"]
end_date = sidebar_data["end_date"]
apply = sidebar_data["apply"]
log_container = sidebar_data.get("log_container")

if apply:
    st.session_state.aplicar = True
    st.session_state["mostrar_tudo_shape"] = False
    st.session_state["mostrar_tudo_clima"] = False


# =====================================================================
# FILTRO SHAPE
# =====================================================================
filtro_shape = {
    "tipo_dado": tipo_dado,
    "selected_uf": selected_uf,
    "selected_empresa": selected_empresa,
    "selected_fazenda": selected_fazenda,
    "selected_municipio": selected_municipio,
}

gdf_filtered = gdf_full.copy()
if st.session_state.get("aplicar", False):
    gdf_filtered = filter_gdf(gdf_full, filtro_shape)


# =====================================================================
# LOAD CSV VIA SERVICE
# =====================================================================
df_csv = None

if st.session_state.get("aplicar", False):
    try:
        filtro_clima = {
            "tipo_dado": tipo_dado,
            "selected_uf": selected_uf,
            "selected_empresa": selected_empresa,
            "selected_fazenda": selected_fazenda,
            "selected_municipio": selected_municipio,
            "start_date": start_date,
            "end_date": end_date,
            "log_container": log_container,
        }

        with st.spinner("Carregando dados climáticos..."):
            df_csv = load_climate_data(filtro_clima)

    except Exception as e:
        logger.error("Erro no carregamento dos CSVs via climate_service: %s", e)
        if log_container:
            log_container.error(f"❌ Erro geral no carregamento: {e}")
        else:
            st.error(f"❌ Erro geral no carregamento: {e}")
        df_csv = None


# =====================================================================
# TABS
# =====================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, = st.tabs(
    [
        "🗺️ Mapa Principal",
        "📋 Dados Shape",
        "📈 Dados de Clima",
        "📉 Análise Avançada",
        "Previsão do Tempo (Teste)",
        "Tendência Climática (Teste)",
        "Imagens Atuais (Teste)",
    ]
)

with tab1:
    render_tab_mapa(gdf_full, gdf_filtered, filtro_shape)

with tab2:
    render_tab_shape(gdf_filtered)

with tab3:
    render_tab_clima(df_csv)

with tab4:
    render_tab_analise(
        df_csv,
        tipo_dado=tipo_dado,
        selected_uf=selected_uf,
        selected_municipio=selected_municipio,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        start_date=start_date,
        end_date=end_date,
    )

with tab5:
    render_tab_previsao(
        gdf_filtered=gdf_filtered,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_municipio=selected_municipio,
        selected_uf=selected_uf,
        logo_path=LOGO_PATH,
    )

with tab6:
    render_tab_tendencia_climatica(
        gdf_filtered=gdf_filtered,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_municipio=selected_municipio,
        selected_uf=selected_uf,
        logo_path=LOGO_PATH,
    )

with tab7:
    render_tab_imagens_tempo_real(
        gdf_filtrado=gdf_filtered,
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_uf=selected_uf,
        selected_municipio=selected_municipio,
    )