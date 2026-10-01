"""Medições sobre o histórico de vendas reais do FUTBIN (get_fc27_sales_history).

As horas das vendas vêm como o site as mostra ("Oct 1, 12:42 PM"), sem ano e
sem fuso. Verificado a 01/10/2026: a venda mais recente marcava 12:42 quando
eram 11:44 UTC, e as seis cartas pedidas davam o mesmo — UTC+1, que nessa data
é a hora de Londres (e de Lisboa).

Assume-se hora de Londres, e não um desvio fixo de +1h: a 25/10/2026 Londres
passa a UTC+0, e um desvio fixo desalinhava as vendas uma hora da média
horária (revisão independente de 01/10/2026). **Não está verificado que o site
siga a hora de Londres no Inverno**: na primeira leitura depois de 25/10,
repetir a verificação (venda mais recente contra a hora UTC da leitura).
"""

import statistics as st
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

FUSO_DO_SITE = ZoneInfo("Europe/London")


def instante_utc(texto, referencia):
    """'Oct 1, 12:42 PM' → datetime em UTC.

    O site não dá o ano. `referencia` é o instante (com fuso) em que as vendas
    foram lidas: o ano é o dela, excepto se isso puser a venda mais de um dia
    no futuro — então é do ano anterior (vendas de Dezembro lidas em Janeiro).
    """
    # O ano entra no texto, e não com .replace(year=) depois: sem ano o
    # strptime usa 1900, que não é bissexto, e "Feb 29" rebentava.
    for ano in (referencia.year, referencia.year - 1):
        try:
            local = datetime.strptime(f"{texto} {ano}", "%b %d, %I:%M %p %Y")
        except ValueError:  # 29 de Fevereiro num ano que não é bissexto
            continue
        local = local.replace(tzinfo=FUSO_DO_SITE)
        if local <= referencia + timedelta(days=1):
            return local.astimezone(timezone.utc)
    raise ValueError(f"venda no futuro: {texto!r} lida a {referencia}")


def vendidas(sales, referencia):
    """[(instante UTC, preço, tipo)] das vendas concretizadas (sem 'Unsold')."""
    return [
        (instante_utc(s["time"], referencia), int(s["sold_price"]), s["sale_type"])
        for s in sales
        if s["sale_type"] != "Unsold" and s["sold_price"]
    ]


def vendas_por_hora(sales, referencia):
    v = vendidas(sales, referencia)
    if len(v) < 2:
        return None
    horas = (max(t for t, _, _ in v) - min(t for t, _, _ in v)).total_seconds() / 3600
    return len(v) / horas if horas > 0 else None


def taxa_nao_vendidas(sales):
    return sum(s["sale_type"] == "Unsold" for s in sales) / len(sales) if sales else None


def razao_face_a_media(sales, referencia, horario, tipo=None):
    """Mediana de preço_vendido / média horária do FUTBIN na mesma hora UTC.

    1,00 quer dizer que a média do FUTBIN é o preço a que se transacciona de
    facto. `horario` é {datetime UTC truncado à hora: preço médio}.
    """
    razoes = []
    for t, preco, tp in vendidas(sales, referencia):
        if tipo and tp != tipo:
            continue
        media = horario.get(t.replace(minute=0, second=0, microsecond=0))
        if media:
            razoes.append(preco / media)
    return st.median(razoes) if razoes else None


def custo_de_ida_e_volta(sales, referencia, taxa=0.05):
    """ROI de comprar ao quartil de baixo e vender ao de cima das vendas
    'Buy Now' na mesma janela, e de comprar e vender ambos à mediana.

    Diz quanto da diferença de preço a taxa come, sem nenhum movimento de
    mercado: é o custo mínimo de uma operação.
    """
    precos = sorted(p for _, p, tp in vendidas(sales, referencia) if tp == "Buy Now")
    if len(precos) < 4:
        return None
    q1, mediana, q3 = st.quantiles(precos, n=4)
    return {
        "mediana_mediana": (1 - taxa) * mediana / mediana - 1,
        "q1_mediana": (1 - taxa) * mediana / q1 - 1,
        "dispersao_q3_q1": q3 / q1 - 1,
    }
