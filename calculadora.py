"""Contas de uma operação no mercado: quanto se ganha depois da taxa.

Sem regras de dimensionamento: quanto do saldo pôr numa carta é uma
constante que ainda não foi medida (AGENTS.md: medir em vez de arbitrar).
A calculadora mostra os números; a decisão é de quem opera.
"""

import math

TAXA = 0.05


def receita_liquida(venda, taxa=TAXA):
    """O que entra no saldo por uma venda: a EA fica com a taxa."""
    return venda * (1 - taxa)


def preco_minimo_venda(compra, taxa=TAXA):
    """O preço de venda a partir do qual não se perde dinheiro."""
    return compra / (1 - taxa)


def quantidade_maxima(saldo, compra):
    """Quantas cópias cabem no saldo, ao preço de compra."""
    if compra <= 0:
        return 0
    return max(0, math.floor(saldo / compra))


def operacao(compra, venda, quantidade, taxa=TAXA):
    """Resultado de comprar `quantidade` cópias a `compra` e vendê-las a `venda`."""
    investido = compra * quantidade
    recebido = receita_liquida(venda, taxa) * quantidade
    lucro = recebido - investido
    return {
        "investido": investido,
        "recebido": recebido,
        "lucro": lucro,
        "roi": lucro / investido if investido else 0.0,
    }
