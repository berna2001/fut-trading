"""Cartas das promos grandes do FC 26, com a data e hora a que saiu cada uma.

Para o estudo "o que uma promo faz às cartas base dos jogadores que recebem
carta nova" é preciso saber quem recebeu carta e QUANDO: numa promo a Team 1
sai numa sexta e a Team 2 na seguinte, e medir uma carta da Team 2 a partir
da data da Team 1 dava resultados errados.

Fonte: as páginas de "rarities" do FUT.GG (e a de squads do Future Stars, que
não tem página de rarity no índice). São públicas, o robots.txt do FUT.GG não
as proíbe, e trazem por carta o nome, o rating, o identificador e o createdAt.
Encontradas no índice https://www.fut.gg/rarities/ a 21/10/2026, não
adivinhadas (regra do AGENTS.md). As páginas trazem também um preço
(currentDbPrice), que NÃO se extrai.

Urgência: estas páginas mostram o FC 26 porque o FC 27 ainda não teve estas
promos; quando tiver (o Ultimate Scream do FC 27 abre a 23/10/2026), passam a
mostrar o FC 27. Por isso o HTML em bruto fica guardado em precos/futgg/.
"""

import csv
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

PASTA = Path(__file__).with_name("precos") / "futgg"
SAIDA = PASTA / "cartas_promos_fc26.csv"
BASE = "https://www.fut.gg"

PAGINAS = {
    "Ultimate Scream": "/rarities/ultimate-scream/",
    "Thunderstruck": "/rarities/thunderstruck/",
    "Team of the Year": "/rarities/team-of-the-year/",
    "Future Stars": "/squads/future-stars/future-stars/",
    "FUT Birthday": "/rarities/fut-birthday/",
    "Team of the Season": "/rarities/team-of-the-season/",
    "Futties": "/rarities/futties/",
}
COLUNAS = ["promo", "ea_id", "jogador_id", "jogador_slug", "nome", "rating", "raridade", "saiu_em",
           "nacao_id", "liga_id", "clube_id"]

_ALT = re.compile(r'futgg-player-item-card/26-(\d+)\.[^"]*" alt="([^"]+) - (\d{2}) - ([^"]+)"')
_DATA = re.compile(r'item-social-small/26-(\d+)\.[^"]*",isCurrentGame:[^,]*,createdAt:"([^"]+)"')
_LINK = re.compile(r'href="/players/(\d+)-([a-z0-9\-]+)/26-(\d+)/"')
_PAGINAS = re.compile(r'href="[^"]*\?page=(\d+)"')
# Nação, liga e clube de cada carta: os identificadores da EA nos endereços
# das imagens. Dentro de cada carta vêm por esta ordem — clube, nação, liga,
# imagem da carta (com o ea_id) e createdAt — por isso os de uma carta são os
# últimos antes da sua imagem. Os nomes vêm à parte (_NOMES): um objecto
# repetido na página aparece só como referência ($R[n]), sem o nome.
_IMAGEM = {tipo: re.compile(rf'{tipo}ImageUrl:"[^"]*/2026/{tipo}/(\d+)\.')
           for tipo in ("nation", "league", "club")}
_NOMES = re.compile(r'eaId:(\d+),(?:game:"\d+",)?slug:"[^"]*",name:"([^"]+)",[^{}]*?'
                    r'imagePath:"2026/(nation|league|club)/')


def extrair(html_texto, promo):
    """Cartas de uma página: [{promo, ea_id, jogador_id, jogador_slug, nome,
    rating, raridade, saiu_em}]. Só cartas com data e nome; sem preços."""
    # html.unescape: um nome com entidades ("Jo&#227;o") não se encontrava
    # depois na pesquisa do parse.bot, e cada pesquisa custa um crédito.
    nomes = {ea: (html.unescape(nome), int(r), html.unescape(rar))
             for ea, nome, r, rar in _ALT.findall(html_texto)}
    datas = dict(_DATA.findall(html_texto))
    jogadores = {ea: (jid, slug) for jid, slug, ea in _LINK.findall(html_texto)}
    ligacoes = _ligacoes(html_texto)
    cartas = []
    for ea, (nome, rating, raridade) in nomes.items():
        if ea not in datas:
            continue
        jid, slug = jogadores.get(ea, ("", ""))
        nacao, liga, clube = ligacoes.get(ea, ("", "", ""))
        cartas.append({"promo": promo, "ea_id": ea, "jogador_id": jid, "jogador_slug": slug,
                       "nome": nome, "rating": rating, "raridade": raridade,
                       "saiu_em": datas[ea], "nacao_id": nacao, "liga_id": liga,
                       "clube_id": clube})
    return cartas


def _ligacoes(html_texto):
    """{ea_id: (nação, liga, clube)}: os últimos ids de cada tipo antes da
    imagem da carta."""
    posicoes = {tipo: [(m.start(), m.group(1)) for m in r.finditer(html_texto)]
                for tipo, r in _IMAGEM.items()}
    out = {}
    # A imagem da carta aparece duas vezes: uma solta, mais acima, e outra
    # dentro do registo, colada ao createdAt. Só a segunda tem antes de si a
    # nação, a liga e o clube da própria carta; a primeira tem os da carta
    # anterior (o João Félix saía com o clube do Vinícius).
    for m in _DATA.finditer(html_texto):
        ids = []
        for tipo in ("nation", "league", "club"):
            antes = [v for p, v in posicoes[tipo] if p < m.start()]
            ids.append(antes[-1] if antes else "")
        out[m.group(1)] = tuple(ids)
    return out


def nomes_de_ligacoes(html_texto):
    """{(tipo, id): nome} para nações, ligas e clubes definidos na página."""
    return {(tipo, i): html.unescape(nome) for i, nome, tipo in _NOMES.findall(html_texto)}


def ultima_pagina(html_texto):
    numeros = [int(n) for n in _PAGINAS.findall(html_texto)]
    return max(numeros) if numeros else 1


def descarregar(caminho, ficheiro, pausa=2.0):
    """Lê do disco se já foi descarregada; senão descarrega e guarda."""
    if ficheiro.exists():
        return ficheiro.read_text(encoding="utf-8")
    pedido = urllib.request.Request(BASE + caminho, headers={"User-Agent": "Mozilla/5.0 fut-trading"})
    with urllib.request.urlopen(pedido, timeout=30) as r:
        texto = r.read().decode("utf-8", errors="replace")
    PASTA.mkdir(parents=True, exist_ok=True)
    ficheiro.write_text(texto, encoding="utf-8")
    time.sleep(pausa)  # educado com o site
    return texto


def recolher():
    cartas = []
    for promo, caminho in PAGINAS.items():
        nome = caminho.strip("/").replace("/", "_")
        primeira = descarregar(caminho, PASTA / f"{nome}_p1.html")
        if "EA SPORTS FC 26" not in primeira:
            raise RuntimeError(f"{promo}: a página já não é do FC 26 ({caminho})")
        paginas = [primeira] + [
            descarregar(f"{caminho}?page={n}", PASTA / f"{nome}_p{n}.html")
            for n in range(2, ultima_pagina(primeira) + 1)
        ]
        for texto in paginas:
            cartas += extrair(texto, promo)
    vistos, unicas = set(), []
    for c in cartas:
        if (c["promo"], c["ea_id"]) not in vistos:
            vistos.add((c["promo"], c["ea_id"]))
            unicas.append(c)
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(unicas)
    return unicas


if __name__ == "__main__":
    cartas = recolher()
    from collections import Counter
    for promo, n in Counter(c["promo"] for c in cartas).items():
        print(f"{promo}: {n} cartas")
    print(f"total {len(cartas)} -> {SAIDA}", file=sys.stderr)
