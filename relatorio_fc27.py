"""Gera estudos/medicao_fc27.md a partir de precos/fc27/.

Responde à primeira limitação do estudo do FC 26: a média do FUTBIN é um
preço a que se compra e vende de facto? E acrescenta os perfis por hora e
por dia da semana que os dados horários do FC 27 permitem.

Só percentagens e contagens, nunca preços (o repositório é público).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import descarregar_fc26 as D26
import descarregar_fc27 as D27
import perfis as PF
import vendas as V

SAIDA = Path(__file__).with_name("estudos") / "medicao_fc27.md"
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
ANO = 2026


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def horario(carta_id):
    dados = json.loads((D27.PASTA / f"horario_{carta_id}.json").read_text(encoding="utf-8"))
    return {datetime.fromtimestamp(p["timestamp"] / 1000, timezone.utc): int(p["price"])
            for p in dados["prices"] if int(p["price"]) > 0}


def gerar():
    lista = json.loads((D27.PASTA / "lista_86.json").read_text(encoding="utf-8"))
    cartas = D26.escolher_como_no_estudo(lista["results"], D27.N_CARTAS)
    series = {int(c["id"]): horario(int(c["id"])) for c in cartas}
    inicio = min(min(s) for s in series.values())
    fim = max(max(s) for s in series.values())

    L = []
    a = L.append
    a("# Medição no FC 27 — vendas reais e perfis horários\n")
    a("*Gerado por `relatorio_fc27.py`. Não editar à mão.*\n")
    a(f"**Dados:** {len(cartas)} cartas gold rare 86 do FC 27, PC. Histórico horário de "
      f"{inicio:%d/%m %H}h a {fim:%d/%m %H}h UTC, e as últimas ~500 vendas de cada uma, "
      f"lidas a 01/10/2026. 29 créditos.\n")

    a("## A média do FUTBIN é executável?\n")
    a("Cada venda compara-se com a média horária do FUTBIN da mesma hora UTC. "
      "1,00 = vendeu-se exactamente à média.\n")
    a("| carta | vendas/hora | não vendidas | Buy Now ÷ média | licitação ÷ média "
      "| dispersão Q3/Q1 |\n|---|---|---|---|---|---|")
    bins, bids = [], []
    for c in cartas:
        cid = int(c["id"])
        s = json.loads((D27.PASTA / f"vendas_{cid}.json").read_text(encoding="utf-8"))["sales"]
        rb = V.razao_face_a_media(s, ANO, series[cid], "Buy Now")
        rl = V.razao_face_a_media(s, ANO, series[cid], "Bid")
        bins.append(rb)
        if rl:
            bids.append(rl)
        ida = V.custo_de_ida_e_volta(s, ANO)
        a(f"| {c['name']} | {V.vendas_por_hora(s, ANO):.0f} | {V.taxa_nao_vendidas(s):.0%} "
          f"| {rb:.3f} | {'—' if rl is None else f'{rl:.3f}'} | {pct(ida['dispersao_q3_q1'])} |")
    a(f"\n**Sim.** As compras Buy Now concretizaram-se entre {min(bins):.3f} e "
      f"{max(bins):.3f} da média horária. As licitações ganhas saíram entre "
      f"{pct(min(bids) - 1)} e {pct(max(bids) - 1)} face à média: comprar por "
      f"licitação é mais barato, mas não se sabe quantas se perdem. Do lado da venda, "
      f"uma parte das listagens não vende à primeira (coluna \"não vendidas\"), o que "
      f"obriga a relistar.\n")
    a("Isto valida o uso da média diária no estudo do FC 26, para estas cartas e "
      "neste momento do mercado.\n")

    a("## Hora do dia\n")
    a("Preço face à média das 24 horas centradas (mediana). Horas em UTC: "
      "as promos abrem às 17h UTC (18h UK).\n")
    p = PF.perfil_horario(series.values())
    a("| " + " | ".join(f"{h:02d}" for h in range(24)) + " |")
    a("|" + "---|" * 24)
    a("| " + " | ".join(f"{p[h] * 100:+.1f}" for h in range(24)) + " |\n")
    barata, cara = min(p, key=p.get), max(p, key=p.get)
    # Comparar a diferença com os 5% directamente estava errado: a primeira
    # versão desta frase dizia que +6,2% era "menor do que a taxa". O que
    # conta é o ROI líquido de comprar na hora barata e vender na cara.
    roi_hora = 0.95 * (1 + p[cara]) / (1 + p[barata]) - 1
    a(f"Mais barata às {barata:02d}h UTC ({pct(p[barata])}), mais cara às {cara:02d}h UTC "
      f"({pct(p[cara])}). Comprar às {barata:02d}h e vender às {cara:02d}h do mesmo dia "
      f"dá {pct(roi_hora)} líquido, "
      + ("perto de zero: a hora sozinha quase não paga uma operação, mas escolhe o "
         "momento de uma que já se ia fazer.\n" if abs(roi_hora) < 0.02 else
         "o que merece ser estudado como estratégia própria.\n"))

    a("## Dia da semana\n")
    ps = PF.perfil_semanal(series.values())
    a("| " + " | ".join(DIAS[d] for d in sorted(ps)) + " |")
    a("|" + "---|" * len(ps))
    a("| " + " | ".join(f"{pct(ps[d][0])} ({ps[d][1]})" for d in sorted(ps)) + " |\n")
    a("Entre parênteses, dias-carta. **São duas semanas, e são as do crash de "
      "lançamento.** Mostra fim-de-semana barato e início de semana caro, como no "
      "FC 26, mas não chega para confirmar o ciclo. Precisa de mais semanas.\n")

    a("## Limites\n")
    a("- **As cartas 86 do FC 27 ainda não são fodder.** Valem ordens de grandeza "
      "diferentes entre si e cada uma segue o seu caminho. O ciclo do FC 26 é de "
      "fodder, cujo preço vem da procura de SBCs; só deve aparecer quando o mercado "
      "do FC 27 amadurecer.\n"
      "- **As horas das vendas assumem UTC+1**, verificado a 01/10/2026. Muda no "
      "fim de Outubro com o fim da hora de Verão.\n"
      "- **6 cartas, um só rating, um só dia de vendas.** É uma verificação, não um "
      "estudo.\n")
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
