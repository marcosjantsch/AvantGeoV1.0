# -*- coding: utf-8 -*-
from pathlib import Path
import streamlit as st


SATELLITE_PRODUCTS_INFO = {
    "Imagem Sentinel RGB": {
        "descricao": (
            "Composição natural em cores reais, normalmente usando as bandas "
            "Red, Green e Blue. É a visualização mais intuitiva para inspeção "
            "geral da paisagem, estradas, talhões, sombras, solo exposto e água."
        ),
        "bandas": "B4 (Red), B3 (Green), B2 (Blue)",
        "uso": (
            "Ideal para interpretação visual geral, reconhecimento de solo exposto, "
            "tons amarelados, acinzentados, falhas de plantio, manchas de vegetação "
            "e comparação com observação de campo."
        ),
    },
    "NDVI": {
        "descricao": (
            "Índice clássico de vigor vegetativo. Mede a diferença normalizada "
            "entre o infravermelho próximo e o vermelho."
        ),
        "bandas": "NDVI = (B8 - B4) / (B8 + B4)",
        "uso": (
            "Excelente para saúde vegetal, biomassa, vigor e contraste entre "
            "vegetação saudável e áreas degradadas."
        ),
    },
    "NDWI": {
        "descricao": (
            "Índice relacionado à água e umidade. Pode destacar vegetação úmida "
            "ou presença de água, dependendo da formulação utilizada."
        ),
        "bandas": "Exemplo: (B3 - B8) / (B3 + B8)",
        "uso": (
            "Útil para identificar áreas úmidas, drenagens, presença de água "
            "e diferenças de umidade na vegetação."
        ),
    },
    "EVI": {
        "descricao": (
            "Índice de vegetação que corrige parte dos efeitos atmosféricos e "
            "da saturação do NDVI em vegetação densa."
        ),
        "bandas": "EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))",
        "uso": (
            "Muito bom para vegetação densa, análise de vigor e comparação mais "
            "estável em áreas florestais."
        ),
    },
    "SAVI": {
        "descricao": (
            "Índice ajustado para influência do solo, reduzindo o impacto de solo "
            "exposto na resposta espectral."
        ),
        "bandas": "SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)",
        "uso": (
            "Recomendado em áreas com solo aparente, vegetação rala, falhas de cobertura "
            "e mosaicos com mistura entre solo e vegetação."
        ),
    },
    "NBR": {
        "descricao": (
            "Índice muito usado para queimadas, cicatriz de fogo e alterações severas "
            "na vegetação."
        ),
        "bandas": "NBR = (B8 - B12) / (B8 + B12)",
        "uso": (
            "Melhor escolha para identificação de queimadas, severidade de fogo "
            "e comparação de áreas queimadas versus não queimadas."
        ),
    },
    "MSI": {
        "descricao": (
            "Índice de estresse hídrico baseado na razão entre SWIR e NIR."
        ),
        "bandas": "MSI = B11 / B8",
        "uso": (
            "Bom para identificar estresse hídrico, redução de umidade da vegetação "
            "e diferenças de condição hídrica entre talhões."
        ),
    },
    "GNDVI": {
        "descricao": (
            "Variação do NDVI usando a banda verde, muito relacionada ao teor de clorofila."
        ),
        "bandas": "GNDVI = (B8 - B3) / (B8 + B3)",
        "uso": (
            "Útil para avaliação de clorofila, diferenças sutis de vigor e resposta "
            "de vegetação ativa."
        ),
    },
    "RGB Landsat": {
        "descricao": (
            "Composição natural equivalente para Landsat, ajustada conforme o sensor."
        ),
        "bandas": (
            "Landsat 5/7: SR_B3, SR_B2, SR_B1 | "
            "Landsat 8/9: SR_B4, SR_B3, SR_B2"
        ),
        "uso": (
            "Visualização natural da paisagem usando cenas Landsat, útil para "
            "interpretação visual e análise histórica."
        ),
    },

    "Imagem Sentinel RGB Ajustada": {
    "descricao": (
        "Versão da composição RGB natural com ajuste de brilho, contraste e gamma "
        "para melhorar a leitura visual da cena."
    ),
    "bandas": "B4 (Red), B3 (Green), B2 (Blue)",
    "uso": (
        "Indicada para inspeção visual quando a composição RGB original estiver "
        "escura demais. Facilita a identificação de solo exposto, variações de cor, "
        "falhas e contrastes na paisagem."
    ),
},

}


def render_tab_dados_satelite(logo_path: str = None):
    st.subheader("🛰️ Dados de satélite")

    produto = st.selectbox(
        "Selecione o tipo de imagem para ver a explicação",
        options=list(SATELLITE_PRODUCTS_INFO.keys()),
        index=0,
    )

    info = SATELLITE_PRODUCTS_INFO[produto]

    st.markdown("### Descrição")
    st.write(info["descricao"])

    st.markdown("### Bandas / fórmula")
    st.code(info["bandas"])

    st.markdown("### Aplicação prática")
    st.write(info["uso"])

    st.markdown("---")

    st.markdown("### Interpretação resumida")
    if produto in ["Imagem Sentinel RGB", "RGB Landsat"]:
        st.write(
            "Melhor opção para leitura visual direta de solo exposto, áreas amareladas, "
            "tons acinzentados, manchas, falhas e inspeção geral do terreno."
        )
    elif produto in ["NDVI", "EVI", "GNDVI", "SAVI"]:
        st.write(
            "Mais indicados para vigor vegetativo, biomassa, clorofila e contraste "
            "entre vegetação sadia e vegetação estressada."
        )
    elif produto in ["NDWI", "MSI"]:
        st.write(
            "Mais indicados para umidade, água e condição hídrica da vegetação."
        )
    elif produto == "NBR":
        st.write(
            "Melhor opção para queimadas, cicatrizes de fogo e danos severos à cobertura vegetal."
        )

    if logo_path and Path(logo_path).exists():
        st.markdown("---")
        st.image(logo_path, width=180)