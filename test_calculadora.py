"""Testes da calculadora de operações."""

import pytest

import calculadora as C


def test_vender_ao_preco_de_compra_perde_a_taxa():
    r = C.operacao(1000, 1000, 10)
    assert r["investido"] == 10000
    assert r["recebido"] == pytest.approx(9500)
    assert r["lucro"] == pytest.approx(-500)
    assert r["roi"] == pytest.approx(-0.05)


def test_preco_minimo_de_venda_da_lucro_zero():
    for compra in [650, 4000, 22000, 63000]:
        minimo = C.preco_minimo_venda(compra)
        assert minimo > compra
        assert C.operacao(compra, minimo, 3)["lucro"] == pytest.approx(0, abs=1e-6)


def test_lucro_cresce_com_a_venda_e_com_a_quantidade_quando_positivo():
    assert C.operacao(1000, 1200, 1)["lucro"] < C.operacao(1000, 1300, 1)["lucro"]
    assert C.operacao(1000, 1200, 2)["lucro"] == pytest.approx(2 * C.operacao(1000, 1200, 1)["lucro"])
    # O ROI não depende da quantidade.
    assert C.operacao(1000, 1200, 7)["roi"] == pytest.approx(C.operacao(1000, 1200, 1)["roi"])


def test_quantidade_maxima_arredonda_para_baixo_e_nao_rebenta():
    assert C.quantidade_maxima(100000, 4000) == 25
    assert C.quantidade_maxima(100000, 4001) == 24
    assert C.quantidade_maxima(3999, 4000) == 0
    assert C.quantidade_maxima(100000, 0) == 0


def test_operacao_sem_quantidade_tem_roi_zero():
    assert C.operacao(1000, 1200, 0)["roi"] == 0.0
