from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_TITLE = "Avant GE"
APP_ICON = "🛰️"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

EE_PROJECT = "avantv2"
ASSET_FAZENDAS = "projects/avantv1-475717/assets/GFP/Geo_Limites_GFP_Setembro_2025"
COL_EMPRESA = "EMPRESA"
COL_FAZENDA = "FAZENDA"

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "Logo.png"

GEO_PATH = str(BASE_DIR / "data" / "Geo.shp")

AUTH_ENABLED = True

DEFAULT_START_DATE = "2026-04-01"
DEFAULT_END_DATE = None
DEFAULT_CLOUD = 20
