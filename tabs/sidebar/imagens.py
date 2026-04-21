# -*- coding: utf-8 -*-
import streamlit as st

from services.gee_catalog import get_available_visual_products


def _touch_image_nonce():
    st.session_state["image_selection_nonce"] = st.session_state.get("image_selection_nonce", 0) + 1


def _get_product_options_for_satellite(satellite: str):
    return get_available_visual_products(satellite)


def _find_scene_by_id(available_images, selected_scene_id):
    if not available_images or not selected_scene_id:
        return None
    return next(
        (
            img
            for img in available_images
            if img.get("id") == selected_scene_id or img.get("asset_id") == selected_scene_id
        ),
        None,
    )


def _sync_current_image_selection(selected_scene_id, selected_product_name):
    previous_scene_id = st.session_state.get("selected_scene_id")
    previous_product_name = st.session_state.get("selected_product_name")

    st.session_state["selected_scene_id"] = selected_scene_id
    st.session_state["selected_product_name"] = selected_product_name

    if previous_scene_id != selected_scene_id or previous_product_name != selected_product_name:
        _touch_image_nonce()


def _prepare_scene_widget_state(available_images, image_options, labels, reset_for_new_query):
    selected_scene_mem = None if reset_for_new_query else _find_scene_by_id(
        available_images,
        st.session_state.get("selected_scene_id"),
    )
    default_label = next(
        (label for label, img in image_options.items() if img == selected_scene_mem),
        labels[0],
    )

    current_label = None if reset_for_new_query else st.session_state.get("sb_selected_scene_label")
    if current_label not in image_options:
        current_label = default_label
        st.session_state["sb_selected_scene_label"] = current_label

    return current_label, image_options.get(current_label) or image_options[default_label]


def _prepare_product_widget_state(scene_preview, reset_for_new_query):
    fixed_product_name = scene_preview.get("fixed_product_name")
    if fixed_product_name:
        return fixed_product_name, None

    product_options = _get_product_options_for_satellite(scene_preview.get("satellite"))
    pending_product = st.session_state.pop("_pending_product_widget_value", None)
    current_product = pending_product

    if current_product not in product_options:
        current_product = None if reset_for_new_query else st.session_state.get("sb_selected_product_name")

    if current_product not in product_options:
        selected_product_mem = None if reset_for_new_query else st.session_state.get("selected_product_name")
        current_product = selected_product_mem if selected_product_mem in product_options else product_options[0]

    st.session_state["sb_selected_product_name"] = current_product
    return current_product, product_options


def _resolve_product_for_scene(scene, requested_product_name):
    fixed_product_name = scene.get("fixed_product_name")
    if fixed_product_name:
        return fixed_product_name, False

    product_options = _get_product_options_for_satellite(scene.get("satellite"))
    if requested_product_name in product_options:
        return requested_product_name, False

    fallback_product = product_options[0]
    return fallback_product, True


def _handle_product_change(selected_scene, selected_product_name):
    effective_product_name, _ = _resolve_product_for_scene(selected_scene, selected_product_name)
    _sync_current_image_selection(selected_scene.get("id"), effective_product_name)
    return effective_product_name


def _handle_scene_change(selected_scene, selected_product_name):
    effective_product_name, requires_product_refresh = _resolve_product_for_scene(
        selected_scene,
        selected_product_name,
    )
    _sync_current_image_selection(selected_scene.get("id"), effective_product_name)

    if requires_product_refresh:
        st.session_state["_pending_product_widget_value"] = effective_product_name
        st.rerun()

    return effective_product_name


def render_sidebar_imagens(available_images=None):
    if available_images is None:
        available_images = []

    current_query_nonce = int(st.session_state.get("query_result_nonce", 0))
    initialized_query_nonce = st.session_state.get("_image_selection_initialized_query_nonce")
    reset_for_new_query = initialized_query_nonce != current_query_nonce

    selected_scene_id = None
    selected_product_name = None

    if available_images:
        image_options = {img["label"]: img for img in available_images}
        labels = list(image_options.keys())

        current_label, scene_preview = _prepare_scene_widget_state(
            available_images,
            image_options,
            labels,
            reset_for_new_query,
        )

        preview_scene_id = scene_preview.get("id")
        initial_product_name, product_options = _prepare_product_widget_state(
            scene_preview,
            reset_for_new_query,
        )

        st.markdown("### Tipo de imagem")
        if product_options is None:
            selected_product_name = initial_product_name
            st.caption(f"Tipo definido pela cena selecionada: {selected_product_name}")
        else:
            selected_product_name = st.radio(
                "Selecione o tipo de imagem",
                options=product_options,
                index=product_options.index(initial_product_name),
                key="sb_selected_product_name",
            )

        st.markdown("---")
        st.markdown("### Imagens disponiveis")
        selected_label = st.radio(
            "Selecione uma cena",
            options=labels,
            index=labels.index(current_label),
            key="sb_selected_scene_label",
        )

        selected_scene = image_options.get(selected_label) or scene_preview
        selected_scene_id = selected_scene.get("id")

        if selected_scene_id != preview_scene_id:
            selected_product_name = _handle_scene_change(selected_scene, selected_product_name)
        else:
            selected_product_name = _handle_product_change(selected_scene, selected_product_name)

        st.session_state["_image_selection_initialized_query_nonce"] = current_query_nonce
    else:
        st.session_state["selected_scene_id"] = None
        st.session_state["selected_product_name"] = None
        st.session_state["sb_selected_scene_label"] = None
        st.session_state["sb_selected_product_name"] = None
        st.session_state["_image_selection_initialized_query_nonce"] = current_query_nonce
        st.markdown("### Tipo de imagem")
        st.caption("Nenhuma cena disponivel para definir o tipo de imagem.")
        st.markdown("---")
        st.markdown("### Imagens disponiveis")
        st.caption("Nenhuma cena listada para a area e periodo atuais.")

    return {
        "available_images": available_images,
        "selected_scene_id": selected_scene_id,
        "selected_product_name": selected_product_name,
    }
