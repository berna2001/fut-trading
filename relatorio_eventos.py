"""Gera estudos/eventos_fc26.md a partir dos históricos em precos/fc26/.

Todos os números do relatório saem daqui; nenhum se escreve à mão. Se o
código ou os dados mudarem, corre-se outra vez (lição do bet: números
publicados envelhecem dentro do próprio commit).

O relatório só tem percentagens e contagens, nunca preços: o repositório é
público e os preços são dados do FUTBIN (AGENTS.md).
"""

import json
import statistics as st
from datetime import date, timedelta
from pathlib import Path

import descarregar_fc26 as D
import estudo_eventos as E

PASTA = Path(__file__).with_name("precos") / "fc26"
SAIDA = Path(__file__).with_name("estudos") / "eventos_fc26.md"
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

# As primeiras 4 semanas são o crash de lançamento, que não se repete dentro
# da época e domina qualquer janela que o apanhe.
INICIO = date(2025, 10, 20)
FIM = date(2026, 9, 13)
# Corte da validação do ciclo semanal: escolhe-se na primeira metade, mede-se
# na segunda.
CORTE = date(2026, 3, 16)
FODDER = [84, 85, 86, 87]  # o 83 fica de fora: ver secção do 83


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def carregar():
    series = {}
    for r in D.RATINGS:
        lista = json.loads((PASTA / f"lista_{r}.json").read_text(encoding="utf-8"))
        series[r] = [E.ler_serie(PASTA / f"hist_{c['id']}.json")
                     for c in D.escolher(lista["results"])]
    return series


def semanas(series, dia_compra, duracao, inicio, fim):
    out, d = [], inicio + timedelta(days=(dia_compra - inicio.weekday()) % 7)
    while d + timedelta(days=duracao) <= fim:
        r = E.roi_evento(series, d, 0, duracao)
        if r is not None:
            out.append(r)
        d += timedelta(days=7)
    return out


def perfil_semanal(series, inicio, fim):
    """Preço de cada dia face à média da sua semana (seg-dom), mediana."""
    desvios = {i: [] for i in range(7)}
    seg = inicio + timedelta(days=(0 - inicio.weekday()) % 7)
    for s in series:
        d = seg
        while d + timedelta(days=6) <= fim:
            w = [s.get(d + timedelta(days=i)) for i in range(7)]
            if all(w):
                m = st.mean(w)
                for i in range(7):
                    desvios[i].append(w[i] / m - 1)
            d += timedelta(days=7)
    return {i: st.median(v) for i, v in desvios.items()}


def resumo(v):
    return f"{pct(st.median(v))} | {pct(st.mean(v))} | {sum(x > 0 for x in v)}/{len(v)}"


def gerar():
    series = carregar()
    fodder = [s for r in FODDER for s in series[r]]
    eventos = sorted(E.ler_eventos(Path(__file__).with_name("eventos_fc26.csv")),
                     key=lambda e: e["data"])
    n_cartas = sum(len(v) for v in series.values())
    L = []
    a = L.append

    a("# Estudo de eventos — fodder do PC no FC 26\n")
    a("*Gerado por `relatorio_eventos.py`. Não editar à mão.*\n")
    a(f"**Dados:** histórico diário de PC (média diária do FUTBIN, via parse.bot) de "
      f"{n_cartas} cartas gold rare normais, {len(D.RATINGS)} ratings "
      f"({D.RATINGS[0]}-{D.RATINGS[-1]}), de {INICIO:%d/%m/%Y} a {FIM:%d/%m/%Y}. "
      f"As 4 primeiras semanas (crash de lançamento) ficam de fora.\n")
    a("**ROI sempre líquido da taxa de 5%:** `0,95 × venda / compra − 1`. "
      "Por cada dia, a mediana entre as cartas.\n")

    a("## Referência: comprar e vender num dia qualquer\n")
    a("| rating | janela de 4 dias começada num dia qualquer |\n|---|---|")
    for r in D.RATINGS:
        a(f"| {r} | {pct(E.roi_referencia(series[r], 4, INICIO, FIM))} |")
    a("\nÉ a taxa, mais nada: sem saber de nenhum evento, o preço mediano não se "
      "mexe numa janela curta, e a taxa come 5%. Qualquer estratégia tem de "
      "bater isto **e** o zero de ficar parado.\n")

    a("## O ciclo semanal\n")
    a("Preço de cada dia face à média da sua semana (84-87, mediana):\n")
    p = perfil_semanal(fodder, INICIO, FIM)
    a("| " + " | ".join(DIAS) + " |\n|" + "---|" * 7)
    a("| " + " | ".join(pct(p[i]) for i in range(7)) + " |\n")

    ca = E.ciclo_semanal(fodder, INICIO, CORTE - timedelta(days=1))
    dc, dv = max(ca, key=lambda k: ca[k][0])
    dur = (dv - dc) % 7
    a(f"**Validação fora da amostra.** A melhor combinação (dia de compra → dia de "
      f"venda) escolhe-se só na primeira metade (até {CORTE - timedelta(days=1):%d/%m/%Y}) e "
      f"mede-se na segunda, que não entrou na escolha. "
      f"Escolhida: **comprar {DIAS[dc]}, vender {DIAS[dv]}**.\n")
    a("| período | mediana | média | semanas positivas |\n|---|---|---|---|")
    a(f"| 1.ª metade (escolha) | {resumo(semanas(fodder, dc, dur, INICIO, CORTE - timedelta(days=1)))} |")
    a(f"| 2.ª metade (teste) | {resumo(semanas(fodder, dc, dur, CORTE, FIM))} |\n")

    a(f"Por rating ({DIAS[dc]} → {DIAS[dv]}):\n")
    a("| rating | 1.ª metade | 2.ª metade |\n|---|---|---|")
    for r in D.RATINGS:
        v1 = semanas(series[r], dc, dur, INICIO, CORTE - timedelta(days=1))
        v2 = semanas(series[r], dc, dur, CORTE, FIM)
        a(f"| {r} | {pct(st.median(v1))} ({sum(x > 0 for x in v1)}/{len(v1)}) "
          f"| {pct(st.median(v2))} ({sum(x > 0 for x in v2)}/{len(v2)}) |")
    a("")

    a("## Promos grandes\n")
    a("Datas em `eventos_fc26.csv`, cada uma confirmada por duas fontes. "
      "E = dia em que a promo abre (sexta, 18h UK). Comprar em E−k, vender em E+h.\n")
    t = E.tabela(fodder, eventos)
    ordem = sorted(t, key=lambda kh: -(E.media(t[kh]) or -9))
    a("| comprar | vender | ROI médio | " + " | ".join(e["nome"] for e in eventos) + " |")
    a("|---|---|---|" + "---|" * len(eventos))
    for kh in ordem[:6] + ordem[-3:]:
        k, h = kh
        venda = "véspera" if h == -1 else ("dia E" if h == 0 else f"E+{h}")
        a(f"| E−{k} | {venda} | {pct(E.media(t[kh]))} | "
          + " | ".join(pct(x) for x in t[kh]) + " |")
    a("")

    for n in (3, 4, 5):
        (k, h), tr, te = E.validar(fodder, eventos, n)
        a(f"- Escolhendo nos primeiros {n} eventos: E−{k} → E{h:+d} "
          f"({pct(tr)} no treino); nos {len(te)} seguintes: "
          + ", ".join(pct(x) for x in te) + f" (média {pct(E.media(te))}).")
    # Comprar em E−5 e vender na véspera de uma promo de sexta é comprar ao
    # domingo e vender à quinta: o ciclo semanal. A comparação justa é com
    # uma semana qualquer, não com o zero.
    normais = semanas(fodder, 6, 4, INICIO, FIM)
    promo = [E.roi_evento(fodder, e["data"], 5, -1) for e in eventos]
    a(f"\n**As promos grandes acrescentam pouco ao ciclo semanal.** E−5 → véspera é "
      f"domingo → quinta. Numa semana qualquer, domingo → quinta dá mediana "
      f"{pct(st.median(normais))} e média {pct(st.mean(normais))} ({len(normais)} semanas); "
      f"nas 7 semanas de promo grande, mediana {pct(st.median(promo))} e média "
      f"{pct(st.mean(promo))}.")
    a("\nA janela escolhida muda com o corte. **Com 7 eventos isto não chega para "
      "escolher uma janela de compra.** O que é estável é o que acontece depois "
      "do lançamento:\n")
    a("| rating | comprar E−5, vender na véspera | comprar E−5, segurar até E+1 |\n|---|---|---|")
    for r in D.RATINGS:
        a(f"| {r} | {pct(E.media([E.roi_evento(series[r], e['data'], 5, -1) for e in eventos]))} "
          f"| {pct(E.media([E.roi_evento(series[r], e['data'], 5, 1) for e in eventos]))} |")
    a("")

    a("## O 83\n")
    s83 = series[83]
    dias_83 = [d for s in s83 for d in s if INICIO <= d <= FIM]
    no_minimo = [d for s in s83 for d, v in s.items()
                 if INICIO <= d <= FIM and v <= min(s.values()) * 1.02]
    a(f"Em {len(no_minimo) / len(dias_83):.0%} dos dias-carta, o 83 esteve a menos de "
      f"2% do seu preço mínimo da época. Não sobe com os eventos e perde a taxa "
      f"em cada operação.\n")

    a("## Limites\n")
    a("- **A média diária não é um preço executável.** Comprar ao preço médio de "
      "domingo e vender ao de quarta assume que se consegue comprar e vender perto "
      "da média. O histórico de vendas (`get_fc27_sales_history`) mede isso, e "
      "falta medi-lo.\n"
      "- **É o FC 26.** O FC 27 pode ter outro dia de rewards e outro calendário. "
      "O ciclo tem de ser confirmado com dados do FC 27 antes de se recomendar.\n"
      "- **Promos grandes: 7 eventos.** Dá para ver o que é consistente (não segurar "
      "depois do lançamento), não para afinar uma janela.\n"
      "- **Fuga de informação:** comprar k dias antes de uma promo pressupõe que a "
      "data era pública. Para as promos grandes era (calendário e leaks com 1-2 "
      "semanas), mas não está medido evento a evento.\n")
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
