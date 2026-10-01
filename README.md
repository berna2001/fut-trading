# fut-trading

Conselheiro de trading para o mercado de transferências do **EA FC 27 Ultimate Team, no PC**.

Diz que cartas comprar, a que preço e quando vender, de forma a maximizar o ROI líquido, com o saldo que tens no momento. **Não compra nem vende nada sozinho.** Automatizar a web app viola os termos da EA e dá ban à conta, coins incluídos. As operações fazes tu.

## Fontes

| O quê | Fonte | Custo |
|---|---|---|
| Preços de PC, histórico horário (14 dias) e diário (desde o lançamento), vendas reais | [parse.bot — futbin.com API](https://parse.bot/marketplace/1b6234f9-0dfb-4cca-99b4-2d6d37aec6a7/futbin-com-api) | 200 créditos/mês grátis |
| Leaks de promos e SBCs | RSS do Google News, SoccerGaming e Khel Now, que republicam os leaks dos insiders do X | grátis |

O X tem os leaks primeiro, mas a API dele é paga ($0,005 por post lido), e por isso ficou de fora.

## Como funciona

1. **Recolha:** preços e notícias, gravados com o instante em que ficaram conhecidos.
2. **Estudo de eventos:** como se mexeram os preços à volta de cada promo, SBC e queda de rewards, no FC 26 e no FC 27, já líquidos da taxa de 5%.
3. **Recomendações:** só das estratégias que dão ROI positivo fora da amostra, dimensionadas pelo saldo e pela liquidez de cada carta.

## A app

`app.py`, em Streamlit, tem três abas:

- **Notícias:** leaks, SBCs, TOTW, evoluções e promos, filtráveis por categoria.
- **Calculadora:** lucro e ROI de uma operação depois da taxa, preço mínimo de venda e quantas cópias cabem no saldo.
- **Estudos:** os relatórios em `estudos/`.

Lê só ficheiros do repositório, por isso não precisa de chave nenhuma. Localmente: `streamlit run app.py`. Na Streamlit Community Cloud: repositório `berna2001/fut-trading`, ramo `main`, ficheiro `app.py`.

## Arranque

```bash
git config core.hooksPath .githooks
pip install -r requirements.txt
```

A chave do parse.bot lê-se de `PARSE_API_KEY`. Nunca vai para o repositório: localmente fica num `.env` (ignorado pelo git) e na CI num *secret*.
