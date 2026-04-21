from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _first_env(*names: str):
    for name in names:
        value = os.getenv(name)
        if value and str(value).strip():
            return str(value).strip()
    return None

APP_TITLE = "Avant GE"
APP_ICON = "🛰️"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

EE_PROJECT = _first_env("EE_PROJECT", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "GCLOUD_PROJECT")
ASSET_FAZENDAS = "projects/avantv1-475717/assets/GFP/Geo_Limites_GFP_Setembro_2025"
COL_EMPRESA = "EMPRESA"
COL_FAZENDA = "FAZENDA"

LOGO_PATH = str(BASE_DIR / "assets" / "Logo.png")
GEO_PATH = str(BASE_DIR / "data" / "Geo.shp")

AUTH_ENABLED = True

DEFAULT_START_DATE = "2015-06-27"
DEFAULT_END_DATE = None
DEFAULT_CLOUD = 20
