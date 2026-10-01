# Estudo de eventos — fodder do PC no FC 26

*Gerado por `relatorio_eventos.py`. Não editar à mão.*

**Dados:** histórico diário de PC (média diária do FUTBIN, via parse.bot) de 65 cartas gold rare normais, 5 ratings (83-87), de 20/10/2025 a 13/09/2026. As 4 primeiras semanas (crash de lançamento) ficam de fora.

**ROI sempre líquido da taxa de 5%:** `0,95 × venda / compra − 1`. Por cada dia, a mediana entre as cartas.

## Referência: comprar e vender num dia qualquer

| rating | janela de 4 dias começada num dia qualquer |
|---|---|
| 83 | -5.0% |
| 84 | -5.0% |
| 85 | -5.0% |
| 86 | -5.1% |
| 87 | -3.4% |

É a taxa, mais nada: sem saber de nenhum evento, o preço mediano não se mexe numa janela curta, e a taxa come 5%. Qualquer estratégia tem de bater isto **e** o zero de ficar parado.

## O ciclo semanal

Preço de cada dia face à média da sua semana (84-87, mediana):

| seg | ter | qua | qui | sex | sáb | dom |
|---|---|---|---|---|---|---|
| -2.8% | -0.9% | +7.3% | +5.9% | +1.5% | -4.8% | -8.0% |

**Validação fora da amostra.** A melhor combinação (dia de compra → dia de venda) escolhe-se só na primeira metade (até 15/03/2026) e mede-se na segunda, que não entrou na escolha. Escolhida: **comprar sáb, vender qua**.

| período | mediana | média | semanas positivas |
|---|---|---|---|
| 1.ª metade (escolha) | +15.1% | +14.6% | 20/20 |
| 2.ª metade (teste) | +4.3% | +10.4% | 17/25 |

Por rating (sáb → qua):

| rating | 1.ª metade | 2.ª metade |
|---|---|---|
| 83 | -5.0% (6/20) | -5.0% (4/25) |
| 84 | +11.2% (15/20) | -4.1% (6/25) |
| 85 | +19.1% (20/20) | +5.5% (16/25) |
| 86 | +18.6% (20/20) | +6.0% (18/25) |
| 87 | +9.6% (14/20) | +7.1% (15/25) |

## Promos grandes

Datas em `eventos_fc26.csv`, cada uma confirmada por duas fontes. E = dia em que a promo abre (sexta, 18h UK). Comprar em E−k, vender em E+h.

| comprar | vender | ROI médio | Ultimate Scream | Black Friday / Thunderstruck | Team of the Year | Future Stars | FUT Birthday | Team of the Season | Futties |
|---|---|---|---|---|---|---|---|---|---|
| E−5 | E+7 | +17.6% | +10.6% | -27.1% | -21.6% | +89.4% | +16.4% | -3.2% | +58.7% |
| E−3 | E+7 | +13.3% | +3.7% | -27.2% | -25.4% | +87.8% | +13.6% | -9.6% | +50.3% |
| E−5 | véspera | +11.2% | +9.7% | -2.7% | +31.2% | +10.0% | +23.3% | -8.8% | +15.8% |
| E−3 | véspera | +6.4% | +3.5% | -4.0% | +29.7% | +6.2% | +11.4% | -13.2% | +11.1% |
| E−5 | dia E | +4.5% | +8.7% | -25.4% | +15.7% | +13.8% | +11.7% | -7.6% | +14.7% |
| E−1 | E+7 | +1.6% | -3.9% | -25.4% | -45.4% | +71.5% | -4.9% | -5.0% | +24.4% |
| E−2 | E+2 | -25.2% | +5.8% | -31.6% | -48.2% | +2.3% | -46.5% | -50.5% | -7.8% |
| E−7 | E+1 | -26.1% | +0.8% | -39.9% | -42.6% | +3.7% | -46.1% | -58.2% | -0.6% |
| E−2 | E+1 | -27.3% | -2.4% | -41.2% | -48.9% | +2.8% | -42.0% | -50.1% | -9.1% |

- Escolhendo nos primeiros 3 eventos: E−5 → E-1 (+12.7% no treino); nos 4 seguintes: +10.0%, +23.3%, -8.8%, +15.8% (média +10.1%).
- Escolhendo nos primeiros 4 eventos: E−5 → E+7 (+12.8% no treino); nos 3 seguintes: +16.4%, -3.2%, +58.7% (média +24.0%).
- Escolhendo nos primeiros 5 eventos: E−5 → E-1 (+14.3% no treino); nos 2 seguintes: -8.8%, +15.8% (média +3.5%).

**As promos grandes acrescentam pouco ao ciclo semanal.** E−5 → véspera é domingo → quinta. Numa semana qualquer, domingo → quinta dá mediana +11.3% e média +13.1% (46 semanas); nas 7 semanas de promo grande, mediana +10.0% e média +11.2%.

A janela escolhida muda com o corte. **Com 7 eventos isto não chega para escolher uma janela de compra.** O que é estável é o que acontece depois do lançamento:

| rating | comprar E−5, vender na véspera | comprar E−5, segurar até E+1 |
|---|---|---|
| 83 | -4.1% | -4.1% |
| 84 | +14.7% | -2.8% |
| 85 | +13.3% | -16.5% |
| 86 | +11.3% | -12.2% |
| 87 | +8.9% | -1.9% |

## O 83

Em 57% dos dias-carta, o 83 esteve a menos de 2% do seu preço mínimo da época. Não sobe com os eventos e perde a taxa em cada operação.

## Limites

- **A média diária não é um preço executável.** Comprar ao preço médio de domingo e vender ao de quarta assume que se consegue comprar e vender perto da média. O histórico de vendas (`get_fc27_sales_history`) mede isso, e falta medi-lo.
- **É o FC 26.** O FC 27 pode ter outro dia de rewards e outro calendário. O ciclo tem de ser confirmado com dados do FC 27 antes de se recomendar.
- **Promos grandes: 7 eventos.** Dá para ver o que é consistente (não segurar depois do lançamento), não para afinar uma janela.
- **Fuga de informação:** comprar k dias antes de uma promo pressupõe que a data era pública. Para as promos grandes era (calendário e leaks com 1-2 semanas), mas não está medido evento a evento.
