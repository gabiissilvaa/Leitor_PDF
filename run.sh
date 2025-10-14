#!/bin/bash
echo "Instalando dependências..."
pip install -r requirements.txt

echo ""
echo "Iniciando aplicação Streamlit..."
streamlit run app.py