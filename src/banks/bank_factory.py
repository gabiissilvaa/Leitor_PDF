import re
from typing import Optional
from .base_bank_processor import BaseBankProcessor
from .santander_processor import SantanderProcessor

class BankProcessorFactory:
    """Factory para criar processadores específicos de bancos"""
    
    # Registro de bancos disponíveis
    AVAILABLE_BANKS = {
        'santander': {
            'name': 'Banco Santander',
            'code': '033',
            'processor_class': SantanderProcessor,
            'description': 'Banco Santander (Brasil) S.A.'
        },
        # Futuros bancos podem ser adicionados aqui
        # 'itau': {
        #     'name': 'Banco Itaú',
        #     'code': '341',
        #     'processor_class': ItauProcessor,
        #     'description': 'Itaú Unibanco S.A.'
        # },
        # 'bradesco': {
        #     'name': 'Banco Bradesco',
        #     'code': '237',
        #     'processor_class': BradescoProcessor,
        #     'description': 'Banco Bradesco S.A.'
        # }
    }
    
    @classmethod
    def get_available_banks(cls) -> dict:
        """Retorna lista de bancos disponíveis"""
        return {
            bank_id: {
                'name': info['name'],
                'code': info['code'],
                'description': info['description']
            }
            for bank_id, info in cls.AVAILABLE_BANKS.items()
        }
    
    @classmethod
    def create_processor(cls, bank_id: str, debug_mode: bool = False) -> Optional[BaseBankProcessor]:
        """Cria processador específico para o banco solicitado"""
        
        if bank_id not in cls.AVAILABLE_BANKS:
            available_banks = ', '.join(cls.AVAILABLE_BANKS.keys())
            raise ValueError(f"Banco '{bank_id}' não suportado. Bancos disponíveis: {available_banks}")
        
        bank_info = cls.AVAILABLE_BANKS[bank_id]
        processor_class = bank_info['processor_class']
        
        return processor_class(debug_mode=debug_mode)
    
    @classmethod
    def get_bank_by_code(cls, bank_code: str) -> Optional[str]:
        """Retorna ID do banco pelo código bancário"""
        for bank_id, info in cls.AVAILABLE_BANKS.items():
            if info['code'] == bank_code:
                return bank_id
        return None
    
    @classmethod
    def detect_bank_from_text(cls, text: str) -> Optional[str]:
        """Tenta detectar o banco baseado no texto do PDF"""
        text_lower = text.lower()
        
        # Padrões para detectar Santander
        santander_patterns = [
            r'banco\s+santander',
            r'santander\s+brasil',
            r'033\s*-?\s*santander',
            r'santander.*s\.?a\.?',
            r'conta\s+corrente\s+santander',
            r'extrato\s+santander',
            r'way\s+santander',
            r'santander\s+pay'
        ]
        
        for pattern in santander_patterns:
            if re.search(pattern, text_lower):
                return 'santander'
        
        # Futuros padrões para outros bancos podem ser adicionados aqui
        
        return None
    
    @classmethod
    def is_bank_supported(cls, bank_id: str) -> bool:
        """Verifica se um banco é suportado"""
        return bank_id in cls.AVAILABLE_BANKS
    
    @classmethod
    def get_bank_info(cls, bank_id: str) -> Optional[dict]:
        """Retorna informações de um banco específico"""
        if bank_id in cls.AVAILABLE_BANKS:
            return cls.AVAILABLE_BANKS[bank_id].copy()
        return None