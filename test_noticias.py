"""Testes da recolha de notícias. Não tocam na rede."""

from datetime import datetime, timedelta, timezone

import pytest

import noticias as N

AGORA = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

RSS = """<?xml version="1.0"?><rss><channel>
<item><title><![CDATA[FC 27 Destined for Glory Team 2 Players Leaked]]></title>
<link>https://soccergaming.com/a</link><pubDate>Mon, 28 Sep 2026 15:13:00 +0000</pubDate></item>
<item><title>EA FC 27 TOTW 3 Leaks: Odegaard &amp; Chawinga - RealSport101</title>
<link>https://news.google.com/x</link><pubDate>Wed, 30 Sep 2026 19:22:00 +0200</pubDate></item>
<item><title>Liverpool 27-28 Away Kit Leaked - Footy Headlines</title>
<link>https://f/x</link><pubDate>Tue, 29 Sep 2026 09:46:00 GMT</pubDate></item>
<item><title>Sem data</title><link>https://x</link></item>
</channel></rss>"""


@pytest.mark.parametrize("titulo, esperado", [
    ("FC 27 Destined for Glory Team 2 Players Leaked", "leak"),
    ("FC 27 TOTW 3 Leaks: Odegaard, Chawinga & Full Squad Stats", "leak"),
    ("FC 27 League & Nation Advanced SBC: All Requirements", "sbc"),
    ("EA Sports FC 27 Team of the Week 3 Revealed", "totw"),
    ("FC 27 Pivot Shift Evolution Guide: Best Players", "evolucao"),
    ("FC 27 Red Bull Promo Explained: Rewards & How It Works", "promo"),
    ("FC 27 Ultimate Scream start date", "promo"),
    # Ruído: fala do jogo mas não mexe no mercado.
    ("Liverpool 27-28 Away Kit Leaked", None),
    ("EA FC 27 Career Mode Update: Transfers, OVR Fixes", None),
    ("FC 27 Burger King promo explained: How to get codes and rewards", None),
    ("FC 27 Lite Lets You Play The Game for Free", None),
    # Fala de promos mas não do jogo.
    ("Premier League Team of the Week: Gameweek 6", None),
    ("Football Manager 27 promo leaked", None),
])
def test_classificar(titulo, esperado):
    assert N.classificar(titulo) == esperado


def test_ler_rss_converte_para_utc_e_tira_cdata_e_entidades():
    itens = N.ler_rss(RSS, "teste")
    assert len(itens) == 3  # o item sem data fica de fora
    assert itens[0]["titulo"] == "FC 27 Destined for Glory Team 2 Players Leaked"
    assert itens[1]["titulo"].startswith("EA FC 27 TOTW 3 Leaks: Odegaard & Chawinga")
    # 19:22 em +0200 são 17:22 UTC. Compara-se o texto e não o datetime:
    # datetimes com fuso são iguais em qualquer fuso, e passavam sem a
    # conversão, mas o CSV gravava "+02:00" ao lado de linhas em UTC.
    assert itens[1]["publicado_em"].isoformat() == "2026-09-30T17:22:00+00:00"


def test_juntar_filtra_e_regista_os_dois_instantes():
    linhas, novas = N.juntar([], N.ler_rss(RSS, "teste"), AGORA)
    assert [n["categoria"] for n in novas] == ["leak", "leak"]  # o kit saiu
    assert novas[0]["publicado_em"] == "2026-09-28T15:13:00+00:00"
    assert all(n["visto_em"] == AGORA.isoformat(timespec="seconds") for n in novas)


def test_a_mesma_noticia_em_duas_fontes_conta_uma_vez():
    a = {"publicado_em": AGORA, "fonte": "gnews_leaks", "link": "g",
         "titulo": "FC 27 Destined for Glory Team 2 Players Leaked - Insider Gaming"}
    b = dict(a, fonte="soccergaming", link="s",
             titulo="FC 27 Destined for Glory Team 2 Players Leaked")
    _, novas = N.juntar([], [a, b], AGORA)
    assert len(novas) == 1


def test_recolha_posterior_nao_apaga_nem_adia_o_visto_em():
    primeira, _ = N.juntar([], N.ler_rss(RSS, "teste"), AGORA)
    depois = AGORA + timedelta(hours=2)
    segunda, novas = N.juntar([dict(l) for l in primeira], N.ler_rss(RSS, "outra"), depois)
    assert novas == []
    assert segunda == primeira


def test_gravar_e_ler_devolve_o_mesmo(tmp_path):
    caminho = tmp_path / "noticias.csv"
    linhas, _ = N.juntar([], N.ler_rss(RSS, "teste"), AGORA)
    N.gravar(linhas, caminho)
    assert N.ler_registo(caminho) == linhas


def test_gravar_usa_fins_de_linha_unix(tmp_path):
    # Com "\r\n" a primeira recolha no Linux reescreveu as 13 linhas do
    # registo só por causa dos fins de linha.
    caminho = tmp_path / "noticias.csv"
    linhas, _ = N.juntar([], N.ler_rss(RSS, "teste"), AGORA)
    N.gravar(linhas, caminho)
    assert b"\r" not in caminho.read_bytes()


def test_uma_fonte_em_baixo_nao_cala_as_outras(tmp_path, monkeypatch):
    def descarregar(url):
        if url == "mau":
            raise OSError("em baixo")
        return RSS

    monkeypatch.setattr(N, "descarregar", descarregar)
    novas, falhas = N.recolher(tmp_path / "n.csv", {"a": "mau", "b": "bom"}, AGORA)
    assert len(novas) == 2 and len(falhas) == 1


def test_ao_vivo_junta_o_arquivo_e_as_fontes_sem_gravar(tmp_path, monkeypatch):
    arquivo = tmp_path / "noticias.csv"
    antigas, _ = N.juntar([], N.ler_rss(RSS, "teste"), AGORA)
    N.gravar(antigas, arquivo)
    antes = arquivo.read_bytes()

    nova = RSS.replace("Destined for Glory Team 2 Players Leaked", "Team 3 SBC leaked")
    def descarregar(url):
        if url == "b":
            raise OSError("fonte em baixo")
        return nova

    monkeypatch.setattr(N, "descarregar", descarregar)
    linhas, novas, falhas = N.ao_vivo(arquivo, {"a": "a", "b": "b"}, AGORA + timedelta(hours=1))

    assert [n["titulo"] for n in novas] == ["FC 27 Team 3 SBC leaked"]
    assert len(linhas) == len(antigas) + 1
    assert len(falhas) == 1
    # Não grava: o arquivo é só da recolha agendada.
    assert arquivo.read_bytes() == antes
