import pandas as pd
import numpy as np

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

    if len(vizinhos) < 3:
        if len(vizinhos) < 2: return None
        x_pontos = vizinhos[coluna_busca].values
    else:
        x_pontos = vizinhos[coluna_busca].values

    res = {}
    for col in df.columns:
        if col == 'dist': continue
        y_pontos = vizinhos[col].values
        res[col] = lagrange_2_grau(x_pontos, y_pontos, valor_alvo)
    
    return pd.DataFrame([res])

def definir_estado(res_interp):
    print("\n--- ANÁLISE DE ESTADO ---")
    print("Escolha uma propriedade conhecida:")
    print("1. Entalpia (h)\n2. Entropia (s)\n3. Volume Específico (v)")
    opcao = input("Escolha (1, 2 ou 3): ")

    mapa = {
        '1': ('h', 'hf (kJ/kg)', 'hg (kJ/kg)'),
        '2': ('s', 'sf (kJ/kg.K)', 'sg (kJ/kg.K)'),
        '3': ('v', 'vf (m3/kg)', 'vg (m3/kg)')
    }

    if opcao in mapa:
        label, col_f, col_g = mapa[opcao]
        
        # Busca dinâmica das colunas f e g
        col_f_real = next((c for c in res_interp.columns if col_f.split(' ')[0] in c), None)
        col_g_real = next((c for c in res_interp.columns if col_g.split(' ')[0] in c), None)

        if not col_f_real or not col_g_real:
            print("[!] Erro: Colunas de saturação (f/g) não encontradas no CSV.")
            return

        val_f = res_interp[col_f_real].values[0]
        val_g = res_interp[col_g_real].values[0]
        
        val_real = float(input(f"Digite o valor de {label} que você tem: ").replace(',', '.'))

        # LÓGICA DE DECISÃO DE ESTADO
        if val_real < val_f:
            print(f"ESTADO: Líquido Comprimido (Sub-resfriado)")
        elif val_real > val_g:
            print(f"ESTADO: Vapor Superaquecido")
        else:
            # Caso esteja entre f e g, calcula o título
            titulo = (val_real - val_f) / (val_g - val_f)
            
            if round(titulo, 4) >= 1.0000:
                print(f"ESTADO: Vapor Saturado Seco (x = 1.0)")
            elif round(titulo, 4) <= 0.0000:
                print(f"ESTADO: Líquido Saturado (x = 0.0)")
            else:
                print(f"ESTADO: Mistura Saturada Líquido-Vapor")
                print(f"TÍTULO (x): {titulo:.4f} (ou {titulo*100:.2f}%)")
    else:
        print("Opção inválida.")

def buscar_dados():
    tabela = input("Qual tabela (A2, A3, A4, A5)? ").strip().upper()
    try:
        df = pd.read_csv(f"{tabela}.csv", sep=';', decimal=',', engine='python')
        df.columns = df.columns.str.strip()
    except:
        print(f"\n[!] Arquivo {tabela}.csv não encontrado!")
        return

    if tabela in ["A4", "A5"]:
        p_alvo = float(input("Pressão p (bar): ").replace(',', '.'))
        t_alvo = float(input("Temperatura T (C): ").replace(',', '.'))
        bloco_p = df[df['p (bar)'] == p_alvo]
        if bloco_p.empty:
            print(f"\n[!] Pressão {p_alvo} não encontrada.")
        else:
            res = interpolar_lagrange(bloco_p, 'T (C)', t_alvo)
            print("\n--- RESULTADO (LAGRANGE 2º GRAU) ---")
            print(res)
            print("\nESTADO: Vapor Superaquecido")
            
    else:
        print(f"\nColunas detectadas: {list(df.columns)}")
        col_busca = input("Buscar por qual coluna? ").strip()
        if col_busca not in df.columns:
            print("[!] Coluna não encontrada.")
            return

        valor = float(input(f"Valor para {col_busca}: ").replace(',', '.'))
        res = interpolar_lagrange(df, col_busca, valor)
        
        if res is not None:
            print("\n--- RESULTADO (LAGRANGE 2º GRAU) ---")
            print(res)
            definir_estado(res)

print("="*45)
print("SISTEMA TERMODINÂMICO - MÉTODO DE LAGRANGE")
print("="*45)
buscar_dados()