# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Tuple

import ee
import streamlit as st

from core.settings import EE_PROJECT


def _project_candidates() -> List[str]:
    candidates: List[str] = []
    for candidate in [EE_PROJECT]:
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
    configured_project = EE_PROJECT

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

        if "no project found" in msg or "Call with project=" in msg:
            configured_text = configured_project or "nenhum projeto configurado"
            attempted_text = " | ".join(attempted_projects) if attempted_projects else "sem tentativas com projeto explicito"
            return (
                False,
                "Falha ao inicializar o Earth Engine: nenhum projeto GCP utilizavel foi encontrado para estas credenciais. "
                f"Projeto configurado: {configured_text}. "
                "No ambiente online, defina EE_PROJECT ou GOOGLE_CLOUD_PROJECT para um projeto em que a conta tenha "
                "a permissao serviceusage.services.use (por exemplo, roles/serviceusage.serviceUsageConsumer) "
                "e em que a Earth Engine API esteja habilitada. "
                f"Tentativas: {attempted_text}",
            )

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

        if "serviceusage.services.use" in msg or "does not have required permission to use project" in msg:
            attempted_text = " | ".join(attempted_projects) if attempted_projects else "sem projetos explicitos"
            return (
                False,
                "As credenciais atuais nao tem permissao para usar o projeto GCP configurado no Earth Engine. "
                "No ambiente online, configure EE_PROJECT ou GOOGLE_CLOUD_PROJECT para um projeto acessivel por essa conta "
                "e conceda a permissao roles/serviceusage.serviceUsageConsumer, mantendo tambem a Earth Engine API habilitada. "
                f"Tentativas: {attempted_text}",
            )

        attempted_text = " | ".join(attempted_projects) if attempted_projects else "sem projetos explicitos"
        return False, f"Falha ao inicializar o Earth Engine: {exc}. Tentativas: {attempted_text}"
