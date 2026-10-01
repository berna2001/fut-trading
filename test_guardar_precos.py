"""Testes do guarda de preços. Os casos são os que a revisão de 01/10/2026
mostrou passarem pelo grep antigo."""

import subprocess
import sys
from pathlib import Path

import pytest

import guardar_precos as G


@pytest.mark.parametrize("cabecalho", [
    "carta_id,data,preco_pc",
    'id,"price"',          # entre aspas
    "id,preço",            # com acento
    "id,Price PC",         # maiúsculas e espaço
    "id,coins",
    "id,player_id,price_pc_coins",
    "id,sold_price,listed_price",
])
def test_csv_com_preco_e_recusado(cabecalho):
    assert G.problemas("x.csv", cabecalho + "\n1,2,3\n")


@pytest.mark.parametrize("cabecalho", [
    "id,publicado_em,visto_em,fonte,categoria,titulo,link",   # noticias.csv
    "instante,endpoint,parametros,creditos",                   # creditos.csv
    "data,nome,tipo,confirmacao",                              # eventos_fc26.csv
])
def test_csv_do_repositorio_passa(cabecalho):
    assert G.problemas("x.csv", cabecalho + "\n") == []


def test_json_com_chave_de_preco_e_recusado_mesmo_aninhada():
    assert G.problemas("a.json", '{"data": {"results": [{"id": 1, "price_pc": 650}]}}')
    assert G.problemas("a.json", '{"prices": [{"timestamp": 1, "price": 2}]}')


def test_json_dos_estudos_passa():
    texto = Path(__file__).with_name("estudos").joinpath("numeros_fc26.json").read_text(encoding="utf-8")
    assert G.problemas("estudos/numeros_fc26.json", texto) == []


def test_pasta_precos_e_parquet_sao_recusados():
    assert G.problemas("precos/fc26/hist_1.json", "{}")
    assert G.problemas("dados.parquet", "")


def test_o_repositorio_actual_passa():
    # Corre o script como a CI corre: sobre o git ls-files.
    r = subprocess.run([sys.executable, "guardar_precos.py"], cwd=Path(__file__).parent,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_o_script_falha_quando_ha_precos(tmp_path):
    mau = tmp_path / "mau.csv"
    mau.write_text("id,price\n1,650\n", encoding="utf-8")
    bom = tmp_path / "bom.csv"
    bom.write_text("id,nome\n1,x\n", encoding="utf-8")
    assert G.main([str(bom)]) == 0
    assert G.main([str(bom), str(mau)]) == 1
