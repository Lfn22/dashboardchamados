# --- Dashboard de Chamados com CSV Automático ---
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
from datetime import datetime, timedelta
import os

# --- Verifica se o CSV existe ---
if not os.path.isfile("chamados.csv"):
    st.info("Arquivo 'chamados.csv' não encontrado. Gerando dados fictícios...")

    setores = ["Financeiro", "TI", "RH", "Comercial", "Logística"]
    status = ["Aberto", "Em andamento", "Resolvido"]

    np.random.seed(42)
    df = pd.DataFrame({
        "ID": range(1, 101),
        "setor": [random.choice(setores) for _ in range(100)],
        "data": [datetime.today() - timedelta(days=random.randint(0, 365)) for _ in range(100)],
        "status": [random.choice(status) for _ in range(100)],
        "tempo_resolucao": np.random.randint(1, 72, size=100)  # horas
    })

    df.to_csv("chamados.csv", index=False)
    st.success("CSV 'chamados.csv' criado com sucesso!")

# --- Carregar os dados ---
df = pd.read_csv("chamados.csv")
df["data"] = pd.to_datetime(df["data"])

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Chamados",
    page_icon="📊",
    layout="wide",
)

# --- Barra Lateral (Filtros Avançados) ---
st.sidebar.header("🔍 Filtros")

# Filtro de datas
data_min = df["data"].min()
data_max = df["data"].max()
datas_selecionadas = st.sidebar.date_input(
    "Período",
    value=[data_min, data_max],
    min_value=data_min,
    max_value=data_max
)

# Filtro de setor
setores = sorted(df["setor"].unique())
setores_sel = st.sidebar.multiselect("Setor", setores, default=setores)

# Filtro de status
status = sorted(df["status"].unique())
status_sel = st.sidebar.multiselect("Status", status, default=status)

# --- Filtragem do DataFrame ---
df_filtrado = df[
    (df["setor"].isin(setores_sel)) &
    (df["status"].isin(status_sel)) &
    (df["data"] >= pd.to_datetime(datas_selecionadas[0])) &
    (df["data"] <= pd.to_datetime(datas_selecionadas[1]))
]

# --- Título ---
st.title("📊 Dashboard de Chamados")
st.markdown("Analise os chamados por setor, status e tempo de resolução. Use os filtros à esquerda para refinar a visualização.")

# --- KPIs (Métricas Principais) ---
st.subheader("📌 Métricas Gerais")

if not df_filtrado.empty:
    tempo_medio = df_filtrado["tempo_resolucao"].mean()
    taxa_resolucao = (df_filtrado["status"].eq("Resolvido").mean()) * 100
    total_chamados = df_filtrado.shape[0]
    setor_top = df_filtrado["setor"].mode()[0]
else:
    tempo_medio, taxa_resolucao, total_chamados, setor_top = 0, 0, 0, "-"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tempo Médio de Resolução", f"{tempo_medio:.1f}h")
col2.metric("Taxa de Resolução", f"{taxa_resolucao:.1f}%")
col3.metric("Total de Chamados", total_chamados)
col4.metric("Setor com Mais Chamados", setor_top)

st.markdown("---")

# --- Gráficos ---
st.subheader("📈 Análises Visuais")

# Layout de gráficos
col_graf1, col_graf2 = st.columns(2)

# Gráfico 1 - Chamados por Setor
with col_graf1:
    if not df_filtrado.empty:
        chamados_por_setor = df_filtrado.groupby("setor")["ID"].count().reset_index()
        graf1 = px.bar(
            chamados_por_setor,
            x="setor",
            y="ID",
            title="Chamados por Setor",
            labels={"ID": "Quantidade de Chamados", "setor": "Setor"},
            color="setor",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(graf1, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para Chamados por Setor.")

# Gráfico 2 - Status dos Chamados
with col_graf2:
    if not df_filtrado.empty:
        status_count = df_filtrado["status"].value_counts().reset_index()
        status_count.columns = ["Status", "Quantidade"]
        graf2 = px.pie(
            status_count,
            names="Status",
            values="Quantidade",
            title="Distribuição dos Status",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        graf2.update_traces(textinfo="percent+label")
        st.plotly_chart(graf2, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para Status.")

# Segunda linha de gráficos
col_graf3, col_graf4 = st.columns(2)

# Gráfico 3 - Boxplot do Tempo de Resolução por Setor
with col_graf3:
    if not df_filtrado.empty:
        graf3 = px.box(
            df_filtrado,
            x="setor",
            y="tempo_resolucao",
            title="Distribuição do Tempo de Resolução por Setor",
            labels={"setor": "Setor", "tempo_resolucao": "Tempo (horas)"},
            color="setor",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(graf3, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para Boxplot de Tempo.")

# Gráfico 4 - Evolução de Chamados por Mês
with col_graf4:
    if not df_filtrado.empty:
        df_filtrado["mes"] = df_filtrado["data"].dt.to_period("M").astype(str)
        chamados_por_mes = df_filtrado.groupby("mes")["ID"].count().reset_index()
        graf4 = px.line(
            chamados_por_mes,
            x="mes",
            y="ID",
            title="Evolução de Chamados por Mês",
            markers=True,
            labels={"ID": "Chamados", "mes": "Mês"},
            line_shape="linear"
        )
        st.plotly_chart(graf4, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para Evolução Mensal.")

# --- Botão para download dos dados filtrados ---
st.markdown("---")
st.subheader("📥 Exportar Dados Filtrados")
if not df_filtrado.empty:
    st.download_button(
        label="📥 Baixar CSV",
        data=df_filtrado.to_csv(index=False),
        file_name="chamados_filtrados.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhum dado para exportar.")

# --- Tabela de Dados Detalhados ---
st.markdown("---")
st.subheader("📋 Chamados Detalhados")
st.dataframe(df_filtrado)
