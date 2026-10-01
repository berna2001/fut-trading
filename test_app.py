"""Testes da app: corre-a de verdade com o AppTest do Streamlit, sem servidor.

Exercita cada aba, e por isso também as dependências que ela usa por baixo.
No bet, uma dependência usada só indirectamente pelo pandas saiu do
requirements.txt e a app rebentou em produção sem nenhum teste dar por isso.
"""

from pathlib import Path

import pytest

# Import directo e não pytest.importorskip: sem o streamlit no
# requirements.txt, a CI tem de FALHAR aqui, não saltar os testes em silêncio.
import streamlit.testing.v1 as st_testing

APP = str(Path(__file__).with_name("app.py"))


def correr():
    at = st_testing.AppTest.from_file(APP, default_timeout=30)
    at.run()
    return at


def test_app_corre_sem_excepcoes_e_tem_as_quatro_abas():
    at = correr()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Conselheiro", "Notícias", "Calculadora", "Estudos"]


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


def test_conselheiro_da_uma_accao_de_mercado_e_a_regra_de_evitar():
    at = correr()
    caixas = [c.value for grupo in (at.success, at.warning, at.info, at.error) for c in grupo]
    accoes = {"COMPRAR", "VENDER", "ESPERAR"}
    assert sum(any(f"**{a} —" in c for a in accoes) for c in caixas) == 1
    assert any("**EVITAR — Ratings cujo fodder está no preço mínimo" in c for c in caixas)
    # O plano da semana tem os sete dias.
    assert len(at.table[0].value) == 7


ESTRAGADOS = {
    "vazio": "",
    "sem_categoria": "id,publicado_em,titulo,link\n1,2026-10-01T10:00:00+00:00,x,y\n",
    "data_invalida": "id,publicado_em,visto_em,fonte,categoria,titulo,link\n"
                     "1,ontem,ontem,f,leak,x,y\n",
}


@pytest.mark.parametrize("caso", list(ESTRAGADOS))
def test_noticias_estragadas_nao_levam_as_outras_abas(caso, tmp_path, monkeypatch):
    # Revisão de 01/10/2026: com estes três ficheiros a app inteira parava no
    # primeiro separador e a calculadora ficava sem métricas.
    f = tmp_path / "noticias.csv"
    f.write_text(ESTRAGADOS[caso], encoding="utf-8")
    monkeypatch.setenv("FUT_NOTICIAS", str(f))
    at = correr()
    assert not at.exception
    # Calculadora intacta.
    assert len(at.metric) == 4
    # Conselheiro intacto: dá a acção do dia e avisa que as notícias falharam.
    caixas = [c.value for grupo in (at.success, at.warning, at.info, at.error) for c in grupo]
    assert sum(any(f"**{a} —" in c for a in ("COMPRAR", "VENDER", "ESPERAR")) for c in caixas) == 1
    assert any("Não consegui ler as notícias" in w.value for w in at.warning)
    # Só a aba das notícias mostra o erro; os estudos continuam lá.
    assert sum("Esta aba falhou" in e.value for e in at.error) == 1
    assert len(at.expander) > 0


SABADO = "2026-11-07T12:00:00+00:00"   # depois do lançamento


def test_sabado_a_app_mostra_a_quantia_do_conselheiro(monkeypatch, tmp_path):
    import conselheiro as K
    from datetime import datetime

    vazio = tmp_path / "n.csv"
    vazio.write_text("id,publicado_em,visto_em,fonte,categoria,titulo,link\n", encoding="utf-8")
    monkeypatch.setenv("FUT_NOTICIAS", str(vazio))
    monkeypatch.setenv("FUT_AGORA", SABADO)
    at = correr()
    entradas = {n.label: n for n in at.number_input}
    entradas["Saldo actual (coins)"].set_value(50_000)
    entradas["Já investido neste ciclo (coins)"].set_value(10_000).run()
    assert any("sábado, 07/11" in h.value for h in at.subheader)
    compra = next(c.value for c in at.success if "**COMPRAR —" in c.value)
    q = K.quantias(50_000, 10_000, datetime.fromisoformat(SABADO))
    for r, v in q.items():
        assert f"{v:,.0f} em {r}" in compra
    assert f"total {sum(q.values()):,.0f}" in compra


def test_noticia_de_promo_recente_aparece_no_conselheiro(monkeypatch, tmp_path):
    f = tmp_path / "n.csv"
    f.write_text("id,publicado_em,visto_em,fonte,categoria,titulo,link\n"
                 "a,2026-11-05T10:00:00+00:00,2026-11-05T10:00:00+00:00,x,leak,"
                 "Promo Teste leaked,https://x\n", encoding="utf-8")
    monkeypatch.setenv("FUT_NOTICIAS", str(f))
    monkeypatch.setenv("FUT_AGORA", SABADO)
    at = correr()
    assert any("Promo Teste leaked" in c.value for c in at.info)


def test_plano_so_tem_roi_nos_dias_de_compra(monkeypatch):
    import conselheiro as K

    monkeypatch.setenv("FUT_AGORA", SABADO)
    at = correr()
    plano = at.table[0].value
    roi = dict(zip(plano["dia"], plano["comprar hoje, vender quarta"]))
    for dia in ("quarta", "quinta", "sexta"):
        assert roi[dia] == "—"
    assert roi["sábado"] == K.pct(K.FORA_DA_AMOSTRA[5]["mediana"])
