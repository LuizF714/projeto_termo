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

# --- INTERFACE ---
st.set_page_config(page_title="Termo Lagrange - UDF", layout="wide")
st.title("🚀 Assistente de Tabelas Termodinâmicas")
st.markdown("**Estudante:** Luiz Felipe | **Instituição:** UDF | Suporte à Análise Exergética")

# Criando as abas conforme sua solicitação
tab1, tab2 = st.tabs(["📊 Consulta Geral (Modo Original)", "🌡️ Busca por P e T (Novo Modo)"])

# --- ABA 1: O JEITO QUE JÁ FUNCIONAVA ---
with tab1:
    st.header("Modo de Busca Original")
    tabela_sel = st.selectbox("Selecione a Tabela:", 
                              ["A2 - Água Saturada (Temp)", "A3 - Água Saturada (Pressão)", 
                               "A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t1")
    t_id = tabela_sel.split(' - ')[0][:2]

    try:
        df = pd.read_csv(f"{t_id}.csv", sep=';', decimal=',', engine='python')
        df.columns = df.columns.str.strip()

        if t_id in ["A4", "A5"]:
            # Pressões pré-definidas para facilitar
            pressoes = sorted(df['p (bar)'].unique())
            p_alvo = st.selectbox("Selecione a Pressão (bar):", pressoes, key="p1")
            bloco = df[df['p (bar)'] == p_alvo]
            
            col_busca = st.selectbox("Buscar por qual variável?", bloco.columns, key="c1")
            valor = st.number_input(f"Insira o valor de {col_busca}:", format="%.4f", key="v1")
            
            if st.button("Interpolar Dados", key="b1"):
                res = interpolar_lagrange(bloco, col_busca, valor)
                st.dataframe(res)
        else:
            col_busca = st.selectbox("Buscar por qual variável?", df.columns, key="c2")
            valor = st.number_input(f"Insira o valor de {col_busca}:", format="%.4f", key="v2")
            
            if st.button("Calcular Saturação", key="b2"):
                res = interpolar_lagrange(df, col_busca, valor)
                st.dataframe(res)
    except: st.error("Erro ao carregar arquivo.")

# --- ABA 2: O NOVO MODO (PRESSÃO E TEMPERATURA JUNTOS) ---
with tab2:
    st.header("Busca por Estado Definido (P e T)")
    st.write("Use esta aba quando o problema fornecer a Pressão e a Temperatura simultaneamente.")
    
    tabela_sel_2 = st.selectbox("Selecione a Região:", 
                                ["A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t2")
    t_id_2 = tabela_sel_2.split(' - ')[0][:2]

    try:
        df2 = pd.read_csv(f"{t_id_2}.csv", sep=';', decimal=',', engine='python')
        df2.columns = df2.columns.str.strip()
        
        pressoes2 = sorted(df2['p (bar)'].unique())
        
        c1, c2 = st.columns(2)
        with c1:
            p_final = st.selectbox("Pressão (bar):", pressoes2, key="p2")
        with c2:
            t_final = st.number_input("Temperatura (°C):", value=200.0, format="%.2f", key="v3")
            
        if st.button("Encontrar Propriedades", key="b3"):
            bloco2 = df2[df2['p (bar)'] == p_final]
            res2 = interpolar_lagrange(bloco2, 'T (C)', t_final)
            st.success(f"Estado encontrado para {p_final} bar e {t_final} °C")
            st.dataframe(res2)
    except: st.error("Erro ao carregar arquivo.")

st.divider()
st.caption("UDF 2026 - Engenharia Mecânica")