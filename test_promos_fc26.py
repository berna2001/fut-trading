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
