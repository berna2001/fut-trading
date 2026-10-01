"""App do fut-trading: notícias que mexem no mercado, estudos e calculadora.

Lê só ficheiros do repositório (noticias.csv, estudos/*.md), que as Actions
mantêm actualizados. Não chama o parse.bot nem precisa de chave nenhuma, e
nunca toca na conta EA: o bot aconselha, não opera.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import calculadora as C

RAIZ = Path(__file__).parent
CATEGORIAS = {
    "leak": "Leak",
    "sbc": "SBC",
    "totw": "TOTW",
    "evolucao": "Evolução",
    "promo": "Promo",
}

st.set_page_config(page_title="FUT Trading — PC", page_icon="⚽", layout="wide")
st.title("FUT Trading — EA FC 27, PC")
st.caption("Conselheiro de mercado. Não compra nem vende nada: as operações fazes tu.")

with st.sidebar:
    saldo = st.number_input("Saldo actual (coins)", min_value=0, value=100_000, step=1_000)
    st.caption("Fica só nesta sessão. Actualiza-o depois de cada compra ou venda.")


def ler_noticias():
    f = RAIZ / "noticias.csv"
    if not f.exists():
        return pd.DataFrame(columns=["publicado_em", "categoria", "titulo", "link"])
    df = pd.read_csv(f)
    # format="ISO8601": os instantes vêm com fuso ("+00:00"). Sem formato, o
    # pandas adivinha e avisa — e no bet um aviso destes escondia um erro de
    # datas.
    df["publicado_em"] = pd.to_datetime(df["publicado_em"], format="ISO8601", utc=True)
    return df.sort_values("publicado_em", ascending=False)


aba_noticias, aba_calc, aba_estudos = st.tabs(["Notícias", "Calculadora", "Estudos"])

with aba_noticias:
    df = ler_noticias()
    escolhidas = st.multiselect(
        "Categorias", list(CATEGORIAS), default=list(CATEGORIAS),
        format_func=CATEGORIAS.get,
    )
    df = df[df["categoria"].isin(escolhidas)]
    st.caption(
        f"{len(df)} notícias. Recolhidas de 2 em 2 horas dos RSS do Google News e do "
        "SoccerGaming, que republicam os leaks dos insiders do X. Hora de publicação em UTC."
    )
    for _, n in df.head(60).iterrows():
        rotulo = CATEGORIAS.get(n["categoria"], n["categoria"])
        st.markdown(
            f"**{rotulo}** · {n['publicado_em']:%d/%m %H:%M} — [{n['titulo']}]({n['link']})"
        )

with aba_calc:
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
        "a impõe. Uma referência medida: as cartas 86 do FC 27 venderam entre 34 e 385 "
        "cópias por hora a 01/10/2026 (ver Estudos)."
    )

with aba_estudos:
    st.caption(
        "Resultados medidos, com a taxa descontada. Ainda não são recomendações: o ciclo "
        "semanal do FC 26 tem de ser confirmado no FC 27."
    )
    for f in sorted((RAIZ / "estudos").glob("*.md")):
        texto = f.read_text(encoding="utf-8")
        titulo = texto.splitlines()[0].lstrip("# ").strip()
        with st.expander(titulo, expanded=False):
            st.markdown(texto.split("\n", 1)[1])
