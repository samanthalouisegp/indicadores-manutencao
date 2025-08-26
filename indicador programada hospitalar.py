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
        
        df['Status'] = np.where(pd.isna(df['Data de Solução']), 'Não Executado', 'Executado')

        df['Mes_Abertura'] = df['Data de Abertura'].dt.to_period('M')
        df['Mes_Solucao'] = df['Data de Solução'].dt.to_period('M')

    except KeyError as e:
        st.error(f"ERRO: A coluna {e} não foi encontrada na planilha.")
        st.info("Verifique se o nome das colunas 'Setor', 'Abertura' e 'Data de Solução' estão corretos.")
        st.stop()
        
    # --- FILTROS DE UNIDADE E MÊS ---
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        lista_unidades = ['Todas as Unidades'] + sorted(df['Unidade'].unique().tolist())
        unidade_selecionada = st.selectbox("Selecione a Unidade:", options=lista_unidades)

    with col_filtro2:
        meses_nomes_ordem = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho']
        mes_selecionado = st.selectbox("Selecione o Mês:", options=['Todos os Meses'] + meses_nomes_ordem)
    
    # --- Lógica de filtragem ---
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
    
    meses_nomes = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho'}
    indicador_mensal['Meses'] = indicador_mensal['Mês'].dt.month.map(meses_nomes)
    
    indicador_mensal['Meses'] = pd.Categorical(indicador_mensal['Meses'], categories=meses_nomes_ordem, ordered=True)
    indicador_mensal.sort_values('Meses', inplace=True)

    # --- EXIBIÇÃO: INDICADORES RESUMO ---
    st.subheader("Indicadores Mensais")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tabela de Indicadores")
        st.dataframe(
            indicador_mensal.style.format({
                'Efetividade (%)': "{:.2f}%",
                'Planejadas': "{:.0f}",
                'Executadas': "{:.0f}",
                'Acumuladas': "{:.0f}"
            }),
            use_container_width=True
        )

    with col2:
        st.subheader("Gráfico de Efetividade")
        st.bar_chart(data=indicador_mensal, x='Meses', y="Efetividade (%)")

    # --- TABELA DE ORDENS DE SERVIÇO DETALHADA ---
    st.markdown("---")
    st.subheader("Ordens de Serviço Detalhadas")

    # Filtra os dados detalhados pelo mês selecionado
    if mes_selecionado != 'Todos os Meses':
        mes_numero = list(meses_nomes.keys())[list(meses_nomes.values()).index(mes_selecionado)]
        df_detalhes = df_filtrado[df_filtrado['Data de Abertura'].dt.month == mes_numero].copy()
    else:
        df_detalhes = df_filtrado.copy()

    df_detalhes = df_detalhes[[
        'Mes_Abertura',
        'Status',
        'Unidade',
        'Equipamento',
        'Tipo',
        'Tipo de Manutenção'
    ]].copy()

    df_detalhes.rename(columns={
        'Mes_Abertura': 'Mês de Abertura',
        'Status': 'Status',
        'Unidade': 'Unidade',
        'Equipamento': 'Equipamento',
        'Tipo': 'Tipo',
        'Tipo de Manutenção': 'Tipo de Manutenção'
    }, inplace=True)

    df_detalhes['Mês de Abertura'] = df_detalhes['Mês de Abertura'].dt.to_timestamp().dt.strftime('%B %Y').str.title()
    
    st.dataframe(df_detalhes, use_container_width=True, hide_index=True, height=400)

else:
    st.info("Por favor, faça o upload da sua planilha para começar a análise.")
