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

**Mas não nas cartas certas.** Estas 6 são as primeiras da página do site, não o fodder mais barato do rating: a mais cara custava 16 vezes o fodder. Não valida o estudo do FC 26 para o fodder; mostra que, nestas cartas e neste dia, a média horária era o preço a que se transaccionava.

## Hora do dia

Preço face à média das 24 horas centradas (mediana). **Horas de Londres** (e de Lisboa): as promos abrem às 18h. Em hora de Londres o perfil não muda com a mudança da hora a 25/10; em UTC mudaria uma hora.

| 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -0.7 | -1.3 | -1.6 | -1.6 | -2.6 | -1.8 | -1.5 | -1.1 | -0.6 | -0.2 | +0.5 | +0.2 | +0.2 | +0.1 | +0.7 | +1.2 | +1.5 | +2.5 | +3.6 | +1.9 | +1.5 | +0.1 | -0.9 | -0.8 |

Mais barata às 04h (-2.6%), mais cara às 18h (+3.6%). Comprar às 04h e vender às 18h do mesmo dia dá +1.0% líquido, perto de zero: a hora sozinha quase não paga uma operação, mas escolhe o momento de uma que já se ia fazer.

## Dia da semana

| seg | ter | qua | qui | sex | sáb | dom |
|---|---|---|---|---|---|---|
| +9.1% (4) | +13.9% (6) | +5.9% (6) | -3.5% (5) | -10.5% (5) | -7.5% (5) | -3.3% (5) |

Entre parênteses, dias-carta. **São duas semanas, e são as do crash de lançamento, com 4 a 6 dias-carta por dia.** O fim-de-semana sai barato, como no FC 26, mas o resto não bate: aqui segunda e terça são os dias mais caros, no FC 26 eram quarta e quinta. Não confirma nem desmente o ciclo.

## Limites

- **As cartas medidas não são o fodder.** Foram escolhidas pela ordem do site (revisão independente de 01/10/2026). Havia fodder 86 na página mais barato do que todas as escolhidas; a próxima medição usa `descarregar_fc27.fodder()`, que escolhe as mais baratas.
- **As horas das vendas assumem a hora de Londres**, verificado a 01/10/2026 (UTC+1). Depois de 25/10, quando Londres passa a UTC+0, tem de se verificar outra vez que o site acompanha a mudança.
- **6 cartas, um só rating, um só dia de vendas.** É uma verificação, não um estudo.
