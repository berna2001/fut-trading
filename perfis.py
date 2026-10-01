"""Perfis de preço por hora do dia e por dia da semana, a partir de séries
horárias ({datetime UTC: preço}).

Cada preço compara-se com a média de uma janela centrada nele (24 horas
para a hora do dia, 7 dias para o dia da semana). Assim a tendência do
mercado não se confunde com o perfil: numa semana de queda, segunda seria
sempre "cara" só por vir antes, e a janela centrada tira isso.
"""

import statistics as st
from datetime import timedelta


def perfil_horario(series):
    """{hora UTC: desvio mediano face à média das 24 h centradas}."""
    desvios = {h: [] for h in range(24)}
    for s in series:
        for t, p in s.items():
            janela = [s.get(t + timedelta(hours=k)) for k in range(-12, 12)]
            if all(janela):
                desvios[t.hour].append(p / st.mean(janela) - 1)
    return {h: st.median(v) for h, v in desvios.items() if v}


def medias_diarias(serie, min_horas=20):
    """{date: média do dia}, só para dias com pelo menos min_horas pontos."""
    por_dia = {}
    for t, p in serie.items():
        por_dia.setdefault(t.date(), []).append(p)
    return {d: st.mean(v) for d, v in por_dia.items() if len(v) >= min_horas}


def perfil_semanal(series):
    """{dia da semana: (desvio mediano face aos 7 dias centrados, n)}."""
    desvios = {d: [] for d in range(7)}
    for s in series:
        dm = medias_diarias(s)
        for d, p in dm.items():
            janela = [dm.get(d + timedelta(days=k)) for k in range(-3, 4)]
            if all(janela):
                desvios[d.weekday()].append(p / st.mean(janela) - 1)
    return {d: (st.median(v), len(v)) for d, v in desvios.items() if v}
