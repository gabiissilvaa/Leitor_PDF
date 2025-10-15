#!/usr/bin/env python3
"""
Teste para verificar se todas as transferências do dia 3 são captadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor

# Simulação de linhas de extrato do dia 03/07/2025
lines = [
    "03/07 PIX RECEBIDO 150,00",
    "03/07 TRANSFERÊNCIA ENVIADA 200,00",
    "03/07 TED RECEBIDO 300,00",
    "03/07 DOC ENVIADO 400,00",
    "03/07 TRANSFERÊNCIA ENTRE CONTAS 500,00",
    "03/07 PAGAMENTO 600,00",
    "03/07 SAQUE 700,00",
    "03/07 DEPÓSITO 800,00",
    "03/07 PIX ENVIADO 900,00",
    "03/07 TRANSFERÊNCIA NÃO IDENTIFICADA 1000,00",
    # Linhas que não são transferências
    "03/07 TARIFA MENSALIDADE 10,00",
    "03/07 JUROS 5,00",
]

def test_transfers_day_3():
    processor = PDFProcessor(debug_mode=True)
    results = []
    for line in lines:
        result = processor._parse_transaction_line(line, "03/07/2025")
        if result:
            results.append(result)
            print(f"✅ Capturada: {result['data']} | {result['descricao']} | R$ {result['valor']}")
        else:
            print(f"❌ Ignorada: {line}")
    print(f"\nTotal de transferências captadas: {len(results)} de {len(lines)} linhas")
    print("\nResumo das transferências captadas no dia 3:")
    for r in results:
        print(f"- {r['descricao']} | R$ {r['valor']}")

if __name__ == "__main__":
    test_transfers_day_3()