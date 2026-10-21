# Química: o fodder ligado às promos sobe mais? (H4, FC 26)

*Gerado por `relatorio_ligacoes.py`. Não editar à mão. Regras fixadas em `plano_promos_jogadores.md` antes do cálculo.*

**Dados:** 18 dias de promo (10+ cartas novas no dia), 800 cartas de promo com nação e liga (FUT.GG), 52 cartas de fodder 84-87 com histórico diário de PC (FUTBIN). Uma carta está **ligada** num dia se a nação ou a liga dela tem 3+ cartas novas nesse dia; as outras são o controlo, nas mesmas datas. Efeito = ROI das ligadas − ROI das não ligadas (medianas, líquido da taxa).

## Análise do plano (nomes de liga só por nome)

23 das 52 cartas têm uma liga cujo nome o FUT.GG escreve de outra maneira (Barclays WSL, D1 Arkema, GPFBL, NWSL, Serie A TIM). Para essas, só a nação conta.

| janela | dias | efeito mediano | dias com efeito > 0 | 1.ª metade | 2.ª metade | passa? |
|---|---|---|---|---|---|---|
| H4a D−7 → D−1 (antecipar) | 18 | +0.1% | 9/18 | +1.4% (6/9) | -0.9% (3/9) | não |
| H4b D−1 → D+3 (logo depois) | 18 | +0.0% | 9/18 | -0.2% (4/9) | +2.8% (5/9) | não |
| H4c D → D+7 (a semana a seguir) | 18 | +0.4% | 10/18 | -1.5% (3/9) | +6.2% (7/9) | não |

## Análise secundária — desvio ao plano (com correspondências de liga)

Acrescenta as correspondências Serie A TIM = Serie A Enilive; Barclays WSL = Barclays Women’s Super League; NWSL = National Women's Soccer League; D1 Arkema = Arkema Première Ligue; GPFBL = Google Pixel Frauen-Bundesliga. Cada uma tem um só candidato no FUT.GG. Não estava no plano: vale menos.

| janela | dias | efeito mediano | dias com efeito > 0 | 1.ª metade | 2.ª metade | passa? |
|---|---|---|---|---|---|---|
| H4a D−7 → D−1 (antecipar) | 18 | +0.7% | 11/18 | +0.9% (7/9) | -0.9% (4/9) | não |
| H4b D−1 → D+3 (logo depois) | 18 | +0.2% | 9/18 | -0.4% (3/9) | +10.8% (6/9) | não |
| H4c D → D+7 (a semana a seguir) | 18 | +0.3% | 9/18 | -3.6% (2/9) | +6.5% (7/9) | não |

## Limites

- **É fodder 84-87, não as cartas que a química mais move.** Quem procura ligações para uma carta de promo nova procura sobretudo cartas jogáveis da mesma nação ou liga. Um resultado nulo aqui não exclui o efeito nessas cartas; um resultado positivo aqui é um bom sinal para elas.
- **Poucas cartas ligadas por dia:** a amostra é de 52 cartas, e num dia típico só algumas são da nação ou da liga em destaque.
- **É o FC 26.**
