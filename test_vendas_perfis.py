"""Testes das medições sobre vendas reais e dos perfis horários. Sem rede."""

from datetime import datetime, timedelta, timezone

import pytest

import perfis as PF
import vendas as V

UTC = timezone.utc


def venda(hora_local, preco, tipo="Buy Now"):
    return {"time": hora_local, "sold_price": None if tipo == "Unsold" else preco,
            "listed_price": preco, "sale_type": tipo}


# O instante em que as vendas foram lidas (01/10/2026, 11:44 UTC).
LIDO = datetime(2026, 10, 1, 11, 44, tzinfo=UTC)


def test_hora_do_site_e_hora_de_londres_no_verao():
    # Verificado a 01/10/2026: "12:42 PM" no site eram 11:42 UTC.
    assert V.instante_utc("Oct 1, 12:42 PM", LIDO) == datetime(2026, 10, 1, 11, 42, tzinfo=UTC)
    assert V.instante_utc("Oct 1, 12:28 AM", LIDO) == datetime(2026, 9, 30, 23, 28, tzinfo=UTC)


def test_no_inverno_londres_e_utc():
    # Depois de 25/10/2026 Londres passa a UTC+0: um desvio fixo de +1h
    # desalinhava as vendas uma hora (revisão de 01/10/2026).
    lido = datetime(2026, 11, 10, 12, tzinfo=UTC)
    assert V.instante_utc("Nov 10, 9:30 AM", lido) == datetime(2026, 11, 10, 9, 30, tzinfo=UTC)
    # A noite da mudança: 01:30 de 25/10 ainda é BST (UTC+1).
    lido = datetime(2026, 10, 25, 12, tzinfo=UTC)
    assert V.instante_utc("Oct 25, 12:30 AM", lido) == datetime(2026, 10, 24, 23, 30, tzinfo=UTC)


def test_vendas_de_dezembro_lidas_em_janeiro_sao_do_ano_anterior():
    lido = datetime(2027, 1, 1, 0, 30, tzinfo=UTC)
    assert V.instante_utc("Dec 31, 11:50 PM", lido) == datetime(2026, 12, 31, 23, 50, tzinfo=UTC)
    assert V.instante_utc("Jan 1, 12:10 AM", lido) == datetime(2027, 1, 1, 0, 10, tzinfo=UTC)


def test_29_de_fevereiro_nao_rebenta():
    lido = datetime(2028, 3, 1, 12, tzinfo=UTC)  # 2028 é bissexto
    assert V.instante_utc("Feb 29, 10:00 AM", lido) == datetime(2028, 2, 29, 10, tzinfo=UTC)
    # Lido em 2029: o 29/02/2029 não existe, tem de saltar para 2028.
    lido = datetime(2029, 1, 10, tzinfo=UTC)
    assert V.instante_utc("Feb 29, 10:00 AM", lido) == datetime(2028, 2, 29, 10, tzinfo=UTC)


def test_data_a_frente_da_leitura_e_do_ano_anterior():
    # "Oct 5" lido a 01/10/2026 não pode ser deste ano: é de 2025.
    assert V.instante_utc("Oct 5, 10:00 AM", LIDO) == datetime(2025, 10, 5, 9, tzinfo=UTC)
    # Até um dia à frente aceita-se como deste ano (relógios desacertados).
    assert V.instante_utc("Oct 2, 10:00 AM", LIDO).year == 2026


def test_29_de_fevereiro_impossivel_e_erro():
    # Lido em 2027: nem 2027 nem 2026 têm 29 de Fevereiro.
    with pytest.raises(ValueError):
        V.instante_utc("Feb 29, 10:00 AM", datetime(2027, 3, 1, tzinfo=UTC))


def test_nao_vendidas_ficam_de_fora_das_vendas_mas_contam_na_taxa():
    s = [venda("Oct 1, 10:00 AM", 100), venda("Oct 1, 10:30 AM", 0, "Unsold"),
         venda("Oct 1, 11:00 AM", 90, "Bid"), venda("Oct 1, 11:10 AM", 0, "Unsold")]
    assert [p for _, p, _ in V.vendidas(s, LIDO)] == [100, 90]
    assert V.taxa_nao_vendidas(s) == 0.5


def test_vendas_por_hora():
    s = [venda("Oct 1, 10:00 AM", 100), venda("Oct 1, 10:30 AM", 100),
         venda("Oct 1, 12:00 PM", 100), venda("Oct 1, 11:00 AM", 0, "Unsold")]
    assert V.vendas_por_hora(s, LIDO) == pytest.approx(3 / 2)


def test_razao_compara_com_a_media_da_mesma_hora_utc():
    # As vendas das 10:xx locais são das 09:xx UTC: têm de ser comparadas com
    # a média das 09:00 UTC (100), não com a das 10:00 (200).
    horario = {datetime(2026, 10, 1, 9, tzinfo=UTC): 100,
               datetime(2026, 10, 1, 10, tzinfo=UTC): 200}
    s = [venda("Oct 1, 10:05 AM", 102), venda("Oct 1, 10:50 AM", 98, "Bid"),
         venda("Oct 1, 10:55 AM", 104)]
    assert V.razao_face_a_media(s, LIDO, horario, "Buy Now") == pytest.approx(1.03)
    assert V.razao_face_a_media(s, LIDO, horario, "Bid") == pytest.approx(0.98)
    assert V.razao_face_a_media(s, LIDO, horario) == pytest.approx(1.02)


def test_ida_e_volta_a_mediana_e_so_a_taxa():
    s = [venda("Oct 1, 10:00 AM", p) for p in [90, 95, 100, 100, 105, 110]]
    c = V.custo_de_ida_e_volta(s, LIDO)
    assert c["mediana_mediana"] == pytest.approx(-0.05)
    assert c["q1_mediana"] > c["mediana_mediana"]   # comprar mais barato ajuda
    assert c["dispersao_q3_q1"] > 0


def _serie_horaria(dias, f, inicio=datetime(2026, 9, 7, tzinfo=UTC)):  # segunda
    return {inicio + timedelta(hours=i): f(inicio + timedelta(hours=i)) for i in range(24 * dias)}


def test_perfil_horario_acha_o_pico_e_ignora_a_tendencia():
    # Tendência forte de queda, mais um pico às 17h. Sem janela centrada, as
    # primeiras horas do dia pareceriam caras só por virem antes.
    inicio = datetime(2026, 9, 7, tzinfo=UTC)
    s = _serie_horaria(10, lambda t: 1000 - (t - inicio).total_seconds() / 3600
                       + (50 if t.hour == 17 else 0))
    p = PF.perfil_horario([s])
    assert max(p, key=p.get) == 17
    assert abs(p[0]) < 0.01 and abs(p[23]) < 0.01


def test_perfil_semanal_acha_o_dia_barato():
    s = _serie_horaria(28, lambda t: 80 if t.weekday() == 6 else 100)
    p = PF.perfil_semanal([s])
    assert min(p, key=lambda d: p[d][0]) == 6
    assert p[6][0] < 0 < p[2][0]


def test_medias_diarias_exigem_dia_quase_completo():
    s = _serie_horaria(2, lambda t: 100)
    s = {t: p for t, p in s.items() if not (t.day == 8 and t.hour >= 10)}
    assert list(PF.medias_diarias(s)) == [datetime(2026, 9, 7).date()]


def test_nao_vendida_com_preco_zero_nao_conta_como_venda():
    # A documentação diz que vem null, mas o site mostra 0. As duas formas
    # têm de ficar de fora.
    s = [venda("Oct 1, 10:00 AM", 100),
         {"time": "Oct 1, 10:05 AM", "sold_price": 0, "listed_price": 120, "sale_type": "Unsold"},
         {"time": "Oct 1, 10:06 AM", "sold_price": 120, "listed_price": 120, "sale_type": "Unsold"}]
    assert [p for _, p, _ in V.vendidas(s, LIDO)] == [100]


def test_perfil_semanal_de_uma_tendencia_pura_e_plano():
    # Queda constante, nenhum efeito de dia da semana. Com uma janela que não
    # fosse centrada, cada dia comparava-se com dias mais baratos à frente e
    # parecia caro.
    inicio = datetime(2026, 9, 7, tzinfo=UTC)
    s = _serie_horaria(35, lambda t: 10000 - (t - inicio).total_seconds() / 3600)
    p = PF.perfil_semanal([s])
    assert all(abs(d) < 0.002 for d, _ in p.values())


def test_perfil_horario_em_hora_de_londres_desloca_uma_hora_no_verao():
    # Pico às 17h UTC em Setembro = 18h de Londres (abertura das promos).
    s = _serie_horaria(10, lambda t: 1000 + (50 if t.hour == 17 else 0))
    em_utc = PF.perfil_horario([s])
    em_londres = PF.perfil_horario([s], V.FUSO_DO_SITE)
    assert max(em_utc, key=em_utc.get) == 17
    assert max(em_londres, key=em_londres.get) == 18
