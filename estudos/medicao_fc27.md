# Medição no FC 27 — vendas reais e perfis horários

*Gerado por `relatorio_fc27.py`. Não editar à mão.*

**Dados:** 6 cartas gold rare 86 do FC 27, PC. Histórico horário de 18/09 00h a 01/10 11h UTC, e as últimas ~500 vendas de cada uma, lidas a 01/10/2026. 29 créditos.

## A média do FUTBIN é executável?

Cada venda compara-se com a média horária do FUTBIN da mesma hora UTC. 1,00 = vendeu-se exactamente à média.

| carta | vendas/hora | não vendidas | Buy Now ÷ média | licitação ÷ média | dispersão Q3/Q1 |
|---|---|---|---|---|---|
| Georgia Stanway | 385 | 27% | 1.007 | 0.992 | +3.2% |
| Katie McCabe | 83 | 12% | 1.013 | 0.966 | +0.0% |
| Chloe Kelly | 126 | 26% | 1.004 | 0.861 | +10.4% |
| Dominik Szoboszlai | 213 | 5% | 1.002 | 1.006 | +4.7% |
| Alexander Isak | 34 | 17% | 1.000 | 0.932 | +12.2% |
| Martin Ødegaard | 35 | 23% | 1.004 | 0.923 | +4.5% |

**Sim.** As compras Buy Now concretizaram-se entre 1.000 e 1.013 da média horária. As licitações ganhas saíram entre -13.9% e +0.6% face à média: comprar por licitação é mais barato, mas não se sabe quantas se perdem. Do lado da venda, uma parte das listagens não vende à primeira (coluna "não vendidas"), o que obriga a relistar.

Isto valida o uso da média diária no estudo do FC 26, para estas cartas e neste momento do mercado.

## Hora do dia

Preço face à média das 24 horas centradas (mediana). Horas em UTC: as promos abrem às 17h UTC (18h UK).

| 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -1.3 | -1.6 | -1.6 | -2.6 | -1.8 | -1.5 | -1.1 | -0.6 | -0.2 | +0.5 | +0.2 | +0.2 | +0.1 | +0.7 | +1.2 | +1.5 | +2.5 | +3.6 | +1.9 | +1.5 | +0.1 | -0.9 | -0.8 | -0.7 |

Mais barata às 03h UTC (-2.6%), mais cara às 17h UTC (+3.6%). Comprar às 03h e vender às 17h do mesmo dia dá +1.0% líquido, perto de zero: a hora sozinha quase não paga uma operação, mas escolhe o momento de uma que já se ia fazer.

## Dia da semana

| seg | ter | qua | qui | sex | sáb | dom |
|---|---|---|---|---|---|---|
| +9.1% (4) | +13.9% (6) | +5.9% (6) | -3.5% (5) | -10.5% (5) | -7.5% (5) | -3.3% (5) |

Entre parênteses, dias-carta. **São duas semanas, e são as do crash de lançamento.** Mostra fim-de-semana barato e início de semana caro, como no FC 26, mas não chega para confirmar o ciclo. Precisa de mais semanas.

## Limites

- **As cartas 86 do FC 27 ainda não são fodder.** Valem ordens de grandeza diferentes entre si e cada uma segue o seu caminho. O ciclo do FC 26 é de fodder, cujo preço vem da procura de SBCs; só deve aparecer quando o mercado do FC 27 amadurecer.
- **As horas das vendas assumem UTC+1**, verificado a 01/10/2026. Muda no fim de Outubro com o fim da hora de Verão.
- **6 cartas, um só rating, um só dia de vendas.** É uma verificação, não um estudo.
