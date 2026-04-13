import streamlit as st
import pandas as pd
import numpy as np

# --- FUNÇÕES DE CÁLCULO ---
def lagrange_2_grau(x_pontos, y_pontos, x_alvo):
    n = len(x_pontos)
    resultado = 0
    for i in range(n):
        termo = y_pontos[i]
        for j in range(n):
            if i != j:
                termo *= (x_alvo - x_pontos[j]) / (x_pontos[i] - x_pontos[j])
        resultado += termo
    return resultado

def interpolar_lagrange(df, coluna_busca, valor_alvo):
    df = df.apply(pd.to_numeric, errors='coerce').dropna(subset=[coluna_busca])
    df = df.sort_values(by=coluna_busca)
    if valor_alvo in df[coluna_busca].values:
        return df[df[coluna_busca] == valor_alvo]
    df_temp = df.copy()
    df_temp['dist'] = (df_temp[coluna_busca] - valor_alvo).abs()
    vizinhos = df_temp.nsmallest(3, 'dist').sort_values(by=coluna_busca)
    if len(vizinhos) < 2: return None
    x_pontos = vizinhos[coluna_busca].values
    res = {}
    for col in df.columns:
        if col == 'dist': continue
        y_pontos = vizinhos[col].values
        res[col] = lagrange_2_grau(x_pontos, y_pontos, valor_alvo)
    return pd.DataFrame([res])

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Termo Lagrange - UnB", layout="wide")
st.title("🚀 Assistente de Tabelas Termodinâmicas")
st.markdown("**Estudante:** Luiz F. | Suporte à Análise Exergética")

# Criando as Abas (Tabs) que você sugeriu
tab1, tab2 = st.tabs(["💧 Modo Saturação", "🔥 Modo Estado Definido (P e T)"])

# --- ABA 1: SATURAÇÃO ---
with tab1:
    st.header("Busca em Tabelas de Saturação")
    nome_tabela = st.selectbox("Selecione a Tabela:", 
                               ["A2 - Água Saturada (Temperatura)", 
                                "A3 - Água Saturada (Pressão)"], key="sat_t")
    tabela_id = "A2" if "A2" in nome_tabela else "A3"

    try:
        df = pd.read_csv(f"{tabela_id}.csv", sep=';', decimal=',', engine='python')
        df.columns = df.columns.str.strip()
        
        col_busca = st.selectbox("Propriedade de Entrada:", df.columns, key="sat_c")
        valor_alvo = st.number_input(f"Valor para {col_busca}:", format="%.4f", key="sat_v")
        
        if st.button("Calcular Saturação", use_container_width=True):
            res = interpolar_lagrange(df, col_busca, valor_alvo)
            st.subheader("📍 Propriedades de Saturação")
            st.dataframe(res)
    except:
        st.error(f"Certifique-se que o arquivo {tabela_id}.csv está no GitHub.")

# --- ABA 2: ESTADO DEFINIDO ---
with tab2:
    st.header("Busca por Coordenadas (P e T)")
    nome_tabela_2 = st.selectbox("Selecione a Região:", 
                                 ["A4 - Vapor d'água Superaquecido", 
                                  "A5 - Água Líquida Comprimida"], key="def_t")
    tabela_id_2 = "A4" if "A4" in nome_tabela_2 else "A5"

    try:
        df_2 = pd.read_csv(f"{tabela_id_2}.csv", sep=';', decimal=',', engine='python')
        df_2.columns = df_2.columns.str.strip()
        
        # Lógica para mostrar apenas as pressões que existem no CSV
        pressões_disponiveis = sorted(df_2['p (bar)'].unique())
        
        c1, c2 = st.columns(2)
        with c1:
            p_alvo = st.selectbox("Selecione a Pressão (bar):", pressões_disponiveis)
        with c2:
            t_alvo = st.number_input("Digite a Temperatura (°C):", value=200.0, format="%.2f")
            
        if st.button("Calcular Estado Definido", use_container_width=True):
            bloco_p = df_2[df_2['p (bar)'] == p_alvo]
            res_2 = interpolar_lagrange(bloco_p, 'T (C)', t_alvo)
            st.subheader(f"📍 Propriedades para {p_alvo} bar")
            st.dataframe(res_2)
    except:
        st.error(f"Erro ao carregar {tabela_id_2}.csv.")

st.divider()
st.caption("Engenharia Mecânica - UnB 2026")