# components/sidebar.py
from datetime import date
import streamlit as st
from core.settings import TIPOS_DADO, ANOS_DISPONIVEIS, MESES_DISPONIVEIS

def safe_unique(gdf, col):
    if col not in gdf.columns:
        return []
    return sorted([str(x) for x in gdf[col].dropna().unique()])

def render_sidebar(gdf_full):
    st.sidebar.markdown(
    '<div style="font-size:16px; font-weight:600; margin-bottom:-6px;">Selecione a opção</div>',
    unsafe_allow_html=True
    )
    
 

    
    st.sidebar.markdown("---")

    tipo_dado = st.sidebar.selectbox("Tipo de Dados", TIPOS_DADO)

    selected_uf = None
    selected_empresa = None
    selected_fazenda = None
    selected_municipio = None

    if tipo_dado == "Dados por Estado":
        ufs = safe_unique(gdf_full, "UF")
        selected_uf = st.sidebar.selectbox("Selecione UF", ufs) if ufs else None

    elif tipo_dado == "Dados por Empresa":
        empresas = safe_unique(gdf_full, "EMPRESA")
        selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresas) if empresas else None

    elif tipo_dado == "Dados Empresa/Fazenda":
        empresas = safe_unique(gdf_full, "EMPRESA")
        selected_empresa = st.sidebar.selectbox("Selecione Empresa", empresas) if empresas else None

        if selected_empresa and "EMPRESA" in gdf_full.columns and "FAZENDA" in gdf_full.columns:
            gdf_emp = gdf_full[gdf_full["EMPRESA"].astype(str) == str(selected_empresa)]
            fazendas = safe_unique(gdf_emp, "FAZENDA")
            selected_fazenda = st.sidebar.selectbox("Selecione Fazenda", fazendas) if fazendas else None

    elif tipo_dado == "Dados por Município":
        ufs = safe_unique(gdf_full, "UF")
        selected_uf = st.sidebar.selectbox("Selecione UF", ufs) if ufs else None

        if selected_uf and "UF" in gdf_full.columns and "MUNICIPIO" in gdf_full.columns:
            gdf_uf = gdf_full[gdf_full["UF"].astype(str) == str(selected_uf)]
            municipios = safe_unique(gdf_uf, "MUNICIPIO")
            selected_municipio = st.sidebar.selectbox("Selecione Município", municipios) if municipios else None

    st.sidebar.markdown("---")
    st.sidebar.subheader("Período mensal")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_mes_nome = st.selectbox("Mês inicial", list(MESES_DISPONIVEIS.keys()), index=0)
    with col2:
        start_ano = st.selectbox("Ano inicial", ANOS_DISPONIVEIS, index=ANOS_DISPONIVEIS.index(2026))

    col3, col4 = st.sidebar.columns(2)
    with col3:
        end_mes_nome = st.selectbox("Mês final", list(MESES_DISPONIVEIS.keys()), index=11)
    with col4:
        end_ano = st.selectbox("Ano final", ANOS_DISPONIVEIS, index=ANOS_DISPONIVEIS.index(2026))

    start_date = date(start_ano, MESES_DISPONIVEIS[start_mes_nome], 1)
    end_date = date(end_ano, MESES_DISPONIVEIS[end_mes_nome], 1)

    apply = st.sidebar.button("✅ Aplicar Filtros")
    log_container = st.sidebar.container() if apply else st.sidebar.empty()

    return {
        "tipo_dado": tipo_dado,
        "selected_uf": selected_uf,
        "selected_empresa": selected_empresa,
        "selected_fazenda": selected_fazenda,
        "selected_municipio": selected_municipio,
        "start_date": start_date,
        "end_date": end_date,
        "apply": apply,
        "log_container": log_container,
    }