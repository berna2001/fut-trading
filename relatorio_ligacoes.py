"""Gera estudos/ligacoes_fc26.md: a H4 (química) medida no fodder do FC 26.

Aplica o plano de estudos/plano_promos_jogadores.md tal como foi escrito a
21/10/2026, antes do cálculo. A análise com correspondências de nomes de liga
é secundária e está assinalada como desvio ao plano.

Só percentagens e contagens, nunca preços (o repositório é público).
"""

import csv
import glob
import json
import statistics as st
from pathlib import Path

import descarregar_fc26 as D
import estudo_eventos as E
import estudo_ligacoes as L
import promos_fc26 as PR

SAIDA = Path(__file__).with_name("estudos") / "ligacoes_fc26.md"
RATINGS = [84, 85, 86, 87]  # plano: o 83 está no mínimo e não pode subir
DESCRICAO = {"H4a": "D−7 → D−1 (antecipar)", "H4b": "D−1 → D+3 (logo depois)",
             "H4c": "D → D+7 (a semana a seguir)"}


def pct(x):
    return f"{x * 100:+.1f}%"


def carregar():
    cartas = list(csv.DictReader(open(PR.SAIDA, encoding="utf-8")))
    nomes = {}
    for f in glob.glob(str(PR.PASTA / "*.html")):
        nomes.update(PR.nomes_de_ligacoes(Path(f).read_text(encoding="utf-8", errors="replace")))
    fodder = []
    for r in RATINGS:
        lista = json.loads((D.PASTA / f"lista_{r}.json").read_text(encoding="utf-8"))
        for c in D.escolher_como_no_estudo(lista["results"]):
            fodder.append((c, E.ler_serie(D.PASTA / f"hist_{c['id']}.json")))
    return cartas, nomes, fodder


def construir(cartas, nomes, fodder):
    promos = L.dias_de_promo(cartas)
    ligas_gg = {L.normalizar(v) for (t, _), v in nomes.items() if t == "league"}
    sem_cruzar = sorted({c["league"] for c, _ in fodder if L.normalizar(c["league"]) not in ligas_gg})
    n_sem = sum(L.normalizar(c["league"]) not in ligas_gg for c, _ in fodder)

    a = []
    a.append("# Química: o fodder ligado às promos sobe mais? (H4, FC 26)\n")
    a.append("*Gerado por `relatorio_ligacoes.py`. Não editar à mão. Regras fixadas em "
             "`plano_promos_jogadores.md` antes do cálculo.*\n")
    a.append(f"**Dados:** {len(promos)} dias de promo (10+ cartas novas no dia), "
             f"{len(cartas)} cartas de promo com nação e liga (FUT.GG), {len(fodder)} cartas "
             f"de fodder 84-87 com histórico diário de PC (FUTBIN). Uma carta está **ligada** "
             f"num dia se a nação ou a liga dela tem 3+ cartas novas nesse dia; as outras são "
             f"o controlo, nas mesmas datas. Efeito = ROI das ligadas − ROI das não ligadas "
             f"(medianas, líquido da taxa).\n")

    for titulo, alias, nota in [
        ("Análise do plano (nomes de liga só por nome)", None,
         f"{n_sem} das {len(fodder)} cartas têm uma liga cujo nome o FUT.GG escreve de outra "
         f"maneira ({', '.join(sem_cruzar)}). Para essas, só a nação conta."),
        ("Análise secundária — desvio ao plano (com correspondências de liga)", L.ALIAS_LIGAS,
         "Acrescenta as correspondências " + "; ".join(f"{k} = {v}" for k, v in L.ALIAS_LIGAS.items())
         + ". Cada uma tem um só candidato no FUT.GG. Não estava no plano: vale menos."),
    ]:
        a.append(f"## {titulo}\n")
        a.append(nota + "\n")
        a.append("| janela | dias | efeito mediano | dias com efeito > 0 | 1.ª metade | 2.ª metade | passa? |")
        a.append("|---|---|---|---|---|---|---|")
        for h, (k, hh) in L.JANELAS.items():
            ef = L.efeitos(fodder, promos, nomes, k, hh, alias)
            ok, metades = L.passa(ef)
            v = [e for _, e, _, _ in ef]
            if not v:
                a.append(f"| {h} {DESCRICAO[h]} | 0 | — | — | — | — | não |")
                continue
            m = " | ".join(f"{pct(med)} ({pos}/{n})" for med, pos, n in metades) if metades else "— | —"
            a.append(f"| {h} {DESCRICAO[h]} | {len(v)} | {pct(st.median(v))} | "
                     f"{sum(x > 0 for x in v)}/{len(v)} | {m} | {'**sim**' if ok else 'não'} |")
        a.append("")

    a.append("## Limites\n")
    a.append("- **É fodder 84-87, não as cartas que a química mais move.** Quem procura "
             "ligações para uma carta de promo nova procura sobretudo cartas jogáveis da mesma "
             "nação ou liga. Um resultado nulo aqui não exclui o efeito nessas cartas; um "
             "resultado positivo aqui é um bom sinal para elas.\n"
             "- **Poucas cartas ligadas por dia:** a amostra é de 52 cartas, e num dia típico "
             "só algumas são da nação ou da liga em destaque.\n"
             "- **É o FC 26.**\n")
    return "\n".join(a)


def gerar():
    SAIDA.write_text(construir(*carregar()), encoding="utf-8", newline="\n")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
