"""Estudo de eventos: como se mexe o fodder do PC à volta das promos grandes.

A estratégia avaliada é a mais simples possível: comprar no dia E-k e vender
no dia E+h, onde E é o dia em que a promo abre. O preço de cada dia é a média
diária do FUTBIN para o PC. O retorno é sempre líquido da taxa de 5%:

    roi = 0,95 × venda / compra − 1

Duas referências, e as duas têm de ser batidas:
  * ficar parado (roi = 0);
  * a mesma janela de k+h dias começada num dia qualquer da época. Se a
    estratégia não for melhor do que isso, o lucro vem da tendência do
    mercado, não do evento.

Fuga de informação: comprar k dias antes só é legítimo se a data do evento já
era pública nessa altura. As promos grandes têm data anunciada ou leaked com
uma a duas semanas de antecedência (o leak da Destined for Glory Team 2 saiu
4 dias antes), e por isso k fica limitado a 7. Não está medido evento a
evento para o FC 26.

Validação fora da amostra: a melhor janela (k, h) escolhe-se nos eventos da
primeira metade da época e avalia-se nos da segunda, que não entraram na
escolha.
"""

import csv
import json
import random
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TAXA = 0.05
KS = [1, 2, 3, 5, 7]          # dias de compra antes do evento
HS = [-1, 0, 1, 2, 3, 7]      # dias de venda depois (−1 = véspera)


def roi_liquido(compra, venda, taxa=TAXA):
    return (1 - taxa) * venda / compra - 1


def ler_serie(caminho):
    """{date: preço} de um ficheiro de histórico do parse.bot."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return {
        datetime.fromtimestamp(p["timestamp"] / 1000, timezone.utc).date(): int(p["price"])
        for p in dados.get("prices", [])
        if int(p["price"]) > 0
    }


def ler_eventos(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return [
            {**l, "data": date.fromisoformat(l["data"])}
            for l in csv.DictReader(f)
        ]


def roi_janela(serie, compra, venda):
    if compra not in serie or venda not in serie:
        return None
    return roi_liquido(serie[compra], serie[venda])


def roi_evento(series, dia_evento, k, h):
    """Mediana, entre cartas, do ROI de comprar em E-k e vender em E+h."""
    compra, venda = dia_evento - timedelta(days=k), dia_evento + timedelta(days=h)
    rois = [r for s in series for r in [roi_janela(s, compra, venda)] if r is not None]
    return statistics.median(rois) if rois else None


def roi_referencia(series, duracao, inicio, fim):
    """Mediana do ROI de uma janela de `duracao` dias começada em qualquer dia
    entre inicio e fim: o que se ganhava sem saber de evento nenhum."""
    rois = []
    dia = inicio
    while dia + timedelta(days=duracao) <= fim:
        r = roi_evento(series, dia, 0, duracao)
        if r is not None:
            rois.append(r)
        dia += timedelta(days=1)
    return statistics.median(rois) if rois else None


def tabela(series, eventos, ks=KS, hs=HS):
    """{(k, h): [roi por evento]} — só janelas com venda depois da compra."""
    return {
        (k, h): [roi_evento(series, e["data"], k, h) for e in eventos]
        for k in ks for h in hs if h > -k
    }


def media(valores):
    v = [x for x in valores if x is not None]
    return statistics.mean(v) if v else None


def melhor_janela(series, eventos_treino, ks=KS, hs=HS):
    """A janela (k, h) com maior ROI médio nos eventos de treino."""
    t = tabela(series, eventos_treino, ks, hs)
    candidatas = {kh: media(v) for kh, v in t.items() if media(v) is not None}
    return max(candidatas, key=candidatas.get)


def validar(series, eventos, n_treino, ks=KS, hs=HS):
    """Escolhe a janela nos primeiros n_treino eventos (por data) e mede-a nos
    restantes. Devolve (janela, roi médio no treino, rois no teste)."""
    ordenados = sorted(eventos, key=lambda e: e["data"])
    treino, teste = ordenados[:n_treino], ordenados[n_treino:]
    k, h = melhor_janela(series, treino, ks, hs)
    no_treino = media([roi_evento(series, e["data"], k, h) for e in treino])
    no_teste = [roi_evento(series, e["data"], k, h) for e in teste]
    return (k, h), no_treino, no_teste


def ciclo_semanal(series, inicio, fim):
    """ROI mediano de comprar num dia da semana e vender noutro da mesma semana
    (até 6 dias depois). Chave: (dia_compra, dia_venda), 0 = segunda."""
    resultado = {}
    for dc in range(7):
        for dur in range(1, 7):
            rois = []
            dia = inicio + timedelta(days=(dc - inicio.weekday()) % 7)
            while dia + timedelta(days=dur) <= fim:
                r = roi_evento(series, dia, 0, dur)
                if r is not None:
                    rois.append(r)
                dia += timedelta(days=7)
            if rois:
                resultado[(dc, (dc + dur) % 7)] = (statistics.median(rois), len(rois))
    return resultado


def variacao(series, dia_a, dia_b):
    """Mediana, entre cartas, da variação de preço de dia_a para dia_b, sem
    taxa: é o que se perde ou ganha por segurar, não o ROI de uma operação."""
    v = [s[dia_b] / s[dia_a] - 1 for s in series if dia_a in s and dia_b in s]
    return statistics.median(v) if v else None


def intervalo_bootstrap(valores, estatistica=statistics.median, n=2000, nivel=0.95, semente=0):
    """Intervalo de confiança por bootstrap (percentis), reprodutível pela
    semente: o relatório tem de dar sempre os mesmos números."""
    rng = random.Random(semente)
    k = len(valores)
    est = sorted(estatistica([valores[rng.randrange(k)] for _ in range(k)]) for _ in range(n))
    cauda = (1 - nivel) / 2
    return est[int(cauda * n)], est[int((1 - cauda) * n) - 1]
