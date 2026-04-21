# -*- coding: utf-8 -*-
from __future__ import annotations


def build_header_config(
    modo_entrada: str,
    selected_empresa=None,
    selected_fazenda=None,
    parsed_coordinates=None,
    uploaded_kml=None,
) -> dict:
    return {
        "app_name": "Avant GEO",
        "mode_badge": "",
        "subtitle": "",
    }
