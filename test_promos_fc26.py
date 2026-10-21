"""Testes da extracção das cartas das promos do FC 26. Sem rede."""

import promos_fc26 as PR

# Recorte com a forma das páginas do FUT.GG (21/10/2026): a imagem da carta
# com o alt "Nome - rating - Raridade", a ligação do jogador, e os dados com
# o createdAt. Inclui um preço, que não pode ser extraído.
PAGINA = """
<a href="/players/238794-vinicius-jr/26-67347658/"><img src="https://x/2026/futgg-player-item-card/26-67347658.abc.webp" alt="Vini Jr. - 90 - Ultimate Scream"/></a>
<a href="/players/242444-joao-felix/26-67351308/"><img src="https://x/2026/futgg-player-item-card/26-67351308.def.webp" alt="Jo&#227;o F&#233;lix - 86 - Ultimate Scream"/></a>
<a href="/players/1-sem-data/26-999/"><img src="https://x/2026/futgg-player-item-card/26-999.ghi.webp" alt="Sem Data - 85 - Ultimate Scream"/></a>
{currentDbPrice:123456,socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-67347658.b46.webp",isCurrentGame:!1,createdAt:"2025-10-24T17:00:20.165471Z"}
{currentDbPrice:654321,socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-67351308.61b.webp",isCurrentGame:!1,createdAt:"2025-10-31T18:00:28.203383Z"}
<a href="/rarities/ultimate-scream/?page=2">2</a><a href="/rarities/ultimate-scream/?page=3">3</a>
"""


def test_extrai_nome_rating_data_e_jogador_sem_preco():
    cartas = {c["ea_id"]: c for c in PR.extrair(PAGINA, "Ultimate Scream")}
    assert set(cartas) == {"67347658", "67351308"}       # a sem data fica de fora
    vini = cartas["67347658"]
    assert vini["nome"] == "Vini Jr." and vini["rating"] == 90
    assert vini["saiu_em"] == "2025-10-24T17:00:20.165471Z"
    assert vini["jogador_id"] == "238794" and vini["jogador_slug"] == "vinicius-jr"
    # Cada carta com a sua data: a Team 2 saiu uma semana depois.
    assert cartas["67351308"]["saiu_em"].startswith("2025-10-31")
    assert cartas["67351308"]["nome"] == "João Félix"   # entidades desfeitas
    # Nenhum campo com preço, nem o valor do preço em lado nenhum.
    for c in cartas.values():
        assert set(c) == set(PR.COLUNAS)
        assert "123456" not in str(c) and "654321" not in str(c)


def test_ultima_pagina():
    assert PR.ultima_pagina(PAGINA) == 3
    assert PR.ultima_pagina("<html>sem paginação</html>") == 1


def test_colunas_nao_tem_preco():
    import guardar_precos as G
    assert not any(G.e_preco(c) for c in PR.COLUNAS)


# Duas cartas seguidas, com a forma real (21/10/2026): a imagem de cada carta
# aparece uma vez solta, antes, e outra dentro do registo, a seguir ao clube,
# à nação e à liga da própria carta. A primeira versão do extractor usava a
# solta e dava à 2.ª carta a nação, a liga e o clube da 1.ª.
DUAS = """
<img src="https://x/2026/futgg-player-item-card/26-111.a.webp" alt="Vini Jr. - 90 - Ultimate Scream"/>
<img src="https://x/2026/futgg-player-item-card/26-222.b.webp" alt="João Félix - 86 - Ultimate Scream"/>
socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-111.s.webp" ,eaId:111,commonName:"Vini Jr.",
clubImageUrl:"https://x/2026/club/243.c.png",nationImageUrl:"https://x/2026/nation/54.n.png",leagueImageUrl:"https://x/2026/league/53.l.png",
socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-111.s.webp",isCurrentGame:!1,createdAt:"2025-10-24T17:00:00Z",
club:$R[1]={id:1,eaId:243,game:"26",slug:"243-real-madrid",name:"Real Madrid",leagueEaId:53,imagePath:"2026/club/243.c.png"},
nation:$R[2]={id:2,eaId:54,slug:"brazil",name:"Brazil",imagePath:"2026/nation/54.n.png"},
league:$R[3]={id:3,eaId:53,slug:"laliga",name:"LALIGA EA SPORTS",imagePath:"2026/league/53.l.png"},
socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-222.s.webp" ,eaId:222,commonName:"João Félix",
clubImageUrl:"https://x/2026/club/112139.c.png",nationImageUrl:"https://x/2026/nation/38.n.png",leagueImageUrl:"https://x/2026/league/350.l.png",
socialImageUrl:"https://x/2026/futgg-player-item-social-small/26-222.s.webp",isCurrentGame:!1,createdAt:"2025-10-31T18:00:00Z",
nation:$R[4]={id:4,eaId:38,slug:"portugal",name:"Portugal",imagePath:"2026/nation/38.n.png"},
nation:$R[2],
nation:$R[5]={id:5,eaId:108,slug:"cote-divoire",name:"C&#244;te d&#39;Ivoire",imagePath:"2026/nation/108.n.png"},
"""


def test_cada_carta_fica_com_a_sua_nacao_liga_e_clube():
    c = {k["ea_id"]: k for k in PR.extrair(DUAS, "Ultimate Scream")}
    assert (c["111"]["nacao_id"], c["111"]["liga_id"], c["111"]["clube_id"]) == ("54", "53", "243")
    assert (c["222"]["nacao_id"], c["222"]["liga_id"], c["222"]["clube_id"]) == ("38", "350", "112139")


def test_nomes_das_ligacoes_ignoram_referencias_sem_nome():
    n = PR.nomes_de_ligacoes(DUAS)
    assert n[("nation", "54")] == "Brazil" and n[("nation", "38")] == "Portugal"
    assert n[("league", "53")] == "LALIGA EA SPORTS" and n[("club", "243")] == "Real Madrid"
    assert n[("nation", "108")] == "Côte d'Ivoire"          # entidades desfeitas
    assert len([k for k in n if k[0] == "nation"]) == 3   # o "$R[2]" repetido não cria entrada
