"""Testes da escolha de cartas e dos pedidos das descargas. Sem rede."""

import pytest

import descarregar_fc26 as D26
import descarregar_fc27 as D27


def carta(i, preco, versao="Normal"):
    return {"id": str(i), "name": f"c{i}", "version": versao, "price_pc_coins": preco}


# Como as 86 do FC 27 a 01/10/2026: caras primeiro na ordem do site.
PAGINA = [
    carta(1, 61_500), carta(2, 0), carta(3, 21_750), carta(4, 3_800),
    carta(5, 3_900, "TOTW"), carta(6, 13_000), carta(7, 3_900), carta(8, 4_300),
]


def test_fodder_sao_as_mais_baratas_transaccionaveis():
    escolhidas = D26.escolher_fodder(PAGINA, 3)
    assert [c["id"] for c in escolhidas] == ["4", "7", "8"]


def test_fodder_ignora_preco_zero_e_cartas_que_nao_sao_gold_rare():
    ids = {c["id"] for c in D26.escolher_fodder(PAGINA, 10)}
    assert "2" not in ids          # preço 0
    assert "5" not in ids          # TOTW
    assert len(ids) == 6


def test_selecao_do_estudo_mantem_a_ordem_do_site():
    # Os relatórios reproduzem os estudos já feitos com as cartas em cache:
    # a ordem tem de continuar a do site, não a do preço.
    assert [c["id"] for c in D26.escolher_como_no_estudo(PAGINA, 3)] == ["1", "3", "4"]


def test_lista_fodder_pede_ao_site_por_preco_de_pc(monkeypatch, tmp_path):
    pedidos = []

    def chamar(endpoint, **params):
        pedidos.append((endpoint, params))
        return {"results": PAGINA}

    monkeypatch.setattr(D27, "PASTA", tmp_path)
    monkeypatch.setattr(D27.P, "chamar", chamar)
    escolhidas = D27.fodder(86, 2)
    endpoint, params = pedidos[0]
    assert endpoint == "get_players_by_rating"
    assert params["sort_by_price"] == "asc" and params["platform"] == "pc"
    assert params["year"] == "27" and params["version"] == "gold_rare"
    assert params["min_rating"] == params["max_rating"] == 86
    assert [c["id"] for c in escolhidas] == ["4", "7"]
    # Segunda vez vem da cache: não paga outra vez.
    D27.fodder(86, 2)
    assert len(pedidos) == 1
