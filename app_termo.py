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

tab1, tab2 = st.tabs(["📊 Consulta Geral", "🔄 Busca Cruzada e Interpolação Dupla"])

# --- CONVERSOR DE PRESSÃO ---
def converter_para_bar(valor, unidade):
    if unidade == "Pa (Pascal)": return valor / 100000
    if unidade == "kPa (Quilopascal)": return valor / 100
    return valor

# --- ABA 1: CONSULTA GERAL ---
with tab1:
    st.header("Busca Simples (1 Variável)")
    tabela_sel = st.selectbox("Tabela:", ["A2 - Água Saturada (T)", "A3 - Água Saturada (P)", "A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t1")
    t_id = tabela_sel[:2]
    try:
        df = pd.read_csv(f"{t_id}.csv", sep=';', decimal=',', engine='python').apply(pd.to_numeric, errors='coerce')
        df.columns = df.columns.str.strip()
        
        col_busca = st.selectbox("Propriedade de entrada:", df.columns, key="c1")
        v_input = st.number_input(f"Valor de {col_busca}:", format="%.4f", key="v1")
        
        v_calc = converter_para_bar(v_input, unidade_p) if "p (bar)" in col_busca else v_input

        if st.button("Calcular", key="b1", use_container_width=True):
            res = interpolar_lagrange(df, col_busca, v_calc)
            if unidade_p != "bar" and "p (bar)" in res.columns:
                fator = 100000 if unidade_p == "Pa (Pascal)" else 100
                res[f"p ({unidade_p.split()[0]})"] = res["p (bar)"] * fator
            st.dataframe(res)
    except: st.error("Erro ao carregar arquivo.")

# --- ABA 2: BUSCA CRUZADA (TUDO VOLTOU) ---
with tab2:
    st.header("Busca por Duas Variáveis")
    st.write("Funciona para valores exatos da tabela ou interpolação dupla (ex: 400 kPa).")
    
    tabela_sel2 = st.selectbox("Selecione a Tabela:", ["A2 - Água Saturada", "A3 - Água Saturada", "A4 - Vapor Superaquecido", "A5 - Líquida Comprimida"], key="t2")
    t_id2 = tabela_sel2[:2]

    try:
        df2 = pd.read_csv(f"{t_id2}.csv", sep=';', decimal=',', engine='python').apply(pd.to_numeric, errors='coerce')
        df2.columns = df2.columns.str.strip()
        
        c1, c2 = st.columns(2)
        with c1:
            v1_nome = st.selectbox("1ª Propriedade (Ex: p ou T):", df2.columns, key="c2_aba2")
            v1_in = st.number_input(f"Valor de {v1_nome}:", format="%.4f", key="v1_aba2")
            v1_calc = converter_para_bar(v1_in, unidade_p) if "p (bar)" in v1_nome else v1_in

        with c2:
            cols_restantes = [c for c in df2.columns if c != v1_nome]
            v2_nome = st.selectbox("2ª Propriedade (Ex: h, s, v):", cols_restantes, key="c3_aba2")
            v2_in = st.number_input(f"Valor de {v2_nome}:", format="%.4f", key="v2_aba2")
            v2_calc = converter_para_bar(v2_in, unidade_p) if "p (bar)" in v2_nome else v2_in

        if st.button("Realizar Busca Cruzada", key="b2", use_container_width=True):
            # Lógica de Interpolação Dupla
            v1_unicos = sorted(df2[v1_nome].unique())
            v1_menores = [v for v in v1_unicos if v <= v1_calc]
            v1_maiores = [v for v in v1_unicos if v > v1_calc]

            if not v1_menores or not v1_maiores:
                # Se o valor for exato ou estiver fora da faixa
                res_final = interpolar_lagrange(df2[df2[v1_nome] == v1_calc], v2_nome, v2_calc) if v1_calc in v1_unicos else None
            else:
                # Interpolação Dupla de fato
                val1, val2 = v1_menores[-1], v1_maiores[0]
                res_v1 = interpolar_lagrange(df2[df2[v1_nome] == val1], v2_nome, v2_calc)
                res_v2 = interpolar_lagrange(df2[df2[v1_nome] == val2], v2_nome, v2_calc)
                
                if res_v1 is not None and res_v2 is not None:
                    dupla_df = pd.concat([res_v1, res_v2])
                    res_final = interpolar_lagrange(dupla_df, v1_nome, v1_calc)
                else: res_final = None

            if res_final is not None:
                if unidade_p != "bar" and "p (bar)" in res_final.columns:
                    fator = 100000 if unidade_p == "Pa (Pascal)" else 100
                    res_final[f"p ({unidade_p.split()[0]})"] = res_final["p (bar)"] * fator
                st.success("Resultado da Interpolação:")
                st.dataframe(res_final)
            else:
                st.error("Valores fora da faixa ou erro na interpolação.")
    except Exception as e: st.error(f"Erro: {e}")

st.divider()
st.caption("UDF 2026 - Engenharia Mecânica")