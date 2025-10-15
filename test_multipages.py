#!/usr/bin/env python3
"""
Teste para verificar processamento de transações que se estendem por múltiplas páginas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

def test_multipage_transactions():
    """Testa processamento de transações distribuídas em múltiplas páginas"""
    
    print("🧪 Testando processamento de múltiplas páginas...")
    
    # Simular conteúdo de duas páginas onde o dia 3 se estende entre elas
    page1_content = """
EXTRATO BANCÁRIO - JULHO 2025
Período: 01/07/2025 a 31/07/2025

Data        Descrição                           Valor
01/07       PIX RECEBIDO                        100,00
01/07       TRANSFERÊNCIA ENVIADA               50,00
02/07       TED RECEBIDO                        200,00
02/07       SAQUE                               75,00

03/07       PIX RECEBIDO                        150,00
03/07       TRANSFERÊNCIA ENVIADA               200,00

------- FIM DA PÁGINA 1 -------
"""

    page2_content = """
EXTRATO BANCÁRIO - JULHO 2025 (continuação)

03/07       TED RECEBIDO                        300,00
03/07       DOC ENVIADO                         400,00
03/07       TRANSFERÊNCIA ENTRE CONTAS          500,00
03/07       PAGAMENTO                           600,00

04/07       PIX ENVIADO                         250,00
04/07       DEPÓSITO                            300,00
"""
    
    processor = PDFProcessor(debug_mode=False)
    
    print("\n📄 PÁGINA 1:")
    print("=" * 50)
    transactions_page1 = processor._extract_structured_data(page1_content, debug_mode=False)
    
    print(f"\n✅ Página 1 - Transações encontradas: {len(transactions_page1)}")
    day3_page1 = [t for t in transactions_page1 if t.get('data', '').startswith('03/07')]
    print(f"📅 Dia 3 (Página 1): {len(day3_page1)} transações")
    for t in day3_page1:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")
    
    print("\n📄 PÁGINA 2:")
    print("=" * 50)
    transactions_page2 = processor._extract_structured_data(page2_content, debug_mode=False)
    
    print(f"\n✅ Página 2 - Transações encontradas: {len(transactions_page2)}")
    day3_page2 = [t for t in transactions_page2 if t.get('data', '').startswith('03/07')]
    print(f"📅 Dia 3 (Página 2): {len(day3_page2)} transações")
    for t in day3_page2:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")
    
    # Simular combinação como faria o processador
    all_transactions = transactions_page1 + transactions_page2
    total_day3 = [t for t in all_transactions if t.get('data', '').startswith('03/07')]
    
    print(f"\n📊 RESUMO TOTAL:")
    print("=" * 50)
    print(f"Total de transações: {len(all_transactions)}")
    print(f"Total dia 3: {len(total_day3)} transações")
    print(f"Esperado dia 3: 6 transações (2 na página 1 + 4 na página 2)")
    
    if len(total_day3) == 6:
        print("✅ SUCESSO: Todas as transações do dia 3 foram capturadas!")
    else:
        print("❌ PROBLEMA: Algumas transações do dia 3 foram perdidas!")
        print("\nTransações do dia 3 encontradas:")
        for t in total_day3:
            print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")

if __name__ == "__main__":
    test_multipage_transactions()