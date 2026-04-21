# -*- coding: utf-8 -*-
from __future__ import annotations


def build_header_styles() -> str:
    return f"""
    <style>
    section.main > div.block-container {{
        padding-top: 0.35rem;
    }}

    .ag-header-wrap {{
        margin: -4px 0 4px 0;
        padding: 0;
    }}

    .ag-header-card {{
        border: none;
        border-radius: 0;
        padding: 2px 0 4px 0;
        background: transparent;
        box-shadow: none;
    }}

    .ag-header-left {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .ag-header-logo-fallback {{
        width: 58px;
        height: 58px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0f766e, #2563eb);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.18);
    }}

    .ag-header-title-row {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin: 0;
        padding: 0;
    }}

    .ag-header-title {{
        font-size: 21px;
        font-weight: 800;
        line-height: 1.05;
        margin: 0;
        padding: 0;
        letter-spacing: -0.2px;
    }}

    .ag-header-version {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        line-height: 1;
        opacity: 0.88;
        border: 1px solid rgba(120, 120, 120, 0.18);
    }}

    .ag-header-user-row {{
        border: none;
        border-radius: 0;
        padding: 0;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 8px;
        min-height: 30px;
        white-space: nowrap;
        overflow: hidden;
    }}

    .ag-header-user-inline {{
        font-size: 13.5px;
        line-height: 1.25;
        opacity: 0.96;
        font-weight: 600;
        letter-spacing: 0.1px;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    div[data-testid="stButton"] > button[kind="secondary"] {{
        min-height: 30px;
        border-radius: 8px;
        font-weight: 700;
    }}

    div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {{
        gap: 0.2rem;
    }}

    div[data-testid="stSidebar"] div[data-baseweb="tab"] {{
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }}

    div[data-testid="stSidebar"] .stMarkdown {{
        margin-bottom: 0.15rem;
    }}

    div[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
        gap: 0.35rem;
    }}

    @media (max-width: 900px) {{
        .ag-header-title {{
            font-size: 18px;
        }}
        .ag-header-user-inline {{
            font-size: 12.5px;
        }}
        .ag-header-card {{
            padding: 2px 0 4px 0;
        }}
        .ag-header-user-row {{
            white-space: normal;
            align-items: flex-start;
        }}
    }}
    </style>
    """
