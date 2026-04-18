# -*- coding: utf-8 -*-
from typing import Tuple
import ee
import streamlit as st

from core.settings import EE_PROJECT


@st.cache_resource
def init_ee() -> Tuple[bool, str]:
    try:
        ee.Initialize(project=EE_PROJECT)
        return True, "Earth Engine inicializado com sucesso."
    except Exception as exc:
        msg = str(exc)
        if "not registered to use Earth Engine" in msg:
            return (
                False,
                "O projeto 'avantv2' ainda não foi registrado para uso no Earth Engine. "
                "Acesse https://console.cloud.google.com/earth-engine/configuration?project=avantv2 "
                "e conclua o registro.",
            )
        if "SERVICE_DISABLED" in msg or "API has not been used" in msg:
            return (
                False,
                "A Earth Engine API não está ativada no projeto 'avantv2'. "
                "Ative em https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project=avantv2",
            )
        return False, f"Falha ao inicializar o Earth Engine: {exc}"
