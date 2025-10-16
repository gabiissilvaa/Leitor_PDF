#!/usr/bin/env python3
"""
Script de teste para verificar a funcionalidade da aplicação expandida
"""

import sys
import os

# Adicionar o diretório src ao path para importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_bank_factory():
    """Testa o BankProcessorFactory"""
    print("🧪 Testando BankProcessorFactory...")
    
    try:
        from src.banks import BankProcessorFactory
        
        # Testar bancos disponíveis
        available_banks = BankProcessorFactory.get_available_banks()
        print(f"✅ Bancos disponíveis: {list(available_banks.keys())}")
        
        # Testar criação do processador Santander
        santander_processor = BankProcessorFactory.create_processor('santander', debug_mode=True)
        print(f"✅ Processador Santander criado: {santander_processor.bank_name}")
        
        # Testar detecção de banco
        sample_text = "BANCO SANTANDER BRASIL S.A. Extrato de Conta Corrente"
        detected_bank = BankProcessorFactory.detect_bank_from_text(sample_text)
        print(f"✅ Banco detectado: {detected_bank}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do BankProcessorFactory: {str(e)}")
        return False

def test_santander_processor():
    """Testa o processador específico do Santander"""
    print("\n🧪 Testando SantanderProcessor...")
    
    try:
        from src.banks import SantanderProcessor
        
        processor = SantanderProcessor(debug_mode=True)
        
        # Testar extração de data
        test_lines = [
            "01/07/2025 PIX TRANSFERENCIA ENVIADA 150,00",
            "02/07/2025 PAGAMENTO DEBITO AUTOMATICO 1.200,50",
            "03/07 CREDITO SALARIO 3.500,00"
        ]
        
        for line in test_lines:
            date = processor.extract_date_from_line(line)
            transaction_type = processor.classify_transaction_type(line)
            values = processor.extract_all_values(line)
            
            print(f"   Linha: {line}")
            print(f"   📅 Data: {date}")
            print(f"   💰 Tipo: {transaction_type}")
            print(f"   💵 Valores: {values}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do SantanderProcessor: {str(e)}")
        return False

def test_multibank_processor():
    """Testa o processador multibank"""
    print("\n🧪 Testando MultibankPDFProcessor...")
    
    try:
        from src.multibank_pdf_processor import MultibankPDFProcessor
        
        # Testar inicialização
        processor = MultibankPDFProcessor(bank_id='santander', debug_mode=True)
        print(f"✅ Processador multibank criado para: {processor.bank_processor.bank_name}")
        
        # Testar obtenção de bancos suportados
        supported_banks = processor.get_supported_banks()
        print(f"✅ Bancos suportados: {list(supported_banks.keys())}")
        
        # Testar detecção automática
        sample_text = "SANTANDER BRASIL S.A. movimentação da conta"
        detected_bank = processor.auto_detect_bank(sample_text)
        print(f"✅ Detecção automática: {detected_bank}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do MultibankPDFProcessor: {str(e)}")
        return False

def test_imports():
    """Testa se todos os imports estão funcionando"""
    print("\n🧪 Testando imports...")
    
    try:
        # Testar imports principais
        from src.banks import BaseBankProcessor, SantanderProcessor, BankProcessorFactory
        from src.multibank_pdf_processor import MultibankPDFProcessor
        
        print("✅ Todos os imports principais funcionaram")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports: {str(e)}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes da aplicação expandida...\n")
    
    tests = [
        test_imports,
        test_bank_factory,
        test_santander_processor,
        test_multibank_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 50)
    
    print(f"\n📊 Resultado dos testes: {passed}/{total} passou")
    
    if passed == total:
        print("🎉 ✅ Todos os testes passaram! A aplicação está pronta.")
        print("\n💡 Para usar a aplicação:")
        print("   streamlit run app.py")
    else:
        print("⚠️ ❌ Alguns testes falharam. Verifique os erros acima.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())