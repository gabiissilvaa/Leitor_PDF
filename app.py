import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import re
import pdfplumber
from src.pdf_processor import PDFProcessor
from src.multibank_pdf_processor import MultibankPDFProcessor
from src.data_analyzer import DataAnalyzer
from src.notification_manager import NotificationManager
from src.performance_manager import CacheManager, PerformanceOptimizer
from src.banks import BankProcessorFactory

def main():
    st.set_page_config(
        page_title="Leitor de PDF - Extrato Bancário",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Leitor de PDF - Extrato Bancário")
    st.markdown("---")
    
    # Sidebar para seleção do banco
    with st.sidebar:
        st.header("🏦 Seleção do Banco")
        
        # Obter bancos disponíveis
        available_banks = BankProcessorFactory.get_available_banks()
        
        # Opções de banco (sem detecção automática)
        bank_options = [""] + [
            f"🏦 {info['name']} ({info['code']})" 
            for bank_id, info in available_banks.items()
        ]
        
        selected_bank_option = st.selectbox(
            "⚠️ Selecione seu banco (obrigatório):",
            bank_options,
            help="Selecione seu banco para usar os padrões específicos de extração",
            placeholder="Escolha seu banco..."
        )
        
        # Converter seleção para bank_id
        selected_bank_id = None
        if selected_bank_option and selected_bank_option != "":
            # Extrair o ID do banco da seleção
            for bank_id, info in available_banks.items():
                if info['name'] in selected_bank_option:
                    selected_bank_id = bank_id
                    break
        
        # Mostrar informações do banco selecionado
        if selected_bank_id:
            bank_info = available_banks[selected_bank_id]
            st.success(f"✅ **{bank_info['name']}**\n"
                      f"📋 {bank_info['description']}\n"
                      f"🔢 Código: {bank_info['code']}\n"
                      f"🎯 Processamento otimizado ativo!")
        else:
            st.warning("⚠️ **Selecione seu banco**\n"
                      "É necessário escolher o banco para processar o extrato.\n"
                      "Isso garante máxima precisão na extração.")
        
        st.markdown("---")
        
        # Upload do arquivo (só aparece se banco foi selecionado)
        if selected_bank_id:
            st.header("📁 Upload do Arquivo")
            uploaded_file = st.file_uploader(
                "Selecione seu arquivo PDF",
                type=['pdf'],
                help=f"Faça upload do seu extrato do {available_banks[selected_bank_id]['name']} em PDF"
            )
            
            if uploaded_file:
                st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
                
                # Mostrar informações do arquivo
                file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
                st.info(f"📊 Tamanho: {file_size:.2f} MB")
                
                if file_size > 5:
                    st.warning("⚠️ Arquivo grande - otimizações ativas")
        else:
            st.header("📁 Upload do Arquivo")
            st.info("⬆️ **Primeiro selecione seu banco acima**\n"
                   "O upload ficará disponível após a seleção.")
            uploaded_file = None
            
        # Como usar
        with st.expander("📖 Como Usar"):
            st.markdown("""
            **🏦 Instruções Passo a Passo:**
            1. 🏦 **PRIMEIRO:** Selecione seu banco na lista acima
            2. 📁 **SEGUNDO:** Faça upload do seu extrato bancário em PDF
            3. ⚙️ **AUTOMÁTICO:** Sistema usa configurações específicas do seu banco
            4. 📊 **RESULTADO:** Visualize os dados organizados por data
            5. 📈 **ANÁLISE:** Explore gráficos de créditos e débitos
            
            **🎯 Por que selecionar o banco é importante:**
            - ✅ **Maior precisão:** Cada banco tem formato próprio
            - ✅ **Melhor extração:** Padrões específicos otimizados
            - ✅ **Menos erros:** Reconhecimento preciso de transações
            - ✅ **Classificação correta:** Créditos e débitos identificados corretamente
            
            **🏦 Bancos com Processamento Otimizado:**
            - 🟢 **Santander:** Processamento específico ativo
            - 🔄 **Outros:** Processamento genérico (em desenvolvimento)
            
            **💾 Cache:**
            - Arquivos processados são salvos
            - Próxima consulta será instantânea
            - Cache válido por 24 horas
            """)
    
    # Verificar se banco foi selecionado para mostrar conteúdo
    if not selected_bank_id:
        st.warning("⚠️ **Primeiro selecione seu banco na barra lateral**")
        st.info("👈 Use a barra lateral para escolher seu banco antes de continuar")
        return
    
    if uploaded_file is not None:
        try:
            # Container principal para o processamento
            st.header("🔄 Processamento")
            
            # Mostrar informações do banco selecionado no processamento
            bank_info = available_banks[selected_bank_id]
            st.success(f"🏦 **Processando com {bank_info['name']}**")
            st.info(f"🎯 **Usando padrões específicos do {bank_info['name']} ({bank_info['code']})**\n"
                   f"✅ Máxima precisão garantida para este banco")
            
            # Informações do arquivo
            file_info_col1, file_info_col2, file_info_col3 = st.columns(3)
            file_content = uploaded_file.getvalue()
            file_size_kb = len(file_content) / 1024
            file_size_mb = file_size_kb / 1024
            
            with file_info_col1:
                st.metric("📁 Arquivo", uploaded_file.name)
            with file_info_col2:
                if file_size_mb > 1:
                    st.metric("📊 Tamanho", f"{file_size_mb:.1f} MB")
                else:
                    st.metric("📊 Tamanho", f"{file_size_kb:.1f} KB")
            
            # Inicializar gerenciadores de performance
            cache_manager = CacheManager()
            file_hash = cache_manager.get_file_hash(file_content)
            
            with file_info_col3:
                # Verificar se existe arquivo processado anteriormente
                cached_transactions = cache_manager.load_from_cache(file_hash)
                if cached_transactions:
                    st.metric("⚡ Status", "Processado")
                else:
                    st.metric("🔄 Status", "Aguardando")
            
            # Limpar cache antigo automaticamente
            cache_manager.clear_old_cache()
            
            # Verificar se podemos usar dados salvos
            if cached_transactions:
                st.success("🚀 **Carregando dados salvos...**")
                transactions = cached_transactions
                
                # Mostrar informações do cache
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"⚡ **Cache Carregado!**\n"
                           f"- 📋 {len(transactions)} transações\n"
                           f"- 🚀 Carregamento instantâneo\n"
                           f"- 💾 Dados salvos anteriormente")
                
                with col2:
                    # Calcular estatísticas rápidas
                    total_credit = sum(t['valor'] for t in transactions if t['tipo'] == 'Crédito')
                    total_debit = sum(t['valor'] for t in transactions if t['tipo'] == 'Débito')
                    st.metric("💰 Resumo Rápido", f"R$ {total_credit - total_debit:,.2f}", 
                             delta=f"{len(transactions)} transações")
            else:
                # Verificar tamanho do arquivo e mostrar estimativas
                with pdfplumber.open(uploaded_file) as pdf:
                    total_pages = len(pdf.pages)
                
                # Mostrar informações sobre processamento
                col1, col2 = st.columns(2)
                with col1:
                    st.warning(f"📄 **Arquivo para processar:**\n"
                             f"- 📄 {total_pages} páginas\n"
                             f"- ⏱️ Tempo estimado: {PerformanceOptimizer.estimate_processing_time(total_pages)}\n"
                             f"- 💾 Cache será criado")
                
                with col2:
                    if total_pages > 20:
                        # Mostrar dicas de performance
                        PerformanceOptimizer.show_performance_tips(total_pages)
                
                # Processar arquivo
                st.markdown("---")
                
                # Criar elementos de progresso
                st.info("🔄 **Iniciando processamento...**")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Obter debug_mode do session_state se existir
                debug_mode = st.session_state.get('debug_mode', False)
                
                # Usar sempre o processador específico do banco selecionado
                st.info(f"� **Inicializando processador específico do {bank_info['name']}**")
                processor = MultibankPDFProcessor(bank_id=selected_bank_id, debug_mode=debug_mode)
                
                transactions = processor.extract_transactions(
                    uploaded_file, 
                    progress_bar, 
                    status_text,
                    bank_id=selected_bank_id
                )
                
                # Salvar no cache se encontrou transações
                if transactions:
                    cache_manager.save_to_cache(file_hash, transactions)
            
            # Inicializar gerenciador de notificações
            notification_manager = NotificationManager()
            
            # Mostrar progresso e notificações
            notification_manager.show_processing_steps(transactions)
            
            if transactions:
                st.markdown("---")
                
                # Analisar os dados
                analyzer = DataAnalyzer(transactions)
                daily_summary = analyzer.get_daily_summary()
                
                # Tabs para organizar melhor a visualização
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📋 Resumo Diário", 
                    "📊 Gráficos", 
                    "📈 Estatísticas", 
                    "📄 Detalhes Completos",
                    "⚡ Performance"
                ])
                
                with tab1:
                    st.header("📋 Resumo por Data")
                    display_daily_summary(daily_summary)
                
                with tab2:
                    st.header("📊 Visualizações")
                    display_charts(daily_summary)
                
                with tab3:
                    st.header("📈 Estatísticas Gerais")
                    display_statistics(analyzer)
                    
                    # Botão para mostrar celebração
                    if st.button("🎉 Finalizar Análise"):
                        notification_manager.show_completion_celebration(len(transactions))
                
                with tab4:
                    st.header("📄 Transações Detalhadas")
                    display_detailed_transactions(transactions)
                
                with tab5:
                    st.header("⚡ Informações de Performance")
                    display_performance_info(total_pages if 'total_pages' in locals() else 0, 
                                           len(transactions), cached_transactions is not None)
                
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            
            # Mostrar detalhes do erro para debug
            with st.expander("🔍 Detalhes do erro"):
                st.code(str(e), language="text")
                st.markdown("""
                **Se o problema persistir:**
                - Verifique se o arquivo não está corrompido
                - Teste com um arquivo menor primeiro
                - Certifique-se de que é um extrato bancário válido
                - Tente converter o PDF para um formato mais simples
                """)
    else:
        # Página inicial - exigir seleção de banco
        if not selected_bank_id:
            st.info("👆 **Primeiro selecione seu banco na barra lateral**")
            
            # Mostrar bancos suportados
            st.markdown("## 🏦 **Bancos Suportados**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **✅ Processamento Específico Ativo:**
                """)
                
                for bank_id, bank_info in available_banks.items():
                    st.markdown(f"- 🟢 **{bank_info['name']}** ({bank_info['code']})")
                    st.markdown(f"  *{bank_info['description']}*")
                    st.markdown(f"  🎯 *Padrões específicos otimizados*")
            
            with col2:
                st.markdown("""
                **� Em Desenvolvimento:**
                - 🟡 Itaú (341)
                - 🟡 Bradesco (237)
                - 🟡 Banco do Brasil (001)
                - 🟡 Caixa Econômica Federal (104)
                """)
            
            st.markdown("---")
            
            # Instruções de uso
            with st.expander("ℹ️ Por que selecionar o banco é obrigatório?", expanded=True):
                st.markdown("""
                **🎯 Garantia de Precisão Máxima:**
                
                **✅ Vantagens do processamento específico:**
                - � **100% de precisão:** Cada banco tem formato único
                - 🚀 **Velocidade otimizada:** Processamento direcionado
                - � **Reconhecimento inteligente:** Padrões específicos do banco
                - � **Classificação correta:** Créditos e débitos precisos
                - 🧠 **Interpretação contextual:** Entende linguagem do banco
                
                **� Como funciona:**
                1. 🏦 **Você seleciona o banco** na barra lateral
                2. 📁 **Upload do extrato** fica disponível
                3. 🎯 **Sistema usa padrões específicos** do seu banco
                4. ⚡ **Extração otimizada** e mais precisa
                5. 📊 **Resultados confiáveis** garantidos
                
                **❌ Por que não usamos detecção automática:**
                - Pode gerar erros de identificação
                - Reduz precisão da extração
                - Processamento mais lento
                - Resultados menos confiáveis
                """)
                
            # Seção de feedback e expansão futura
            st.markdown("## 🔮 **Próximos Bancos**")
            st.info("""
            **📅 Roadmap de desenvolvimento:**
            - 🔜 **Q1 2026:** Itaú (341)
            - 🔜 **Q1 2026:** Bradesco (237)
            - 🔜 **Q2 2026:** Banco do Brasil (001)
            - 🔜 **Q2 2026:** Caixa Econômica Federal (104)
            
            **💡 Seu banco não está na lista?** 
            Entre em contato para priorizar o desenvolvimento!
            """)
        else:
            # Se banco foi selecionado mas não há arquivo
            st.info("👆 **Agora faça upload do seu extrato PDF na barra lateral**")
            
            bank_info = available_banks[selected_bank_id]
            st.success(f"✅ **Banco selecionado:** {bank_info['name']}")
            st.markdown(f"🎯 **Pronto para processar extratos do {bank_info['name']} com máxima precisão!**")

def display_daily_summary(daily_summary):
    """Exibe o resumo diário das transações otimizado"""
    if daily_summary.empty:
        st.info("Nenhuma transação encontrada")
        return
    
    st.markdown("### 📊 Resumo Financeiro por Data")
    
    # Para arquivos grandes, mostrar resumo compacto primeiro
    if len(daily_summary) > 10:
        st.info(f"📄 **Arquivo grande detectado:** {len(daily_summary)} dias com movimentação")
        
        # Mostrar top 5 dias com maior movimento
        daily_summary['movimento_total'] = daily_summary['credito'] + daily_summary['debito']
        top_days = daily_summary.nlargest(5, 'movimento_total')
        
        st.markdown("#### 🔝 Top 5 Dias com Maior Movimento:")
        for _, row in top_days.iterrows():
            st.markdown(f"**{row['data']}** - Total: R$ {row['movimento_total']:,.2f} "
                       f"(💚 R$ {row['credito']:,.2f} / 🔴 R$ {row['debito']:,.2f})")
        
        # Opção para mostrar todos
        if st.button("📋 Mostrar Todos os Dias"):
            show_all = True
        else:
            show_all = False
    else:
        show_all = True
    
    if show_all:
        for index, row in daily_summary.iterrows():
            date_str = row['data']
            credit = row['credito']
            debit = row['debito']
            balance = row['saldo']
            num_trans = row['num_transacoes']
            
            # Card estilizado para cada dia
            with st.container():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    border-left: 4px solid {'#28a745' if balance >= 0 else '#dc3545'};
                    margin-bottom: 1rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin: 0; color: #495057;">📅 {date_str}</h4>
                    <p style="margin: 0.5rem 0; color: #6c757d;">{num_trans} transação(ões)</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Métricas em colunas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💚 Crédito", f"R$ {credit:,.2f}")
                
                with col2:
                    st.metric("🔴 Débito", f"R$ {debit:,.2f}")
                
                with col3:
                    delta_color = "normal" if balance >= 0 else "inverse"
                    st.metric("⚖️ Saldo do Dia", f"R$ {balance:,.2f}",
                             delta=f"R$ {balance:,.2f}", delta_color=delta_color)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Resumo total
    total_credit = daily_summary['credito'].sum()
    total_debit = daily_summary['debito'].sum()
    total_balance = total_credit - total_debit
    
    st.markdown("---")
    st.markdown("### 📊 **Resumo Total do Período**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Créditos", f"R$ {total_credit:,.2f}")
    with col2:
        st.metric("💸 Total Débitos", f"R$ {total_debit:,.2f}")
    with col3:
        balance_color = "normal" if total_balance >= 0 else "inverse"
        st.metric("📈 Saldo Final", f"R$ {total_balance:,.2f}", delta_color=balance_color)

def display_statistics(analyzer):
    """Exibe estatísticas gerais"""
    stats = analyzer.get_statistics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("💰 Total Crédito", f"R$ {stats['total_credito']:,.2f}")
        st.metric("💸 Total Débito", f"R$ {stats['total_debito']:,.2f}")
        st.metric("📊 Saldo Final", f"R$ {stats['saldo_final']:,.2f}")
    
    with col2:
        st.metric("📈 Maior Crédito", f"R$ {stats['maior_credito']:,.2f}")
        st.metric("📉 Maior Débito", f"R$ {stats['maior_debito']:,.2f}")
        st.metric("🔢 Total Transações", stats['total_transacoes'])

def display_charts(daily_summary):
    """Exibe gráficos dos dados"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - Crédito vs Débito por dia
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Crédito',
            x=daily_summary['data'],
            y=daily_summary['credito'],
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            name='Débito',
            x=daily_summary['data'],
            y=daily_summary['debito'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title='Crédito vs Débito por Dia',
            xaxis_title='Data',
            yaxis_title='Valor (R$)',
            barmode='group'
        )
        st.plotly_chart(fig)
    
    with col2:
        # Gráfico de linha - Saldo acumulado
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_summary['data'],
            y=daily_summary['saldo'],
            mode='lines+markers',
            line={'color': 'blue'},
            name='Saldo'
        ))
        
        fig.update_layout(
            title='Saldo Diário',
            xaxis_title='Data',
            yaxis_title='Saldo (R$)'
        )
        st.plotly_chart(fig)

def display_detailed_transactions(transactions):
    """Exibe tabela detalhada das transações otimizada"""
    df = pd.DataFrame(transactions)
    
    # Para arquivos grandes, mostrar opções de paginação
    if len(df) > 100:
        st.warning(f"📄 **Arquivo grande:** {len(df)} transações encontradas")
        
        # Opções de visualização
        view_option = st.radio(
            "Escolha como visualizar:",
            ["📊 Resumo por Período", "📋 Tabela Completa", "🔍 Busca Específica"]
        )
        
        if view_option == "📊 Resumo por Período":
            # Mostrar resumo agrupado
            monthly_summary = df.groupby(df['data'].str[-7:]).agg({
                'valor': ['count', 'sum'],
                'tipo': lambda x: (x == 'Crédito').sum()
            }).round(2)
            st.dataframe(monthly_summary, width='stretch')
            return
        
        elif view_option == "🔍 Busca Específica":
            search_term = st.text_input("🔍 Buscar na descrição:")
            if search_term:
                filtered_df = df[df['descricao'].str.contains(search_term, case=False, na=False)]
                st.dataframe(filtered_df, width='stretch')
            return
    
    # Filtros padrão
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dates = df['data'].unique()
        selected_date = st.selectbox("Filtrar por Data", ["Todas"] + list(dates))
    
    with col2:
        tipos = df['tipo'].unique()
        selected_type = st.selectbox("Filtrar por Tipo", ["Todos"] + list(tipos))
    
    with col3:
        min_value = st.number_input("Valor Mínimo", min_value=0.0, value=0.0)
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if selected_date != "Todas":
        filtered_df = filtered_df[filtered_df['data'] == selected_date]
    
    if selected_type != "Todos":
        filtered_df = filtered_df[filtered_df['tipo'] == selected_type]
    
    if min_value > 0:
        filtered_df = filtered_df[filtered_df['valor'] >= min_value]
    
    # Exibir tabela
    st.dataframe(
        filtered_df,
        width='stretch',
        column_config={
            "data": "Data",
            "descricao": "Descrição",
            "tipo": "Tipo",
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
        }
    )
    
    # Download dos dados
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Baixar dados filtrados (CSV)",
        data=csv,
        file_name=f"transacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def display_performance_info(total_pages, total_transactions, used_cache):
    """Exibe informações de performance"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 **Estatísticas de Processamento**")
        st.metric("📄 Páginas Processadas", total_pages)
        st.metric("📋 Transações Encontradas", total_transactions)
        
        if total_pages > 0:
            st.metric("🔍 Taxa de Sucesso", f"{(total_transactions/total_pages):.1f} trans/página")
    
    with col2:
        st.markdown("### ⚡ **Performance**")
        
        if used_cache:
            st.success("💾 **Cache Utilizado**\n- Carregamento instantâneo\n- Dados salvos localmente")
        else:
            st.info("🔄 **Processamento Realizado**\n- Arquivo analisado completamente\n- Cache criado para próximas consultas")
        
        # Limpeza de cache manual
        if st.button("🧹 Limpar Cache"):
            cache_manager = CacheManager()
            cache_manager.clear_old_cache()
            st.success("Cache limpo com sucesso!")

if __name__ == "__main__":
    main()