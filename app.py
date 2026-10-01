"""App do fut-trading: conselheiro, notícias que mexem no mercado, calculadora e estudos.

Lê só ficheiros do repositório (noticias.csv, estudos/), que as Actions
mantêm actualizados. Não chama o parse.bot nem precisa de chave nenhuma, e
nunca toca na conta EA: o bot aconselha, não opera.

Cada aba corre dentro do seu próprio try. Uma falha numa aba escreve o erro
nessa aba e não leva as outras (lição do bet, repetida aqui e apanhada pela
revisão independente de 01/10/2026: um noticias.csv vazio deitava a app
inteira abaixo, calculadora incluída).
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import calculadora as C
import conselheiro as K
import noticias as N

RAIZ = Path(__file__).parent
# Variável de ambiente só para os testes poderem apontar a um ficheiro
# estragado; em produção é sempre o noticias.csv do repositório.
NOTICIAS = Path(os.environ.get("FUT_NOTICIAS", RAIZ / "noticias.csv"))
CATEGORIAS = {
    "leak": "Leak",
    "sbc": "SBC",
    "totw": "TOTW",
    "evolucao": "Evolução",
    "promo": "Promo",
}
CAIXA = {
    "COMPRAR": st.success,
    "VENDER": st.warning,
    "ESPERAR": st.info,
    "EVITAR": st.error,
    "AVISO": st.info,
}

st.set_page_config(page_title="FUT Trading — PC", page_icon="⚽", layout="wide")
st.title("FUT Trading — EA FC 27, PC")
st.caption("Conselheiro de mercado. Não compra nem vende nada: as operações fazes tu.")

with st.sidebar:
    saldo = st.number_input("Saldo actual (coins)", min_value=0, value=100_000, step=1_000)
    investido = st.number_input(
        "Já investido neste ciclo (coins)", min_value=0, value=0, step=1_000,
        help="O que gastaste em compras desde sábado e ainda não vendeste, ao preço de "
             "compra. O tecto do conselheiro é sobre o capital do ciclo (saldo + isto), "
             "não sobre o saldo do dia.",
    )
    st.caption("Fica só nesta sessão. Actualiza os dois depois de cada compra ou venda.")


# Leitura ao vivo dos RSS, para as notícias não dependerem da recolha
# agendada (que no GitHub chega com horas de atraso). FUT_AO_VIVO=0 desliga-a:
# os testes fazem-no para nunca irem à rede.
AO_VIVO = os.environ.get("FUT_AO_VIVO", "1") != "0"


@st.cache_data(ttl=30 * 60, show_spinner=False)
def _ao_vivo(caminho):
    """Uma ida às fontes a cada 30 minutos, partilhada por todas as visitas."""
    linhas, novas, falhas = N.ao_vivo(Path(caminho))
    return linhas, len(novas), falhas, datetime.now(timezone.utc)


def estado_noticias():
    """(fonte, detalhe) para mostrar de onde vieram as notícias."""
    if not AO_VIVO:
        return "arquivo", "só o noticias.csv (leitura ao vivo desligada)"
    _, novas, falhas, quando = _ao_vivo(str(NOTICIAS))
    hora = quando.astimezone(ZoneInfo("Europe/Lisbon"))
    texto = f"actualizado às {hora:%H:%M} (Lisboa); {novas} ainda não arquivada(s)"
    if falhas:
        texto += f"; fontes em falha: {len(falhas)} de {len(N.FONTES)}"
    return "ao vivo", texto


def ler_noticias():
    if AO_VIVO:
        linhas, _, _, _ = _ao_vivo(str(NOTICIAS))
        df = pd.DataFrame(linhas, columns=None if linhas else
                          ["publicado_em", "categoria", "titulo", "link"])
    elif not NOTICIAS.exists():
        return pd.DataFrame(columns=["publicado_em", "categoria", "titulo", "link"])
    else:
        df = pd.read_csv(NOTICIAS)
    # Sem isto, um ficheiro sem "categoria" lia-se bem e rebentava depois,
    # dentro do conselheiro, levando a aba inteira (apanhado pelo teste).
    falta = {"publicado_em", "categoria", "titulo", "link"} - set(df.columns)
    if falta:
        raise ValueError(f"faltam colunas no noticias.csv: {sorted(falta)}")
    # format="ISO8601": os instantes vêm com fuso ("+00:00"). Sem formato, o
    # pandas adivinha e avisa — e no bet um aviso destes escondia um erro de
    # datas.
    df["publicado_em"] = pd.to_datetime(df["publicado_em"], format="ISO8601", utc=True)
    return df.sort_values("publicado_em", ascending=False)


def aba_conselheiro():
    # FUT_AGORA só para os testes poderem fixar o dia (um sábado, uma sexta
    # depois da promo); em produção é sempre o relógio.
    agora = (datetime.fromisoformat(os.environ["FUT_AGORA"]) if "FUT_AGORA" in os.environ
             else datetime.now(timezone.utc))
    lisboa = agora.astimezone(ZoneInfo("Europe/Lisbon"))
    st.subheader(f"Agora: {K.DIAS[lisboa.weekday()]}, {lisboa:%d/%m %H:%M} (Lisboa)")
    # As notícias só acrescentam avisos: se falharem, os conselhos continuam.
    try:
        noticias = ler_noticias().to_dict("records")
    except Exception as e:
        noticias = []
        st.warning(f"Não consegui ler as notícias ({type(e).__name__}); "
                   "os conselhos abaixo não incluem avisos de promos.")
    for c in K.conselhos(agora, saldo, noticias, investido_no_ciclo=investido):
        # Dois espaços antes do \n: quebra de linha em Markdown.
        linhas = [f"**{c.acao} — {c.o_que}**", f"*Quando:* {c.quando}", c.porque]
        if c.quantia is not None:
            por_rating = ", ".join(
                f"{v:,.0f} em {r}" for r, v in K.quantias(saldo, investido, agora).items()
            )
            fraccao = K.FRACCAO_LANCAMENTO if K.em_lancamento(agora) else K.FRACCAO_MAXIMA
            linhas.append(
                f"*Quanto, ainda neste ciclo:* {por_rating} (total {c.quantia:,.0f}; tecto de "
                f"{fraccao:.0%} do capital do ciclo, o resto fica de reserva)"
            )
        linhas.append(f"*Confiança:* {c.confianca}")
        CAIXA[c.acao]("  \n".join(linhas))

    st.markdown("#### Plano da semana")
    st.caption(
        "FC 26, fodder 84-87. O preço face à média é da época inteira; o ROI de comprar "
        "e vender à quarta é medido só na 2.ª metade, com o intervalo de 95%. Vender "
        "sempre antes de sexta às 18h de Londres, quando abre a promo."
    )

    def roi(d):
        f = K.FORA_DA_AMOSTRA.get(d)
        if f is None:
            return "—", "—"
        return K.pct(f["mediana"]), f"{K.pct(f['ic'][0])} a {K.pct(f['ic'][1])}"

    st.table(pd.DataFrame({
        "dia": K.DIAS,
        "preço face à média da semana": [K.pct(K.PERFIL_FC26[d]) for d in range(7)],
        "comprar hoje, vender quarta": [roi(d)[0] for d in range(7)],
        "intervalo 95%": [roi(d)[1] for d in range(7)],
    }))


def aba_noticias():
    df = ler_noticias()
    escolhidas = st.multiselect(
        "Categorias", list(CATEGORIAS), default=list(CATEGORIAS),
        format_func=CATEGORIAS.get,
    )
    df = df[df["categoria"].isin(escolhidas)]
    _, detalhe = estado_noticias()
    st.caption(
        f"{len(df)} notícias, dos RSS do Google News e do SoccerGaming, que republicam os "
        f"leaks dos insiders do X — {detalhe}. Hora de publicação em UTC."
    )
    for _, n in df.head(60).iterrows():
        rotulo = CATEGORIAS.get(n["categoria"], n["categoria"])
        st.markdown(
            f"**{rotulo}** · {n['publicado_em']:%d/%m %H:%M} — [{n['titulo']}]({n['link']})"
        )


def aba_calculadora():
    st.subheader("Quanto ganho nesta operação?")
    c1, c2, c3 = st.columns(3)
    compra = c1.number_input("Preço de compra", min_value=1, value=4_000, step=50)
    venda = c2.number_input("Preço de venda", min_value=1, value=4_500, step=50)
    maximo = C.quantidade_maxima(saldo, compra)
    quantidade = c3.number_input(
        "Quantidade", min_value=0, value=min(maximo, 10), step=1,
        help=f"Cabem {maximo} no saldo actual.",
    )
    r = C.operacao(compra, venda, quantidade)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Investido", f"{r['investido']:,.0f}")
    m2.metric("Recebido (−5%)", f"{r['recebido']:,.0f}")
    m3.metric("Lucro", f"{r['lucro']:+,.0f}")
    m4.metric("ROI", f"{r['roi'] * 100:+.1f}%")

    st.info(
        f"Para não perder dinheiro, vende a **{C.preco_minimo_venda(compra):,.0f}** ou mais "
        f"(a EA fica com 5% de cada venda). Com o saldo actual cabem **{maximo}** cópias."
    )
    if quantidade > maximo:
        st.warning("A quantidade passa o saldo actual.")
    st.caption(
        "A quantidade a arriscar numa carta não está medida, por isso a calculadora não "
        "a impõe. Uma referência: as cartas 86 do FC 27 medidas venderam entre 34 e 385 "
        "cópias por hora a 01/10/2026, mas não eram o fodder mais barato (ver Estudos)."
    )


def aba_estudos():
    # Antes dizia "ainda não são recomendações", ao lado de um Conselheiro que
    # recomenda (achado 9 da revisão de 01/10/2026).
    st.caption(
        "As medições em que o Conselheiro se baseia, com a taxa descontada e os limites "
        "de cada uma. O ciclo semanal é do FC 26 e ainda não foi confirmado no FC 27: é "
        "por isso que as compras têm confiança média ou baixa."
    )
    for f in sorted((RAIZ / "estudos").glob("*.md")):
        texto = f.read_text(encoding="utf-8")
        titulo = texto.splitlines()[0].lstrip("# ").strip()
        with st.expander(titulo, expanded=False):
            st.markdown(texto.split("\n", 1)[1])


ABAS = {
    "Conselheiro": aba_conselheiro,
    "Notícias": aba_noticias,
    "Calculadora": aba_calculadora,
    "Estudos": aba_estudos,
}
for aba, desenhar in zip(st.tabs(list(ABAS)), ABAS.values()):
    with aba:
        try:
            desenhar()
        except Exception as e:
            # Nunca st.stop(): pararia o script e levava as abas seguintes.
            st.error(f"Esta aba falhou ({type(e).__name__}: {e}). As outras continuam a "
                     "funcionar.")
