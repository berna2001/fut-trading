"""Testes do gerador do relatório do FC 26, com séries sintéticas.

O relatorio_eventos.py não tinha nenhum teste (revisão independente de
01/10/2026): as mutações "escolher o ciclo com a época inteira", "meter o 83
no fodder" e "semanas de terça a segunda" sobreviviam todas. Cada teste aqui
monta um mercado em que a resposta certa se sabe à partida.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest

import estudo_eventos as E
import relatorio_eventos as R

DIAS_TODOS = [R.INICIO - timedelta(days=40) + timedelta(days=i)
              for i in range((R.FIM - R.INICIO).days + 60)]
EVENTOS = E.ler_eventos(Path(__file__).with_name("eventos_fc26.csv"))


def serie(f):
    return {d: f(d) for d in DIAS_TODOS}


def mercado(f, por_rating=2, f83=None, n83=2):
    """{rating: [séries]} com o mesmo padrão em 84-87 e outro no 83."""
    m = {r: [serie(f) for _ in range(por_rating)] for r in (84, 85, 86, 87)}
    m[83] = [serie(f83 or f) for _ in range(n83)]
    return m


# 1.ª metade: sábado barato, quarta cara. 2.ª metade: domingo barato, quinta
# cara, com mais força. Na época inteira ganharia domingo → quinta; escolhendo
# só na 1.ª metade, tem de ganhar sábado → quarta.
def troca_a_meio(d):
    if d < R.CORTE:
        return {5: 850, 2: 1150}.get(d.weekday(), 1000)
    return {6: 700, 3: 1400}.get(d.weekday(), 1000)


def test_a_regra_escolhe_se_so_na_primeira_metade():
    texto, numeros = R.construir(mercado(troca_a_meio), EVENTOS)
    assert "Escolhida: **comprar sáb, vender qua**" in texto
    # Na 2.ª metade, sábado e quarta valem o mesmo: a regra perde a taxa.
    assert numeros["fora_da_amostra"]["5"]["mediana"] == pytest.approx(-0.05)
    # Só as semanas da 2.ª metade, e nenhuma positiva (a 1.ª metade tinha
    # todas positivas; se entrasse, apareciam aqui).
    fodder = [s for r in (84, 85, 86, 87) for s in mercado(troca_a_meio)[r]]
    assert numeros["fora_da_amostra"]["5"]["n"] == len(R.semanas(fodder, 5, 4, R.CORTE, R.FIM))
    assert numeros["fora_da_amostra"]["5"]["positivas"] == 0
    # E domingo → quarta mede o domingo barato da 2.ª metade.
    assert numeros["fora_da_amostra"]["6"]["mediana"] == pytest.approx(0.95 * 1000 / 700 - 1)


def test_o_83_nao_entra_nos_numeros_do_fodder():
    plano = lambda d: 1000
    louco = lambda d: 3000 if d.weekday() == 2 else 500
    _, so_fodder = R.construir(mercado(plano), EVENTOS)
    _, com_83 = R.construir(mercado(plano, f83=louco, n83=20), EVENTOS)
    assert com_83["fora_da_amostra"] == so_fodder["fora_da_amostra"]
    assert com_83["perfil_semanal"] == so_fodder["perfil_semanal"]


def test_perfil_usa_semanas_de_segunda_a_domingo():
    # Tendência pura, sem efeito de dia: numa semana de segunda a domingo, a
    # segunda é o dia mais baixo face à média da semana e o domingo o mais alto.
    inicio = DIAS_TODOS[0]
    p = R.perfil_semanal([serie(lambda d: 1000 + (d - inicio).days)], R.INICIO, R.FIM)
    assert min(p, key=p.get) == 0 and max(p, key=p.get) == 6
    assert p[0] == pytest.approx(-p[6], rel=0.01)


def test_perfil_etiqueta_pelo_dia_da_semana_verdadeiro():
    # Domingo barato, quarta cara, sem tendência: as etiquetas têm de cair
    # nesses dias seja qual for o dia em que a janela começa.
    s = serie(lambda d: {6: 900, 2: 1100}.get(d.weekday(), 1000))
    for inicio in (R.INICIO, R.INICIO + timedelta(days=1), R.INICIO + timedelta(days=4)):
        p = R.perfil_semanal([s], inicio, R.FIM)
        assert min(p, key=p.get) == 6 and max(p, key=p.get) == 2


def test_custo_de_segurar_separa_semanas_de_promo_das_outras():
    # Quinta (véspera) a 1100 e sábado a 700 nas semanas de promo; quarta a
    # 1000, para que comparar com a quarta em vez da quinta dê outro número.
    sabados_promo = {e["data"] + timedelta(days=1) for e in EVENTOS}
    quintas_promo = {e["data"] - timedelta(days=1) for e in EVENTOS}
    cai = lambda d: 700 if d in sabados_promo else 1100 if d in quintas_promo else 1000
    _, numeros = R.construir(mercado(cai), EVENTOS)
    sextas = [R.INICIO + timedelta(days=(4 - R.INICIO.weekday()) % 7 + 7 * i) for i in range(60)]
    normais = [f for f in sextas if f + timedelta(days=1) <= R.FIM
               and f not in {e["data"] for e in EVENTOS}]
    for r in ("85", "86", "87"):
        s = numeros["segurar_depois_da_promo"][r]
        assert s["promo_media"] == pytest.approx(700 / 1100 - 1)
        assert s["promo_pior"] == pytest.approx(700 / 1100 - 1)
        assert s["normal_mediana"] == pytest.approx(0.0)
        assert s["promo_n"] == len(EVENTOS)
        assert s["normal_n"] == len(normais)


def test_fracao_no_minimo():
    assert R.fracao_no_minimo([serie(lambda d: 750)], R.INICIO, R.FIM) == 1.0
    # Metade dos dias no mínimo, metade 50% acima.
    alterna = serie(lambda d: 750 if d.toordinal() % 2 else 1125)
    assert R.fracao_no_minimo([alterna], R.INICIO, R.FIM) == pytest.approx(0.5, abs=0.01)
    _, numeros = R.construir(mercado(lambda d: 1000, f83=lambda d: 750), EVENTOS)
    assert numeros["fracao_no_minimo"]["83"] == [1.0, 1.0]


def test_aparada_tira_as_pontas():
    # Assimétrico de propósito: com pontas simétricas a média não muda.
    v = [0.0] * 8 + [0.5, 1.0]
    assert R.aparada(v) == pytest.approx(0.5 / 8)
    assert R.aparada([0.01, 0.02, 0.03]) == pytest.approx(0.02)


def test_relatorio_tem_a_sensibilidade_com_todos_os_cortes():
    texto, _ = R.construir(mercado(troca_a_meio), EVENTOS)
    for corte in R.CORTES_SENSIBILIDADE:
        assert f"| {corte:%d/%m/%Y} |" in texto


def test_semanas_conta_a_ultima_janela_que_acaba_no_fim():
    # Sábado → quarta: a última janela que cabe acaba exactamente em FIM?
    fim = date(2026, 9, 9)  # uma quarta
    v = R.semanas([serie(lambda d: 1000)], 5, 4, date(2026, 8, 1), fim)
    assert len(v) == 6  # sábados de 01/08 a 05/09
