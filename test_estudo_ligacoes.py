"""Testes da H4 (química), com dados sintéticos."""

from datetime import date, timedelta

import pytest

import estudo_ligacoes as L

NOMES = {("nation", "54"): "Brazil", ("nation", "38"): "Portugal",
         ("league", "53"): "LALIGA EA SPORTS", ("league", "31"): "Serie A Enilive"}


def carta_nova(dia, nacao="54", liga="53"):
    return {"saiu_em": f"{dia:%Y-%m-%d}T17:00:00Z", "nacao_id": nacao, "liga_id": liga}


def test_dias_de_promo_so_com_dez_ou_mais_cartas_e_em_hora_de_londres():
    d = date(2025, 10, 24)
    cartas = [carta_nova(d)] * 10 + [carta_nova(d + timedelta(days=7))] * 9
    # A 24/10/2025 Londres ainda estava em hora de Verão (UTC+1): 23:30 UTC
    # é 00:30 de 25/10, outro dia.
    tarde = {"saiu_em": "2025-10-24T23:30:00Z", "nacao_id": "54", "liga_id": "53"}
    dias = L.dias_de_promo(cartas + [tarde])
    assert list(dias) == [d]
    assert L.dia_em_londres(tarde["saiu_em"]) == date(2025, 10, 25)


def test_fortes_precisa_de_tres_cartas():
    cartas = [carta_nova(date(2025, 1, 1), "54", "53")] * 3 + [carta_nova(date(2025, 1, 1), "38", "31")] * 2
    assert L.fortes(cartas, "nacao_id", NOMES, "nation") == {"brazil"}
    assert L.fortes(cartas, "liga_id", NOMES, "league") == {"laligaeasports"}


def test_ligada_por_nacao_ou_liga_e_alias_so_quando_pedido():
    nac, lig = {"brazil"}, {"serieaenilive"}
    assert L.esta_ligada({"nation": "Brazil", "league": "Premier League"}, nac, lig)
    italiana = {"nation": "Italy", "league": "Serie A TIM"}
    assert not L.esta_ligada(italiana, nac, lig)                       # plano: só nome
    assert L.esta_ligada(italiana, nac, lig, L.ALIAS_LIGAS)             # secundária
    assert L.normalizar("Côte d'Ivoire") == "cotedivoire"


def _serie(f, inicio=date(2025, 9, 1), dias=400):
    return {inicio + timedelta(days=i): f(inicio + timedelta(days=i)) for i in range(dias)}


def test_efeito_e_ligadas_menos_nao_ligadas_nas_mesmas_datas():
    d = date(2025, 10, 24)
    promos = {d: [carta_nova(d, "54", "53")] * 10}
    sobe = _serie(lambda x: 120 if x >= d else 100)       # ligada: +20% no dia
    plano = _serie(lambda x: 100)
    fodder = [({"nation": "Brazil", "league": "Ligue 1"}, sobe),
              ({"nation": "Italy", "league": "Ligue 1"}, plano)]
    (dia, efeito, nl, nn), = L.efeitos(fodder, promos, NOMES, 1, 3)
    assert dia == d and nl == 1 and nn == 1
    assert efeito == pytest.approx((0.95 * 120 / 100 - 1) - (0.95 - 1))


def test_dia_sem_ligadas_sai():
    d = date(2025, 10, 24)
    promos = {d: [carta_nova(d, "54", "53")] * 10}
    fodder = [({"nation": "Italy", "league": "Ligue 1"}, _serie(lambda x: 100))]
    assert L.efeitos(fodder, promos, NOMES, 1, 3) == []


def test_passa_exige_as_duas_metades():
    d0 = date(2026, 1, 1)
    def dias(vals):
        return [(d0 + timedelta(days=i), v, 1, 1) for i, v in enumerate(vals)]
    assert L.passa(dias([0.02, 0.03, 0.01, 0.02, 0.04, 0.01]))[0]
    # A 1.ª metade positiva e a 2.ª negativa: não passa.
    assert not L.passa(dias([0.02, 0.03, 0.01, -0.02, -0.04, 0.01]))[0]
    # Mediana positiva mas só metade dos dias positivos: não passa.
    assert not L.passa(dias([0.05, -0.01, 0.05, -0.01, 0.05, -0.01, 0.05, -0.01]))[0]
    assert not L.passa(dias([0.1, 0.1, 0.1]))[0]          # menos de 4 dias


def test_dia_sem_controlo_sai():
    # Todas as cartas ligadas: não há com que comparar, o dia não conta.
    d = date(2025, 10, 24)
    promos = {d: [carta_nova(d, "54", "53")] * 10}
    fodder = [({"nation": "Brazil", "league": "Ligue 1"}, _serie(lambda x: 100))]
    assert L.efeitos(fodder, promos, NOMES, 1, 3) == []
