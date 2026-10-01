"""Configuração comum dos testes."""

import pytest


@pytest.fixture(autouse=True)
def sem_rede_nem_cache(monkeypatch):
    # A app lê os RSS ao vivo. Nos testes nunca: um teste que vai à rede
    # depende de sites alheios e falha quando eles falham. O teste do caminho
    # ao vivo liga-o de propósito, com as fontes simuladas.
    monkeypatch.setenv("FUT_AO_VIVO", "0")
    # A cache do Streamlit vive no processo e passava de um teste para o
    # seguinte.
    import streamlit as st
    st.cache_data.clear()
    yield
