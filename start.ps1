# Iniciar Leitor de PDF
Write-Host "Iniciando Leitor de PDF - Extrato Bancario..." -ForegroundColor Green

# Verificar Python
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python nao encontrado. Instale o Python primeiro." -ForegroundColor Red
    pause
    exit 1
}

# Instalar dependências se necessário
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

# Iniciar aplicação
Write-Host "Iniciando aplicacao..." -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
streamlit run app.py