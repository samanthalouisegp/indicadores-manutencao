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
        # Extrai a Unidade do nome do Setor
        df['Unidade'] = df['Setor'].astype(str).str.split('_').str[0]
        
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

    # --- Lógica de Análise Mensal com 'Arrastes' ---
    meses = pd.period_range(start="2025-01", end="2025-07", freq='M')
    indicador_mensal = pd.DataFrame(index=meses, columns=['Planejadas', 'Executadas', 'Arraste'])
    
    manutencoes_pendentes = pd.DataFrame()

    for mes in meses:
        abertas_no_mes = df_filtrado[df_filtrado['Mes_Abertura'] == mes].copy()
        
        planejadas_no_mes = pd.concat([abertas_no_mes, manutencoes_pendentes])
        
        executadas_no_mes = planejadas_no_mes[planejadas_no_mes['Mes_Solucao'] == mes]
        
        manutencoes_pendentes = planejadas_no_mes[
            (pd.isna(planejadas_no_mes['Data de Solução'])) | 
            (planejadas_no_mes['Mes_Solucao'] != planejadas_no_mes['Mes_Abertura'])
        ]

        indicador_mensal.loc[mes, 'Planejadas'] = len(planejadas_no_mes)
        indicador_mensal.loc[mes, 'Executadas'] = len(executadas_no_mes)
        indicador_mensal.loc[mes, 'Arraste'] = len(manutencoes_pendentes)

    indicador_mensal['Efetividade (%)'] = (indicador_mensal['Executadas'] / indicador_mensal['Planejadas'] * 100).fillna(0)
    
    # --- Prepara a tabela para os gráficos ---
    indicador_mensal = indicador_mensal.reset_index()
    indicador_mensal.rename(columns={'index': 'Mês'}, inplace=True)
    indicador_mensal['Mês'] = indicador_mensal['Mês'].astype(str)

    # --- Exibir os Resultados na Página Web ---
    st.subheader("Tabela de Indicadores Mensais")
    st.dataframe(
        indicador_mensal.style.format({
            'Efetividade (%)': "{:.2f}%",
            'Planejadas': "{:.0f}",
            'Executadas': "{:.0f}",
            'Arraste': "{:.0f}"
        }),
        use_container_width=True
    )

    # --- Exibir APENAS o gráfico de percentual ---
    st.subheader("Análise Gráfica")
    st.bar_chart(data=indicador_mensal, x='Mês', y="Efetividade (%)")

else:
    st.info("Por favor, faça o upload da sua planilha para começar a análise.")
