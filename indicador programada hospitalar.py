# --- Lógica de Análise Mensal com 'Acumuladas' ---
    meses = pd.period_range(start="2025-01", end="2025-07", freq='M')
    indicador_mensal = pd.DataFrame(index=meses, columns=['Planejadas', 'Executadas', 'Acumuladas'])
    
    manutencoes_acumuladas = pd.DataFrame()

    for mes in meses:
        abertas_no_mes = df_filtrado[df_filtrado['Mes_Abertura'] == mes].copy()
        
        planejadas_no_mes = pd.concat([abertas_no_mes, manutencoes_acumuladas])
        
        executadas_no_mes = planejadas_no_mes[planejadas_no_mes['Mes_Solucao'] == mes]
        
        manutencoes_acumuladas = planejadas_no_mes[
            (pd.isna(planejadas_no_mes['Data de Solução'])) | 
            (planejadas_no_mes['Mes_Solucao'] > mes)
        ]

        indicador_mensal.loc[mes, 'Planejadas'] = len(planejadas_no_mes)
        indicador_mensal.loc[mes, 'Executadas'] = len(executadas_no_mes)
        indicador_mensal.loc[mes, 'Acumuladas'] = len(manutencoes_acumuladas)

    # --- CÓDIGO CORRIGIDO: DIVISÃO SEGURA ---
    # Usa a função div do pandas para tratar a divisão por zero.
    # O parâmetro 'fill_value' garante que, se o denominador for zero, a divisão retorne 1 (ou 100%)
    indicador_mensal['Efetividade (%)'] = (indicador_mensal['Executadas'].div(indicador_mensal['Planejadas'], fill_value=1) * 100)
    
    # Em seguida, garante que se a quantidade planejada for 0, a efetividade seja 100%
    indicador_mensal.loc[indicador_mensal['Planejadas'] == 0, 'Efetividade (%)'] = 100.0

    indicador_mensal = indicador_mensal.reset_index()
    indicador_mensal.rename(columns={'index': 'Mês'}, inplace=True)
    indicador_mensal['Mês'] = pd.to_datetime(indicador_mensal['Mês']).dt.strftime('%B').str.title()

    # --- NOVO LAYOUT: COLUNAS LADO A LADO ---
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
        st.bar_chart(data=indicador_mensal, x='Mês', y="Efetividade (%)")
