from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

APP_TITLE = "Visualizador de Shapefile e Dados Climáticos"
APP_ICON = "🗺️"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

SIMPLIFICATION_TOLERANCE = 0.001
MAX_FEATURES_FULL_MAP = 5000

GEO_PATH = str(BASE_DIR / "Geo.shp")
LOGO_PATH = str(BASE_DIR / "assets" / "Logo.tif")

AUTH_ENABLED = os.path.exists(BASE_DIR / "config.yaml")

TIPOS_DADO = [
    "Todos os Dados",
    "Dados por Estado",
    "Dados por Empresa",
    "Dados Empresa/Fazenda",
    "Dados por Município",
]

MESES_DISPONIVEIS = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
}

ANOS_DISPONIVEIS = list(range(2010, 2027))
