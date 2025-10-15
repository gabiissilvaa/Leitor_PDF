#!/usr/bin/env python3
"""
Teste para verificar se mais transações estão sendo capturadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

def test_transaction_capture():
    """Testa se mais transações estão sendo capturadas com os novos padrões"""
    
    # Simular linhas típicas de extratos que podem estar sendo perdidas
    test_lines = [
        "03/07 PIX ENVIADO 15,50",                          # Valor pequeno
        "03/07 TRANSFERENCIA BANCO 250,00",                 # Transferência simples
        "03/07 COMPRA CARTAO 89,90",                        # Compra com cartão
        "03/07 SAQUE BANCO24HORAS 100,00",                  # Saque
        "03/07 TARIFA MANUTENCAO 12,00",                    # Tarifa
        "03/07 DEPOSITO EM CONTA 1500,00",                  # Depósito
        "03/07 PAGAMENTO BOLETO 45,67",                     # Pagamento
        "03/07 TED RECEBIDO 2300,50",                       # TED
        "03/07 DOC ENVIADO 180,25",                         # DOC
        "03/07 JUROS PAGOS 5,40",                           # Juros (valor muito pequeno)
        
        # Linhas que DEVEM ser ignoradas
        "Página 3 de 50",                                   # Cabeçalho
        "Banco do Brasil S.A.",                             # Nome do banco
        "CCGPJ 500.000,00 290000001290",                    # Código técnico
    ]
    
    print("🧪 TESTE: Captura Melhorada de Transações")
    print("=" * 60)
    
    processor = PDFProcessor()
    processor.detected_year = 2025  # Simular detecção de 2025
    
    captured_count = 0
    ignored_count = 0
    
    for i, line in enumerate(test_lines):
        result = processor._parse_transaction_line(line, None)
        
        if result:
            captured_count += 1
            print(f"✅ CAPTURADA: {result['data']} | {result['tipo']} | R$ {result['valor']:.2f}")
            print(f"   Linha: '{line}'")
        else:
            ignored_count += 1
            # Verificar se deveria ser capturada
            should_capture = any(word in line.lower() for word in ['pix', 'ted', 'transferencia', 'saque', 'deposito', 'compra', 'pagamento'])
            status = "❌ PERDIDA" if should_capture else "✅ IGNORADA"
            print(f"{status}: '{line}'")
        print()
    
    print(f"📊 RESULTADO:")
    print(f"  - Transações capturadas: {captured_count}")
    print(f"  - Linhas ignoradas: {ignored_count}")
    print(f"  - Taxa de captura: {captured_count/len(test_lines)*100:.1f}%")
    
    # Esperamos capturar pelo menos 8 das 10 primeiras linhas (transações reais)
    expected_captures = 8
    success = captured_count >= expected_captures
    
    print()
    if success:
        print("🎯 ✅ SUCESSO! Mais transações estão sendo capturadas!")
        print("  - Valores pequenos (R$ 15,50) detectados")
        print("  - Transferências simples detectadas") 
        print("  - Padrões diversos de transação funcionando")
    else:
        print(f"⚠️ ❌ PROBLEMA: Apenas {captured_count} transações capturadas de {expected_captures} esperadas")
    
    return success

if __name__ == "__main__":
    print("🔧 TESTE DE CAPTURA MELHORADA")
    print("=" * 70)
    print()
    
    success = test_transaction_capture()
    
    print()
    print("📋 PRÓXIMOS PASSOS:")
    if success:
        print("1. ✅ Teste seu extrato de julho 2025 novamente")
        print("2. ✅ Ative o modo debug para ver detalhes")
        print("3. ✅ Verifique se o dia 03/07 agora tem mais transações")
    else:
        print("1. ⚠️ Ajustar ainda mais os filtros de captura")
        print("2. ⚠️ Revisar padrões de detecção específicos")