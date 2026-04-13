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
        return df[df[coluna_busca] == valor_alvo].iloc[[0]]
    
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

st.sidebar.header("⚙️ Configurações")
unidade_p = st.sidebar.radio("Unidade de Pressão:", ["bar", "Pa (Pascal)", "kPa (Quilopascal)"])

st.title("🚀 Assistente de Tabelas Termodinâmicas")
st.markdown(f"**Estudante:** Luiz Felipe | **Matrícula:** 29898617 | **UDF**")

tab1, tab2 = st.tabs(["📊 Consulta Geral", "🔄 Interpolação Dupla (P e T)"])

# --- CONVERSOR DE PRESSÃO ---
def converter_para_bar(valor, unidade):
    if unidade == "Pa (Pascal)": return valor / 100000
    if unidade == "kPa (Quilopascal)": return valor / 100
    return valor

# --- ABA 1: CONSULTA GERAL ---
with tab1:
    st.header("Busca Simples")
    tabela_sel = st.selectbox("Tabela:", ["A2", "A3", "A4", "A5"], key="t1")
    try:
        df = pd.read_csv(f"{tabela_sel}.csv", sep=';', decimal=',', engine='python').apply(pd.to_numeric, errors='coerce')
        col_busca = st.selectbox("Propriedade de entrada:", df.columns, key="c1")
        v_input = st.number_input(f"Valor de {col_busca}:", format="%.4f", key="v1")
        
        v_calc = converter_para_bar(v_input, unidade_p) if "p (bar)" in col_busca else v_input

        if st.button("Calcular", key="b1"):
            res = interpolar_lagrange(df, col_busca, v_calc)
            st.dataframe(res)
    except: st.error("Erro ao carregar arquivo.")

# --- ABA 2: INTERPOLAÇÃO DUPLA (O que você pediu) ---
with tab2:
    st.header("Busca por P e T (Qualquer valor)")
    st.info("Esta aba permite buscar pressões que NÃO estão na tabela através de interpolação dupla.")
    
    tabela_sel2 = st.selectbox("Região:", ["A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t2")
    t_id2 = tabela_sel2[:2]

    try:
        df2 = pd.read_csv(f"{t_id2}.csv", sep=';', decimal=',', engine='python').apply(pd.to_numeric, errors='coerce')
        
        c1, c2 = st.columns(2)
        with c1:
            p_in = st.number_input(f"Pressão ({unidade_p}):", format="%.2f", key="p_dupla")
            p_bar = converter_para_bar(p_in, unidade_p)
        with c2:
            t_in = st.number_input("Temperatura (°C):", value=200.0, format="%.2f", key="t_dupla")

        if st.button("Realizar Interpolação Dupla", key="b2"):
            # 1. Pegar as pressões únicas
            p_unicas = sorted(df2['p (bar)'].unique())
            
            # Encontrar as pressões vizinhas
            p_menores = [p for p in p_unicas if p <= p_bar]
            p_maiores = [p for p in p_unicas if p > p_bar]
            
            if not p_menores or not p_maiores:
                st.error("Pressão fora da faixa da tabela.")
            else:
                p1, p2 = p_menores[-1], p_maiores[0]
                
                # Interpolar T para p1 e p2
                res_p1 = interpolar_lagrange(df2[df2['p (bar)'] == p1], 'T (C)', t_in)
                res_p2 = interpolar_lagrange(df2[df2['p (bar)'] == p2], 'T (C)', t_in)
                
                # Interpolar entre os resultados de p1 e p2 usando a pressão alvo
                final_df = pd.concat([res_p1, res_p2])
                final_res = interpolar_lagrange(final_df, 'p (bar)', p_bar)
                
                st.success(f"Resultado para {p_in} {unidade_p} ({p_bar:.2f} bar) e {t_in} °C")
                st.dataframe(final_res)
    except: st.error("Erro nos arquivos.")

st.divider()
st.caption("UDF 2026 - Engenharia Mecânica")