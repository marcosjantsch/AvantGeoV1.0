# tabs/tab_mapa.py
import numpy as np
import pandas as pd
import folium
import streamlit as st

from folium.plugins import Fullscreen, MiniMap, MeasureControl, MousePosition
from streamlit_folium import st_folium

from core.settings import MAX_FEATURES_FULL_MAP


def _add_basemaps(m: folium.Map) -> None:
    """
    Adiciona múltiplas camadas de mapa base.
    """

    # Base padrão
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        show=True,
        control=True,
    ).add_to(m)

    # Satélite ESRI
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Imagery",
        show=False,
        control=True,
    ).add_to(m)

    # Topográfico ESRI
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Topo",
        show=False,
        control=True,
    ).add_to(m)

    # Topográfico aberto
    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="OpenTopoMap",
        name="OpenTopoMap",
        show=False,
        control=True,
    ).add_to(m)

    # Mapa outdoor
    folium.TileLayer(
        tiles="https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png",
        attr="Stadia Maps",
        name="Stadia Outdoors",
        show=False,
        control=True,
    ).add_to(m)

    # Limites via WMS do IBGE
    try:
        folium.WmsTileLayer(
            url="https://geoservicos.ibge.gov.br/geoserver/ows?",
            name="IBGE Limites (WMS)",
            layers="CGEO:BC250_2019_UF",
            fmt="image/png",
            transparent=True,
            attr="IBGE",
            overlay=True,
            control=True,
            show=False,
        ).add_to(m)
    except Exception:
        pass


def _get_cor_exibicao(tipo_exib: str) -> str:
    color_map = {
        "Todos os Dados": "#DFF500",
        "Dados por Estado": "#F500B4",
        "Dados por Empresa": "#00C4F5",
        "Dados Empresa/Fazenda": "#FF3B30",
        "Dados por Município": "#F5C400",
    }
    return color_map.get(tipo_exib, "#3388ff")


def _preparar_gdf_exibicao(gdf_map):
    """
    Padroniza campos numéricos e textos auxiliares para tooltip.
    """
    gdf_map = gdf_map.copy()

    for col in ["AREA_T", "AREA_PRODU"]:
        if col in gdf_map.columns:
            gdf_map[col] = pd.to_numeric(gdf_map[col], errors="coerce").round(1)

    if "AREA_T" in gdf_map.columns:
        gdf_map["AREA_T_TXT"] = gdf_map["AREA_T"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    if "AREA_PRODU" in gdf_map.columns:
        gdf_map["AREA_PRODU_TXT"] = gdf_map["AREA_PRODU"].apply(
            lambda x: f"{x:.1f} ha" if pd.notna(x) else "N/A"
        )

    return gdf_map


def _criar_tooltip(gdf_map):
    tooltip_fields = [
        c
        for c in [
            "UF",
            "MUNICIPIO",
            "EMPRESA",
            "FAZENDA",
            "AREA_T_TXT",
            "AREA_PRODU_TXT",
        ]
        if c in gdf_map.columns
    ]

    tooltip_aliases_map = {
        "UF": "UF",
        "MUNICIPIO": "Município",
        "EMPRESA": "Empresa",
        "FAZENDA": "Fazenda",
        "AREA_T_TXT": "Área Total",
        "AREA_PRODU_TXT": "Área Produtiva",
    }
    tooltip_aliases = [tooltip_aliases_map.get(c, c) for c in tooltip_fields]

    return tooltip_fields, tooltip_aliases


def render_tab_mapa(gdf_full, gdf_filtered, filtro):
    st.markdown('<div class="section-title">Mapa Principal</div>', unsafe_allow_html=True)

    aplicar = st.session_state.get("aplicar", False)
    gdf_map = gdf_filtered if aplicar else gdf_full
    tipo_exib = filtro["tipo_dado"] if aplicar else "Todos os Dados"

    if gdf_map is None or gdf_map.empty:
        st.info("Nenhuma geometria disponível para exibição no mapa.")
        return

    col_opt1, col_opt2 = st.columns(2)

    with col_opt1:
        usar_geometria_original = st.checkbox(
            "Exibir polígonos sem simplificação",
            value=False,
            key="mapa_sem_simplificacao",
            help="Mostra as geometrias originais do shapefile. Pode deixar o mapa mais pesado.",
        )

    with col_opt2:
        mostrar_preenchimento = st.checkbox(
            "Preencher polígonos",
            value=True,
            key="mapa_preenchimento",
            help="Quando desmarcado, exibe apenas o contorno das feições.",
        )

    gdf_map = gdf_map.copy()

    if usar_geometria_original and "__geometry_original__" in gdf_map.columns:
        gdf_map["geometry"] = gdf_map["__geometry_original__"]

    area_total_mapa = (
        float(pd.to_numeric(gdf_map["AREA_T"], errors="coerce").sum())
        if "AREA_T" in gdf_map.columns
        else np.nan
    )
    area_produ_mapa = (
        float(pd.to_numeric(gdf_map["AREA_PRODU"], errors="coerce").sum())
        if "AREA_PRODU" in gdf_map.columns
        else np.nan
    )
    n_municipios = (
        int(gdf_map["MUNICIPIO"].dropna().astype(str).nunique())
        if "MUNICIPIO" in gdf_map.columns
        else 0
    )
    n_fazendas = (
        int(gdf_map["FAZENDA"].dropna().astype(str).nunique())
        if "FAZENDA" in gdf_map.columns
        else 0
    )
    n_feicoes = len(gdf_map)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fazendas", str(n_fazendas))
    c2.metric(
        "Área total (ha)",
        f"{area_total_mapa:.1f}" if pd.notna(area_total_mapa) else "N/A",
    )
    c3.metric(
        "Área produtiva (ha)",
        f"{area_produ_mapa:.1f}" if pd.notna(area_produ_mapa) else "N/A",
    )
    c4.metric("Municípios", str(n_municipios))
    c5.metric("Feições", f"{n_feicoes:,}".replace(",", "."))

    if len(gdf_map) > MAX_FEATURES_FULL_MAP:
        st.warning(
            f"⚠️ Muitas feições ({len(gdf_map)}). "
            f"Renderizando apenas {MAX_FEATURES_FULL_MAP}."
        )
        gdf_map = gdf_map.head(MAX_FEATURES_FULL_MAP)

    gdf_map = _preparar_gdf_exibicao(gdf_map)

    try:
        bounds = gdf_map.total_bounds
        minx, miny, maxx, maxy = bounds
    except Exception:
        st.error("Não foi possível calcular os limites espaciais das geometrias.")
        return

    if any(pd.isna(v) for v in [minx, miny, maxx, maxy]):
        st.error("Os limites espaciais das geometrias são inválidos.")
        return

    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles=None,
        control_scale=True,
    )

    try:
        m.fit_bounds([[miny, minx], [maxy, maxx]])
    except Exception:
        pass

    _add_basemaps(m)

    Fullscreen(
        position="topright",
        title="Tela cheia",
        title_cancel="Sair da tela cheia",
        force_separate_button=True,
    ).add_to(m)

    MiniMap(toggle_display=True, position="bottomright").add_to(m)

    MeasureControl(
        position="topleft",
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        primary_area_unit="sqmeters",
        secondary_area_unit="hectares",
    ).add_to(m)

    MousePosition(
        position="bottomleft",
        separator=" | ",
        prefix="Coordenadas",
        lat_formatter="function(num) {return L.Util.formatNum(num, 6);}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 6);}",
    ).add_to(m)

    color = _get_cor_exibicao(tipo_exib)
    tooltip_fields, tooltip_aliases = _criar_tooltip(gdf_map)

    gdf_render = gdf_map.drop(columns=["__geometry_original__"], errors="ignore").copy()

    folium.GeoJson(
        data=gdf_render.to_json(),
        name="Fazendas",
        style_function=lambda x: {
            "fillColor": color,
            "color": color,
            "weight": 1.4,
            "fillOpacity": 0.40 if mostrar_preenchimento else 0.00,
        },
        highlight_function=lambda x: {
            "fillColor": color,
            "color": "#000000",
            "weight": 2.6,
            "fillOpacity": 0.65 if mostrar_preenchimento else 0.10,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            sticky=True,
            labels=True,
            localize=True,
        ),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(
        m,
        width=1400,
        height=620,
        key="mapa_principal",
        returned_objects=[],
    )

    st.caption(
        "Bases disponíveis: OpenStreetMap, Esri World Imagery, Esri World Topo, "
        "OpenTopoMap, Stadia Outdoors e IBGE Limites (WMS)."
    )