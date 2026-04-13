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

# SELETOR DE UNIDADE GLOBAL NA BARRA LATERAL
st.sidebar.header("⚙️ Configurações")
unidade_p = st.sidebar.radio("Unidade de Pressão:", ["bar", "Pa (Pascal)"])

st.title("🚀 Assistente de Tabelas Termodinâmicas")
# MATRÍCULA REESTABELECIDA AQUI:
st.markdown(f"""
**Estudante:** Luiz Felipe | **Matrícula:** 29898617  
**Instituição:** UDF | **Unidade Atual:** {unidade_p}
""")

tab1, tab2 = st.tabs(["📊 Consulta Geral (1 Variável)", "🔄 Busca Cruzada (2 Variáveis)"])

# --- ABA 1: CONSULTA ORIGINAL ---
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
            pressoes_bar = sorted(df['p (bar)'].unique())
            if unidade_p == "Pa (Pascal)":
                pressoes_exibicao = [p * 100000 for p in pressoes_bar]
                p_escolhida = st.selectbox("Selecione a Pressão fixa (Pa):", pressoes_exibicao, key="p1")
                p_alvo = p_escolhida / 100000
            else:
                p_alvo = st.selectbox("Selecione a Pressão fixa (bar):", pressoes_bar, key="p1")
            
            df = df[df['p (bar)'] == p_alvo]
        
        col_busca = st.selectbox("Buscar por qual variável?", df.columns, key="c1")
        
        label_input = f"Insira o valor de {col_busca}"
        if "p (bar)" in col_busca and unidade_p == "Pa (Pascal)":
            label_input += " (em Pa)"
            
        valor = st.number_input(label_input, format="%.4f", key="v1")
        valor_calculo = (valor / 100000) if ("p (bar)" in col_busca and unidade_p == "Pa (Pascal)") else valor

        if st.button("Interpolar Dados", key="b1"):
            res = interpolar_lagrange(df, col_busca, valor_calculo)
            if unidade_p == "Pa (Pascal)" and "p (bar)" in res.columns:
                res["p (Pa)"] = res["p (bar)"] * 100000
            st.dataframe(res)

    except: st.error("Erro ao carregar arquivo.")

# --- ABA 2: BUSCA CRUZADA ---
with tab2:
    st.header("Identificação de Estado por Par de Propriedades")
    tabela_sel_2 = st.selectbox("Selecione a Tabela de Busca:", 
                                ["A2 - Água Saturada", "A3 - Água Saturada", 
                                 "A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t2")
    t_id_2 = tabela_sel_2.split(' - ')[0][:2]

    try:
        df2 = pd.read_csv(f"{t_id_2}.csv", sep=';', decimal=',', engine='python')
        df2.columns = df2.columns.str.strip()
        
        c1, c2 = st.columns(2)
        with c1:
            v1_nome = st.selectbox("1ª Propriedade (Base):", df2.columns, key="c2_aba2")
            label_v1 = f"Valor de {v1_nome}"
            if "p (bar)" in v1_nome and unidade_p == "Pa (Pascal)":
                label_v1 += " (em Pa)"
            
            v1_valor = st.number_input(label_v1, format="%.4f", key="v1_aba2")
            v1_calculo = (v1_valor / 100000) if ("p (bar)" in v1_nome and unidade_p == "Pa (Pascal)") else v1_valor

        with c2:
            colunas_restantes = [col for col in df2.columns if col != v1_nome]
            v2_nome = st.selectbox("2ª Propriedade (Para Interpolar):", colunas_restantes, key="c3_aba2")
            label_v2 = f"Valor de {v2_nome}"
            if "p (bar)" in v2_nome and unidade_p == "Pa (Pascal)":
                label_v2 += " (em Pa)"
                
            v2_valor = st.number_input(label_v2, format="%.4f", key="v2_aba2")
            v2_calculo = (v2_valor / 100000) if ("p (bar)" in v2_nome and unidade_p == "Pa (Pascal)") else v2_valor
            
        if st.button("Encontrar Estado Completo", key="b3"):
            bloco_final = df2[df2[v1_nome] == v1_calculo]
            
            if bloco_final.empty:
                res_temp = interpolar_lagrange(df2, v1_nome, v1_calculo)
                res_final = interpolar_lagrange(res_temp, v2_nome, v2_calculo) if res_temp is not None else None
            else:
                res_final = interpolar_lagrange(bloco_final, v2_nome, v2_calculo)

            if res_final is not None:
                if unidade_p == "Pa (Pascal)" and "p (bar)" in res_final.columns:
                    res_final["p (Pa)"] = res_final["p (bar)"] * 100000
                st.success("Estado Encontrado!")
                st.dataframe(res_final)
            else:
                st.error("Não foi possível interpolar. Verifique se os valores estão dentro da faixa da tabela.")
                
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

st.divider()
st.caption("UDF 2026 - Engenharia Mecânica | Suporte à Análise Exergética")