import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

class DataAnalyzer:
    """Classe responsável por analisar e organizar os dados das transações"""
    
    def __init__(self, transactions: List[Dict[str, Any]]):
        self.transactions = transactions
        self.df = pd.DataFrame(transactions) if transactions else pd.DataFrame()
        
        if not self.df.empty:
            # Converter data para datetime
            self.df['data_dt'] = pd.to_datetime(self.df['data'], format='%d/%m/%Y', errors='coerce')
            # Ordenar por data
            self.df = self.df.sort_values('data_dt')
    
    def get_daily_summary(self) -> pd.DataFrame:
        """Retorna resumo diário com totais de crédito e débito por data"""
        if self.df.empty:
            return pd.DataFrame()
        
        # Agrupar por data
        daily_data = []
        
        for date in self.df['data'].unique():
            date_transactions = self.df[self.df['data'] == date]
            
            # Calcular totais de crédito e débito
            credit_total = date_transactions[
                date_transactions['tipo'] == 'Crédito'
            ]['valor'].sum()
            
            debit_total = date_transactions[
                date_transactions['tipo'] == 'Débito'
            ]['valor'].sum()
            
            # Calcular saldo do dia
            daily_balance = credit_total - debit_total
            
            daily_data.append({
                'data': date,
                'credito': credit_total,
                'debito': debit_total,
                'saldo': daily_balance,
                'num_transacoes': len(date_transactions)
            })
        
        # Criar DataFrame e ordenar por data
        summary_df = pd.DataFrame(daily_data)
        if not summary_df.empty:
            summary_df['data_dt'] = pd.to_datetime(summary_df['data'], format='%d/%m/%Y')
            summary_df = summary_df.sort_values('data_dt').drop('data_dt', axis=1)
        
        return summary_df
    
    def get_statistics(self) -> Dict[str, float]:
        """Retorna estatísticas gerais das transações"""
        if self.df.empty:
            return {
                'total_credito': 0.0,
                'total_debito': 0.0,
                'saldo_final': 0.0,
                'maior_credito': 0.0,
                'maior_debito': 0.0,
                'total_transacoes': 0
            }
        
        credit_transactions = self.df[self.df['tipo'] == 'Crédito']
        debit_transactions = self.df[self.df['tipo'] == 'Débito']
        
        total_credit = credit_transactions['valor'].sum()
        total_debit = debit_transactions['valor'].sum()
        
        return {
            'total_credito': total_credit,
            'total_debito': total_debit,
            'saldo_final': total_credit - total_debit,
            'maior_credito': credit_transactions['valor'].max() if not credit_transactions.empty else 0.0,
            'maior_debito': debit_transactions['valor'].max() if not debit_transactions.empty else 0.0,
            'total_transacoes': len(self.df)
        }
    
    def get_transactions_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Retorna todas as transações de uma data específica"""
        if self.df.empty:
            return []
        
        date_transactions = self.df[self.df['data'] == date]
        return date_transactions.to_dict('records')
    
    def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
        """Retorna todas as transações de um tipo específico (Crédito/Débito)"""
        if self.df.empty:
            return []
        
        type_transactions = self.df[self.df['tipo'] == transaction_type]
        return type_transactions.to_dict('records')
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """Retorna resumo mensal das transações"""
        if self.df.empty:
            return pd.DataFrame()
        
        # Adicionar colunas de mês e ano
        df_copy = self.df.copy()
        df_copy['mes'] = df_copy['data_dt'].dt.month
        df_copy['ano'] = df_copy['data_dt'].dt.year
        df_copy['mes_ano'] = df_copy['data_dt'].dt.strftime('%m/%Y')
        
        # Agrupar por mês/ano
        monthly_data = []
        
        for month_year in df_copy['mes_ano'].unique():
            month_transactions = df_copy[df_copy['mes_ano'] == month_year]
            
            credit_total = month_transactions[
                month_transactions['tipo'] == 'Crédito'
            ]['valor'].sum()
            
            debit_total = month_transactions[
                month_transactions['tipo'] == 'Débito'
            ]['valor'].sum()
            
            monthly_data.append({
                'mes_ano': month_year,
                'credito': credit_total,
                'debito': debit_total,
                'saldo': credit_total - debit_total,
                'num_transacoes': len(month_transactions)
            })
        
        return pd.DataFrame(monthly_data)
    
    def search_transactions(self, search_term: str) -> List[Dict[str, Any]]:
        """Busca transações por termo na descrição"""
        if self.df.empty:
            return []
        
        # Busca case-insensitive na descrição
        matching_transactions = self.df[
            self.df['descricao'].str.contains(search_term, case=False, na=False)
        ]
        
        return matching_transactions.to_dict('records')
    
    def get_top_transactions(self, transaction_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna as maiores transações (por valor)"""
        if self.df.empty:
            return []
        
        df_filtered = self.df.copy()
        
        if transaction_type:
            df_filtered = df_filtered[df_filtered['tipo'] == transaction_type]
        
        top_transactions = df_filtered.nlargest(limit, 'valor')
        return top_transactions.to_dict('records')