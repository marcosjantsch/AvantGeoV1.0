# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import streamlit.components.v1 as components


_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "coordinate_marker_map"
_coordinate_marker_component = components.declare_component(
    "coordinate_marker_map",
    path=str(_FRONTEND_DIR),
)


def render_coordinate_marker_map(
    latitude: float,
    longitude: float,
    zoom: int = 12,
    height: int = 760,
    key: str = "coordinate_marker_map",
) -> Optional[Dict[str, Any]]:
    return _coordinate_marker_component(
        latitude=float(latitude),
        longitude=float(longitude),
        zoom=int(zoom),
        height=int(height),
        key=key,
        default=None,
    )
