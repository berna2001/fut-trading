# Estudo de eventos — fodder do PC no FC 26

*Gerado por `relatorio_eventos.py`. Não editar à mão.*

**Dados:** histórico diário de PC (média diária do FUTBIN, via parse.bot) de 65 cartas gold rare normais, 5 ratings (83-87), de 20/10/2025 a 13/09/2026. Os primeiros 32 dias (crash de lançamento) ficam de fora.

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

## O que a app usa: ROI medido só na 2.ª metade

Comprar em cada dia e vender qua, fodder 84-87, semanas de 16/03/2026 a 13/09/2026. Intervalo de 95% por bootstrap da mediana.

| comprar | mediana | intervalo 95% | média aparada 10% | semanas positivas |
|---|---|---|---|---|
| sáb | +4.3% | -0.5% a +11.5% | +7.2% | 17/25 |
| dom | +6.6% | -0.4% a +14.3% | +9.2% | 17/25 |
| seg | +2.9% | -1.5% a +8.5% | +5.0% | 16/26 |
| ter | -0.0% | -2.6% a +8.2% | +2.9% | 13/26 |

Só sáb → qua foi escolhido na 1.ª metade; os outros dias são medidos na mesma janela, mas não foram escolhidos antes, e por isso valem menos. Os ratings 85-87 que a app recomenda foram escolhidos já a ver a 2.ª metade (o 84 saiu por ter sido negativo lá): para eles, isto não é fora da amostra.

**Sensibilidade às datas de corte.** A mesma escolha (melhor par na 1.ª parte, medido na 2.ª) com outros cortes:

| corte | escolhido | mediana depois do corte | semanas positivas |
|---|---|---|---|
| 05/01/2026 | sáb → qua | +8.6% | 27/35 |
| 02/02/2026 | sáb → qua | +7.7% | 23/31 |
| 16/03/2026 | sáb → qua | +4.3% | 17/25 |
| 13/04/2026 | dom → qui | +1.5% | 11/21 |
| 11/05/2026 | sáb → qua | +4.3% | 11/17 |

O par de dias muda com o corte. O que se mantém é a forma: comprar ao fim-de-semana, vender a meio da semana.

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

**As promos grandes acrescentam pouco ao ciclo semanal.** E−5 → véspera é domingo → quinta. Em todas as semanas, incluindo as de promo, domingo → quinta dá mediana +11.3% e média +13.1% (46 semanas); nas 7 semanas de promo grande, mediana +10.0% e média +11.2%.

A janela escolhida muda com o corte. **Com 7 eventos isto não chega para escolher uma janela de compra.** O que é estável é o que acontece depois do lançamento:

| rating | comprar E−5, vender na véspera | comprar E−5, segurar até E+1 |
|---|---|---|
| 83 | -4.1% | -4.1% |
| 84 | +14.7% | -2.8% |
| 85 | +13.3% | -16.5% |
| 86 | +11.3% | -12.2% |
| 87 | +8.9% | -1.9% |

## Quanto custa segurar depois de a promo abrir

Variação de preço, sem taxa, da véspera (quinta) para o dia a seguir à abertura (sábado). Semanas de promo grande contra as outras semanas.

| rating | promo: média | promo: pior | promo: melhor | outras semanas: mediana |
|---|---|---|---|---|
| 85 | -24.3% | -59.3% | +30.7% | -14.6% |
| 86 | -21.8% | -50.9% | +22.5% | -13.3% |
| 87 | -19.5% | -43.2% | +23.3% | -12.6% |

Mesmo numa semana normal, segurar de quinta para sábado custa; numa semana de promo grande custa mais, e com muita dispersão.

## Ratings no preço mínimo

Fracção de dias-carta a menos de 2% do preço mínimo da época da própria carta:

| rating | 1.ª metade | 2.ª metade |
|---|---|---|
| 83 | 55% | 58% |
| 84 | 10% | 37% |
| 85 | 0% | 4% |
| 86 | 0% | 5% |
| 87 | 0% | 1% |

O 83 esteve no mínimo a época toda. O 84 colou ao mínimo na 2.ª metade, e foi aí que deixou de dar lucro (na 1.ª metade o ciclo deu-lhe lucro). Um rating no mínimo não tem para onde descer, mas também não sobe com a procura: perde a taxa em cada operação.

## Limites

- **A média diária pode não ser um preço executável.** No FC 27 as compras Buy Now saíram à média horária (`medicao_fc27.md`), mas em cartas que não eram o fodder mais barato do rating. Falta medir no fodder.
- **As cartas deste estudo são as primeiras da página do site, não as mais baratas do rating.** Dentro de cada rating os preços movem-se juntos, mas não está verificado que o fodder mais barato se comporte igual.
- **É o FC 26.** O FC 27 pode ter outro dia de rewards e outro calendário. O ciclo tem de ser confirmado com dados do FC 27 antes de se recomendar.
- **Promos grandes: 7 eventos.** Dá para ver o que é consistente (não segurar depois do lançamento), não para afinar uma janela.
- **Ultimate Scream (24/10/2025):** as janelas que compram mais de 4 dias antes começam antes de 20/10/2025, ainda dentro do crash de lançamento.
- **Fuga de informação:** comprar k dias antes de uma promo pressupõe que a data era pública. Para as promos grandes era (calendário e leaks com 1-2 semanas), mas não está medido evento a evento.
