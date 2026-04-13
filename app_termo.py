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

tab1, tab2 = st.tabs(["📊 Consulta Geral (1 Variável)", "🔄 Busca Cruzada (2 Variáveis)"])

# --- ABA 1: MANTIDA CONFORME VOCÊ GOSTA ---
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
            pressoes = sorted(df['p (bar)'].unique())
            p_alvo = st.selectbox("Selecione a Pressão fixa (bar):", pressoes, key="p1")
            df = df[df['p (bar)'] == p_alvo]
        
        col_busca = st.selectbox("Buscar por qual variável?", df.columns, key="c1")
        valor = st.number_input(f"Insira o valor de {col_busca}:", format="%.4f", key="v1")
        
        if st.button("Interpolar Dados", key="b1"):
            res = interpolar_lagrange(df, col_busca, valor)
            st.dataframe(res)
    except: st.error("Erro ao carregar arquivo.")

# --- ABA 2: O NOVO MODO MULTI-VARIÁVEL ---
with tab2:
    st.header("Identificação de Estado por Par de Propriedades")
    st.write("Escolha a tabela e entre com duas informações (ex: Pressão e Entalpia).")
    
    tabela_sel_2 = st.selectbox("Selecione a Tabela de Busca:", 
                                ["A2 - Água Saturada", "A3 - Água Saturada", 
                                 "A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t2")
    t_id_2 = tabela_sel_2.split(' - ')[0][:2]

    try:
        df2 = pd.read_csv(f"{t_id_2}.csv", sep=';', decimal=',', engine='python')
        df2.columns = df2.columns.str.strip()
        
        # Primeira Variável (Se for A4/A5, sugerimos a Pressão primeiro por ser o padrão das tabelas)
        c1, c2 = st.columns(2)
        with c1:
            if t_id_2 in ["A4", "A5"]:
                pressoes2 = sorted(df2['p (bar)'].unique())
                v1_nome = "p (bar)"
                v1_valor = st.selectbox("1ª Propriedade: Selecione a Pressão (bar):", pressoes2, key="p2")
            else:
                v1_nome = st.selectbox("1ª Propriedade (Base):", df2.columns, key="c2_aba2")
                v1_valor = st.number_input(f"Valor da 1ª propriedade ({v1_nome}):", format="%.4f", key="v1_aba2")

        # Segunda Variável
        with c2:
            colunas_restantes = [col for col in df2.columns if col != v1_nome]
            v2_nome = st.selectbox("2ª Propriedade (Para Interpolar):", colunas_restantes, key="c3_aba2")
            v2_valor = st.number_input(f"Valor da 2ª propriedade ({v2_nome}):", format="%.4f", key="v2_aba2")
            
        if st.button("Encontrar Estado Completo", key="b3"):
            # Filtra pela primeira propriedade
            bloco_final = df2[df2[v1_nome] == v1_valor]
            
            if bloco_final.empty:
                # Se não for valor exato (comum em A2/A3), interpola primeiro a base
                res_temp = interpolar_lagrange(df2, v1_nome, v1_valor)
                st.warning("Nota: A 1ª propriedade foi interpolada para gerar a base de busca.")
                st.dataframe(res_temp)
            else:
                # Interpola a segunda propriedade dentro do bloco da primeira
                res2 = interpolar_lagrange(bloco_final, v2_nome, v2_valor)
                st.success(f"Resultado encontrado para {v1_nome}={v1_valor} e {v2_nome}={v2_valor}")
                st.dataframe(res2)
                
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

st.divider()
st.caption("UDF 2026 - Engenharia Mecânica")