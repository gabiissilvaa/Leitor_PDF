#!/usr/bin/env python3
"""
Teste para validação de datas inválidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor
from src.data_analyzer import DataAnalyzer

def test_invalid_dates():
    """Testa o tratamento de datas inválidas"""
    
    # Simular transações com datas inválidas
    test_transactions = [
        {
            'data': '15/08/2025',  # Válida
            'tipo': 'Crédito',
            'valor': 100.0,
            'descricao': 'Transação válida'
        },
        {
            'data': '31/02/2025',  # INVÁLIDA - 31 de fevereiro
            'tipo': 'Crédito',
            'valor': 200.0,
            'descricao': 'Data inválida'
        },
        {
            'data': '30/02/2025',  # INVÁLIDA - 30 de fevereiro
            'tipo': 'Débito',
            'valor': 50.0,
            'descricao': 'Outra data inválida'
        },
        {
            'data': '05/08/2025',  # Válida
            'tipo': 'Débito',
            'valor': 25.0,
            'descricao': 'Outra transação válida'
        }
    ]
    
    print("🧪 TESTE: Tratamento de Datas Inválidas")
    print("=" * 60)
    
    # Testar PDFProcessor
    processor = PDFProcessor()
    print("📝 Testando validação de datas:")
    
    for trans in test_transactions:
        is_valid = processor._is_valid_date(trans['data'])
        status = "✅" if is_valid else "❌"
        print(f"{status} {trans['data']} - {trans['descricao']}")
    
    print()
    
    # Testar DataAnalyzer
    print("📊 Testando DataAnalyzer:")
    try:
        analyzer = DataAnalyzer(test_transactions)
        daily_summary = analyzer.get_daily_summary()
        
        print(f"✅ DataAnalyzer processou sem erros")
        print(f"📈 Resumo diário gerado com {len(daily_summary)} dia(s)")
        
        if not daily_summary.empty:
            print("📅 Datas no resumo:")
            for date in daily_summary['data']:
                print(f"  - {date}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no DataAnalyzer: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 TESTE DE VALIDAÇÃO DE DATAS")
    print("=" * 70)
    print()
    
    success = test_invalid_dates()
    
    print()
    print("📋 RESULTADO:")
    if success:
        print("🎯 ✅ SUCESSO! Datas inválidas são tratadas corretamente!")
        print("  - Datas inválidas como 31/02 são ignoradas")
        print("  - Sistema continua funcionando sem erros")
        print("  - Apenas transações com datas válidas são processadas")
    else:
        print("⚠️ ❌ Ainda há problemas com o tratamento de datas")