"""Descarrega o histórico diário de PC do FC 26 para o estudo de eventos.

Custo, pelos preços de 01/10/2026:
  listas de cartas: 5 páginas × 5 créditos = 25
  históricos:       13 cartas × 5 ratings × 2 créditos = 130
  total:            155 dos 184 que restavam no mês.

Porquê fodder 83-87 em gold rare normal: é o que os SBCs consomem, por isso é
onde os eventos mexem na procura; e cartas do mesmo rating movem-se juntas, o
que deixa medir o efeito com um índice por rating em vez de carta a carta.
13 cartas por rating chegam para a mediana não depender de uma carta só.

Tudo fica em cache em precos/fc26/ (fora do git, ver AGENTS.md). Uma segunda
execução não volta a pagar o que já está em disco.
"""

import json
import sys
from pathlib import Path

import parse_api as P

PASTA = Path(__file__).with_name("precos") / "fc26"
RATINGS = [83, 84, 85, 86, 87]
CARTAS_POR_RATING = 13


def _cache(nome, obter):
    f = PASTA / nome
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    dados = obter()
    PASTA.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(dados), encoding="utf-8")
    return dados


def _transaccionaveis(resultados):
    """Gold rare normais com preço de PC. Preço 0 = sem mercado (não
    transaccionável ou sem listagens): não diz nada sobre o mercado."""
    return [
        r for r in resultados
        if (r.get("version") or "").lower() in ("normal", "gold rare", "rare")
        and int(r.get("price_pc_coins") or 0) > 0
    ]


def escolher_como_no_estudo(resultados, n=CARTAS_POR_RATING):
    """As primeiras n cartas pela ordem do site — o critério dos estudos já
    feitos (FC 26 e medição do FC 27).

    Só existe para os relatórios reproduzirem esses estudos com as cartas que
    estão em cache. Não serve para escolher fodder: a revisão de 01/10/2026
    mostrou que, nas 86 do FC 27, escolhia cartas de 61 500 e 21 750 quando
    as mais baratas estavam a 3 800. Para descargas novas: escolher_fodder.
    """
    return _transaccionaveis(resultados)[:n]


def escolher_fodder(resultados, n=CARTAS_POR_RATING):
    """As n cartas mais baratas no PC — o fodder, que é o que o conselheiro
    manda comprar."""
    return sorted(_transaccionaveis(resultados), key=lambda r: int(r["price_pc_coins"]))[:n]


def cartas_do_rating(rating):
    return _cache(f"lista_{rating}.json", lambda: P.chamar(
        "get_players_by_rating", year="26", min_rating=rating, max_rating=rating,
        version="gold_rare", platform="pc", page=1,
    ))


def historico(carta_id):
    return _cache(f"hist_{carta_id}.json", lambda: P.chamar(
        "get_player_price_history", year="26", platform="pc",
        player_id=carta_id, graph_type="daily_graph",
    ))


if __name__ == "__main__":
    so_listas = "--so-listas" in sys.argv
    for rating in RATINGS:
        lista = cartas_do_rating(rating)
        escolhidas = escolher_como_no_estudo(lista["results"])
        print(f"{rating}: {len(lista['results'])} na página, {len(escolhidas)} escolhidas")
        if so_listas:
            continue
        for carta in escolhidas:
            h = historico(int(carta["id"]))
            print(f"   {carta['id']:>6} {carta['name'][:24]:24} {len(h.get('prices', []))} dias")
    print("gasto no mês:", P.gasto_no_mes())
