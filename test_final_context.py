#!/usr/bin/env python3
"""
Teste final para verificar se o contexto de data entre páginas está funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

def test_final_multipage_context():
    """Teste final do contexto entre páginas"""
    
    print("🎯 TESTE FINAL - Contexto de data entre páginas")
    print("=" * 70)
    
    # Simular extrato real onde dia 3 se estende por duas páginas
    page1_text = """
EXTRATO BANCÁRIO EMPRESA XYZ
Período: 01/07/2025 a 31/07/2025
Agência: 1234   Conta: 567890-1

01/07/2025  PIX RECEBIDO CLIENTE A                      500,00
01/07/2025  TAXA MANUTENÇÃO                            -15,00
02/07/2025  TED RECEBIDO FORNECEDOR                   1.200,00
02/07/2025  PAGAMENTO BOLETO                           -800,00

03/07/2025  PIX RECEBIDO VENDAS                        750,00
03/07/2025  TRANSFERÊNCIA ENVIADA FOLHA               -2.000,00

--- Página 1 de 2 ---
"""

    page2_text = """
EXTRATO BANCÁRIO EMPRESA XYZ (continuação)

DOC RECEBIDO CLIENTE B                                1.500,00
PAGAMENTO CARTÃO                                       -300,00
TRANSFERÊNCIA ENTRE CONTAS                             -800,00
TED ENVIADO FORNECEDOR                               -1.200,00

04/07/2025  PIX ENVIADO FUNCIONÁRIO                    -400,00
04/07/2025  DEPÓSITO EM DINHEIRO                      2.000,00
05/07/2025  SAQUE CAIXA ELETRÔNICO                     -100,00
"""

    processor = PDFProcessor(debug_mode=False)
    
    print("📄 Processando Página 1:")
    transactions_p1 = processor._extract_structured_data_with_context(page1_text, debug_mode=False)
    
    day3_p1 = [t for t in transactions_p1 if '03/07' in t.get('data', '')]
    print(f"   Transações do dia 3: {len(day3_p1)}")
    for t in day3_p1:
        print(f"   ✅ {t['data']} | {t['descricao'][:40]}... | R$ {t['valor']}")
    
    print(f"   Último contexto de data: {processor.last_date_context}")
    
    print("\n📄 Processando Página 2 (com contexto):")
    transactions_p2 = processor._extract_structured_data_with_context(page2_text, debug_mode=False)
    
    day3_p2 = [t for t in transactions_p2 if '03/07' in t.get('data', '')]
    print(f"   Transações do dia 3: {len(day3_p2)}")
    for t in day3_p2:
        print(f"   ✅ {t['data']} | {t['descricao'][:40]}... | R$ {t['valor']}")
    
    total_day3 = len(day3_p1) + len(day3_p2)
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Total dia 3: {total_day3} transações")
    print(f"   Página 1: {len(day3_p1)} transações")  
    print(f"   Página 2: {len(day3_p2)} transações")
    
    if total_day3 == 6:  # 2 da página 1 + 4 da página 2
        print("   ✅ SUCESSO: Todas as transações do dia 3 capturadas!")
    else:
        print("   ❌ PROBLEMA: Algumas transações não foram capturadas!")
    
    print(f"\n   Esperado: 6 transações (2 explícitas + 4 por contexto)")
    print(f"   Obtido: {total_day3} transações")

if __name__ == "__main__":
    test_final_multipage_context()