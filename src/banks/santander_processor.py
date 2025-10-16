import re
from typing import List, Optional
from .base_bank_processor import BaseBankProcessor

class SantanderProcessor(BaseBankProcessor):
    """Processador específico para extratos do Banco Santander"""
    
    def __init__(self, debug_mode: bool = False):
        super().__init__(debug_mode)
        self.bank_name = "Santander"
        self.bank_code = "033"
    
    @property
    def date_patterns(self) -> List[str]:
        """Padrões específicos do Santander para datas"""
        return [
            # Padrões prioritários do Santander
            r'^(\d{2})/(\d{2})/(\d{4})',            # DD/MM/YYYY no início
            r'^(\d{2})/(\d{2})/(\d{2})',            # DD/MM/YY no início
            r'^(\d{1,2})/(\d{1,2})/(\d{4})',        # D/M/YYYY no início
            r'^(\d{2})/(\d{2})\s',                  # DD/MM seguido de espaço
            r'^(\d{1,2})/(\d{1,2})\s',              # D/M seguido de espaço
            
            # Padrões específicos do layout Santander
            r'data[:\s]+(\d{2})/(\d{2})/(\d{4})',   # "Data: 01/07/2025"
            r'movto[:\s]+(\d{2})/(\d{2})/(\d{4})',  # "Movto: 01/07/2025"
            r'lançamento[:\s]+(\d{2})/(\d{2})/(\d{4})',  # "Lançamento: 01/07/2025"
            
            # Padrões gerais
            r'(\d{2})/(\d{2})/(\d{4})',             # DD/MM/YYYY
            r'(\d{2})/(\d{2})/(\d{2})',             # DD/MM/YY
            r'(\d{1,2})/(\d{1,2})/(\d{4})',         # D/M/YYYY
            r'(\d{2})/(\d{2})\b',                   # DD/MM
            r'(\d{1,2})/(\d{1,2})\b',               # D/M
        ]
    
    @property
    def value_patterns(self) -> List[str]:
        """Padrões específicos do Santander para valores monetários"""
        return [
            # Padrões prioritários Santander
            r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',               # R$ 1.000,00
            r'(\d{1,3}(?:\.\d{3})*,\d{2})(?!\d)',               # 1.000,00
            r'(\d{4,},\d{2})(?!\d)',                            # 491511,00
            r'R\$\s*(\d+,\d{2})',                               # R$ 123,45
            r'(\d+,\d{2})(?=\s|$)',                             # 123,45
            
            # Padrões específicos do layout Santander
            r'valor[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',   # "Valor: R$ 1.000,00"
            r'valor[:\s]+(\d{1,3}(?:\.\d{3})*,\d{2})',         # "Valor: 1.000,00"
            r'saldo[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',   # "Saldo: R$ 1.000,00"
        ]
    
    @property
    def credit_keywords(self) -> List[str]:
        """Palavras-chave específicas do Santander para créditos"""
        return [
            # Palavras padrão
            'crédito', 'credito', 'entrada', 'depósito', 'deposito',
            'transferência recebida', 'pix recebido', 'ted recebida',
            'doc recebido', 'salário', 'salario', 'rendimento',
            
            # Específicas do Santander
            'credito automatico', 'credito em conta', 'liquidacao automatica',
            'remuneracao', 'rendimento poupanca', 'rendimento cdb',
            'credito salario', 'credito beneficio', 'deposito identificado',
            'transferencia doc credito', 'transferencia ted credito',
            'pix transferencia recebida', 'pix recebimento',
            'santander pay recebido', 'way recebido',
            'estorno credito', 'devolucao credito', 'cancelamento debito',
            'cashback', 'credito cartao', 'credito pre aprovado',
            'emprestimo credito', 'limite especial credito'
        ]
    
    @property
    def debit_keywords(self) -> List[str]:
        """Palavras-chave específicas do Santander para débitos"""
        return [
            # Palavras padrão
            'débito', 'debito', 'saída', 'saque', 'pagamento',
            'transferência enviada', 'pix enviado', 'ted enviada',
            'doc enviado', 'compra', 'taxa', 'tarifa',
            
            # Específicas do Santander
            'debito automatico', 'debito em conta', 'saque terminal',
            'saque santander', 'pagamento debito automatico',
            'transferencia doc debito', 'transferencia ted debito',
            'pix transferencia enviada', 'pix pagamento',
            'santander pay enviado', 'way enviado',
            'tarifa santander', 'tarifa conta corrente', 'tarifa poupanca',
            'anuidade cartao', 'tarifa sms', 'tarifa extrato',
            'iof', 'cpmf', 'imposto renda', 'compulsorio',
            'emprestimo debito', 'financiamento debito',
            'cartao credito', 'fatura cartao', 'compra cartao',
            'saque avulso', 'cheque compensado', 'devolucao cheque',
            'tarifa ted', 'tarifa doc', 'tarifa pix',
            'limite especial debito', 'juros limite especial'
        ]
    
    @property
    def ignore_patterns(self) -> List[str]:
        """Padrões específicos do Santander que devem ser ignorados"""
        return [
            # Padrões gerais
            r'página?\s*[:.]?\s*\d+', r'pagina?\s*[:.]?\s*\d+',
            r'\bpagina?\s*[:.]?\s*\d+/\d+', r'^\d+$', r'^\d+/\d+$',
            r'banco\s+', r'extrato\s+', r'conta\s+corrente',
            r'saldo\s+(anterior|atual)', r'total\s+', r'^\s*[-=]+\s*$',
            r'agencia\s*\d+', r'conta\s*\d+', r'cpf\s*[:.]?\s*\d',
            r'cnpj\s*[:.]?\s*\d', r'^\d+\s*$',
            
            # Específicos do Santander
            r'santander\s+brasil', r'banco\s+santander',
            r'conta\s+corrente\s+santander', r'poupança\s+santander',
            r'agencia\s+santander', r'gerente\s+santander',
            r'cartão\s+santander', r'mastercard\s+santander',
            r'visa\s+santander', r'santander\s+select',
            r'santander\s+empresarial', r'santander\s+van\s+gogh',
            r'way\s+santander', r'santander\s+pay',
            r'código\s+do\s+banco\s+033', r'033\s+santander',
            r'central\s+de\s+atendimento', r'sac\s+santander',
            r'ouvidoria\s+santander', r'ombudsman\s+santander',
            r'desconsidere\s+esta\s+informação',
            r'válido\s+para\s+clientes', r'se\s+o\s+limite\s+de\s+crédito',
            r'tarifa\s+pela\s+disponibilização',
            r'cheque\s+empresa\s+plus', r'santander\s+master',
            r'hipóteses?\s*:', r'durante\s+do\s+prazo',
            r'período\s+de\s+vigência', r'emitente',
            r'ccgpj\s+\d+', r'v\s+\d+,\d+\s+\d+', r'\d{12,}',
            
            # Cabeçalhos e rodapés típicos do Santander
            r'extrato\s+de\s+conta\s+corrente',
            r'extrato\s+de\s+poupança',
            r'movimentação\s+do\s+período',
            r'saldo\s+inicial', r'saldo\s+final',
            r'total\s+de\s+créditos', r'total\s+de\s+débitos',
            r'número\s+da\s+conta', r'número\s+da\s+agência',
            r'titular\s+da\s+conta', r'nome\s+do\s+cliente'
        ]
    
    def extract_date_from_line(self, line: str) -> Optional[str]:
        """Extrai data específica do formato Santander"""
        from datetime import datetime
        
        # Limpar texto
        clean_text = re.sub(r'[^\w\s/.-]', ' ', line)
        
        # Verificar padrões inválidos específicos do Santander
        invalid_patterns = [
            r'pix\s+\d+', r'\d{10,}', r'conta\s+\d+',
            r'agencia\s+\d+', r'codigo\s+\d+', r'ref\s*[:.]?\s*\d+',
            r'documento\s+\d+', r'seq\s*[:.]?\s*\d+', r'\b\d{6,}\b',
            r'valor\s+\d+', r'protocolo\s+\d+', r'autenticacao\s+\d+',
            r'comprovante\s+\d+', r'santander\s+\d+', r'cartao\s+\d+'
        ]
        
        for invalid_pattern in invalid_patterns:
            if re.search(invalid_pattern, clean_text.lower()):
                return None
        
        current_year = datetime.now().year
        
        for pattern in self.date_patterns:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    groups = match.groups()
                    
                    if len(groups) == 2:
                        day, month = groups
                        statement_year = self.detected_year if self.detected_year else current_year
                        year = str(statement_year)
                    elif len(groups) == 3:
                        day, month, year = groups
                        
                        if len(year) == 2:
                            year_int = int(year)
                            if year_int <= 50:
                                year = f"20{year}"
                            else:
                                year = f"19{year}"
                        else:
                            year_int = int(year)
                            statement_year = self.detected_year if self.detected_year else current_year
                            if abs(year_int - statement_year) > 1:
                                year = str(statement_year)
                    else:
                        continue
                    
                    # Validar valores
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    if not (1 <= day_int <= 31 and 1 <= month_int <= 12):
                        continue
                    
                    # Verificar se é data válida
                    try:
                        test_date = datetime(year_int, month_int, day_int)
                        today = datetime.now()
                        if test_date.year < 2020 or test_date.year > today.year + 2:
                            continue
                            
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                        
                    except ValueError:
                        continue
                        
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def classify_transaction_type(self, line: str) -> str:
        """Classifica tipo de transação específico do Santander"""
        line_lower = line.lower()
        
        # Verificar palavras de crédito primeiro
        has_credit = any(keyword in line_lower for keyword in self.credit_keywords)
        if has_credit:
            return 'Crédito'
        
        # Verificar palavras de débito
        has_debit = any(keyword in line_lower for keyword in self.debit_keywords)
        if has_debit:
            return 'Débito'
        
        # Padrões específicos do Santander para classificação
        santander_credit_patterns = [
            r'\+\s*\d', r'entrada\s+', r'receb\w*\s+',
            r'dep\w*\s+', r'liquid\w*\s+', r'rendim\w*\s+',
            r'credit\w*\s+', r'estorn\w*\s+credit',
            r'devol\w*\s+credit', r'cancel\w*\s+debit'
        ]
        
        santander_debit_patterns = [
            r'-\s*\d', r'saida\s+', r'pag\w*\s+',
            r'saque\s+', r'tarif\w*\s+', r'taxa\s+',
            r'debit\w*\s+', r'compra\s+', r'transfer\w*\s+env',
            r'pix\s+env', r'ted\s+env', r'doc\s+env'
        ]
        
        # Verificar padrões de crédito
        for pattern in santander_credit_patterns:
            if re.search(pattern, line_lower):
                return 'Crédito'
        
        # Verificar padrões de débito
        for pattern in santander_debit_patterns:
            if re.search(pattern, line_lower):
                return 'Débito'
        
        # Padrão específico: valores precedidos por + ou -
        if re.search(r'\+\s*\d', line):
            return 'Crédito'
        elif re.search(r'-\s*\d', line):
            return 'Débito'
        
        # Default para crédito se não conseguir classificar
        return 'Crédito'
    
    def extract_description(self, line: str) -> str:
        """Extrai e limpa descrição específica do Santander"""
        
        # Remover padrões comuns do Santander
        cleanup_patterns = [
            r'^\d{2}/\d{2}/\d{4}\s*',           # Data no início
            r'^\d{2}/\d{2}/\d{2}\s*',           # Data abreviada
            r'^\d{2}/\d{2}\s*',                 # Data sem ano
            r'R\$\s*\d+[.,]\d{2}\s*',           # Valores
            r'\d+[.,]\d{2}\s*$',                # Valores no final
            r'santander\s*',                    # Nome do banco
            r'ag\s*\d+\s*',                     # Agência
            r'cc\s*\d+\s*',                     # Conta corrente
            r'conta\s+\d+\s*',                  # Número da conta
            r'banco\s+033\s*',                  # Código do banco
        ]
        
        description = line.strip()
        
        # Aplicar limpezas
        for pattern in cleanup_patterns:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE)
        
        # Limpar espaços múltiplos
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Se ficou muito curto, usar linha original
        if len(description) < 5:
            description = line.strip()
        
        # Capitalizar primeira letra
        if description:
            description = description[0].upper() + description[1:].lower()
        
        return description or line.strip()
    
    def detect_statement_year(self, text: str) -> int:
        """Detecta ano específico para extratos Santander"""
        current_year = datetime.now().year
        
        # Padrões específicos do Santander
        santander_year_patterns = [
            r'extrato\s+santander.*?(\d{4})',
            r'conta\s+corrente.*?(\d{4})',
            r'movimentação.*?(\d{1,2}/\d{1,2}/(\d{4}))',
            r'período.*?(\d{1,2}/\d{1,2}/(\d{4}))',
            r'saldo\s+em\s+(\d{1,2}/\d{1,2}/(\d{4}))',
            r'santander.*?(\d{4})',
            r'(\d{4})\s*-\s*santander',
        ]
        
        # Tentar padrões específicos primeiro
        for pattern in santander_year_patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    year_candidate = match[-1] if isinstance(match, tuple) else match
                    year_int = int(year_candidate)
                    if 2020 <= year_int <= current_year + 1:
                        return year_int
                except (ValueError, IndexError):
                    continue
        
        # Usar método da classe base se não encontrou específico
        return super().detect_statement_year(text)