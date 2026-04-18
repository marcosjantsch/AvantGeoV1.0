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


def _get_default_scene(available_images, selected_scene_id_mem):
    if not available_images:
        return None

    if selected_scene_id_mem:
        selected_scene = next(
            (img for img in available_images if img.get("id") == selected_scene_id_mem),
            None,
        )
        if selected_scene is not None:
            return selected_scene

    return available_images[0]


def render_sidebar_imagens(available_images=None):
    if available_images is None:
        available_images = []

    selected_scene_id_mem = st.session_state.get("selected_scene_id")
    selected_product_mem = st.session_state.get("selected_product_name")

    selected_scene_id = None
    selected_product_name = None

    st.markdown("### Tipo de imagem")

    if available_images:
        selected_scene = _get_default_scene(available_images, selected_scene_id_mem)
        product_options = _get_product_options_for_satellite(selected_scene.get("satellite"))

        current_product = st.session_state.get("sb_selected_product_name")
        if current_product not in product_options:
            current_product = (
                selected_product_mem if selected_product_mem in product_options else product_options[0]
            )
            st.session_state["sb_selected_product_name"] = current_product

        selected_product_name = st.radio(
            "Selecione o tipo de imagem",
            options=product_options,
            index=product_options.index(current_product),
            key="sb_selected_product_name",
        )
    else:
        st.session_state["sb_selected_scene_label"] = None
        st.session_state["sb_selected_product_name"] = None
        st.caption("Nenhuma cena disponivel para definir o tipo de imagem.")

    st.markdown("---")
    st.markdown("### Imagens disponiveis")

    if available_images:
        image_options = {img["label"]: img for img in available_images}
        labels = list(image_options.keys())

        default_label = labels[0]
        if selected_scene_id_mem:
            matched_label = next(
                (label for label, img in image_options.items() if img.get("id") == selected_scene_id_mem),
                None,
            )
            if matched_label is not None:
                default_label = matched_label

        current_label = st.session_state.get("sb_selected_scene_label")
        if current_label not in image_options:
            current_label = default_label
            st.session_state["sb_selected_scene_label"] = current_label

        selected_label = st.radio(
            "Selecione uma cena",
            options=labels,
            index=labels.index(current_label),
            key="sb_selected_scene_label",
        )

        selected_scene = image_options.get(selected_label) or image_options[default_label]
        selected_scene_id = selected_scene.get("id")

        if not selected_product_name:
            product_options = _get_product_options_for_satellite(selected_scene.get("satellite"))
            selected_product_name = (
                selected_product_mem if selected_product_mem in product_options else product_options[0]
            )
    else:
        st.caption("Nenhuma cena listada para a area e periodo atuais.")

    return {
        "available_images": available_images,
        "selected_scene_id": selected_scene_id,
        "selected_product_name": selected_product_name,
    }
