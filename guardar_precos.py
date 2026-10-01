"""Falha se algum preço do parse.bot entrar no repositório (que é público).

Os preços são dados do FUTBIN (AGENTS.md). A CI corre isto sobre os ficheiros
versionados. Antes era um grep no ci.yml, e a revisão independente de
01/10/2026 mostrou que deixava passar `id,"price"`, `id,preço`, `id,Price PC`,
`id,coins` e qualquer JSON. Agora as colunas e chaves são normalizadas
(aspas, maiúsculas, acentos) antes de comparar, e os JSON são verificados.

Uso: python guardar_precos.py [ficheiro ...]   (sem argumentos: git ls-files)
"""

import csv
import io
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

PALAVRAS = ("preco", "price", "coin")


def normalizar(nome):
    # As aspas não precisam de tratamento: o csv.reader já as tira, e a
    # comparação é por substring.
    sem_acentos = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return sem_acentos.lower()


def e_preco(nome):
    n = normalizar(nome)
    return any(p in n for p in PALAVRAS)


def chaves_json(dados):
    if isinstance(dados, dict):
        for k, v in dados.items():
            yield str(k)
            yield from chaves_json(v)
    elif isinstance(dados, list):
        for v in dados:
            yield from chaves_json(v)


def problemas(caminho, texto):
    """Lista de razões para recusar o ficheiro (vazia se estiver bem)."""
    p = Path(caminho)
    if p.parts and p.parts[0] == "precos":
        return [f"{caminho}: ficheiro dentro de precos/"]
    if p.suffix == ".parquet":
        return [f"{caminho}: ficheiro .parquet"]
    if p.suffix == ".csv":
        cabecalho = next(csv.reader(io.StringIO(texto)), [])
        return [f"{caminho}: coluna {c!r}" for c in cabecalho if e_preco(c)]
    if p.suffix == ".json":
        try:
            dados = json.loads(texto)
        except ValueError:
            return []
        return [f"{caminho}: chave {k!r}" for k in sorted(set(chaves_json(dados))) if e_preco(k)]
    return []


def main(ficheiros):
    maus = []
    for f in ficheiros:
        p = Path(f)
        texto = "" if p.suffix == ".parquet" or not p.exists() else p.read_text(
            encoding="utf-8", errors="replace")
        maus += problemas(f, texto)
    for m in maus:
        print("RECUSADO:", m)
    return 1 if maus else 0


if __name__ == "__main__":
    lista = sys.argv[1:] or subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    sys.exit(main(lista))
