"""Medições sobre o histórico de vendas reais do FUTBIN (get_fc27_sales_history).

As horas das vendas vêm como o site as mostra ("Oct 1, 12:42 PM"), sem ano e
sem fuso. Verificado a 01/10/2026: a venda mais recente marcava 12:42 quando
eram 11:44 UTC, e as seis cartas pedidas davam o mesmo. Por isso as horas
estão em UTC+1 (hora de Lisboa/Londres no Verão). Isto muda no fim de
Outubro, quando acaba a hora de Verão, e terá de ser verificado outra vez.
"""

import statistics as st
from datetime import datetime, timedelta, timezone

DESVIO_UTC = timedelta(hours=1)


def instante_utc(texto, ano):
    """'Oct 1, 12:42 PM' → datetime em UTC."""
    local = datetime.strptime(f"{texto} {ano}", "%b %d, %I:%M %p %Y")
    return (local - DESVIO_UTC).replace(tzinfo=timezone.utc)


def vendidas(sales, ano):
    """[(instante UTC, preço, tipo)] das vendas concretizadas (sem 'Unsold')."""
    return [
        (instante_utc(s["time"], ano), int(s["sold_price"]), s["sale_type"])
        for s in sales
        if s["sale_type"] != "Unsold" and s["sold_price"]
    ]


def vendas_por_hora(sales, ano):
    v = vendidas(sales, ano)
    if len(v) < 2:
        return None
    horas = (max(t for t, _, _ in v) - min(t for t, _, _ in v)).total_seconds() / 3600
    return len(v) / horas if horas > 0 else None


def taxa_nao_vendidas(sales):
    return sum(s["sale_type"] == "Unsold" for s in sales) / len(sales) if sales else None


def razao_face_a_media(sales, ano, horario, tipo=None):
    """Mediana de preço_vendido / média horária do FUTBIN na mesma hora UTC.

    1,00 quer dizer que a média do FUTBIN é o preço a que se transacciona de
    facto. `horario` é {datetime UTC truncado à hora: preço médio}.
    """
    razoes = []
    for t, preco, tp in vendidas(sales, ano):
        if tipo and tp != tipo:
            continue
        media = horario.get(t.replace(minute=0, second=0, microsecond=0))
        if media:
            razoes.append(preco / media)
    return st.median(razoes) if razoes else None


def custo_de_ida_e_volta(sales, ano, taxa=0.05):
    """ROI de comprar ao quartil de baixo e vender ao de cima das vendas
    'Buy Now' na mesma janela, e de comprar e vender ambos à mediana.

    Diz quanto da diferença de preço a taxa come, sem nenhum movimento de
    mercado: é o custo mínimo de uma operação.
    """
    precos = sorted(p for _, p, tp in vendidas(sales, ano) if tp == "Buy Now")
    if len(precos) < 4:
        return None
    q1, mediana, q3 = st.quantiles(precos, n=4)
    return {
        "mediana_mediana": (1 - taxa) * mediana / mediana - 1,
        "q1_mediana": (1 - taxa) * mediana / q1 - 1,
        "dispersao_q3_q1": q3 / q1 - 1,
    }
