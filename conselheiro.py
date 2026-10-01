"""O conselheiro: o que comprar, quando, quanto e quando vender.

Junta as regras medidas nos estudos (estudos/*.md) com as notícias recolhidas.
Cada recomendação diz a confiança e de onde vem. As regras e a sua base:

  ciclo semanal       FC 26, validado fora da amostra; falta confirmar no
                      FC 27 → confiança média
  vender antes da     FC 26: segurar fodder 85-86 até ao dia a seguir ao
  promo abrir         lançamento custou 12-17% → confiança alta
  hora do dia         FC 27, duas semanas, +1% → confiança baixa, só afina
                      a hora
  rating no mínimo    FC 26: o 83 esteve no mínimo e perdeu a taxa sempre

Decisões do utilizador, não medidas (01/10/2026):
  * recomendar já, na queda de lançamento do FC 27, com aviso;
  * por categoria até os créditos do parse.bot renovarem;
  * no máximo 70% do saldo por ciclo, espalhado por várias cartas.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

LONDRES = ZoneInfo("Europe/London")
TAXA = 0.05

# Preço de cada dia face à média da sua semana, fodder 84-87 do FC 26.
# Copiado de estudos/eventos_fc26.md ("O ciclo semanal"). O teste
# test_perfil_bate_com_o_relatorio falha se os dois divergirem.
PERFIL_FC26 = {0: -0.028, 1: -0.009, 2: 0.073, 3: 0.059, 4: 0.015, 5: -0.048, 6: -0.080}
DIA_VENDA = 2  # quarta: o dia mais caro do perfil
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

# As promos abrem à sexta às 18h de Londres (17h UTC no Verão, 18h no Inverno).
HORA_PROMO = time(18, 0)

# Os ratings onde o ciclo se manteve positivo nas duas metades da época do
# FC 26 (relatório, "Por rating"). O 84 foi negativo na segunda metade e o 83
# esteve sempre no mínimo.
RATINGS = [85, 86, 87]

# Decisão do utilizador a 01/10/2026: até 70% do saldo por ciclo, o resto de
# reserva. Não é um número medido.
FRACCAO_MAXIMA = 0.70

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


def roi_esperado(dia_compra, dia_venda=DIA_VENDA):
    """ROI líquido de comprar num dia da semana e vender noutro, pelo perfil."""
    return (1 - TAXA) * (1 + PERFIL_FC26[dia_venda]) / (1 + PERFIL_FC26[dia_compra]) - 1


def proxima_promo(agora):
    """O próximo instante de abertura de promo (sexta 18h Londres) a partir de agora."""
    local = agora.astimezone(LONDRES)
    dias = (4 - local.weekday()) % 7
    alvo = datetime.combine(local.date() + timedelta(days=dias), HORA_PROMO, LONDRES)
    if alvo <= local:
        alvo += timedelta(days=7)
    return alvo


def quantias(saldo):
    """{rating: coins} a investir neste ciclo, dividido por igual."""
    total = int(max(saldo, 0) * FRACCAO_MAXIMA)
    return {r: total // len(RATINGS) for r in RATINGS}


def conselhos(agora, saldo, noticias=()):
    """Lista de Conselho para o instante `agora` (datetime com fuso).

    `noticias`: iteráveis de dicts com publicado_em (datetime com fuso),
    categoria e titulo, como no noticias.csv.
    """
    local = agora.astimezone(LONDRES)
    dia = local.weekday()
    promo = proxima_promo(agora)
    antes_da_promo = dia == 4 and local.time() < HORA_PROMO
    out = []

    if local.date() < FIM_LANCAMENTO:
        out.append(Conselho(
            "AVISO", "Queda de lançamento do FC 27",
            f"até {FIM_LANCAMENTO:%d/%m}",
            "O ciclo semanal foi medido no FC 26 a partir da 5.ª semana. Nas primeiras "
            "semanas os preços caem muito, e um fim-de-semana mais barato "
            "pode não chegar para compensar. Opera com quantias menores até lá.",
            "alta",
        ))

    if dia in (5, 6, 0):
        roi = roi_esperado(dia)
        quanto = quantias(saldo)
        out.append(Conselho(
            "COMPRAR",
            "Gold rare 85, 86 e 87 do preço mais baixo de cada rating (fodder)",
            f"hoje ({DIAS[dia]}), de preferência de madrugada (perto das 03h UTC)",
            f"No FC 26, {DIAS[dia]} esteve {PERFIL_FC26[dia] * 100:+.1f}% face à média da "
            f"semana e quarta {PERFIL_FC26[DIA_VENDA] * 100:+.1f}%. Comprar hoje e vender "
            f"quarta dava {roi * 100:+.1f}% líquido. "
            + ("Domingo é o dia mais barato. " if dia == 6 else "")
            + ("Segunda já está a subir: margem menor. " if dia == 0 else "")
            + "Espalha por 3 ou mais cartas diferentes em cada rating, para não "
              "depender de uma só (regra prudente, não medida).",
            "média" if dia in (5, 6) else "baixa",
            quantia=sum(quanto.values()),
        ))
    elif dia == 1:
        out.append(Conselho(
            "ESPERAR", "Fodder 85-87",
            "hoje (terça): não comprar; se tens cartas, segura até amanhã",
            f"Terça está {PERFIL_FC26[1] * 100:+.1f}% face à média. Comprar hoje e "
            f"vender amanhã dava {roi_esperado(1) * 100:+.1f}% líquido no FC 26, menos de "
            f"metade de comprar ao domingo ({roi_esperado(6) * 100:+.1f}%), e essa "
            f"janela não foi validada fora da amostra.",
            "média",
        ))
    elif dia in (2, 3) or antes_da_promo:
        out.append(Conselho(
            "VENDER", "O fodder 85-87 comprado no fim-de-semana",
            ("hoje (quarta), o dia mais caro" if dia == 2 else
             "hoje (quinta), ainda caro" if dia == 3 else
             "JÁ — a promo abre hoje")
            + f"; o mais tardar até {DIAS[promo.weekday()]} às {promo:%H:%M} de Londres",
            "No FC 26, segurar fodder 85-86 até ao dia a seguir à abertura de uma "
            "promo custou entre 12% e 17%. Vende mesmo abaixo do preço de compra se "
            "for preciso: segurar costuma custar mais. Hora mais cara do dia: perto "
            "das 17h UTC.",
            "alta",
        ))
    else:  # sexta depois da promo
        out.append(Conselho(
            "ESPERAR", "Fodder 85-87",
            "hoje (sexta, depois da promo): não comprar",
            "Os preços continuam a descer até domingo, que é o dia mais barato. "
            "A próxima janela de compra é sábado e domingo.",
            "média",
        ))

    out.append(Conselho(
        "EVITAR", "Ratings 83 e 84",
        "sempre",
        "No FC 26 o 83 esteve no preço mínimo e perdeu a taxa em cada operação; o 84 "
        "foi negativo na segunda metade da época. Uma compra aí não tem para onde subir.",
        "alta",
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
