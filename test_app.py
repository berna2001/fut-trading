"""Testes da app: corre-a de verdade com o AppTest do Streamlit, sem servidor.

Exercita cada aba, e por isso também as dependências que ela usa por baixo.
No bet, uma dependência usada só indirectamente pelo pandas saiu do
requirements.txt e a app rebentou em produção sem nenhum teste dar por isso.
"""

from pathlib import Path

# Import directo e não pytest.importorskip: sem o streamlit no
# requirements.txt, a CI tem de FALHAR aqui, não saltar os testes em silêncio.
import streamlit.testing.v1 as st_testing

APP = str(Path(__file__).with_name("app.py"))


def correr():
    at = st_testing.AppTest.from_file(APP, default_timeout=30)
    at.run()
    return at


def test_app_corre_sem_excepcoes_e_tem_as_tres_abas():
    at = correr()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Notícias", "Calculadora", "Estudos"]


def test_noticias_aparecem_e_o_filtro_as_reduz():
    at = correr()
    todas = [m.value for m in at.markdown if "](" in m.value and "·" in m.value]
    assert todas, "nenhuma notícia mostrada"
    at.multiselect[0].set_value(["leak"]).run()
    so_leaks = [m.value for m in at.markdown if "](" in m.value and "·" in m.value]
    assert 0 < len(so_leaks) < len(todas)
    assert all(m.startswith("**Leak**") for m in so_leaks)


def test_calculadora_mostra_o_resultado_da_operacao():
    at = correr()
    # Por omissão: comprar 10 a 4000 e vender a 4500.
    metricas = {m.label: m.value for m in at.metric}
    assert metricas["Investido"] == "40,000"
    assert metricas["Recebido (−5%)"] == "42,750"
    assert metricas["Lucro"] == "+2,750"
    assert metricas["ROI"] == "+6.9%"
    # Vender ao preço de compra perde a taxa.
    entradas = {n.label: n for n in at.number_input}
    entradas["Preço de venda"].set_value(4000).run()
    assert {m.label: m.value for m in at.metric}["ROI"] == "-5.0%"


def test_saldo_limita_a_quantidade_sugerida():
    at = correr()
    entradas = {n.label: n for n in at.number_input}
    entradas["Saldo actual (coins)"].set_value(20_000).run()
    entradas = {n.label: n for n in at.number_input}
    assert "Cabem 5 no saldo actual." in entradas["Quantidade"].help


def test_estudos_tem_um_bloco_por_relatorio():
    at = correr()
    relatorios = list(Path(__file__).with_name("estudos").glob("*.md"))
    assert len(at.expander) == len(relatorios) > 0
