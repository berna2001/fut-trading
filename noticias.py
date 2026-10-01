"""Recolha de notícias e leaks que mexem no mercado do FC 27.

Os leaks aparecem primeiro no X (FutPoliceLeaks, Futdonk, fifa_romania...),
mas a API do X deixou de ter plano gratuito em Fevereiro de 2026. Os sites de
notícias republicam esses leaks, e os RSS deles são gratuitos. O atraso face
ao X não está medido. Exemplo verificado: o leak da Destined for Glory
Team 2 saiu no SoccerGaming e no Insider Gaming a 28/09/2026, para uma promo
que só abre a 02/10.

Cada notícia fica com dois instantes:
  publicado_em — a data do RSS, quando a notícia ficou pública;
  visto_em     — quando esta recolha a leu pela primeira vez.
Num backtest decide-se só com o que já era público no instante da decisão
(regra do AGENTS.md). Para medir o atraso real da recolha, usa-se o visto_em.
"""

import csv
import hashlib
import html
import re
import sys
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

REGISTO = Path(__file__).with_name("noticias.csv")
COLUNAS = ["id", "publicado_em", "visto_em", "fonte", "categoria", "titulo", "link"]

_GN = "https://news.google.com/rss/search?hl=en-GB&gl=GB&ceid=GB:en&q="
# Várias pesquisas estreitas em vez de uma larga: o Google News devolve no
# máximo 100 itens por pesquisa, e uma pesquisa larga enche-se de artigos de
# Career Mode e de equipamentos.
FONTES = {
    "gnews_leaks": _GN + "%22FC+27%22+(leak+OR+leaked+OR+leaks)+when:2d",
    "gnews_sbc": _GN + "%22FC+27%22+(SBC+OR+%22squad+building%22)+when:2d",
    "gnews_promo": _GN + "%22FC+27%22+(promo+OR+%22team+of+the+week%22+OR+TOTW+OR+evolution)+when:2d",
    "soccergaming": "https://soccergaming.com/feed/",
}

# Tem de falar do jogo...
_JOGO = re.compile(r"\b(FC ?27|EA ?FC|EA Sports FC|Ultimate Team|FUT)\b", re.I)

# ...e de alguma coisa que mexa no mercado. A ordem conta: a primeira
# categoria que casar é a que fica. Um leak de um SBC é "leak", porque é a
# antecipação que tem valor de trading.
CATEGORIAS = [
    ("leak", re.compile(r"\b(leak(s|ed)?|rumou?r(s|ed)?|insider)\b", re.I)),
    ("sbc", re.compile(r"\b(SBCs?|squad building)\b", re.I)),
    ("totw", re.compile(r"\b(TOTW|team of the week)\b", re.I)),
    ("evolucao", re.compile(r"\b(evo(lution)?s?)\b", re.I)),
    ("promo", re.compile(
        r"\b(promos?|team \d|campaign|icons?|heroes|"
        r"future stars|ultimate scream|hall of fut|wildcards?|"
        r"team of the year|TOTY|TOTS|destined for glory|path to glory|"
        r"black friday|objectives?|upgrades?|packs?)\b", re.I)),
]

# Ruído frequente nas mesmas pesquisas. Um título que case aqui sai, mesmo que
# fale de promos: "Liverpool 27-28 Away Kit Leaked" não mexe no mercado.
_RUIDO = re.compile(
    r"\b(kits?|career mode|codes?|redeem|pre-?order|"
    r"football manager|eFootball|NBA 2K|Madden|"
    r"best young|ranked)\b", re.I)


def classificar(titulo):
    """Devolve a categoria de mercado do título, ou None se não interessar."""
    if not _JOGO.search(titulo) or _RUIDO.search(titulo):
        return None
    for nome, padrao in CATEGORIAS:
        if padrao.search(titulo):
            return nome
    return None


def _texto(bloco, etiqueta):
    m = re.search(rf"<{etiqueta}[^>]*>(.*?)</{etiqueta}>", bloco, re.S)
    if not m:
        return ""
    t = m.group(1).strip()
    t = re.sub(r"^<!\[CDATA\[(.*)\]\]>$", r"\1", t, flags=re.S)
    return html.unescape(t).strip()


def ler_rss(xml, fonte):
    """Extrai (publicado_em, fonte, titulo, link) de um RSS 2.0."""
    itens = []
    for bloco in re.findall(r"<item>(.*?)</item>", xml, re.S):
        titulo, link, data = _texto(bloco, "title"), _texto(bloco, "link"), _texto(bloco, "pubDate")
        if not titulo or not data:
            continue
        publicado = parsedate_to_datetime(data).astimezone(timezone.utc)
        itens.append({"publicado_em": publicado, "fonte": fonte, "titulo": titulo, "link": link})
    return itens


def identificador(titulo):
    """O mesmo artigo aparece em várias pesquisas e com links diferentes (o
    Google News embrulha-os). Identifica-se pelo título normalizado, sem o
    " - Fonte" que o Google News acrescenta no fim."""
    base = re.sub(r"\s+-\s+[^-]+$", "", titulo).lower()
    base = re.sub(r"[^a-z0-9]+", " ", base).strip()
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def ler_registo(caminho=REGISTO):
    if not Path(caminho).exists():
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def juntar(existentes, itens, agora):
    """Acrescenta as notícias relevantes ainda não registadas.

    Nunca altera nem apaga uma linha existente: o visto_em de uma notícia é o
    da primeira vez que foi vista, e uma recolha posterior não o pode adiar.
    Devolve (linhas, novas).
    """
    vistos = {l["id"] for l in existentes}
    novas = []
    for it in sorted(itens, key=lambda i: i["publicado_em"]):
        categoria = classificar(it["titulo"])
        nid = identificador(it["titulo"])
        if categoria is None or nid in vistos:
            continue
        vistos.add(nid)
        novas.append({
            "id": nid,
            "publicado_em": it["publicado_em"].isoformat(timespec="seconds"),
            "visto_em": agora.isoformat(timespec="seconds"),
            "fonte": it["fonte"],
            "categoria": categoria,
            "titulo": it["titulo"],
            "link": it["link"],
        })
    return existentes + novas, novas


def gravar(linhas, caminho=REGISTO):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        # "\n" e não o "\r\n" de omissão do csv: o ficheiro é escrito no
        # Windows e na Action (Linux), e com "\r\n" cada recolha no Linux
        # reescrevia todas as linhas no diff (commit 53e75e2).
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def descarregar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 fut-trading"})
    with urllib.request.urlopen(pedido, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def recolher(caminho=REGISTO, fontes=FONTES, agora=None):
    agora = agora or datetime.now(timezone.utc)
    itens, falhas = [], []
    for nome, url in fontes.items():
        # Uma fonte em baixo não pode calar as outras.
        try:
            itens += ler_rss(descarregar(url), nome)
        except Exception as e:
            falhas.append(f"{nome}: {type(e).__name__}: {e}")
    linhas, novas = juntar(ler_registo(caminho), itens, agora)
    gravar(linhas, caminho)
    return novas, falhas


if __name__ == "__main__":
    novas, falhas = recolher()
    for n in novas:
        print(f"[{n['categoria']}] {n['publicado_em']}  {n['titulo']}")
    print(f"{len(novas)} novas")
    for f in falhas:
        print("FALHOU", f, file=sys.stderr)
    # Só falha se TODAS as fontes falharem: aí não há recolha nenhuma.
    sys.exit(1 if len(falhas) == len(FONTES) else 0)
