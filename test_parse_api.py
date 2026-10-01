"""Testes do cliente do parse.bot. Não tocam na rede nem gastam créditos."""

import io
import json
from datetime import datetime, timezone

import pytest

import parse_api as P

OUTUBRO = datetime(2026, 10, 15, tzinfo=timezone.utc)


def _livro(tmp_path, linhas):
    f = tmp_path / "creditos.csv"
    f.write_text(
        "instante,endpoint,parametros,creditos\n"
        + "".join(f"{i},{e},{{}},{c}\n" for i, e, c in linhas),
        encoding="utf-8",
    )
    return f


def test_gasto_conta_so_o_mes_corrente(tmp_path):
    livro = _livro(tmp_path, [
        ("2026-09-30T23:59:00+00:00", "x", 50),
        ("2026-10-01T00:00:00+00:00", "x", 7),
        ("2026-10-20T10:00:00+00:00", "x", 3),
        ("2027-10-02T10:00:00+00:00", "x", 99),   # mesmo mês, outro ano
    ])
    assert P.gasto_no_mes(livro, OUTUBRO) == 10


def test_orcamento_recusa_o_que_passa_o_limite_e_aceita_o_que_cabe(tmp_path):
    livro = _livro(tmp_path, [("2026-10-01T00:00:00+00:00", "x", 190)])
    # 190 + 10 = 200 cabe exactamente; 190 + 10 + 1 já não.
    P.verificar_orcamento("get_fc27_market_snapshot", livro, OUTUBRO)
    _livro(tmp_path, [("2026-10-01T00:00:00+00:00", "x", 191)])
    with pytest.raises(P.OrcamentoEsgotado):
        P.verificar_orcamento("get_fc27_market_snapshot", livro, OUTUBRO)


def test_endpoint_sem_custo_e_recusado(tmp_path):
    with pytest.raises(P.ErroParse):
        P.verificar_orcamento("endpoint_inventado", tmp_path / "c.csv", OUTUBRO)


class _Resposta(io.BytesIO):
    def __init__(self, corpo, cobrado):
        super().__init__(json.dumps(corpo).encode())
        self.headers = {"X-Credits-Charged": cobrado} if cobrado else {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _servidor(monkeypatch, corpo, cobrado="2"):
    pedidos = []

    def urlopen(pedido, timeout):
        pedidos.append(pedido)
        return _Resposta(corpo, cobrado)

    monkeypatch.setenv("PARSE_API_KEY", "pmx_teste")
    monkeypatch.setattr(P.urllib.request, "urlopen", urlopen)
    return pedidos


def test_chamada_anota_o_cobrado_e_o_gasto_sobe(tmp_path, monkeypatch):
    livro = tmp_path / "creditos.csv"
    _servidor(monkeypatch, {"status": "success", "data": {"prices": []}}, cobrado="2")
    P.chamar("get_player_price_history", livro=livro, player_id=1)
    P.chamar("get_player_price_history", livro=livro, player_id=2)
    assert P.gasto_no_mes(livro) == 4
    assert b"\r" not in livro.read_bytes()  # mesmo ficheiro no Windows e no Linux


def test_sem_cabecalho_conta_o_preco_de_tabela(tmp_path, monkeypatch):
    livro = tmp_path / "creditos.csv"
    _servidor(monkeypatch, {"status": "success", "data": {}}, cobrado=None)
    P.chamar("get_fc27_market_snapshot", livro=livro, player_ids="1")
    assert P.gasto_no_mes(livro) == 10


def test_historico_pede_sempre_pc_e_converte_os_instantes(tmp_path, monkeypatch):
    corpo = {"status": "success", "data": {"prices": [
        {"timestamp": 1789084800000, "price": 769},
        {"timestamp": 1789171200000, "price": 750},
    ]}}
    pedidos = _servidor(monkeypatch, corpo)
    serie = P.historico_precos(437, ano="27", livro=tmp_path / "c.csv")

    url = pedidos[0].full_url
    assert "platform=pc" in url and "player_id=437" in url and "year=27" in url
    assert pedidos[0].headers["X-api-key"] == "pmx_teste"
    assert serie == [
        (datetime(2026, 9, 11, tzinfo=timezone.utc), 769),
        (datetime(2026, 9, 12, tzinfo=timezone.utc), 750),
    ]


def test_resposta_sem_sucesso_levanta_erro_mas_fica_anotada(tmp_path, monkeypatch):
    livro = tmp_path / "creditos.csv"
    _servidor(monkeypatch, {"status": "error", "error": "x"}, cobrado="2")
    with pytest.raises(P.ErroParse):
        P.chamar("get_player_price_history", livro=livro, player_id=1)
    # O servidor cobrou: o crédito gasto tem de constar, mesmo com o erro.
    assert P.gasto_no_mes(livro) == 2


def test_custos_batem_com_o_agents_md():
    # O AGENTS.md cita custos; se um mudar aqui sem mudar lá, ficam a divergir.
    texto = open("AGENTS.md", encoding="utf-8").read()
    for endpoint in ["get_player_price_history", "get_fc27_sales_history",
                     "get_players_by_rating", "get_fc27_market_snapshot",
                     "get_fc27_sbcs_list"]:
        linha = next(l for l in texto.splitlines() if f"`{endpoint}`" in l)
        assert linha.rstrip(" |").endswith(str(P.CUSTO[endpoint])), endpoint


def _erro_429(retry_after=7):
    corpo = json.dumps({"error": {"error": "Rate limit exceeded", "retry_after": retry_after}})
    return P.urllib.error.HTTPError("u", 429, "Too Many Requests", {}, io.BytesIO(corpo.encode()))


def test_429_espera_o_que_o_servidor_manda_e_tenta_outra_vez(tmp_path, monkeypatch):
    livro = tmp_path / "creditos.csv"
    respostas = [_erro_429(7), _erro_429(3),
                 _Resposta({"status": "success", "data": {"ok": 1}}, "2")]

    def urlopen(pedido, timeout):
        r = respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setenv("PARSE_API_KEY", "pmx_teste")
    monkeypatch.setattr(P.urllib.request, "urlopen", urlopen)
    esperas = []
    dados = P.chamar("get_player_price_history", livro=livro, _dormir=esperas.append, player_id=1)
    assert dados == {"ok": 1}
    assert esperas == [8, 4]
    # Os 429 não cobraram (sem cabeçalho): só o pedido que passou conta.
    assert P.gasto_no_mes(livro) == 2


def test_429_sem_fim_acaba_em_erro(tmp_path, monkeypatch):
    def urlopen(pedido, timeout):
        raise _erro_429(1)

    monkeypatch.setenv("PARSE_API_KEY", "pmx_teste")
    monkeypatch.setattr(P.urllib.request, "urlopen", urlopen)
    esperas = []
    with pytest.raises(P.ErroParse):
        P.chamar("get_player_price_history", livro=tmp_path / "c.csv",
                 _dormir=esperas.append, player_id=1)
    assert len(esperas) == P.TENTATIVAS_429 - 1
