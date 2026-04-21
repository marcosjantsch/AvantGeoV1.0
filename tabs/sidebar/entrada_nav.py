# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from tabs.sidebar.entrada_state import (
    MODO_COORDENADA,
    MODO_EMPRESA_FAZENDA,
    MODO_KML,
    apply_mode_state,
)


MODE_TABS = [
    MODO_EMPRESA_FAZENDA,
    MODO_COORDENADA,
    MODO_KML,
]


def render_mode_tabs() -> str:
    current_mode = st.session_state.get("sb_modo_entrada", MODO_EMPRESA_FAZENDA)
    if current_mode not in MODE_TABS:
        current_mode = MODO_EMPRESA_FAZENDA
        st.session_state["sb_modo_entrada"] = current_mode

    st.markdown("**Modo de entrada**")
    cols = st.columns(len(MODE_TABS))

    for col, mode in zip(cols, MODE_TABS):
        with col:
            clicked = st.button(
                mode,
                key=f"mode_tab_{mode}",
                use_container_width=True,
                type="primary" if current_mode == mode else "secondary",
            )
            if clicked and current_mode != mode:
                st.session_state["sb_modo_entrada"] = mode
                apply_mode_state(mode)
                current_mode = mode
            elif clicked and current_mode == mode and mode == MODO_COORDENADA:
                apply_mode_state(mode)

    return current_mode
