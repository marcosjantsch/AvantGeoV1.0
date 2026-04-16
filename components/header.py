from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image


def _render_logout_button(authenticator, username=None, name=None, role=None) -> None:
    if authenticator is None:
        return

    if st.button("Sair", use_container_width=True):
        try:
            from services.auth_log_service import registrar_logout

            registrar_logout(
                username=username,
                nome=name,
                perfil=role,
            )
        except Exception:
            pass

        st.session_state["login_registrado"] = False

        try:
            authenticator.logout(location="unrendered")
        except TypeError:
            try:
                authenticator.logout("Sair", "unrendered")
            except Exception:
                pass
        except Exception:
            pass

        st.rerun()


def _pill(text: str, icon: str = "") -> str:
    prefix = f"{icon} " if icon else ""
    return (
        "<span style='"
        "display:inline-flex;"
        "align-items:center;"
        "padding:6px 12px;"
        "border-radius:999px;"
        "font-size:12px;"
        "font-weight:500;"
        "line-height:1;"
        "border:1px solid rgba(255,255,255,0.12);"
        "background:rgba(255,255,255,0.06);"
        "white-space:nowrap;"
        "'>"
        f"{prefix}{text}"
        "</span>"
    )


def render_header(
    logo_path: str,
    app_name: str,
    version: str,
    user: Optional[str] = None,
    role: Optional[str] = None,
    username: Optional[str] = None,
    authenticator=None,
    subtitle: str = "Análise de Dados Climáticos",
) -> None:
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    left, center, right = st.columns([3.3, 4.2, 2.5], vertical_alignment="center")

    with left:
        logo_col, text_col = st.columns([1, 6], vertical_alignment="center")

        with logo_col:
            logo_file = Path(logo_path)
            if logo_file.exists():
                try:
                    img = Image.open(logo_file)
                    st.image(img, width=52)
                except Exception:
                    pass

        with text_col:
            st.markdown(
                (
                    "<div style='display:flex; align-items:center; gap:12px; flex-wrap:wrap;'>"
                    f"<span style='font-size:28px; font-weight:700; line-height:1.1;'>{app_name}</span>"
                    f"<span style='font-size:12px; opacity:0.70; padding-top:3px;'>{version}</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    with center:
        st.markdown(
            (
                "<div style='display:flex; justify-content:center; align-items:center; height:100%; text-align:center;'>"
                f"<span style='font-size:22px; font-weight:600; opacity:0.95; line-height:1.15;'>{subtitle}</span>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    with right:
        if user or role or authenticator:
            info_col, btn_col = st.columns([4.0, 1.4], vertical_alignment="center")

            with info_col:
                items = []
                if user:
                    items.append(_pill(str(user), "👤"))
                if role:
                    items.append(_pill(str(role), "🔐"))

                st.markdown(
                    (
                        "<div style='display:flex; justify-content:flex-end; align-items:center; "
                        "gap:8px; flex-wrap:wrap;'>"
                        + "".join(items) +
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )

            with btn_col:
                _render_logout_button(
                    authenticator=authenticator,
                    username=username,
                    name=user,
                    role=role,
                )

    st.markdown(
        (
            "<div style='margin-top:10px; margin-bottom:10px; "
            "border-bottom:1px solid rgba(255,255,255,0.10);'></div>"
        ),
        unsafe_allow_html=True,
    )