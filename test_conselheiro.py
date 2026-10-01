"""Testes do conselheiro. Sem rede; o relatório é lido do repositório."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import conselheiro as K

UTC = timezone.utc
# Semana de 19 a 25/10/2026 (seg-dom), ainda em hora de Verão em Londres
# (UTC+1), e uma semana de Novembro já em hora de Inverno (UTC+0).
VERAO = datetime(2026, 10, 19, 12, tzinfo=UTC)
INVERNO = datetime(2026, 11, 16, 12, tzinfo=UTC)
DEPOIS_DO_LANCAMENTO = datetime(2026, 11, 2, 12, tzinfo=UTC)  # uma segunda


def acoes(agora, saldo=100_000, noticias=()):
    return [c.acao for c in K.conselhos(agora, saldo, noticias)]


def principal(agora, saldo=100_000):
    """A recomendação de mercado do dia (nem aviso nem a de evitar)."""
    return next(c for c in K.conselhos(agora, saldo)
                if c.acao in ("COMPRAR", "VENDER", "ESPERAR"))


@pytest.mark.parametrize("dias, esperado", [
    (0, "COMPRAR"),   # segunda
    (1, "ESPERAR"),   # terça
    (2, "VENDER"),    # quarta
    (3, "VENDER"),    # quinta
    (5, "COMPRAR"),   # sábado
    (6, "COMPRAR"),   # domingo
])
def test_cada_dia_da_semana_tem_a_sua_accao(dias, esperado):
    assert principal(DEPOIS_DO_LANCAMENTO + timedelta(days=dias)).acao == esperado


@pytest.mark.parametrize("semana, hora_utc_promo", [(VERAO, 17), (INVERNO, 18)])
def test_sexta_vende_ate_as_18h_de_londres_e_depois_espera(semana, hora_utc_promo):
    sexta = semana + timedelta(days=4)
    antes = sexta.replace(hour=hora_utc_promo - 1, minute=59)
    depois = sexta.replace(hour=hora_utc_promo, minute=0)
    assert principal(antes).acao == "VENDER"
    assert principal(depois).acao == "ESPERAR"


def test_proxima_promo_e_sexta_as_18h_de_londres():
    p = K.proxima_promo(VERAO)  # segunda 19/10
    assert p.astimezone(UTC) == datetime(2026, 10, 23, 17, tzinfo=UTC)
    p = K.proxima_promo(INVERNO)
    assert p.astimezone(UTC) == datetime(2026, 11, 20, 18, tzinfo=UTC)
    # Exactamente na abertura, a próxima já é a da semana seguinte.
    assert K.proxima_promo(datetime(2026, 10, 23, 17, tzinfo=UTC)).day == 30


def test_so_se_compra_quando_o_roi_esperado_e_positivo():
    for dia in range(7):
        agora = DEPOIS_DO_LANCAMENTO + timedelta(days=dia)
        if principal(agora).acao == "COMPRAR":
            assert K.roi_esperado(agora.astimezone(K.LONDRES).weekday()) > 0
    # E o melhor dia de compra é domingo.
    assert max(range(7), key=K.roi_esperado) == 6


def test_quantia_respeita_a_reserva_e_divide_pelos_ratings():
    q = K.quantias(100_000)
    assert set(q) == {85, 86, 87}
    assert sum(q.values()) <= 70_000
    assert len(set(q.values())) == 1
    assert K.quantias(0) == {85: 0, 86: 0, 87: 0}
    sabado = DEPOIS_DO_LANCAMENTO + timedelta(days=5)
    compra = principal(sabado, saldo=50_000)
    assert compra.quantia == sum(K.quantias(50_000).values()) <= 35_000


def test_aviso_de_lancamento_so_nas_primeiras_semanas():
    assert "AVISO" in acoes(datetime(2026, 10, 3, 12, tzinfo=UTC))
    assert "AVISO" not in acoes(DEPOIS_DO_LANCAMENTO)


def test_noticias_de_promo_recentes_viram_aviso_e_as_antigas_nao():
    agora = DEPOIS_DO_LANCAMENTO
    noticias = [
        {"categoria": "leak", "titulo": "Promo X leaked", "publicado_em": agora - timedelta(days=2)},
        {"categoria": "leak", "titulo": "Promo velha", "publicado_em": agora - timedelta(days=9)},
        {"categoria": "evolucao", "titulo": "Evo nova", "publicado_em": agora - timedelta(days=1)},
    ]
    avisos = [c for c in K.conselhos(agora, 100_000, noticias) if c.acao == "AVISO"]
    assert len(avisos) == 1
    assert "Promo X leaked" in avisos[0].porque
    assert "Promo velha" not in avisos[0].porque and "Evo nova" not in avisos[0].porque


def test_varias_noticias_de_promo_dao_uma_so_caixa_da_mais_recente_para_a_mais_antiga():
    agora = DEPOIS_DO_LANCAMENTO
    noticias = [{"categoria": c, "titulo": t, "publicado_em": agora - timedelta(days=d)}
                for c, t, d in [("leak", "Antiga", 5), ("promo", "Nova", 1), ("leak", "Meio", 3)]]
    avisos = [c for c in K.conselhos(agora, 100_000, noticias) if c.acao == "AVISO"]
    assert len(avisos) == 1
    p = avisos[0].porque
    assert p.index("Nova") < p.index("Meio") < p.index("Antiga")


def test_sem_noticias_de_promo_nao_ha_aviso():
    assert "AVISO" not in acoes(DEPOIS_DO_LANCAMENTO, noticias=[])


def test_83_e_84_sao_sempre_de_evitar():
    for dia in range(7):
        assert "EVITAR" in acoes(DEPOIS_DO_LANCAMENTO + timedelta(days=dia))


def test_perfil_bate_com_o_relatorio():
    # O perfil está copiado do relatório; se o relatório for regenerado com
    # outros números e o perfil não, isto falha.
    texto = Path(__file__).with_name("estudos").joinpath("eventos_fc26.md").read_text(encoding="utf-8")
    linhas = texto.splitlines()
    i = next(i for i, l in enumerate(linhas) if l.startswith("| seg | ter | qua"))
    valores = [float(v) / 100 for v in re.findall(r"([+-]\d+\.\d)%", linhas[i + 2])]
    assert valores == [pytest.approx(K.PERFIL_FC26[d], abs=1e-9) for d in range(7)]


def test_roi_esperado_desconta_a_taxa():
    # Domingo (−8,0%) → quarta (+7,3%): 0,95 × 1,073 / 0,920 − 1.
    assert K.roi_esperado(6) == pytest.approx(0.95 * 1.073 / 0.920 - 1)
    # Comprar e vender no mesmo dia perde exactamente a taxa.
    assert K.roi_esperado(2, 2) == pytest.approx(-0.05)
