import streamlit as st
import pandas as pd
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Termodinâmica - UnB", layout="centered")

# 2. FUNÇÕES MATEMÁTICAS
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
    # Pega os 3 vizinhos mais próximos para Lagrange de 2º grau
    vizinhos = df_temp.nsmallest(3, 'dist').sort_values(by=coluna_busca)
    if len(vizinhos) < 2: return None
    x_pontos = vizinhos[coluna_busca].values
    res = {}
    for col in df.columns:
        if col == 'dist': continue
        y_pontos = vizinhos[col].values
        res[col] = lagrange_2_grau(x_pontos, y_pontos, valor_alvo)
    return res

# 3. INTERFACE
st.header("📊 Análise Termodinâmica - Ciclo ORC")
st.markdown("**Estudante:** Luiz F. | **Matrícula:** 29898617")
st.divider()

tabela_sel = st.selectbox("Selecione a Tabela:", ["A2", "A3", "A4", "A5"])

try:
    # Carregamento do CSV (O separador e decimal devem bater com seus arquivos)
    df = pd.read_csv(f"{tabela_sel}.csv", sep=';', decimal=',', engine='python')
    df.columns = df.columns.str.strip()

    if tabela_sel in ["A4", "A5"]:
        col1, col2 = st.columns(2)
        p = col1.number_input("Pressão p (bar):", value=1.0, step=0.1, format="%.2f")
        t = col2.number_input("Temperatura T (°C):", value=100.0, step=1.0, format="%.1f")
        
        if st.button("Buscar Dados", use_container_width=True):
            bloco = df[df['p (bar)'] == p]
            if bloco.empty:
                st.error("Pressão não encontrada. Tente um valor exato da tabela (ex: 1.0, 5.0).")
            else:
                res = interpolar_lagrange(bloco, 'T (C)', t)
                if res:
                    st.subheader("📍 Propriedades Superaquecido")
                    for k, v in res.items():
                        st.info(f"**{k}:** {v:.5f}")

    else:
        col_busca = st.selectbox("Propriedade de entrada:", df.columns)
        valor_alvo = st.number_input(f"Valor para {col_busca}:", value=100.0, format="%.4f")
        
        if st.button("Calcular Saturação", use_container_width=True):
            res = interpolar_lagrange(df, col_busca, valor_alvo)
            st.session_state['res_sat'] = res
            st.subheader("📍 Propriedades de Saturação")
            for k, v in res.items():
                st.success(f"**{k}:** {v:.5f}")

        if 'res_sat' in st.session_state:
            st.divider()
            st.subheader("🔍 Identificação do Estado")
            prop_analise = st.selectbox("Propriedade para comparação:", ["Entalpia (h)", "Entropia (s)", "Volume (v)"])
            val_real = st.number_input(f"Insira o valor real de {prop_analise}:", format="%.4f")

            if st.button("Verificar Estado"):
                res_i = st.session_state['res_sat']
                # Mapeamento para encontrar as colunas líquida(f) e vapor(g)
                mapa = {"Entalpia (h)": ('hf', 'hg'), "Entropia (s)": ('sf', 'sg'), "Volume (v)": ('vf', 'vg')}
                f_alvo, g_alvo = mapa[prop_analise]
                
                col_f = next((c for c in res_i.keys() if f_alvo in c.lower()), None)
                col_g = next((c for c in res_i.keys() if g_alvo in c.lower()), None)

                if col_f and col_g:
                    vf, vg = res_i[col_f], res_i[col_g]
                    
                    # LÓGICA DE ESTADO REVISADA
                    if val_real <= (vf + 1e-6):
                        st.warning("ESTADO: Líquido Saturado ou Comprimido")
                    elif val_real >= (vg - 1e-6):
                        st.warning("ESTADO: Vapor Saturado ou Superaquecido")
                    else:
                        x = (val_real - vf) / (vg - vf)
                        # Filtro final para evitar "Mistura" em limites de precisão
                        if x > 0.999:
                            st.info("ESTADO: Vapor Saturado Seco (x ≈ 1.0)")
                        elif x < 0.001:
                            st.info("ESTADO: Líquido Saturado (x ≈ 0.0)")
                        else:
                            st.write(f"**ESTADO: Mistura (Líquido + Vapor)**")
                            st.metric("Título (x)", f"{x:.4f}")
                else:
                    st.error("Colunas de saturação não encontradas no CSV.")

except Exception as e:
    st.error(f"Erro: Certifique-se que o arquivo {tabela_sel}.csv está na mesma pasta.")

st.divider()
st.caption("Suporte à Análise Exergética - Engenharia Mecânica")