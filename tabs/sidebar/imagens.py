# -*- coding: utf-8 -*-
import streamlit as st


def _get_product_options_for_satellite(satellite: str):
    if satellite == "Sentinel-2":
        return [
            "Imagem Sentinel RGB",
            "Imagem Sentinel RGB Ajustada",
            "NDVI",
            "NDWI",
            "EVI",
            "SAVI",
            "NBR",
            "MSI",
            "GNDVI",
        ]
    return ["RGB Landsat"]


def render_sidebar_imagens(available_images=None):
    if available_images is None:
        available_images = []

    selected_scene_id_mem = st.session_state.get("selected_scene_id")
    selected_product_mem = st.session_state.get("selected_product_name")

    selected_scene_id = None
    selected_product_name = None

    st.markdown("### Tipo de imagem")

    if available_images:
        if selected_scene_id_mem:
            selected_scene = next(
                (img for img in available_images if img.get("id") == selected_scene_id_mem),
                available_images[0],
            )
        else:
            selected_scene = available_images[0]

        product_options = _get_product_options_for_satellite(
            selected_scene.get("satellite")
        )

        default_product_index = (
            product_options.index(selected_product_mem)
            if selected_product_mem in product_options
            else 0
        )

        selected_product_name = st.radio(
            "Selecione o tipo de imagem",
            options=product_options,
            index=default_product_index,
            key="sb_selected_product_name",
        )
    else:
        st.caption("Nenhuma cena disponível para definir o tipo de imagem.")

    st.markdown("---")
    st.markdown("### Imagens disponíveis")

    if available_images:
        image_options = {img["label"]: img for img in available_images}
        labels = list(image_options.keys())

        default_index = 0
        if selected_scene_id_mem:
            for i, label in enumerate(labels):
                if image_options[label].get("id") == selected_scene_id_mem:
                    default_index = i
                    break

        selected_label = st.radio(
            "Selecione uma cena",
            options=labels,
            index=default_index,
            key="sb_selected_scene_label",
        )

        selected_scene = image_options[selected_label]
        selected_scene_id = selected_scene.get("id")

        if not selected_product_name:
            product_options = _get_product_options_for_satellite(
                selected_scene.get("satellite")
            )
            selected_product_name = (
                selected_product_mem
                if selected_product_mem in product_options
                else product_options[0]
            )
    else:
        st.caption("Nenhuma cena listada para a área e período atuais.")

    return {
        "available_images": available_images,
        "selected_scene_id": selected_scene_id,
        "selected_product_name": selected_product_name,
    }