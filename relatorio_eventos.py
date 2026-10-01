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
FODDER = [84, 85, 86, 87]  # o 83 fica de fora: ver "Ratings no preço mínimo"
RATINGS_APP = [85, 86, 87]  # os que a app recomenda
DIAS_COMPRA = [5, 6, 0, 1]  # sábado, domingo, segunda, terça
DIA_VENDA = 2               # quarta
CORTES_SENSIBILIDADE = [date(2026, 1, 5), date(2026, 2, 2), date(2026, 3, 16),
                        date(2026, 4, 13), date(2026, 5, 11)]
# Os números que o conselheiro usa. Gerados aqui, nunca copiados à mão.
NUMEROS = Path(__file__).with_name("estudos") / "numeros_fc26.json"


def aparada(v, corte=0.1):
    """Média sem os 10% de cada ponta: a média de +10% da 2.ª metade vinha
    de três semanas de +41% a +72%."""
    v = sorted(v)
    k = int(len(v) * corte)
    return st.mean(v[k:len(v) - k]) if len(v) > 2 * k else st.mean(v)


def fracao_no_minimo(series, inicio, fim, margem=0.02):
    dias = [(v, min(s.values())) for s in series for d, v in s.items() if inicio <= d <= fim]
    return sum(v <= m * (1 + margem) for v, m in dias) / len(dias)


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def carregar():
    series = {}
    for r in D.RATINGS:
        lista = json.loads((PASTA / f"lista_{r}.json").read_text(encoding="utf-8"))
        series[r] = [E.ler_serie(PASTA / f"hist_{c['id']}.json")
                     for c in D.escolher_como_no_estudo(lista["results"])]
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


def construir(series, eventos):
    """O relatório e os números que o conselheiro usa, a partir das séries.

    {rating: [ {date: preço} ]} e a lista de eventos. Não lê nem escreve
    ficheiros: assim testa-se com séries sintéticas, sem os preços em disco
    (que não estão no git nem na CI). Devolve (markdown, números).
    """
    fodder = [s for r in FODDER for s in series[r]]
    eventos = sorted(eventos, key=lambda e: e["data"])
    n_cartas = sum(len(v) for v in series.values())
    L = []
    a = L.append

    a("# Estudo de eventos — fodder do PC no FC 26\n")
    a("*Gerado por `relatorio_eventos.py`. Não editar à mão.*\n")
    a(f"**Dados:** histórico diário de PC (média diária do FUTBIN, via parse.bot) de "
      f"{n_cartas} cartas gold rare normais, {len(D.RATINGS)} ratings "
      f"({D.RATINGS[0]}-{D.RATINGS[-1]}), de {INICIO:%d/%m/%Y} a {FIM:%d/%m/%Y}. "
      f"Os primeiros {(INICIO - date(2025, 9, 18)).days} dias (crash de lançamento) "
      f"ficam de fora.\n")
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

    # A app mostrava o ROI do perfil da época inteira, que inclui a metade
    # usada para escolher a regra (revisão independente de 01/10/2026). Os
    # números que ela usa passam a ser estes: só a 2.ª metade, só 84-87 (o
    # conjunto fixado antes de olhar para os resultados), com intervalo.
    a("## O que a app usa: ROI medido só na 2.ª metade\n")
    a(f"Comprar em cada dia e vender {DIAS[DIA_VENDA]}, fodder 84-87, semanas de "
      f"{CORTE:%d/%m/%Y} a {FIM:%d/%m/%Y}. Intervalo de 95% por bootstrap da mediana.\n")
    a("| comprar | mediana | intervalo 95% | média aparada 10% | semanas positivas |"
      "\n|---|---|---|---|---|")
    fora = {}
    for d in DIAS_COMPRA:
        v = semanas(fodder, d, (DIA_VENDA - d) % 7, CORTE, FIM)
        lo, hi = E.intervalo_bootstrap(v)
        fora[d] = {"mediana": st.median(v), "ic": [lo, hi], "aparada": aparada(v),
                   "positivas": sum(x > 0 for x in v), "n": len(v)}
        a(f"| {DIAS[d]} | {pct(st.median(v))} | {pct(lo)} a {pct(hi)} | {pct(aparada(v))} "
          f"| {fora[d]['positivas']}/{len(v)} |")
    a(f"\nSó {DIAS[dc]} → {DIAS[dv]} foi escolhido na 1.ª metade; os outros dias são "
      "medidos na mesma janela, mas não foram escolhidos antes, e por isso valem menos. "
      "Os ratings 85-87 que a app recomenda foram escolhidos já a ver a 2.ª metade (o 84 "
      "saiu por ter sido negativo lá): para eles, isto não é fora da amostra.\n")

    a("**Sensibilidade às datas de corte.** A mesma escolha (melhor par na 1.ª parte, "
      "medido na 2.ª) com outros cortes:\n")
    a("| corte | escolhido | mediana depois do corte | semanas positivas |\n|---|---|---|---|")
    for corte in CORTES_SENSIBILIDADE:
        c = E.ciclo_semanal(fodder, INICIO, corte - timedelta(days=1))
        cc, cv = max(c, key=lambda k: c[k][0])
        v = semanas(fodder, cc, (cv - cc) % 7, corte, FIM)
        a(f"| {corte:%d/%m/%Y} | {DIAS[cc]} → {DIAS[cv]} | {pct(st.median(v))} "
          f"| {sum(x > 0 for x in v)}/{len(v)} |")
    a("\nO par de dias muda com o corte. O que se mantém é a forma: comprar ao "
      "fim-de-semana, vender a meio da semana.\n")

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
      f"domingo → quinta. Em todas as semanas, incluindo as de promo, domingo → quinta "
      f"dá mediana "
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

    # A app dizia "segurar custou 12-17%", que eram ROI de E−5 → E+1, não o
    # custo de segurar (revisão independente de 01/10/2026).
    a("## Quanto custa segurar depois de a promo abrir\n")
    a("Variação de preço, sem taxa, da véspera (quinta) para o dia a seguir à abertura "
      "(sábado). Semanas de promo grande contra as outras semanas.\n")
    a("| rating | promo: média | promo: pior | promo: melhor | outras semanas: mediana |"
      "\n|---|---|---|---|---|")
    segurar = {}
    datas_promo = {e["data"] for e in eventos}
    for r in RATINGS_APP:
        vp = [x for x in (E.variacao(series[r], e["data"] - timedelta(days=1),
                                     e["data"] + timedelta(days=1)) for e in eventos)
              if x is not None]
        sextas = [INICIO + timedelta(days=(4 - INICIO.weekday()) % 7 + 7 * i) for i in range(60)]
        vn = [x for x in (E.variacao(series[r], f - timedelta(days=1), f + timedelta(days=1))
                          for f in sextas if f + timedelta(days=1) <= FIM and f not in datas_promo)
              if x is not None]
        segurar[r] = {"promo_media": st.mean(vp), "promo_pior": min(vp), "promo_melhor": max(vp),
                      "normal_mediana": st.median(vn), "promo_n": len(vp), "normal_n": len(vn)}
        a(f"| {r} | {pct(st.mean(vp))} | {pct(min(vp))} | {pct(max(vp))} | {pct(st.median(vn))} |")
    a("\nMesmo numa semana normal, segurar de quinta para sábado custa; numa semana de "
      "promo grande custa mais, e com muita dispersão.\n")

    a("## Ratings no preço mínimo\n")
    a("Fracção de dias-carta a menos de 2% do preço mínimo da época da própria carta:\n")
    a("| rating | 1.ª metade | 2.ª metade |\n|---|---|---|")
    chao = {}
    for r in D.RATINGS:
        f1, f2 = (fracao_no_minimo(series[r], i, f) for i, f in
                  [(INICIO, CORTE - timedelta(days=1)), (CORTE, FIM)])
        chao[r] = [f1, f2]
        a(f"| {r} | {f1:.0%} | {f2:.0%} |")
    a("\nO 83 esteve no mínimo a época toda. O 84 colou ao mínimo na 2.ª metade, e foi "
      "aí que deixou de dar lucro (na 1.ª metade o ciclo deu-lhe lucro). Um rating no "
      "mínimo não tem para onde descer, mas também não sobe com a procura: perde a "
      "taxa em cada operação.\n")

    numeros = {
        "perfil_semanal": {str(d): p[d] for d in range(7)},
        "dia_venda": DIA_VENDA,
        "fora_da_amostra": {str(d): v for d, v in fora.items()},
        "segurar_depois_da_promo": {str(r): v for r, v in segurar.items()},
        "fracao_no_minimo": {str(r): v for r, v in chao.items()},
    }

    a("## Limites\n")
    a("- **A média diária pode não ser um preço executável.** No FC 27 as compras "
      "Buy Now saíram à média horária (`medicao_fc27.md`), mas em cartas que não eram "
      "o fodder mais barato do rating. Falta medir no fodder.\n"
      "- **As cartas deste estudo são as primeiras da página do site, não as mais "
      "baratas do rating.** Dentro de cada rating os preços movem-se juntos, mas não "
      "está verificado que o fodder mais barato se comporte igual.\n"
      "- **É o FC 26.** O FC 27 pode ter outro dia de rewards e outro calendário. "
      "O ciclo tem de ser confirmado com dados do FC 27 antes de se recomendar.\n"
      "- **Promos grandes: 7 eventos.** Dá para ver o que é consistente (não segurar "
      "depois do lançamento), não para afinar uma janela.\n"
      "- **Ultimate Scream (24/10/2025):** as janelas que compram mais de 4 dias antes "
      "começam antes de 20/10/2025, ainda dentro do crash de lançamento.\n"
      "- **Fuga de informação:** comprar k dias antes de uma promo pressupõe que a "
      "data era pública. Para as promos grandes era (calendário e leaks com 1-2 "
      "semanas), mas não está medido evento a evento.\n")
    return "\n".join(L), numeros


def gerar():
    eventos = E.ler_eventos(Path(__file__).with_name("eventos_fc26.csv"))
    texto, numeros = construir(carregar(), eventos)
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(texto, encoding="utf-8", newline="\n")
    NUMEROS.write_text(json.dumps(numeros, indent=1, ensure_ascii=False),
                       encoding="utf-8", newline="\n")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
