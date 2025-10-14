# Script para instalar Tesseract OCR no Windows

Write-Host "Baixando Tesseract OCR..." -ForegroundColor Yellow

# URLs alternativos para download
$urls = @(
    "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe",
    "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
)

$downloaded = $false
foreach ($url in $urls) {
    try {
        Write-Host "Tentando baixar de: $url" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $url -OutFile "tesseract-installer.exe" -TimeoutSec 30
        $downloaded = $true
        break
    }
    catch {
        Write-Host "Falha: $($_.Exception.Message)" -ForegroundColor Red
        continue
    }
}

if ($downloaded) {
    Write-Host "Download concluido!" -ForegroundColor Green
    Write-Host "Executando instalador..." -ForegroundColor Yellow
    
    # Executar instalador silenciosamente
    Start-Process -FilePath "tesseract-installer.exe" -ArgumentList "/S" -Wait
    
    Write-Host "Instalacao concluida!" -ForegroundColor Green
    
    # Adicionar ao PATH se necessário
    $tesseractPath = "C:\Program Files\Tesseract-OCR"
    if (Test-Path $tesseractPath) {
        $env:PATH += ";$tesseractPath"
        Write-Host "Tesseract adicionado ao PATH temporariamente" -ForegroundColor Green
        
        # Testar instalação
        try {
            & "$tesseractPath\tesseract.exe" --version
            Write-Host "Tesseract instalado com sucesso!" -ForegroundColor Green
        }
        catch {
            Write-Host "Tesseract instalado mas nao funcionando corretamente" -ForegroundColor Yellow
        }
    }
    
    # Limpar arquivo temporário
    Remove-Item "tesseract-installer.exe" -ErrorAction SilentlyContinue
    
} else {
    Write-Host "Nao foi possivel baixar o Tesseract" -ForegroundColor Red
    Write-Host "Instrucoes manuais:" -ForegroundColor Cyan
    Write-Host "1. Baixe de: https://github.com/UB-Mannheim/tesseract/releases"
    Write-Host "2. Instale o arquivo .exe"
    Write-Host "3. Adicione C:\Program Files\Tesseract-OCR ao PATH do sistema"
}