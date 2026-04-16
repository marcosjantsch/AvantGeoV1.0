# tabs/tab_shape.py
import pandas as pd
import streamlit as st
from services.export_service import df_to_excel_bytes

def render_tab_shape(gdf_filtered):
    st.markdown('<div class="section-title">Dados Shape</div>', unsafe_allow_html=True)

    if not st.session_state.get("aplicar", False):
        st.info("Clique em 'Aplicar Filtros' na sidebar para ver os dados do shapefile.")
        return

    if gdf_filtered is None or gdf_filtered.empty:
        st.info("Nenhum dado filtrado para exibir.")
        return

    df_shape = gdf_filtered.copy()
    df_shape = df_shape.drop(columns=["geometry"], errors="ignore")
    df_shape.columns = [str(c).strip() for c in df_shape.columns]

    aliases = {
        "AREA_PORDUT": "AREA_PRODU",
        "AREA_PRODUT": "AREA_PRODU",
        "AREA_PRODUTIVA": "AREA_PRODU",
    }
    df_shape = df_shape.rename(columns={k: v for k, v in aliases.items() if k in df_shape.columns})
    df_shape = df_shape.drop(columns=["LOCAL_PROJ"], errors="ignore")

    for col_area in ["AREA_T", "AREA_PRODU"]:
        if col_area in df_shape.columns:
            df_shape[col_area] = pd.to_numeric(df_shape[col_area], errors="coerce").round(1)

    ordem_prioritaria = [
        "UF", "EMPRESA", "FAZENDA", "MUNICIPIO",
        "AREA_T", "AREA_PRODU", "CENTROIDE_", "CENTROID_1"
    ]
    colunas_existentes = [c for c in ordem_prioritaria if c in df_shape.columns]
    outras_colunas = [c for c in df_shape.columns if c not in colunas_existentes]
    df_shape = df_shape[colunas_existentes + outras_colunas]

    excel_bytes = df_to_excel_bytes(df_shape, sheet_name="Dados_Shape")

    st.download_button(
        label="⬇️ Exportar para Excel (.xlsx)",
        data=excel_bytes,
        file_name="dados_shape.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.info("Foram exibidas somente as 5 primeiras linhas da tabela.")

    if st.button("Exibir tudo", key="btn_exibir_tudo_shape"):
        st.session_state["mostrar_tudo_shape"] = True

    if st.session_state["mostrar_tudo_shape"]:
        st.dataframe(df_shape, use_container_width=True, height=520)
        st.caption(f"Total de registros: {len(df_shape)}")
    else:
        st.dataframe(df_shape.head(5), use_container_width=True, height=220)
        st.caption(f"Mostrando 5 de {len(df_shape)} registros.")