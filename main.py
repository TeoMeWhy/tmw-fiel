from turtle import title

import streamlit as st
import altair as alt

import os
import dotenv

dotenv.load_dotenv()

PALANTIR_URI = os.getenv("PALANTIR_URI")
POINTS_URI = os.getenv("POINTS_URI")

from clients import Palantir, Points
import pandas as pd

@st.cache_resource(ttl='1min')
def load_data():

    palantir_client = Palantir(uri=PALANTIR_URI)
    points_client = Points(uri=POINTS_URI)
    
    palantir_scores = palantir_client.get_scores()
    df_predictions = (pd.DataFrame(palantir_scores["predictions"])
                        .T
                        .reset_index()
                        .rename(columns={"index": "ID Usuário", "score_fiel":"Prob. Fiel"}))

    palantir_features = palantir_client.get_features()
    df_features = (pd.DataFrame(palantir_features["features"])
                    .rename(columns={"id": "ID Usuário"}))

    customers = points_client.get_customers()
    df_customers = (pd.DataFrame(customers)[["uuid", "customer_name", "points"]]
                    .rename(columns={"uuid": "ID Usuário", "customer_name": "Usuário", "points":"Saldo Pontos"}))

    df_analytics = (df_predictions.merge(df_features, on="ID Usuário")
                            .merge(df_customers, on="ID Usuário")
                            .rename(columns={"qtdetransacaod28": "Frequência", "qtdepontosposd28": "Valor", "desclifecycleatual":"Ciclo de Vida Atual"})
                            )
    
    df_ranking = (df_analytics[["Usuário", "Prob. Fiel", "Saldo Pontos", "Frequência", "Valor", "Ciclo de Vida Atual"]]
                            .sort_values(by="Prob. Fiel", ascending=False)
                            .drop(columns=["Prob. Fiel"])
                            )

    df_ranking = (df_ranking[df_ranking["Usuário"].fillna("") != ""]
                        .reset_index(drop=True)
                        .reset_index(drop=False))

    df_ranking.rename(columns={"index": "Ranking"}, inplace=True)
    df_ranking["Ranking"] += 1

    return df_analytics, df_ranking


INFO_LIFE_CYCLE = """
    - 01-CURIOSO: Quando o cliente é mais novo que 7 dias;
    
    - 02-FIEL: Quando o cliente é mais velho que 7 dias e a diferença entre a última e a penúltima transação é menor ou igual a 14 dias;
    
    - 02-RECONQUISTADO: Quando a última transação foi a menos de 7 dias e a diferença entre a última e a penúltima transação é entre 15 e 27 dias;
    
    - 02-REBORN: Quando a última transação foi a menos de 7 dias e a diferença entre a última e a penúltima transação é maior que 27 dias;
    
    - 03-TURISTA: Quando a última transação foi entre 8 e 14 dias atrás;
    
    - 04-DESENCANTADA: Quando a última transação foi entre 15 e 28 dias atrás;
    
    - 05-ZUMBI: Quando a última transação foi há mais de 28 dias;
    
"""


st.set_page_config(
    page_title="Ranking Fiel Téo Me Why",
    page_icon=":key:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Ranking Fiel Téo Me Why")

st.markdown("""
Acompanhamento do nosso programa de fidelidade, com base na probabilidade de fidelidade dos clientes e seus saldos de pontos.
            
A tabela abaixo representa o ranking ordenado de nossos usuários com base na probabilidade de se manter fiel ao projeto Téo Me Why. Quanto **maior** o valor, melhor seu ranking.
            
#### Método e Projeto:

Construímos esse modelo de Machine Learning durante o projeto de [Loyalty Predict](https://www.youtube.com/playlist?list=PLvlkVRRKOYFSNomvdmW4-EA3Ap3cyv4H5), onde construímos Feature Store a partir dos dados transacionais do nosso sistema de fidelidade.

Tanto o chat de nossas [transmissões na Twitch](https://twitch.tv/teomewhy), quanto na nossa [plataforma de cursos](https://cursos.teomewhy.org), geram dados utilizados por estes modelos.

""")

df_analytics, df_ranking = load_data()

st.dataframe(df_ranking, hide_index=True)


st.markdown("""
Quer descobrir o seu score de fidelidade? Confira seu perfil em nossa plataforma [cursos.teomewhy.org/perfil](https://cursos.teomewhy.org/perfil) ou acesse o chat da [Twitch.tv/teomewhy](https://twitch.tv/teomewhy) e envie a mensagem !fiel.
""")


st.markdown(""" ### Frequência x Valor""")

life_cycle = df_analytics["Ciclo de Vida Atual"].unique().tolist()
life_cycle.sort()

grupo_fiel = st.multiselect("Grupo de clientes:", options=life_cycle, help=INFO_LIFE_CYCLE)

if len(grupo_fiel) > 0:
    df_plot = df_analytics[df_analytics["Ciclo de Vida Atual"].isin(grupo_fiel)].copy()

else:
    df_plot = df_analytics.copy()

df_plot = df_plot[df_plot["Usuário"].fillna("") != ""]

chart = alt.Chart(df_plot).mark_circle().encode(
    x='Frequência',
    y='Valor',
    color=alt.Color('Usuário', legend=None),
    size=alt.value(100)
)

col1, col2 = st.columns(2)

col1.altair_chart(chart, use_container_width=True)

ciclo_vida_group = df_plot.groupby("Ciclo de Vida Atual").count()[["Usuário"]].reset_index().rename(columns={"Usuário": "Quantidade Usuários"})
col2.bar_chart(ciclo_vida_group, x="Ciclo de Vida Atual", y="Quantidade Usuários")
