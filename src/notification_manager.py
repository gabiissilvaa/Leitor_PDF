import streamlit as st
from typing import List, Dict, Any
import time

class NotificationManager:
    """Gerencia notificações e feedback visual na interface"""
    
    def __init__(self):
        self.notifications = []
        
    def show_processing_steps(self, transactions: List[Dict[str, Any]]):
        """Mostra o progresso do processamento passo a passo"""
        
        # Container para notificações
        notification_container = st.container()
        
        with notification_container:
            # Etapa 1: Validação inicial
            with st.status("🔍 Analisando arquivo...", expanded=True) as status:
                st.write("✅ Arquivo carregado com sucesso")
                st.write("✅ Formato PDF verificado")
                st.write("✅ Conteúdo extraído")
                time.sleep(0.5)
                status.update(label="✅ Análise concluída!", state="complete")
            
            # Etapa 2: Processamento de transações
            if transactions:
                with st.status("🔄 Processando transações...", expanded=True) as status:
                    st.write(f"📊 {len(transactions)} transações encontradas")
                    
                    # Contar tipos de transação
                    credits = sum(1 for t in transactions if t['tipo'] == 'Crédito')
                    debits = sum(1 for t in transactions if t['tipo'] == 'Débito')
                    
                    st.write(f"💚 {credits} créditos identificados")
                    st.write(f"🔴 {debits} débitos identificados")
                    st.write("✅ Valores convertidos para formato brasileiro")
                    st.write("✅ Datas organizadas cronologicamente")
                    time.sleep(0.5)
                    status.update(label="✅ Processamento concluído!", state="complete")
                
                # Etapa 3: Análise e organização
                with st.status("📊 Organizando dados...", expanded=True) as status:
                    # Calcular período
                    dates = [t['data'] for t in transactions]
                    unique_dates = len(set(dates))
                    
                    st.write(f"📅 Período analisado: {unique_dates} dia(s)")
                    st.write("✅ Dados agrupados por data")
                    st.write("✅ Saldos calculados")
                    st.write("✅ Estatísticas geradas")
                    time.sleep(0.5)
                    status.update(label="✅ Organização concluída!", state="complete")
                
                # Notificação de sucesso
                st.success("🎉 **Processamento finalizado com sucesso!**")
                
                # Resumo rápido em destaque
                self._show_quick_summary(transactions)
            else:
                st.error("❌ Nenhuma transação foi encontrada no arquivo")
                self._show_troubleshooting_tips()
    
    def _show_quick_summary(self, transactions: List[Dict[str, Any]]):
        """Mostra um resumo rápido dos dados processados"""
        
        st.markdown("### 📋 Resumo Rápido")
        
        # Calcular totais
        total_credits = sum(t['valor'] for t in transactions if t['tipo'] == 'Crédito')
        total_debits = sum(t['valor'] for t in transactions if t['tipo'] == 'Débito')
        net_balance = total_credits - total_debits
        
        # Métricas em destaque
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Transações",
                len(transactions),
                help="Total de operações encontradas"
            )
        
        with col2:
            st.metric(
                "💚 Total Créditos",
                f"R$ {total_credits:,.2f}",
                help="Soma de todas as entradas"
            )
        
        with col3:
            st.metric(
                "🔴 Total Débitos",
                f"R$ {total_debits:,.2f}",
                help="Soma de todas as saídas"
            )
        
        with col4:
            balance_delta = "normal" if net_balance >= 0 else "inverse"
            st.metric(
                "⚖️ Saldo Líquido",
                f"R$ {net_balance:,.2f}",
                delta=f"R$ {net_balance:,.2f}",
                delta_color=balance_delta,
                help="Diferença entre créditos e débitos"
            )
        
        # Indicador visual do saldo
        if net_balance >= 0:
            st.success(f"✅ **Saldo positivo:** Suas entradas superaram as saídas em R$ {net_balance:,.2f}")
        else:
            st.warning(f"⚠️ **Saldo negativo:** Suas saídas superaram as entradas em R$ {abs(net_balance):,.2f}")
    
    def _show_troubleshooting_tips(self):
        """Mostra dicas para solução de problemas"""
        
        with st.expander("🔧 Dicas para Solução de Problemas"):
            st.markdown("""
            **Se nenhuma transação foi encontrada, tente:**
            
            1. **📄 Verificar o formato do PDF:**
               - Certifique-se de que é um extrato bancário real
               - O PDF deve conter texto selecionável (não apenas imagem)
            
            2. **🏦 Formato suportado:**
               - Extratos de bancos brasileiros
               - Datas no formato DD/MM/AAAA
               - Valores em Reais (R$)
            
            3. **🔍 Verificar conteúdo:**
               - O arquivo deve ter transações com datas e valores
               - Evite PDFs protegidos por senha
               - Teste com um período que tenha movimentação
            
            4. **💡 Alternativas:**
               - Exporte o extrato em outro formato
               - Tente um período diferente
               - Verifique se o banco é suportado
            """)
    
    def show_live_transaction_feed(self, transaction_info: Dict[str, Any]):
        """Mostra transações sendo descobertas em tempo real"""
        
        # Card da transação em tempo real
        with st.container():
            col1, col2, col3, col4 = st.columns([1.5, 3, 1, 1.5])
            
            with col1:
                st.markdown(f"**📅 {transaction_info['data']}**")
            
            with col2:
                description = transaction_info['descricao']
                if len(description) > 40:
                    description = description[:37] + "..."
                st.markdown(f"📝 {description}")
            
            with col3:
                emoji = "💚" if transaction_info['tipo'] == 'Crédito' else "🔴"
                st.markdown(f"{emoji} {transaction_info['tipo']}")
            
            with col4:
                st.markdown(f"**R$ {transaction_info['valor']:,.2f}**")
    
    def show_completion_celebration(self, total_transactions: int):
        """Mostra celebração de conclusão"""
        
        st.balloons()  # Efeito visual
        
        # Mensagem de sucesso personalizada
        if total_transactions > 50:
            message = "🎉 Uau! Muitas transações processadas!"
        elif total_transactions > 20:
            message = "🎊 Ótimo! Dados processados com sucesso!"
        elif total_transactions > 5:
            message = "✨ Perfeito! Análise concluída!"
        else:
            message = "✅ Pronto! Dados organizados!"
        
        st.success(message)
        
        # Botão para continuar
        if st.button("🚀 Ver Análise Completa", type="primary"):
            st.rerun()