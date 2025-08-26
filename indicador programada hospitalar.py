import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- Configurações da Página do Streamlit ---
st.set_page_config(page_title="Dashboard de Manutenções", layout="wide")

st.title("📊 Indicador de Manutenções Programadas")
st.write("Análise de efetividade mensal (Jan-Jul 2025).")

# --- Carregar a Planilha ---
st.subheader("Carregue a Planilha")
uploaded_file = st.file_uploader("Selecione o arquivo Excel 'Manutenções programadas eng hospitalar.xlsx'", type="xlsx")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="dados")
        st.success("Planilha carregada com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        st.info("Verifique se o nome da aba está correto ('dados') e se a planilha está no formato .xlsx.")
        st.stop()

    # --- Preparar os Dados (Converter Datas e criar a Unidade) ---
    try:
        df['Unidade'] = df['Setor'].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.split('_').str[0]

        df['Data de Abertura'] = pd.to_datetime(df['Abertura'], dayfirst=True)
        df['Data de Solução'] = pd.to_datetime(df['Data de Solução'], dayfirst=True, errors='coerce')

        df['Mes_Abertura'] = df['Data de Abertura'].dt.to_period('M')
        df['Mes_Solucao'] = df['Data de Solução'].dt.to_period('M')

    except KeyError as e:
        st.error(f"ERRO: A coluna {e} não foi encontrada na planilha.")
        st.info("Verifique se o nome das colunas 'Setor', 'Abertura' e 'Data de Solução' estão corretos.")
        st.stop()

    # --- Filtro de Unidade ---
    lista_unidades = ['Todas as Unidades'] + sorted(df['Unidade'].unique().tolist())
    unidade_selecionada = st.selectbox("Selecione a Unidade:", options=lista_unidades)

    if unidade_selecionada != 'Todas as Unidades':
        df_filtrado = df[df['Unidade'] == unidade_selecionada].copy()
    else:
        df_filtrado = df.copy()

    # --- Lógica de Análise Mensal com 'Acumuladas' ---
    meses_periodo = pd.period_range(start="2025-01", end="2025-07", freq='M')
    indicador_mensal = pd.DataFrame(index=meses_periodo, columns=['Planejadas', 'Executadas', 'Acumuladas'])
    
    manutencoes_acumuladas = pd.DataFrame()

    for mes in meses_periodo:
        abertas_no_mes = df_filtrado[df_filtrado['Mes_Abertura'] == mes].copy()
        
        planejadas_no_mes = pd.concat([abertas_no_mes, manutencoes_acumuladas])
        
        executadas_no_mes = df_filtrado[df_filtrado['Mes_Solucao'] == mes]
        
        manutencoes_acumuladas = planejadas_no_mes[
            (pd.isna(planejadas_no_mes['Data de Solução'])) |
            (planejadas_no_mes['Mes_Solucao'] > mes)
        ]

        indicador_mensal.loc[mes, 'Planejadas'] = len(planejadas_no_mes)
        indicador_mensal.loc[mes, 'Executadas'] = len(executadas_no_mes)
        indicador_mensal.loc[mes, 'Acumuladas'] = len(manutencoes_acumuladas)

    indicador_mensal['Efetividade (%)'] = np.where(
        indicador_mensal['Planejadas'] > 0,
        (indicador_mensal['Executadas'] / indicador_mensal['Planejadas'] * 100),
        100.0
    )

    indicador_mensal = indicador_mensal.reset_index()
    indicador_mensal.rename(columns={'index': 'Mês'}, inplace=True)
    
    # --- NOVO CÓDIGO: MAPEA E ORDENA OS MESES ---
    meses_nomes = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho'}
    indicador_mensal['Meses'] = indicador_mensal['Mês'].dt.month.map(meses_nomes)
    
    meses_ordenados = list(meses_nomes.values())
    indicador_mensal['Meses'] = pd.Categorical(indicador_mensal['Meses'], categories=meses_ordenados, ordered=True)
    indicador_mensal.sort_values('Meses', inplace=True)

    # --- NOVO LAYOUT: COLUNAS LADO A LADO ---
