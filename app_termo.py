import streamlit as st
import pandas as pd
import numpy as np

# Força o Streamlit a atualizar a página
st.set_page_config(page_title="Filtro de Termodinâmica - Luiz F.", layout="centered")

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
    return res

# --- CABEÇALHO ---
st.title("📊 Filtro de Termodinâmica")
st.markdown(f"**Desenvolvido por:** Luiz F.")
st.markdown(f"**Matrícula:** 29898617")
st.divider()

tabela_sel = st.selectbox("Selecione a Tabela:", ["A2", "A3", "A4", "A5"])

try:
    df = pd.read_csv(f"{tabela_sel}.csv", sep=';', decimal=',', engine='python')
    df.columns = df.columns.str.strip()

    if tabela_sel in ["A4", "A5"]:
        p = st.number_input("Pressão p (bar):", value=1.0, step=0.1, format="%.2f")
        t = st.number_input("Temperatura T (°C):", value=100.0, step=1.0, format="%.1f")
        
        if st.button("Buscar"):
            bloco = df[df['p (bar)'] == p]
            if bloco.empty:
                st.error("Pressão não encontrada.")
            else:
                res = interpolar_lagrange(bloco, 'T (C)', t)
                st.subheader("📍 Propriedades (Superaquecido)")
                for k, v in res.items():
                    st.info(f"**{k}:** {v:.5f}")
    else:
        col_busca = st.selectbox("Propriedade de entrada:", df.columns)
        valor_alvo = st.number_input(f"Valor para {col_busca}:", value=20.0, format="%.4f")
        
        if st.button("Buscar"):
            res = interpolar_lagrange(df, col_busca, valor_alvo)
            st.session_state['res_sat'] = res # Salva para a análise de estado
            st.subheader("📍 Propriedades na Saturação")
            for k, v in res.items():
                st.success(f"**{k}:** {v:.5f}")

        # --- ANÁLISE DE ESTADO ---
        if 'res_sat' in st.session_state:
            st.divider()
            st.subheader("🔍 Análise de Estado e Título")
            prop_analise = st.selectbox("Comparar com qual propriedade?", ["Entalpia (h)", "Entropia (s)", "Volume (v)"])
            val_conhecido = st.number_input(f"Insira o valor real de {prop_analise}:", step=0.1)

            if st.button("Verificar Estado"):
                res_i = st.session_state['res_sat']
                mapa = {"Entalpia (h)": ('hf', 'hg'), "Entropia (s)": ('sf', 'sg'), "Volume (v)": ('vf', 'vg')}
                pref = mapa[prop_analise]
                
                # Busca as chaves corretas que contém hf/hg, etc.
                col_f = next((c for c in res_i.keys() if pref[0] in c), None)
                col_g = next((c for c in res_i.keys() if pref[1] in c), None)

                if col_f and col_g:
                    vf, vg = res_i[col_f], res_i[col_g]
                    if val_conhecido < vf: st.warning("ESTADO: Líquido Comprimido")
                    elif val_conhecido > vg: st.warning("ESTADO: Vapor Superaquecido")
                    else:
                        x = (val_conhecido - vf) / (vg - vf)
                        st.balloons()
                        st.write(f"**ESTADO: Mistura**")
                        st.metric("Título (x)", f"{x:.4f}")
                else:
                    st.error("Colunas hf/hg não encontradas na tabela selecionada.")

except Exception as e:
    st.error(f"Erro: {e}")

st.divider()
st.caption("Suporte ao TCC - Engenharia Mecânica")