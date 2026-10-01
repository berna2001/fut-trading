"""Cliente do parse.bot (futbin.com API), com livro de créditos.

O plano grátis dá 200 créditos por mês, e um ciclo mal escrito gasta-os numa
tarde. Por isso cada chamada passa por aqui: antes de chamar, confirma que o
custo cabe no orçamento do mês; depois, grava no `creditos.csv` o que o
servidor diz ter cobrado (`X-Credits-Charged`).

O saldo lê-se do nosso livro e não do cabeçalho `X-Credits-Remaining`: a
01/10/2026 esse cabeçalho mostrou 199 e 198 depois de 15 créditos gastos,
enquanto o painel do parse.bot marcava exactamente os 15 (mais 1 de um teste
feito no próprio painel). O `X-Credits-Charged` bateu certo em todas as
chamadas.
"""

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# A cópia canónica da API no marketplace. Pode ser chamada directamente com a
# chave da conta (docs.parse.bot, "Get a marketplace API's detail").
BASE = "https://api.parse.bot/scraper/21963078-8a17-40ff-a896-9b0b0ec3e828/"

# Custo por chamada, lido do campo `price` de cada endpoint em
# https://api.parse.bot/marketplace/apis/1b6234f9-0dfb-4cca-99b4-2d6d37aec6a7
# a 01/10/2026, e confirmado pelo `X-Credits-Charged` nos que foram chamados.
CUSTO = {
    "get_players": 1,
    "search_players": 1,
    "get_player_details": 1,
    "get_market_trends": 1,
    "get_players_by_league": 1,
    "search_players_fc26": 1,
    "get_evos": 1,
    "get_objectives": 1,
    "get_sbcs": 1,
    "get_fc27_sbcs_list": 1,
    "get_player_price_history": 2,
    "get_fc27_player_price": 2,
    "get_fc27_sales_history": 2,
    "search_players_fc27": 3,
    "list_fc27_players": 3,
    "get_players_by_rating": 5,
    "get_fc27_ps_market_prices": 5,
    "get_fc27_market_snapshot": 10,
    "get_fc27_ps_price_updates": 10,
    "get_fc27_sbcs": 10,
    "get_fc27_popular_players": 10,
    "fc27_sbc_solver": 10,
}

CREDITOS_MENSAIS = 200

LIVRO = Path(__file__).with_name("creditos.csv")
COLUNAS = ["instante", "endpoint", "parametros", "creditos"]


class OrcamentoEsgotado(RuntimeError):
    pass


class ErroParse(RuntimeError):
    pass


def _chave():
    chave = os.environ.get("PARSE_API_KEY")
    if chave:
        return chave
    # Localmente a chave vive num .env ignorado pelo git; na CI, num secret.
    env = Path(__file__).with_name(".env")
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            nome, _, valor = linha.partition("=")
            if nome.strip() == "PARSE_API_KEY":
                return valor.strip()
    raise ErroParse("PARSE_API_KEY não definida (nem no ambiente, nem no .env)")


def gasto_no_mes(livro=LIVRO, agora=None):
    """Créditos gastos no mês civil corrente (UTC), segundo o nosso livro.

    O parse.bot mostra uma janela móvel de 30 dias e não diz em que dia o
    saldo renova. O travão conta por mês civil, e isso NÃO impede gastar mais de
    200 em 30 dias seguidos: 200 a 31/10 e mais 200 a 01/11 passam os dois
    (revisão independente de 01/10/2026; esta docstring prometia o contrário).
    Acima do plano é o próprio servidor que recusa; o travão daqui serve para
    não gastar o mês numa tarde, não para o substituir.
    """
    agora = agora or datetime.now(timezone.utc)
    if not Path(livro).exists():
        return 0
    total = 0
    with open(livro, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            instante = datetime.fromisoformat(linha["instante"])
            if (instante.year, instante.month) == (agora.year, agora.month):
                total += int(linha["creditos"])
    return total


def _anotar(endpoint, params, creditos, livro=LIVRO, agora=None):
    novo = not Path(livro).exists()
    with open(livro, "a", newline="", encoding="utf-8") as f:
        # "\n" pela mesma razão que no noticias.gravar: o mesmo ficheiro é
        # escrito no Windows e no Linux.
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        if novo:
            w.writeheader()
        w.writerow({
            "instante": (agora or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
            "endpoint": endpoint,
            "parametros": json.dumps(params, sort_keys=True),
            "creditos": creditos,
        })


def verificar_orcamento(endpoint, livro=LIVRO, agora=None, limite=CREDITOS_MENSAIS):
    """Levanta OrcamentoEsgotado se a chamada passar o limite do mês."""
    if endpoint not in CUSTO:
        # Sem custo conhecido não há como garantir o orçamento.
        raise ErroParse(f"endpoint sem custo registado: {endpoint}")
    gasto = gasto_no_mes(livro, agora)
    if gasto + CUSTO[endpoint] > limite:
        raise OrcamentoEsgotado(
            f"{endpoint} custa {CUSTO[endpoint]}; já gastos {gasto} de {limite} este mês"
        )


# O plano grátis aceita rajadas de 30 pedidos e depois 5 por minuto (resposta
# 429 de 01/10/2026, com "retry_after" em segundos). Um 429 não é erro do
# pedido: espera-se o que o servidor manda e tenta-se outra vez.
TENTATIVAS_429 = 6


def chamar(endpoint, livro=LIVRO, _dormir=time.sleep, **params):
    """Chama um endpoint e devolve o campo `data` da resposta."""
    verificar_orcamento(endpoint, livro)
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    pedido = urllib.request.Request(url, headers={"X-API-Key": _chave()})
    for tentativa in range(TENTATIVAS_429):
        try:
            with urllib.request.urlopen(pedido, timeout=180) as r:
                cobrado = r.headers.get("X-Credits-Charged")
                corpo = json.load(r)
            break
        except urllib.error.HTTPError as e:
            cobrado = e.headers.get("X-Credits-Charged")
            if cobrado:
                _anotar(endpoint, params, int(cobrado), livro)
            texto = e.read().decode()
            if e.code == 429 and tentativa < TENTATIVAS_429 - 1:
                try:
                    espera = float(json.loads(texto)["error"]["retry_after"])
                except (ValueError, KeyError, TypeError):
                    espera = 15.0
                _dormir(espera + 1)
                continue
            raise ErroParse(f"{endpoint}: HTTP {e.code}: {texto[:300]}") from e
    # Se o servidor não disser quanto cobrou, conta-se o preço de tabela: é
    # melhor sobrestimar o gasto do que passar o limite sem saber.
    _anotar(endpoint, params, int(cobrado) if cobrado else CUSTO[endpoint], livro)
    if corpo.get("status") != "success":
        raise ErroParse(f"{endpoint}: {json.dumps(corpo)[:300]}")
    return corpo["data"]


def historico_precos(carta_id, ano="27", granularidade="daily_graph", livro=LIVRO):
    """Série de preços de uma carta no PC: lista de (datetime UTC, preço).

    'daily_graph' cobre a vida toda da carta; 'hourly_graph' só os últimos 14
    dias. Sempre `platform=pc`: o mercado de PC é separado do de consola.
    """
    dados = chamar(
        "get_player_price_history", livro=livro,
        player_id=carta_id, year=ano, platform="pc", graph_type=granularidade,
    )
    return [
        (datetime.fromtimestamp(p["timestamp"] / 1000, timezone.utc), int(p["price"]))
        for p in dados.get("prices", [])
    ]
