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


def principal(agora, saldo=100_000, investido=0):
    """A recomendação de mercado do dia (nem aviso nem a de evitar)."""
    return next(c for c in K.conselhos(agora, saldo, investido_no_ciclo=investido)
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


def test_ciclo_de_tres_dias_nao_passa_os_70_por_cento_do_capital():
    # A revisão de 01/10/2026 simulou isto com a versão antiga: 97 299 de
    # 100 000. Sábado, domingo e segunda, actualizando saldo e investido.
    saldo, investido = 100_000, 0
    for dias in (5, 6, 7):  # sáb, dom, seg depois do lançamento
        agora = DEPOIS_DO_LANCAMENTO + timedelta(days=dias)
        compra = principal(agora, saldo, investido)
        assert compra.acao == "COMPRAR"
        saldo -= compra.quantia
        investido += compra.quantia
    assert 69_000 <= investido <= 70_000


def test_no_lancamento_a_quantia_e_metade():
    sabado_lanc = datetime(2026, 10, 3, 12, tzinfo=UTC)
    sabado_depois = DEPOIS_DO_LANCAMENTO + timedelta(days=5)
    assert K.quantias(100_000, 0, sabado_lanc) == {r: 35_000 // 3 for r in (85, 86, 87)}
    assert K.quantias(100_000, 0, sabado_depois) == {r: 70_000 // 3 for r in (85, 86, 87)}


def test_quantias_nunca_negativas_nem_acima_do_saldo():
    agora = DEPOIS_DO_LANCAMENTO
    assert K.quantias(30_000, 90_000, agora) == {85: 0, 86: 0, 87: 0}   # já passou o tecto
    assert sum(K.quantias(10_000, 0, agora).values()) <= 10_000
    assert K.quantias(0, 0, agora) == {85: 0, 86: 0, 87: 0}
    assert K.quantias(-5, -5, agora) == {85: 0, 86: 0, 87: 0}


def test_compra_cita_os_numeros_fora_da_amostra_e_nao_o_perfil():
    domingo = DEPOIS_DO_LANCAMENTO + timedelta(days=6)
    c = principal(domingo)
    f = K.FORA_DA_AMOSTRA[6]
    assert K.pct(f["mediana"]) in c.porque
    assert K.pct(f["ic"][0]) in c.porque and K.pct(f["ic"][1]) in c.porque
    assert "+10.8%" not in c.porque   # o número do perfil da época inteira


def test_segunda_tem_confianca_baixa_e_sabado_media():
    assert principal(DEPOIS_DO_LANCAMENTO).confianca == "baixa"
    assert principal(DEPOIS_DO_LANCAMENTO + timedelta(days=5)).confianca == "média"


def test_vender_cita_o_custo_real_de_segurar():
    c = principal(DEPOIS_DO_LANCAMENTO + timedelta(days=3))  # quinta
    pior = min(K.SEGURAR[r]["promo_pior"] for r in K.RATINGS)
    assert c.acao == "VENDER" and K.pct(pior) in c.porque
    assert "12% e 17%" not in c.porque


def test_evitar_ratings_no_minimo_aparece_todos_os_dias():
    for dia in range(7):
        cs = K.conselhos(DEPOIS_DO_LANCAMENTO + timedelta(days=dia), 100_000)
        assert any(c.acao == "EVITAR" and "mínimo" in c.o_que for c in cs)


def test_numeros_do_json_batem_com_o_relatorio():
    # O json e o .md saem da mesma execução do relatorio_eventos.py. Se um
    # for regenerado e o outro não, isto falha.
    md = Path(__file__).with_name("estudos").joinpath("eventos_fc26.md").read_text(encoding="utf-8")
    linhas = md.splitlines()
    i = next(i for i, l in enumerate(linhas) if l.startswith("| seg | ter | qua"))
    perfil = [float(v) / 100 for v in re.findall(r"([+-]\d+\.\d)%", linhas[i + 2])]
    assert perfil == [pytest.approx(K.PERFIL_FC26[d], abs=5e-4) for d in range(7)]
    for d, nome in [(5, "sáb"), (6, "dom"), (0, "seg"), (1, "ter")]:
        linha = next(l for l in linhas if l.startswith(f"| {nome} | ") and "/2" in l)
        mediana = float(re.findall(r"([+-]\d+\.\d)%", linha)[0]) / 100
        assert mediana == pytest.approx(K.FORA_DA_AMOSTRA[d]["mediana"], abs=5e-4)


def test_lancamento_dura_os_mesmos_32_dias_que_o_estudo_do_fc26_deixou_de_fora():
    assert (K.INICIO_ESTUDO_FC26 - K.INICIO_MERCADO_FC26).days == 32
    assert K.em_lancamento(datetime(2026, 10, 17, 22, tzinfo=UTC))
    assert not K.em_lancamento(datetime(2026, 10, 18, 0, tzinfo=UTC))


def test_noticia_com_mais_de_7_dias_fica_de_fora():
    agora = DEPOIS_DO_LANCAMENTO
    n = [{"categoria": "leak", "titulo": "Velha", "publicado_em": agora - timedelta(days=7, hours=12)},
         {"categoria": "leak", "titulo": "Recente", "publicado_em": agora - timedelta(days=6, hours=12)}]
    aviso = next(c for c in K.conselhos(agora, 100_000, n) if c.acao == "AVISO")
    assert "Recente" in aviso.porque and "Velha" not in aviso.porque


def test_texto_do_domingo_so_aparece_ao_domingo():
    sabado = principal(DEPOIS_DO_LANCAMENTO + timedelta(days=5))
    domingo = principal(DEPOIS_DO_LANCAMENTO + timedelta(days=6))
    assert "Domingo foi o dia mais barato" not in sabado.porque
    assert "Domingo foi o dia mais barato" in domingo.porque


def test_proxima_promo_usa_o_dia_de_londres_perto_da_meia_noite():
    # Quinta 22/10 às 23:30 UTC já é sexta 00:30 em Londres: a promo é nesse
    # mesmo dia às 18h de Londres, e não no sábado.
    p = K.proxima_promo(datetime(2026, 10, 22, 23, 30, tzinfo=UTC))
    assert p.astimezone(UTC) == datetime(2026, 10, 23, 17, tzinfo=UTC)
