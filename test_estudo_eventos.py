"""Testes do estudo de eventos, com séries sintéticas. Não tocam na rede."""

import json
from datetime import date, timedelta

import pytest

import estudo_eventos as E

D0 = date(2025, 10, 6)  # uma segunda-feira


def serie(n_dias, f, inicio=D0):
    return {inicio + timedelta(days=i): f(inicio + timedelta(days=i)) for i in range(n_dias)}


def test_roi_desconta_a_taxa_e_cresce_com_a_venda():
    assert E.roi_liquido(100, 100) == pytest.approx(-0.05)
    assert E.roi_liquido(100, 110) == pytest.approx(0.045)
    assert E.roi_liquido(100, 120) > E.roi_liquido(100, 110) > E.roi_liquido(100, 100)


def test_roi_evento_usa_o_preco_do_dia_certo():
    # O preço é o número do dia: comprar em E-3 e vender em E+2 dá 5 dias de
    # diferença, e nada de dias vizinhos.
    s = serie(40, lambda d: (d - D0).days + 100)
    e = D0 + timedelta(days=20)
    assert E.roi_evento([s], e, 3, 2) == pytest.approx(0.95 * 122 / 117 - 1)
    assert E.roi_evento([s], e, 3, -1) == pytest.approx(0.95 * 119 / 117 - 1)


def test_roi_evento_e_a_mediana_entre_cartas_e_ignora_cartas_sem_dados():
    e = D0 + timedelta(days=10)
    planas = [serie(30, lambda d: 100) for _ in range(2)]
    sobe = serie(30, lambda d: 200 if d >= e else 100)
    vazia = {}
    assert E.roi_evento(planas + [sobe, vazia], e, 1, 0) == pytest.approx(-0.05)


def test_tabela_so_tem_vendas_depois_da_compra():
    t = E.tabela([serie(30, lambda d: 100)], [{"data": D0 + timedelta(days=15)}],
                 ks=[1, 2], hs=[-2, -1, 0])
    assert set(t) == {(2, -1), (1, 0), (2, 0)}


def test_validacao_escolhe_so_com_os_eventos_de_treino():
    # Nos eventos de treino o preço salta no próprio dia (h=0 é o melhor);
    # nos de teste salta 7 dias depois (h=7). Escolhendo com todos os eventos
    # ganhava h=7; escolhendo só com o treino tem de ganhar h=0.
    treino = [D0 + timedelta(days=20), D0 + timedelta(days=40)]
    teste = [D0 + timedelta(days=60), D0 + timedelta(days=80), D0 + timedelta(days=100)]

    def preco(d):
        if d in treino:
            return 200
        if d in [t + timedelta(days=7) for t in teste]:
            return 400
        return 100

    s = [serie(130, preco)]
    eventos = [{"data": d} for d in teste + treino]  # fora de ordem de propósito
    assert E.melhor_janela(s, eventos, ks=[1], hs=[0, 7]) == (1, 7)
    (k, h), no_treino, no_teste = E.validar(s, eventos, 2, ks=[1], hs=[0, 7])
    assert (k, h) == (1, 0)
    assert no_treino == pytest.approx(0.95 * 2 - 1)
    assert no_teste == [pytest.approx(-0.05)] * 3


def test_referencia_e_a_janela_de_um_dia_qualquer():
    s = serie(60, lambda d: 100)
    assert E.roi_referencia([s], 4, D0, D0 + timedelta(days=59)) == pytest.approx(-0.05)


def test_ciclo_semanal_encontra_domingo_para_quarta():
    # Domingo barato, quarta cara, o resto no meio.
    precos = {6: 100, 2: 130}
    s = serie(70, lambda d: precos.get(d.weekday(), 110))
    c = E.ciclo_semanal([s], D0, D0 + timedelta(days=69))
    melhor = max(c, key=lambda k: c[k][0])
    assert melhor == (6, 2)
    assert c[(6, 2)][0] == pytest.approx(0.95 * 130 / 100 - 1)
    assert c[(2, 6)][0] == pytest.approx(0.95 * 100 / 130 - 1)


def test_ler_serie_converte_milissegundos_e_tira_precos_zero(tmp_path):
    f = tmp_path / "h.json"
    f.write_text(json.dumps({"prices": [
        {"timestamp": 1758153600000, "price": 900},   # 2025-09-18
        {"timestamp": 1758240000000, "price": 0},
    ]}), encoding="utf-8")
    assert E.ler_serie(f) == {date(2025, 9, 18): 900}
