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
        
    # --- Preparar os Dados (Converter Datas) ---
    try:
        df['Data de Abertura'] = pd.to_datetime(df['Abertura'], dayfirst=True)
        df['Data de Solução'] = pd.to_datetime(df['Data de Solução'], dayfirst=True, errors='coerce')
        
        df['Mes_Abertura'] = df['Data de Abertura'].dt.to_period('M')
        df['Mes_Solucao'] = df['Data de Solução'].dt.to_period('M')

    except KeyError as e:
        st.error(f"ERRO: A coluna {e} não foi encontrada na planilha.")
        st.info("Verifique se o nome das colunas 'Abertura' e 'Data de Solução' estão corretos.")
        st.stop()

    # --- Lógica de Análise Mensal com 'Arrastes' ---
    meses = pd.period_range(start="2025-01", end="2025-07", freq='M')
    indicador_mensal = pd.DataFrame(index=meses, columns=['Planejadas', 'Executadas', 'Arraste'])
    
    # DataFrame para rastrear as manutenções pendentes para o próximo mês
    manutencoes_pendentes = pd.DataFrame()

    for mes in meses:
        # Manutenções abertas no mês atual
        abertas_no_mes = df[df['Mes_Abertura'] == mes].copy()
        
        # Planejadas no mês = abertas no mês + arrastadas do mês anterior
        planejadas_no_mes = pd.concat([abertas_no_mes, manutencoes_pendentes])
        
        # Manutenções executadas no mês
        # O filtro agora é para as manutenções cuja data de solução está no mês atual
        executadas_no_mes = planejadas_no_mes[planejadas_no_mes['Mes_Solucao'] == mes]
        
        # --- AQUI ESTÁ A LÓGICA DE ARRASTE ---
        # Manutenções que continuam pendentes (arraste para o próximo mês)
        # Condição 1: A data de solução está vazia (NaN)
        # Condição 2: A data de solução existe, mas é em um mês diferente do de abertura
        manutencoes_pendentes = planejadas_no_mes[
            (pd.isna(planejadas_no_mes['Data de Solução'])) | 
            (planejadas_no_mes['Mes_Solucao'] != planejadas_no_mes['Mes_Abertura'])
        ]

        indicador_mensal.loc[mes, 'Planejadas'] = len(planejadas_no_mes)
        indicador_mensal.loc[mes, 'Executadas'] = len(executadas_no_mes)
        indicador_mensal.loc[mes, 'Arraste'] = len(manutencoes_pendentes)

    indicador_mensal['Efetividade (%)'] = (indicador_mensal['Executadas'] / indicador_mensal['Planejadas'] * 100).fillna(0)
    
    # --- NOVO CÓDIGO AQUI: TRANSFORMA O ÍNDICE EM UMA COLUNA ---
    indicador_mensal = indicador_mensal.reset_index()
    # A coluna de meses agora se chama 'index' por padrão. Vamos renomeá-la para 'Mês'.
    indicador_mensal.rename(columns={'index': 'Mês'}, inplace=True)
    indicador_mensal['Mês'] = indicador_mensal['Mês'].astype(str)

    # --- Dividindo o conteúdo em abas ---
    tab1, tab2 = st.tabs(["Tabela de Indicadores", "Análise Gráfica"])

    with tab1:
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

    with tab2:
        st.subheader("Análise Gráfica")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Manutenções Planejadas vs. Executadas")
            # Agora usamos 'Mês' para o eixo X, que é uma coluna válida
            st.bar_chart(data=indicador_mensal, x='Mês', y=["Planejadas", "Executadas"])

        with col2:
            st.markdown("### Percentual de Efetividade por Mês")
            # Agora usamos 'Mês' para o eixo X, que é uma coluna válida
            st.bar_chart(data=indicador_mensal, x='Mês', y="Efetividade (%)")
else:
    st.info("Por favor, faça o upload da sua planilha para começar a análise.")
