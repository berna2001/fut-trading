# Como trabalhar neste repositório

Herda as regras do projecto `bet`, que foram pagas com erros reais. Aqui ficam as que se aplicam, e as próprias deste domínio.

## Regras de ouro

**Nunca commits directos para `main`.** Ramo + pull request, sempre. O `.githooks/pre-push` recusa-o; activa-o em cada clone com `git config core.hooksPath .githooks`. A única excepção é a Action de recolha, que commita os dados.

**O bot aconselha, não opera.** Nada neste repositório se liga à web app nem à conta EA, nem lê o clube ou o saldo automaticamente. Automatizar o mercado viola os termos da EA e dá ban. O saldo e a carteira são introduzidos à mão.

**Medir em vez de arbitrar.** Nenhuma regra de compra entra por ser "conhecida na comunidade". Cada estratégia é uma hipótese, que se mede num estudo de eventos com validação fora da amostra antes de ser recomendada.

**Verificar antes de afirmar.** Não afirmes o que não correste.

**Uma alteração por PR.**

## O domínio

**O lucro é sempre líquido.** A EA fica com 5% de cada venda: lucro = venda × 0,95 − compra. Um flip de 4% bruto perde dinheiro.

**Só PC.** O mercado de PC é separado do de consola e tem menos liquidez. O parse.bot devolve preços de `ps` e `pc`: usa sempre `platform=pc`.

**Uma notícia conta a partir de quando foi publicada, não de quando o evento acontece.** Cada evento tem dois instantes: `conhecido_em` e `acontece_em`. Num backtest, uma estratégia só pode usar o que já era conhecido no instante da decisão. Foi este o erro mais caro do `bet` (previsões gravadas depois dos jogos).

**O baseline é ficar com os coins parados.** Uma estratégia que não bate isso, líquida de taxa, não se recomenda.

**A liquidez limita o tamanho.** Não se recomenda comprar mais cópias de uma carta do que ela vende numa fracção razoável de uma hora. A quantidade mede-se pelo histórico de vendas.

## Créditos do parse.bot

O plano grátis dá 200 créditos por mês. Custos por chamada, lidos da página da API em 01/10/2026:

| endpoint | créditos |
|---|---|
| `get_player_price_history` (uma carta, horário de 14 dias ou diário completo) | 2 |
| `get_fc27_sales_history` (últimas ~500 vendas de uma carta) | 2 |
| `get_players_by_rating` (30 cartas por página) | 5 |
| `get_fc27_market_snapshot` (até 500 cartas) | 10 |
| `get_fc27_sbcs_list` | 1 |

**O painel do parse.bot é a fonte da verdade sobre o saldo.** O cabeçalho `X-Credits-Remaining` mostrou 199 e 198 depois de 15 créditos gastos.

Antes de qualquer script que gaste créditos em ciclo, calcula o custo mensal e escreve-o no comentário.

## Antes de cada push

```bash
python -m pytest -q -W "error::UserWarning"
git diff --check
```

Os testes não tocam na rede nem gastam créditos.

## Testes

**Todo o teste novo verifica-se por mutação.** Introduz o defeito de propósito e confirma que o teste falha.

**A matemática pode estar errada sem nada falhar.** Quando uma função produz números, exige uma propriedade deles (monotonia, ordem, a taxa a reduzir o lucro), e não só que existam.

## Armadilhas

**Aspas duplas e crases** em mensagens de commit e corpos de PR: usa sempre `git commit -F ficheiro` e `gh pr create --body-file`. No `bet`, uma crase fez o bash correr um `git push` para `main`.

**Um `: ` dentro de um `run:` de uma linha parte o YAML da workflow.** Usa sempre `run: |`.

**Antes de qualquer `git add -A`, corre `git status` e lê a lista.**

## Estilo

Acentos em tudo o que é texto (comentários, docstrings, documentos, texto da app). Nada de acentos no que é dado (nomes de variáveis, colunas, valores nos CSV). Nomes em português.
