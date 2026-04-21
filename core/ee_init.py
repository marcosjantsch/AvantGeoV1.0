# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Tuple

import ee
import streamlit as st

from core.settings import ASSET_FAZENDAS, EE_PROJECT


def _extract_asset_project(asset_path: str) -> str | None:
    prefix = "projects/"
    if not asset_path.startswith(prefix):
        return None
    remainder = asset_path[len(prefix):]
    project = remainder.split("/", 1)[0].strip()
    return project or None


def _project_candidates() -> List[str]:
    candidates: List[str] = []
    for candidate in [EE_PROJECT, _extract_asset_project(ASSET_FAZENDAS)]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _initialize_with_project(project_id: str) -> Tuple[bool, str]:
    try:
        ee.Initialize(project=project_id)
        return True, project_id
    except Exception as exc:
        return False, str(exc)


@st.cache_resource
def init_ee() -> Tuple[bool, str]:
    attempted_projects: List[str] = []

    for project_id in _project_candidates():
        ok, result = _initialize_with_project(project_id)
        if ok:
            return True, f"Earth Engine inicializado com sucesso no projeto '{result}'."
        attempted_projects.append(f"{project_id}: {result}")

    try:
        ee.Initialize()
        return True, "Earth Engine inicializado com sucesso usando as credenciais locais padrao."
    except Exception as exc:
        msg = str(exc)

        if "not registered to use Earth Engine" in msg:
            return (
                False,
                "Nenhum projeto valido do Earth Engine foi encontrado para estas credenciais. "
                "Defina um projeto ativo em EE_PROJECT ou registre o projeto atual no Earth Engine.",
            )

        if "SERVICE_DISABLED" in msg or "API has not been used" in msg:
            return (
                False,
                "A Earth Engine API nao esta ativada no projeto configurado. "
                "Ative a API no projeto GCP que sera usado pelo app.",
            )

        attempted_text = " | ".join(attempted_projects) if attempted_projects else "sem projetos explicitos"
        return False, f"Falha ao inicializar o Earth Engine: {exc}. Tentativas: {attempted_text}"
