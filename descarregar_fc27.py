"""Descarga para medir no FC 27 o que o estudo do FC 26 não pôde medir.

O estudo do FC 26 usou médias diárias, que não são preços executáveis. Aqui
mede-se com as vendas reais: a que preço se compra e se vende de facto,
face à média que o FUTBIN mostra, e quantas vendas há por hora.

Custo, pelos preços de 01/10/2026:
  lista de cartas 86:          5
  6 históricos horários:  6 × 2 = 12
  6 históricos de vendas: 6 × 2 = 12
  total:                       29 — os que restavam dos 200 do mês.

Só o rating 86, porque não há créditos para mais: no FC 26 foi dos que se
mantiveram positivos nas duas metades da época. Os outros ficam para o mês
seguinte.

Cache em precos/fc27/ (fora do git). Uma segunda execução não paga nada.
"""

import sys

import descarregar_fc26 as D26
import parse_api as P

PASTA = D26.PASTA.parent / "fc27"
N_CARTAS = 6


def _cache(nome, obter):
    f = PASTA / nome
    if f.exists():
        return D26.json.loads(f.read_text(encoding="utf-8"))
    dados = obter()
    PASTA.mkdir(parents=True, exist_ok=True)
    f.write_text(D26.json.dumps(dados), encoding="utf-8")
    return dados


def lista():
    return _cache("lista_86.json", lambda: P.chamar(
        "get_players_by_rating", year="27", min_rating=86, max_rating=86,
        version="gold_rare", platform="pc", page=1,
    ))


def lista_fodder(rating, pagina=1):
    """Cartas gold rare de um rating, ordenadas pelo preço de PC, as mais
    baratas primeiro: o fodder. 5 créditos por página.

    Ordenado pelo site sobre o catálogo inteiro, não só sobre uma página. As
    cartas sem preço (0) vêm primeiro e o escolher_fodder deita-as fora.
    """
    return _cache(f"fodder_{rating}_p{pagina}.json", lambda: P.chamar(
        "get_players_by_rating", year="27", min_rating=rating, max_rating=rating,
        version="gold_rare", platform="pc", sort_by_price="asc", page=pagina,
    ))


def fodder(rating, n=N_CARTAS):
    """As n cartas mais baratas do rating no PC."""
    return D26.escolher_fodder(lista_fodder(rating)["results"], n)


def horario(carta_id):
    return _cache(f"horario_{carta_id}.json", lambda: P.chamar(
        "get_player_price_history", year="27", platform="pc",
        player_id=carta_id, graph_type="hourly_graph",
    ))


def vendas(carta_id):
    return _cache(f"vendas_{carta_id}.json", lambda: P.chamar(
        "get_fc27_sales_history", platform="pc", player_id=carta_id,
    ))


if __name__ == "__main__":
    escolhidas = D26.escolher_como_no_estudo(lista()["results"], N_CARTAS)
    print(f"{len(escolhidas)} cartas 86 escolhidas")
    if "--so-lista" in sys.argv:
        sys.exit(0)
    for c in escolhidas:
        h = horario(int(c["id"]))
        v = vendas(int(c["id"]))
        print(f"  {c['id']:>6} {c['name'][:24]:24} {len(h.get('prices', []))} horas, "
              f"{v['summary']['observed_rows']} vendas")
    print("gasto no mês:", P.gasto_no_mes())
