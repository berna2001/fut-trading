# Plano do estudo — o que uma promo faz às cartas base dos jogadores

*Escrito a 21/10/2026, **antes** de descarregar qualquer preço. As hipóteses, as
janelas e a regra de escolha ficam fixadas aqui. Se mudarem depois de ver os
dados, o estudo diz que mudaram e porquê. A revisão independente de
01/10/2026 encontrou no estudo do fodder exactamente o defeito de escolher
regras depois de olhar para o resultado.*

## Pergunta

Quando um jogador recebe uma carta de promo, a carta **base** dele (a gold
normal, transaccionável, que existia antes) sobe ou desce? Em que janela? Isto
diz se faz sentido comprar a carta base de um jogador nomeado num leak, e
quando vender.

## Dados

- **Quem recebeu carta e quando:** `precos/futgg/cartas_promos_fc26.csv`, de
  `promos_fc26.py`. São 800 cartas das 7 promos grandes do FC 26, cada uma com a
  data e hora a que saiu (`saiu_em`), lidas do FUT.GG a 21/10/2026.
- **Preço da carta base:** histórico diário de PC do FUTBIN, via parse.bot,
  depois de 01/11/2026 (renovação dos créditos).

## Regra de escolha (fixa)

1. Ficam de fora as cartas de Icon e de Hero (`raridade` contém "Icon" ou
   "Hero"). Estes jogadores não têm uma carta base gold normal comparável.
2. Cada jogador entra uma só vez, com a sua **primeira** carta de promo na lista.
   E = a data em Londres do `saiu_em` dessa carta.
3. Amostra: **50 jogadores**, sorteados com `random.Random(2026)` entre os
   elegíveis, por ordem de `ea_id`. Não se troca nenhum depois de sorteado.
4. Carta base: o resultado de `search_players_fc26(nome)` com `version`
   "Normal". Se não houver exactamente uma, o jogador sai e **não é
   substituído**. Só se gasta o crédito da pesquisa.

Custo: 50 × (1 pesquisa + 2 histórico) = **150 créditos**, de 200.

## Hipóteses (fixas)

ROI líquido da taxa de 5% sobre a média diária de PC da carta base. Por janela,
a mediana entre jogadores.

| | comprar | vender | o que testa |
|---|---|---|---|
| **H1** antecipação | E−7 | E−1 | comprar quando sai o leak, vender antes da promo |
| **H2** curto prazo depois | E | E+7 | a semana a seguir à promo |
| **H3** longo prazo | E+1 | E+28 | segurar um mês depois da promo |

**Referência, por carta:** a mesma janela (mesmo dia da semana de compra, mesma
duração) em todas as outras semanas da época da mesma carta. O efeito é a
mediana de (ROI na janela da promo − ROI de referência da carta).

## Quando uma hipótese passa

As duas condições, nas duas metades (promos até ao Future Stars contra as
seguintes):

- mediana do efeito > 0;
- mais de metade dos jogadores com efeito > 0.

Só as hipóteses que passam entram no conselheiro, e com a confiança que o
resultado justificar. Se nenhuma passar, isso também é um resultado: comprar
a carta base de um jogador nomeado num leak não é uma estratégia, e a app
deve dizê-lo.

## O que não se testa aqui (e porquê)

- **A carta de promo em si** (comprar a carta nova depois de sair): os preços
  das cartas novas começam no lançamento, sem passado para a referência. Fica
  para quando houver créditos para o FC 27.
- **SBCs e evoluções** que pedem certos jogadores: não há uma lista das
  exigências do FC 26 com datas. Fica para o FC 27, onde o `get_fc27_sbcs`
  dá as exigências.
