@echo off
echo ==================================
echo     INSTALADOR TESSERACT OCR
echo ==================================
echo.
echo Este script criara uma versao portatil do Tesseract
echo ou fornecera instrucoes para instalacao manual.
echo.

:: Verificar se já existe uma instalação
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Tesseract ja instalado em: C:\Program Files\Tesseract-OCR\
    goto :end
)

if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    echo Tesseract ja instalado em: C:\Program Files (x86)\Tesseract-OCR\
    goto :end
)

echo Tesseract nao encontrado no sistema.
echo.
echo OPCOES DE INSTALACAO:
echo.
echo 1. Download Manual:
echo    - Acesse: https://github.com/UB-Mannheim/tesseract/releases
echo    - Baixe: tesseract-ocr-w64-setup-v5.3.3.20231005.exe
echo    - Execute o instalador como Administrador
echo.
echo 2. Chocolatey (se instalado):
echo    choco install tesseract
echo.
echo 3. Winget (Windows 10/11):
echo    winget install --id UB-Mannheim.TesseractOCR
echo.
echo Apos a instalacao, reinicie a aplicacao Streamlit.
echo.

:end
pause