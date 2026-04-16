# services/log_service.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st



LOG_SESSION_KEY = "event_log_records"


def _ensure_log_store() -> List[Dict[str, Any]]:
    if LOG_SESSION_KEY not in st.session_state:
        st.session_state[LOG_SESSION_KEY] = []
    return st.session_state[LOG_SESSION_KEY]


def clear_logs() -> None:
    st.session_state[LOG_SESSION_KEY] = []


def add_log(level, source, message, details=None):
    if "event_log_records" not in st.session_state:
        st.session_state["event_log_records"] = []
    st.session_state["event_log_records"].append({
        "level": level,
        "source": source,
        "message": message,
        "details": details or {}
    })

def log_info(source, message, details=None):
    add_log("INFO", source, message, details)


def get_logs() -> List[Dict[str, Any]]:
    return list(_ensure_log_store())


def logs_to_dataframe() -> pd.DataFrame:
    rows = []
    for item in _ensure_log_store():
        base = {
            "timestamp": item.get("timestamp"),
            "level": item.get("level"),
            "source": item.get("source"),
            "message": item.get("message"),
        }
        details = item.get("details", {}) or {}
        if not isinstance(details, dict):
            details = {"details": str(details)}

        row = {**base, **details}
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=["timestamp", "level", "source", "message"])

    return pd.DataFrame(rows)


def log_warning(source: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    add_log("WARNING", source, message, details)


def log_error(source: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    add_log("ERROR", source, message, details)


def log_success(source: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    add_log("SUCCESS", source, message, details)