# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import os
import pandas as pd
import streamlit as st


LOG_SESSION_KEY = "event_log_records"
LOG_FILE = "logs_auth.csv"


# =========================================================
# BASE
# =========================================================

def _ensure_log_store() -> List[Dict[str, Any]]:
    if LOG_SESSION_KEY not in st.session_state:
        st.session_state[LOG_SESSION_KEY] = []
    return st.session_state[LOG_SESSION_KEY]


def clear_logs() -> None:
    st.session_state[LOG_SESSION_KEY] = []


# =========================================================
# PERSISTÊNCIA
# =========================================================

def _persist_log(record: Dict[str, Any]) -> None:
    try:
        df = pd.DataFrame([record])

        if os.path.exists(LOG_FILE):
            df.to_csv(LOG_FILE, mode="a", header=False, index=False)
        else:
            df.to_csv(LOG_FILE, index=False)

    except Exception as e:
        # não quebra o app se falhar
        print(f"[LOG ERROR] Falha ao salvar log: {e}")


# =========================================================
# LOG PRINCIPAL
# =========================================================

def add_log(level: str, source: str, message: str, details=None):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "source": source,
        "message": message,
    }

    if isinstance(details, dict):
        record.update(details)
    elif details is not None:
        record["details"] = str(details)

    # salva na sessão
    _ensure_log_store().append(record)

    # salva em arquivo
    _persist_log(record)


# =========================================================
# WRAPPERS
# =========================================================

def log_info(source: str, message: str, details=None):
    add_log("INFO", source, message, details)


def log_warning(source: str, message: str, details=None):
    add_log("WARNING", source, message, details)


def log_error(source: str, message: str, details=None):
    add_log("ERROR", source, message, details)


def log_success(source: str, message: str, details=None):
    add_log("SUCCESS", source, message, details)


# =========================================================
# LOG ESPECÍFICO DE LOGIN
# =========================================================

def log_auth_login(user: str, role: str, status: str, username: str = ""):
    add_log(
        level="INFO" if status == "SUCCESS" else "ERROR",
        source="auth_login_log",
        message="Login realizado" if status == "SUCCESS" else "Falha no login",
        details={
            "user": user,
            "username": username,
            "role": role,
            "status": status,
        },
    )


# =========================================================
# CONSULTA
# =========================================================

def get_logs() -> List[Dict[str, Any]]:
    return list(_ensure_log_store())


def logs_to_dataframe() -> pd.DataFrame:
    rows = _ensure_log_store()

    if not rows:
        return pd.DataFrame(columns=["timestamp", "level", "source", "message"])

    return pd.DataFrame(rows)