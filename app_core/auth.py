# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st

from auth import get_user_role, setup_authentication
from services.log_service import add_log


def log_auth_login(user: str, role: str, status: str, username: str = ""):
    add_log(
        level="INFO" if status == "SUCCESS" else "ERROR",
        source="auth_login_log",
        message="Login realizado" if status == "SUCCESS" else "Falha no login",
        details={"user": user, "username": username, "role": role, "status": status},
    )


def resolve_authenticated_user(auth_enabled: bool):
    name = "Usuário"
    username = None
    role = "Acesso local"
    authenticator = None

    if not auth_enabled:
        return authenticator, name, role, username

    authenticator, name, authentication_status, username = setup_authentication()

    if authentication_status is False:
        if not st.session_state.get("auth_login_logged_fail", False):
            log_auth_login(
                user=username or "unknown",
                username=username or "",
                role="unknown",
                status="FAIL",
            )
            st.session_state["auth_login_logged_fail"] = True
        st.error("❌ Usuário ou senha incorretos.")
        st.stop()

    if authentication_status is None:
        st.warning("⚠️ Informe suas credenciais.")
        st.stop()

    role = get_user_role()

    if not st.session_state.get("auth_login_logged_success", False):
        log_auth_login(
            user=name or "unknown",
            username=username or "",
            role=role or "unknown",
            status="SUCCESS",
        )
        st.session_state["auth_login_logged_success"] = True

    return authenticator, name, role, username
