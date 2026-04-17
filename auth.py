# -*- coding: utf-8 -*-
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def load_config():
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("config.yaml não encontrado.")
        st.stop()



def setup_authentication():
    config = load_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    authenticator.login(location="sidebar")

    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    return authenticator, name, authentication_status, username



def get_user_role():
    config = load_config()
    username = st.session_state.get("username")
    if username and username in config["credentials"]["usernames"]:
        return config["credentials"]["usernames"][username].get("role", "user")
    return "user"
