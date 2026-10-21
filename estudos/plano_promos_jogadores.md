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
3. Amostra: **35 jogadores** (eram 50; ver "Opção B" abaixo), sorteados com
   `random.Random(2026)` entre os
   elegíveis, por ordem de `ea_id`. Não se troca nenhum depois de sorteado.
4. Carta base: o resultado de `search_players_fc26(nome)` com `version`
   "Normal". Se não houver exactamente uma, o jogador sai e **não é
   substituído**. Só se gasta o crédito da pesquisa.

Custo: 35 × (1 pesquisa + 2 histórico) = **105 créditos**, de 200.

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

## H4: química (acrescentada a 21/10/2026, antes de calcular)

*Sugestão do utilizador:* quando sai uma promo, sobem as cartas que fazem
ligação de química com as cartas novas (mesma nação, mesma liga, ou ambas).

- **Dias de promo:** cada data em Londres com **10 ou mais** cartas novas no
  `cartas_promos_fc26.csv`.
- **Nações e ligas fortes nesse dia:** as que têm **3 ou mais** cartas novas
  nesse dia.
- **Cartas medidas:** as 65 cartas de fodder do FC 26 já descarregadas, só
  84-87 (o 83 está no preço mínimo e não pode subir). Uma carta está
  **ligada** num dia de promo se a nação **ou** a liga dela for forte nesse
  dia. As outras são o controlo, nas mesmas datas, o que tira o efeito do
  mercado.
- **Nomes:** o FUT.GG dá identificadores com nomes e o FUTBIN dá só nomes;
  cruzam-se pelo nome normalizado. As que não cruzarem ficam listadas no
  relatório, e não são adivinhadas.

| | comprar | vender | o que testa |
|---|---|---|---|
| **H4a** | D−7 | D−1 | antecipar a procura de ligações |
| **H4b** | D−1 | D+3 | a procura de ligações logo depois de a promo abrir |
| **H4c** | D | D+7 | a semana a seguir |

**Efeito por dia:** mediana do ROI das ligadas − mediana do ROI das não
ligadas. **Passa** se, nas duas metades dos dias de promo (antes e depois do
mediano), a mediana do efeito for > 0 e mais de metade dos dias tiver efeito
> 0.

Esta parte **não gasta créditos**: os preços já estão em disco. Se passar no
fodder, a medição em cartas melhores (que é onde a química mais pesa) entra
nos créditos de Novembro, em vez de parte de H1-H3.

## Opção B (decisão do utilizador a 21/10/2026, antes de qualquer dado)

A H4 não passou no fodder (`ligacoes_fc26.md`), e o plano dizia que só se
alargava a cartas melhores se passasse. O utilizador decidiu alargar na
mesma: menos jogadores em H1-H3 (35 em vez de 50) e ~50 créditos para a
química em cartas jogáveis. As regras abaixo ficam fixas antes de
descarregar qualquer preço.

### H4j: química em cartas jogáveis, com o TOTS

O TOTS do FC 26 saiu uma liga por semana. Cada sexta é uma experiência
natural: as cartas da liga em destaque estão ligadas às cartas novas, e as
das outras quatro ligas servem de controlo nas mesmas datas.

| dia (D) | liga do TOTS |
|---|---|
| 17/04/2026 | Serie A |
| 24/04/2026 | Premier League |
| 01/05/2026 | Bundesliga |
| 08/05/2026 | Ligue 1 |
| 15/05/2026 | LaLiga |

Datas do calendário confirmado (FUT.GG, notícia "TOTS release dates"). Cada
uma tem 41 ou mais cartas novas no `cartas_promos_fc26.csv`, e em cada uma a
liga da tabela é a que tem mais cartas TOTS nesse dia (19, contra 11 ou menos
de qualquer outra), verificado a 21/10/2026.

- **Cartas:** `get_players_by_rating(year="26", min_rating=88, max_rating=89,
  version="gold_rare")`, páginas 1 e 2 (10 créditos), com preço de PC > 0 e
  uma das cinco ligas. Ficam de fora os jogadores que têm carta TOTS no
  `cartas_promos_fc26.csv` (porque a carta deles ficaria afectada pela
  própria promo, não pela química). **Até 4 por liga**, sorteadas com
  `random.Random(2026)` por ordem de id; se houver menos de 4, entram todas.
- **Histórico diário de PC** de cada uma: 2 créditos. Até 20 cartas = 40
  créditos.
- **Janelas:** as da H4 (D−7 → D−1, D−1 → D+3, D → D+7).
- **Efeito por dia:** mediana do ROI das cartas da liga do dia − mediana do
  ROI das cartas das outras quatro ligas.
- **Passa** se o efeito for > 0 em **pelo menos 4 dos 5 dias** e a mediana
  dos cinco for > 0. Com 5 dias não há metades; este critério é mais
  exigente para compensar.

Orçamento da opção B: 105 (H1-H3) + 10 + 40 (H4j) = **155 de 200**.

## O que não se testa aqui (e porquê)

- **A carta de promo em si** (comprar a carta nova depois de sair): os preços
  das cartas novas começam no lançamento, sem passado para a referência. Fica
  para quando houver créditos para o FC 27.
- **SBCs e evoluções** que pedem certos jogadores: não há uma lista das
  exigências do FC 26 com datas. Fica para o FC 27, onde o `get_fc27_sbcs`
  dá as exigências.
