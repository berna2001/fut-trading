"""H4 do plano (estudos/plano_promos_jogadores.md): química.

Quando sai uma promo, as cartas que fazem ligação de química com as cartas
novas (mesma nação ou mesma liga) sobem mais do que as outras? Regras fixadas
no plano a 21/10/2026, antes de calcular; aqui só se aplicam.
"""

import re
import statistics as st
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import estudo_eventos as E

LONDRES = ZoneInfo("Europe/London")
MIN_CARTAS_DIA = 10       # plano: "dias com 10 ou mais cartas novas"
MIN_CARTAS_FORTE = 3      # plano: "nações e ligas com 3 ou mais nesse dia"
JANELAS = {"H4a": (7, -1), "H4b": (1, 3), "H4c": (0, 7)}   # (k, h): compra D−k, venda D+h

# NÃO faz parte do plano: os nomes de liga do FUTBIN e do FUT.GG diferem.
# O plano manda cruzar só pelo nome normalizado; esta tabela é para a análise
# secundária, assumida como desvio no relatório. Cada entrada tem um único
# candidato no FUT.GG (verificado a 21/10/2026 nos nomes das páginas).
ALIAS_LIGAS = {
    "Serie A TIM": "Serie A Enilive",
    "Barclays WSL": "Barclays Women’s Super League",
    "NWSL": "National Women's Soccer League",
    "D1 Arkema": "Arkema Première Ligue",
    "GPFBL": "Google Pixel Frauen-Bundesliga",
}


def normalizar(nome):
    sem_acentos = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sem_acentos.lower())


def dia_em_londres(instante_iso):
    return datetime.fromisoformat(instante_iso.replace("Z", "+00:00")).astimezone(LONDRES).date()


def dias_de_promo(cartas, minimo=MIN_CARTAS_DIA):
    """{date: [cartas]} só dos dias com `minimo` ou mais cartas novas."""
    por_dia = {}
    for c in cartas:
        por_dia.setdefault(dia_em_londres(c["saiu_em"]), []).append(c)
    return {d: v for d, v in sorted(por_dia.items()) if len(v) >= minimo}


def fortes(cartas_do_dia, campo, nomes, tipo, minimo=MIN_CARTAS_FORTE):
    """Nomes normalizados das nações (ou ligas) com `minimo`+ cartas nesse dia."""
    contagem = {}
    for c in cartas_do_dia:
        nome = nomes.get((tipo, c[campo]))
        if nome:
            contagem[normalizar(nome)] = contagem.get(normalizar(nome), 0) + 1
    return {n for n, k in contagem.items() if k >= minimo}


def esta_ligada(carta, nacoes_fortes, ligas_fortes, alias=None):
    liga = (alias or {}).get(carta["league"], carta["league"])
    return normalizar(carta["nation"]) in nacoes_fortes or normalizar(liga) in ligas_fortes


def efeitos(fodder, promos, nomes, k, h, alias=None):
    """[(dia, efeito, n_ligadas, n_nao)]: mediana do ROI das ligadas − mediana
    das não ligadas, comprando em D−k e vendendo em D+h.

    `fodder`: [(carta, serie)], com carta["nation"] e carta["league"] (nomes do
    FUTBIN) e serie {date: preço}. Dias sem ligadas ou sem controlo saem.
    """
    out = []
    for d, cartas in promos.items():
        nac = fortes(cartas, "nacao_id", nomes, "nation")
        lig = fortes(cartas, "liga_id", nomes, "league")
        ligadas = [s for c, s in fodder if esta_ligada(c, nac, lig, alias)]
        nao = [s for c, s in fodder if not esta_ligada(c, nac, lig, alias)]
        rl, rn = E.roi_evento(ligadas, d, k, h), E.roi_evento(nao, d, k, h)
        if rl is not None and rn is not None:
            out.append((d, rl - rn, len(ligadas), len(nao)))
    return out


def passa(efeitos_por_dia):
    """Critério do plano: nas duas metades dos dias (antes e depois do dia
    mediano), mediana do efeito > 0 e mais de metade dos dias > 0."""
    v = [e for _, e, _, _ in sorted(efeitos_por_dia)]
    if len(v) < 4:
        return False, []
    metades = [v[: len(v) // 2], v[len(v) // 2:]]
    resumo = [(st.median(m), sum(x > 0 for x in m), len(m)) for m in metades]
    return all(med > 0 and pos * 2 > n for med, pos, n in resumo), resumo
