# -*- coding: utf-8 -*-
from pathlib import Path
import streamlit as st


def render_sidebar_export_downloads(export_result):
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Downloads disponíveis")

        if not export_result:
            st.caption("Nenhum arquivo exportado nesta sessão.")
            return

        png_path = export_result.get("png_path")
        tif_path = export_result.get("tif_path")
        png_name = export_result.get("png_name", "imagem.png")
        tif_name = export_result.get("tif_name", "imagem.tif")

        if png_path and Path(png_path).exists():
            with open(png_path, "rb") as f_png:
                st.download_button(
                    label="📥 Baixar PNG",
                    data=f_png.read(),
                    file_name=png_name,
                    mime="image/png",
                    key=f"download_png_{png_name}",
                    use_container_width=True,
                )
        else:
            st.warning("PNG não encontrado para download.")

        if tif_path and Path(tif_path).exists():
            with open(tif_path, "rb") as f_tif:
                st.download_button(
                    label="📥 Baixar TIFF georreferenciado",
                    data=f_tif.read(),
                    file_name=tif_name,
                    mime="image/tiff",
                    key=f"download_tif_{tif_name}",
                    use_container_width=True,
                )
        else:
            st.warning("TIFF georreferenciado não encontrado para download.")
