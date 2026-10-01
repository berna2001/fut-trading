"""O conselheiro: o que comprar, quando, quanto e quando vender.

Junta as regras medidas nos estudos com as notícias recolhidas. Cada
recomendação diz a confiança e de onde vem. Os números vêm de
estudos/numeros_fc26.json, que o relatorio_eventos.py gera; nada é copiado à
mão (revisão independente de 01/10/2026: a app mostrava o ROI da época
inteira, incluindo a metade usada para escolher a regra).

  ciclo semanal       FC 26, 2.ª metade (fora da amostra só para sábado →
                      quarta); intervalos de 95% incluem o zero → média
  vender antes da     FC 26: segurar de quinta para sábado nas semanas de
  promo abrir         promo custou 20-24% em média → alta
  hora do dia         FC 27, duas semanas, cartas que não eram fodder →
                      baixa, só afina a hora
  ratings no mínimo   FC 26: 83 sempre, 84 na 2.ª metade; FC 27: as 84 a 650
                      a 01/10/2026 → média

Decisões do utilizador, não medidas (01/10/2026):
  * recomendar já, na queda de lançamento do FC 27, com aviso;
  * por categoria até os créditos do parse.bot renovarem;
  * no máximo 70% do capital por ciclo, espalhado por várias cartas.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

LONDRES = ZoneInfo("Europe/London")

_NUMEROS = json.loads(
    Path(__file__).with_name("estudos").joinpath("numeros_fc26.json").read_text(encoding="utf-8")
)
PERFIL_FC26 = {int(d): v for d, v in _NUMEROS["perfil_semanal"].items()}
DIA_VENDA = _NUMEROS["dia_venda"]
# {dia de compra: {"mediana", "ic", "positivas", "n", ...}} — vender à quarta,
# medido só na 2.ª metade da época do FC 26.
FORA_DA_AMOSTRA = {int(d): v for d, v in _NUMEROS["fora_da_amostra"].items()}
SEGURAR = {int(r): v for r, v in _NUMEROS["segurar_depois_da_promo"].items()}

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

# As promos abrem à sexta às 18h de Londres (17h UTC no Verão, 18h no Inverno).
HORA_PROMO = time(18, 0)

# Escolhidos já a ver a 2.ª metade do FC 26 (o 84 saiu por ter sido negativo
# lá, quando colou ao preço mínimo). Não é uma escolha fora da amostra.
RATINGS = [85, 86, 87]

# Decisão do utilizador a 01/10/2026: até 70% do capital do ciclo, o resto de
# reserva. Durante a queda de lançamento, metade disso: o aviso diz para usar
# quantias menores, e a quantia sugerida tem de o cumprir. Nenhum dos dois
# números é medido.
FRACCAO_MAXIMA = 0.70
FRACCAO_LANCAMENTO = 0.35

# O estudo do FC 26 deixou de fora as primeiras ~5 semanas (crash de
# lançamento). O mercado do FC 27 abriu a 16/09/2026 (primeiro ponto do
# histórico diário do FUTBIN), por isso o aviso dura até à mesma distância.
INICIO_FC27 = date(2026, 9, 16)
FIM_LANCAMENTO = INICIO_FC27 + timedelta(days=34)


@dataclass
class Conselho:
    acao: str           # COMPRAR, VENDER, ESPERAR, EVITAR, AVISO
    o_que: str
    quando: str
    porque: str
    confianca: str      # alta, média, baixa
    quantia: int | None = None


def pct(x):
    return f"{x * 100:+.1f}%"


def em_lancamento(agora):
    return agora.astimezone(LONDRES).date() < FIM_LANCAMENTO


def proxima_promo(agora):
    """O próximo instante de abertura de promo (sexta 18h Londres) a partir de agora."""
    local = agora.astimezone(LONDRES)
    dias = (4 - local.weekday()) % 7
    alvo = datetime.combine(local.date() + timedelta(days=dias), HORA_PROMO, LONDRES)
    if alvo <= local:
        alvo += timedelta(days=7)
    return alvo


def quantias(saldo, investido_no_ciclo, agora):
    """{rating: coins} que ainda falta investir neste ciclo.

    O tecto é sobre o capital do ciclo (saldo + o que já foi investido desde
    sábado), não sobre o saldo do dia: com o saldo do dia, comprar 70% ao
    sábado, ao domingo e à segunda chegava a 97% (revisão de 01/10/2026).
    """
    saldo, investido = max(saldo, 0), max(investido_no_ciclo, 0)
    fraccao = FRACCAO_LANCAMENTO if em_lancamento(agora) else FRACCAO_MAXIMA
    # Nunca passa o saldo: f·(s+i) − i ≤ s equivale a (f−1)·(s+i) ≤ 0, que
    # vale para f ≤ 1. Um min(falta, saldo) aqui seria código morto (a
    # mutação que o tirava sobrevivia).
    falta = max(0, int(fraccao * (saldo + investido) - investido))
    return {r: falta // len(RATINGS) for r in RATINGS}


def conselhos(agora, saldo, noticias=(), investido_no_ciclo=0):
    """Lista de Conselho para o instante `agora` (datetime com fuso).

    `noticias`: iteráveis de dicts com publicado_em (datetime com fuso),
    categoria e titulo, como no noticias.csv.
    """
    local = agora.astimezone(LONDRES)
    dia = local.weekday()
    promo = proxima_promo(agora)
    antes_da_promo = dia == 4 and local.time() < HORA_PROMO
    out = []

    if em_lancamento(agora):
        out.append(Conselho(
            "AVISO", "Queda de lançamento do FC 27",
            f"até {FIM_LANCAMENTO:%d/%m}",
            "O ciclo semanal foi medido no FC 26 a partir da 5.ª semana. Nas primeiras "
            "semanas os preços caem muito, e um fim-de-semana mais barato pode não chegar "
            f"para compensar. Por isso a quantia sugerida é {FRACCAO_LANCAMENTO:.0%} do "
            f"capital, e não {FRACCAO_MAXIMA:.0%}, até lá.",
            "alta",
        ))

    if dia in (5, 6, 0):
        f = FORA_DA_AMOSTRA[dia]
        quanto = quantias(saldo, investido_no_ciclo, agora)
        out.append(Conselho(
            "COMPRAR",
            "Gold rare 85, 86 e 87 do preço mais baixo de cada rating (fodder)",
            f"hoje ({DIAS[dia]}); vender {DIAS[DIA_VENDA]}",
            f"No FC 26, comprar {'ao' if dia == 5 else 'à' if dia == 0 else 'ao'} "
            f"{DIAS[dia]} e vender {DIAS[DIA_VENDA]} deu {pct(f['mediana'])} líquido de "
            f"mediana na 2.ª metade da época ({f['positivas']} de {f['n']} semanas "
            f"positivas; intervalo de 95%: {pct(f['ic'][0])} a {pct(f['ic'][1])}, que inclui "
            "perder). "
            + ("Domingo foi o dia mais barato. " if dia == 6 else "")
            + ("Segunda não foi validada fora da amostra e a margem é menor. " if dia == 0 else "")
            + "Espalha por 3 ou mais cartas diferentes em cada rating, para não depender "
              "de uma só (regra prudente, não medida).",
            "média" if dia in (5, 6) else "baixa",
            quantia=sum(quanto.values()),
        ))
    elif dia == 1:
        f = FORA_DA_AMOSTRA[1]
        out.append(Conselho(
            "ESPERAR", "Fodder 85-87",
            "hoje (terça): não comprar; se tens cartas, segura até amanhã",
            f"No FC 26, comprar à terça e vender à quarta deu {pct(f['mediana'])} de "
            f"mediana na 2.ª metade ({f['positivas']} de {f['n']} semanas positivas): "
            "não paga a operação.",
            "média",
        ))
    elif dia in (2, 3) or antes_da_promo:
        piores = [SEGURAR[r]["promo_pior"] for r in RATINGS]
        medias = [SEGURAR[r]["promo_media"] for r in RATINGS]
        normais = [SEGURAR[r]["normal_mediana"] for r in RATINGS]
        out.append(Conselho(
            "VENDER", "O fodder 85-87 comprado no fim-de-semana",
            ("hoje (quarta), o dia mais caro" if dia == 2 else
             "hoje (quinta)" if dia == 3 else
             "JÁ — a promo abre hoje")
            + f"; o mais tardar até {DIAS[promo.weekday()]} às {promo:%H:%M} de Londres",
            "No FC 26, segurar fodder 85-87 de quinta para sábado nas semanas de promo "
            f"grande custou em média {pct(max(medias))} a {pct(min(medias))} (pior caso "
            f"{pct(min(piores))}); numa semana normal, {pct(max(normais))} a "
            f"{pct(min(normais))}. Vende mesmo abaixo do preço de compra se for preciso: "
            "segurar costuma custar mais.",
            "alta",
        ))
    else:  # sexta depois da promo
        out.append(Conselho(
            "ESPERAR", "Fodder 85-87",
            "hoje (sexta, depois da promo): não comprar",
            "Os preços continuam a descer até domingo, que foi o dia mais barato no FC 26. "
            "A próxima janela de compra é sábado e domingo.",
            "média",
        ))

    chao = _NUMEROS["fracao_no_minimo"]
    out.append(Conselho(
        "EVITAR", "Ratings cujo fodder está no preço mínimo (hoje: 83 e 84)",
        "enquanto o mais barato do rating estiver no mínimo",
        f"No FC 26, o 83 esteve no mínimo em {chao['83'][1]:.0%} dos dias da 2.ª metade e "
        f"o 84 passou de {chao['84'][0]:.0%} para {chao['84'][1]:.0%}; foi aí que o 84 "
        "deixou de dar lucro. No mínimo, a carta não acompanha a procura e cada "
        "operação perde a taxa. No FC 27, a 01/10/2026, as 84 com preço estavam todas "
        "a 650. Quando o 84 descolar do mínimo, volta a ser candidato.",
        "média",
    ))

    limite = agora - timedelta(days=7)
    recentes = sorted(
        (n for n in noticias
         if n["categoria"] in ("leak", "promo") and n["publicado_em"] >= limite),
        key=lambda n: n["publicado_em"], reverse=True,
    )
    if recentes:
        # Uma só caixa: uma por notícia repetia o mesmo conselho várias vezes.
        lista = "; ".join(f"{n['titulo']} ({n['publicado_em']:%d/%m})" for n in recentes)
        out.append(Conselho(
            "AVISO", f"{len(recentes)} promo(s) anunciada(s) ou leaked nos últimos 7 dias",
            f"vender o fodder antes de sexta às {HORA_PROMO:%H:%M} de Londres",
            f"{lista}. O efeito de cada promo em concreto não está medido; a regra de "
            "vender antes da abertura está.",
            "baixa",
        ))
    return out
