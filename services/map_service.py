# -*- coding: utf-8 -*-

import folium


def build_base_map(gdf):
    """
    Cria um mapa Folium baseado no centroid do GeoDataFrame.
    """

    # Centro do mapa
    centroid = gdf.geometry.unary_union.centroid
    lat, lon = centroid.y, centroid.x

    m = folium.Map(
        location=[lat, lon],
        zoom_start=10,
        control_scale=True,
    )

    # Adicionar geometria
    folium.GeoJson(
        gdf,
        name="Fazendas",
        style_function=lambda x: {
            "color": "#FF0000",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m