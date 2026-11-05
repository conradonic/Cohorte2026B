import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


GAPMINDER_URL = (
    "https://raw.githubusercontent.com/resbaz/r-novice-gapminder-files/master/"
    "data/gapminder-FiveYearData.csv"
)


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    return pd.read_csv(GAPMINDER_URL)


st.set_page_config(page_title="Gapminder con pandas", layout="wide")

st.title("Gapminder con pandas")

gapminder = cargar_datos()

anios = sorted(gapminder["year"].unique())
continentes = sorted(gapminder["continent"].unique())

with st.sidebar:
    anio = st.select_slider("Año", options=anios, value=max(anios))
    continentes_seleccionados = st.multiselect(
        "Continentes",
        options=continentes,
        default=continentes,
    )

datos_filtrados = gapminder[
    (gapminder["year"] == anio)
    & (gapminder["continent"].isin(continentes_seleccionados))
].copy()

st.dataframe(datos_filtrados, use_container_width=True)

tab_linea, tab_scatter, tab_barras = st.tabs(
    ["Evolución", "Países", "Continentes"]
)

with tab_linea:
    vida_por_continente = (
        gapminder[gapminder["continent"].isin(continentes_seleccionados)]
        .pivot_table(
            index="year",
            columns="continent",
            values="lifeExp",
            aggfunc="mean",
        )
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    vida_por_continente.plot(marker="o", grid=True, ax=ax)
    ax.set_title("Esperanza de vida promedio por continente")
    ax.set_xlabel("Año")
    ax.set_ylabel("Esperanza de vida")
    st.pyplot(fig)

with tab_scatter:
    fig, ax = plt.subplots(figsize=(9, 5))

    for continente, datos_continente in datos_filtrados.groupby("continent"):
        datos_continente.plot.scatter(
            x="gdpPercap",
            y="lifeExp",
            s=datos_continente["pop"] / 1_000_000,
            alpha=0.65,
            label=continente,
            ax=ax,
        )

    ax.set_xscale("log")
    ax.set_title(f"PBI per cápita y esperanza de vida ({anio})")
    ax.set_xlabel("PBI per cápita (escala log)")
    ax.set_ylabel("Esperanza de vida")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Continente")
    st.pyplot(fig)

with tab_barras:
    poblacion_por_continente = (
        datos_filtrados.groupby("continent")["pop"]
        .sum()
        .sort_values(ascending=False)
        / 1_000_000
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    poblacion_por_continente.plot.bar(
        ax=ax,
        title=f"Población por continente ({anio})",
        ylabel="Millones de personas",
        rot=0,
        grid=True,
    )
    st.pyplot(fig)
