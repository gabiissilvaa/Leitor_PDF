from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

class BaseBankProcessor(ABC):
    """Classe base abstrata para processadores de bancos específicos"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.detected_year = None
        self.last_date_context = None
        self.bank_name = "Genérico"
        self.bank_code = "000"
        
    @property
    @abstractmethod
    def date_patterns(self) -> List[str]:
        """Padrões regex específicos do banco para extrair datas"""
        pass
    
    @property
    @abstractmethod 
    def value_patterns(self) -> List[str]:
        """Padrões regex específicos do banco para extrair valores"""
        pass
    
    @property
    @abstractmethod
    def credit_keywords(self) -> List[str]:
        """Palavras-chave que indicam transações de crédito"""
        pass
    
    @property
    @abstractmethod
    def debit_keywords(self) -> List[str]:
        """Palavras-chave que indicam transações de débito"""
        pass
    
    @property
    @abstractmethod
    def ignore_patterns(self) -> List[str]:
        """Padrões que devem ser ignorados (não são transações)"""
        pass
    
    @abstractmethod
    def extract_date_from_line(self, line: str) -> Optional[str]:
        """Extrai data de uma linha específica do banco"""
        pass
    
    @abstractmethod
    def classify_transaction_type(self, line: str) -> str:
        """Classifica o tipo de transação (Crédito/Débito) baseado na linha"""
        pass
    
    @abstractmethod
    def extract_description(self, line: str) -> str:
        """Extrai e limpa a descrição da transação"""
        pass
    
    def detect_statement_year(self, text: str) -> int:
        """Detecta automaticamente o ano do extrato (implementação base)"""
        current_year = datetime.now().year
        
        # Padrões gerais para detectar ano
        header_patterns = [
            r'extrato.*?(\d{4})',
            r'período.*?(\d{1,2}/\d{1,2}/(\d{4}))',
            r'movimentação.*?(\d{4})',
            r'(\d{4})\s*-\s*\d{1,2}',
            r'(\d{1,2}/\d{1,2}/(\d{4}))\s*a\s*\d{1,2}/\d{1,2}/\d{4}',
        ]
        
        # Tentar encontrar ano em cabeçalhos
        for pattern in header_patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    year_candidate = match[-1] if isinstance(match, tuple) else match
                    year_int = int(year_candidate)
                    if 2020 <= year_int <= current_year + 1:
                        return year_int
                except (ValueError, IndexError):
                    continue
        
        # Analisar datas completas
        full_date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        date_matches = re.findall(full_date_pattern, text)
        
        year_frequency = {}
        for day, month, year in date_matches:
            try:
                day_int, month_int, year_int = int(day), int(month), int(year)
                if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 2020 <= year_int <= current_year + 1:
                    year_frequency[year_int] = year_frequency.get(year_int, 0) + 1
            except ValueError:
                continue
        
        if year_frequency:
            most_likely_year = max(year_frequency.items(), key=lambda x: x[1])[0]
            return most_likely_year
        
        return current_year
    
    def extract_all_values(self, text: str) -> List[float]:
        """Extrai todos os valores monetários de uma linha (implementação base)"""
        values = []
        
        for pattern in self.value_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    clean_value = match.replace('R$', '').replace(' ', '')
                    
                    if ',' in clean_value and '.' in clean_value:
                        clean_value = clean_value.replace('.', '').replace(',', '.')
                    elif ',' in clean_value:
                        clean_value = clean_value.replace(',', '.')
                    
                    value = float(clean_value)
                    if value > 0:
                        values.append(value)
                        
                except (ValueError, AttributeError):
                    continue
        
        return values
    
    def is_line_ignored(self, line: str) -> bool:
        """Verifica se uma linha deve ser ignorada"""
        line_lower = line.lower()
        
        for pattern in self.ignore_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False
    
    def validate_date(self, date_str: str) -> bool:
        """Valida se uma string representa uma data válida"""
        try:
            datetime.strptime(date_str, '%d/%m/%Y')
            return True
        except (ValueError, TypeError):
            return False
    
    def parse_transaction_line(self, line: str, current_date: str = None) -> Optional[Dict[str, Any]]:
        """Analisa uma linha e tenta extrair informações de transação (implementação base)"""
        
        line_clean = line.strip()
        
        # Verificar se deve ignorar a linha
        if self.is_line_ignored(line_clean):
            return None
        
        # Extrair data da linha se disponível
        line_date = self.extract_date_from_line(line_clean)
        if line_date:
            current_date = line_date
        
        if not current_date:
            return None
        
        # Extrair valores
        values = self.extract_all_values(line_clean)
        if not values:
            return None
        
        # Filtrar valores significativos
        significant_values = [v for v in values if 1.0 <= v <= 50000000.0]
        if not significant_values:
            return None
        
        # Classificar tipo de transação
        transaction_type = self.classify_transaction_type(line_clean)
        
        # Extrair descrição
        description = self.extract_description(line_clean)
        
        # Usar o maior valor encontrado
        value = max(significant_values)
        
        return {
            'data': current_date,
            'tipo': transaction_type,
            'valor': value,
            'descricao': description,
            'linha_original': line_clean,
            'banco': self.bank_name
        }
    
    def clean_and_sort_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas e ordena transações por data"""
        
        if not transactions:
            return []
        
        # Filtrar transações com datas válidas
        valid_transactions = []
        invalid_count = 0
        
        for transaction in transactions:
            if self.validate_date(transaction.get('data', '')):
                valid_transactions.append(transaction)
            else:
                invalid_count += 1
        
        if invalid_count > 0 and self.debug_mode:
            try:
                import streamlit as st
                st.info(f"📅 {invalid_count} transação(ões) com datas inválidas foram ignoradas")
            except ImportError:
                print(f"📅 {invalid_count} transação(ões) com datas inválidas foram ignoradas")
        
        # Remover duplicatas
        seen = set()
        unique_transactions = []
        
        for transaction in valid_transactions:
            key = (transaction['data'], transaction['tipo'], transaction['valor'])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
        
        # Ordenar por data
        try:
            unique_transactions.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))
        except Exception:
            pass  # Manter ordem original se não conseguir ordenar
        
        return unique_transactions