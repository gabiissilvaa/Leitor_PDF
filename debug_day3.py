#!/usr/bin/env python3
"""
Debug específico para linhas do dia 3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

def debug_day3_lines():
    """Debug das linhas específicas do dia 3"""
    
    print("🔍 DEBUG - Análise das linhas do dia 3")
    print("=" * 50)
    
    # Linhas específicas do dia 3
    test_lines = [
        "03/07/2025  PIX RECEBIDO VENDAS                        750,00",
        "03/07/2025  TRANSFERÊNCIA ENVIADA FOLHA               -2.000,00",
        "DOC RECEBIDO CLIENTE B                                1.500,00",
        "PAGAMENTO CARTÃO                                       -300,00",
    ]
    
    processor = PDFProcessor(debug_mode=False)
    
    print("📝 Testando linha por linha:")
    for i, line in enumerate(test_lines, 1):
        print(f"\n{i}. Linha: '{line}'")
        
        # Testar extração de data
        date_extracted = processor._extract_date(line)
        print(f"   Data extraída: {date_extracted}")
        
        # Testar extração de valores
        values = processor._extract_all_values(line)
        print(f"   Valores extraídos: {values}")
        
        # Testar parsing completo
        if date_extracted:
            transaction = processor._parse_transaction_line(line)
            if transaction:
                print(f"   ✅ Transação: {transaction['tipo']} R$ {transaction['valor']}")
            else:
                print(f"   ❌ Não foi possível extrair transação")
        else:
            # Testar com data de contexto
            transaction = processor._parse_transaction_line(line, "03/07/2025")
            if transaction:
                print(f"   ✅ Transação (com contexto): {transaction['tipo']} R$ {transaction['valor']}")
            else:
                print(f"   ❌ Não foi possível extrair transação mesmo com contexto")

def debug_full_page():
    """Debug de página completa"""
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG - Página completa")
    print("=" * 60)
    
    page_text = """03/07/2025  PIX RECEBIDO VENDAS                        750,00
03/07/2025  TRANSFERÊNCIA ENVIADA FOLHA               -2.000,00"""
    
    processor = PDFProcessor(debug_mode=False)
    
    print("Texto da página:")
    print(page_text)
    
    print("\n📊 Processamento completo:")
    transactions = processor._extract_structured_data_with_context(page_text, debug_mode=False)
    
    print(f"Transações encontradas: {len(transactions)}")
    for t in transactions:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor')}")

if __name__ == "__main__":
    debug_day3_lines()
    debug_full_page()