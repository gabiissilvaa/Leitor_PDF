#!/usr/bin/env python3
"""
Teste para simular problemas reais de PDFs bancários com múltiplas páginas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

def test_real_multipage_issues():
    """Testa problemas reais que podem ocorrer em PDFs bancários"""
    
    print("🧪 Testando problemas reais de PDFs bancários...")
    
    # Simular página 1 com linha de data incompleta no final
    page1_content = """
BANCO XYZ - EXTRATO DE CONTA CORRENTE
Cliente: João Silva
Conta: 12345-6
Período: 01/07/2025 a 31/07/2025

01/07/2025  PIX RECEBIDO JOSE                          150,00
01/07/2025  TED ENVIADA EMPRESA ABC                     -75,50
02/07/2025  SAQUE CAIXA ELETRÔNICO                     -100,00
02/07/2025  DEPÓSITO EM CONTA                           200,00

03/07/2025  PIX RECEBIDO MARIA                          300,00
03/07/2025  TRANSFERÊNCIA ENVIADA                       -50,00

Continua na próxima página...
"""

    # Simular página 2 que continua sem repetir a data
    page2_content = """
BANCO XYZ - EXTRATO DE CONTA CORRENTE (Continuação)

TED RECEBIDO FORNECEDOR XYZ                           450,00
DOC ENVIADO PAGAMENTO                                -120,00
TRANSFERÊNCIA ENTRE CONTAS                           -200,00
PAGAMENTO CARTÃO DE CRÉDITO                          -80,00

04/07/2025  PIX ENVIADO PEDRO                         -150,00
04/07/2025  SAQUE ATM                                  -50,00
"""

    processor = PDFProcessor(debug_mode=False)
    
    print("\n📄 ANÁLISE PÁGINA 1:")
    print("=" * 60)
    transactions_page1 = processor._extract_structured_data(page1_content, debug_mode=False)
    
    print(f"Transações encontradas na página 1: {len(transactions_page1)}")
    day3_page1 = [t for t in transactions_page1 if t.get('data', '').startswith('03/07')]
    print(f"Dia 3 na página 1: {len(day3_page1)} transações")
    for t in day3_page1:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")
    
    print("\n📄 ANÁLISE PÁGINA 2:")
    print("=" * 60)
    transactions_page2 = processor._extract_structured_data(page2_content, debug_mode=False)
    
    print(f"Transações encontradas na página 2: {len(transactions_page2)}")
    day3_page2 = [t for t in transactions_page2 if t.get('data', '').startswith('03/07')]
    print(f"Dia 3 na página 2: {len(day3_page2)} transações")
    for t in day3_page2:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")
    
    print("\n🔍 PROBLEMA IDENTIFICADO:")
    print("=" * 60)
    print("As transações da página 2 que pertencem ao dia 3 NÃO têm")
    print("data explícita - elas dependem da data da página anterior!")
    
    # Testar com contexto de data carregada da página anterior
    print("\n🔧 TESTANDO SOLUÇÃO COM CONTEXTO:")
    print("=" * 60)
    
    # Modificar o processamento para manter contexto da data
    processor.last_date_context = None
    
    # Processar página 1 e capturar última data
    for t in transactions_page1:
        if t.get('data'):
            processor.last_date_context = t['data']
    
    print(f"Última data da página 1: {processor.last_date_context}")
    
    # Processar página 2 com contexto
    transactions_page2_with_context = processor._parse_with_date_context(page2_content, processor.last_date_context)
    
    day3_page2_fixed = [t for t in transactions_page2_with_context if t.get('data', '').startswith('03/07')]
    print(f"Dia 3 na página 2 (com contexto): {len(day3_page2_fixed)} transações")
    for t in day3_page2_fixed:
        print(f"   - {t.get('data')} | {t.get('descricao')} | R$ {t.get('valor', 0)}")
    
    total_day3 = len(day3_page1) + len(day3_page2_fixed)
    print(f"\n📊 TOTAL DIA 3 (com correção): {total_day3} transações")
    print("✅ Esperado: 6 transações (2 + 4)")

def test_improved_multipage_processor():
    """Testa uma versão melhorada do processador que mantém contexto entre páginas"""
    
    print("\n" + "="*80)
    print("🚀 TESTANDO PROCESSADOR MELHORADO")
    print("="*80)
    
    # Simular conteúdo que se estende por páginas
    pages_content = [
        # Página 1
        """
EXTRATO JULHO 2025

01/07  PIX RECEBIDO                     100,00
01/07  SAQUE                            -50,00
02/07  TED RECEBIDO                     200,00

03/07  PIX RECEBIDO                     150,00
03/07  TRANSFERÊNCIA ENVIADA           -200,00
""",
        # Página 2 - continua dia 3 sem data explícita
        """
TED RECEBIDO                            300,00
DOC ENVIADO                            -400,00
TRANSFERÊNCIA ENTRE CONTAS             -500,00

04/07  PIX ENVIADO                     -250,00
04/07  DEPÓSITO                         300,00
"""
    ]
    
    processor = PDFProcessor(debug_mode=False)
    all_transactions = []
    last_date = None
    
    for page_num, content in enumerate(pages_content, 1):
        print(f"\n📄 PROCESSANDO PÁGINA {page_num}:")
        
        # Extrair transações da página
        page_transactions = processor._extract_structured_data(content, debug_mode=False)
        
        # Aplicar contexto de data se necessário
        fixed_transactions = []
        for transaction in page_transactions:
            if transaction.get('data'):
                last_date = transaction['data']
                fixed_transactions.append(transaction)
            else:
                # Transação sem data - usar última data conhecida
                if last_date:
                    transaction['data'] = last_date
                    transaction['data_inferida'] = True
                    fixed_transactions.append(transaction)
                    print(f"   🔧 Data inferida: {last_date} para '{transaction.get('descricao', '')}'")
        
        all_transactions.extend(fixed_transactions)
        
        day3_this_page = [t for t in fixed_transactions if t.get('data', '').startswith('03/07')]
        print(f"   Dia 3 nesta página: {len(day3_this_page)} transações")
    
    total_day3 = [t for t in all_transactions if t.get('data', '').startswith('03/07')]
    print(f"\n✅ TOTAL FINAL DIA 3: {len(total_day3)} transações")
    print("Todas as transações do dia 3:")
    for t in total_day3:
        inferida = " (inferida)" if t.get('data_inferida') else ""
        print(f"   - {t.get('data')}{inferida} | {t.get('descricao')} | R$ {t.get('valor', 0)}")

if __name__ == "__main__":
    test_real_multipage_issues()
    test_improved_multipage_processor()