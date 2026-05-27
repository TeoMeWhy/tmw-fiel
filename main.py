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
                            .rename(columns={
                                "qtdetransacaod28": "Frequência",
                                "qtdepontosposd28": "Valor",
                                "desclifecycleatual":"Ciclo de Vida Atual",
                                "avgintervalodiasvida": "Intervalo entre Dias"
                            })
                    )
    
    columns = ["Usuário", "Prob. Fiel", "Saldo Pontos", "Frequência", "Valor", "Intervalo entre Dias", "Ciclo de Vida Atual"]
    
    df_ranking = (df_analytics[columns]
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

st.dataframe(df_ranking, hide_index=True, height=250)


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

col1, col2 = st.columns(2)


chart = alt.Chart(df_plot).mark_circle().encode(
    x='Frequência',
    y='Valor',
    color=alt.Color('Usuário', legend=None),
    size=alt.value(100)
)

col1.altair_chart(chart, use_container_width=True)
col1.markdown("""
- Cada ponto é um usuário;
- Quanto mais à direita, mais frequente é a sua participação, com muita interação durante as lives e na plataforma de cursos;
- Quanto mais acima, maior o valor de pontos acumulados, provável que está farmando produtos mais valiosos, como streak de presença;              
""")

ciclo_vida_group = df_plot.groupby("Ciclo de Vida Atual").count()[["Usuário"]].reset_index().rename(columns={"Usuário": "Quantidade Usuários"})
col2.bar_chart(ciclo_vida_group, x="Ciclo de Vida Atual", y="Quantidade Usuários")
col2.markdown("""
Distribuição dos usuário pelos ciclos de vida presentes. Essa regra se dá apenas pela recência e pela idade na base, ou seja, tempo desde a última interação e tempos desde a primeira interação.
             
""")

st.markdown("""
#### Curva de Recorrência
""")

df_survival = df_plot.groupby(["Intervalo entre Dias"])[["Usuário"]].count()
df_survival = df_survival.reset_index(drop=False).rename(columns={"Usuário": "Quantidade Usuários"}).sort_values(by="Intervalo entre Dias")
df_survival["Qtde Acumulada"] = df_survival["Quantidade Usuários"].cumsum()
df_survival["Prob Acumulada"] = (df_survival["Qtde Acumulada"] / df_survival["Quantidade Usuários"].sum()).round(4)
st.line_chart(df_survival, x="Intervalo entre Dias", y="Prob Acumulada", width='stretch')

st.markdown("""
Nossa curva apresenta um crescimento bem rápido. Isso significa que nossos usuários tem uma alta probabilidade de se manterem ativos, são recorrentes em um período curto.

Metade de nossa base volta (em média) antes de 9 dias, e 80% voltam antes de 30 dias.

* Desconsideramos da análise usuários que tiveram apenas 1 dia de atividade, ou seja, aqueles que não tiveram uma segunda interação, pois não conseguimos calcular o intervalo entre dias para esses casos.
""")