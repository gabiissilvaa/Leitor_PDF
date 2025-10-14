import pdfplumber
import re
import io
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st
import os
import platform

try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    
    # Configurar caminho do Tesseract no Windows
    if platform.system() == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]
        
        tesseract_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tesseract_path = path
                break
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            OCR_AVAILABLE = True
        else:
            OCR_AVAILABLE = False
    else:
        OCR_AVAILABLE = True
        
except ImportError:
    OCR_AVAILABLE = False

class PDFProcessor:
    """Classe responsável por processar PDFs e extrair transações bancárias"""
    
    def __init__(self):
        # Padrões regex para diferentes formatos de data (mais abrangentes)
        self.date_patterns = [
            r'(\d{2})/(\d{2})/(\d{4})',      # DD/MM/YYYY
            r'(\d{2})/(\d{2})/(\d{2})',      # DD/MM/YY
            r'(\d{2})-(\d{2})-(\d{4})',      # DD-MM-YYYY
            r'(\d{2})\.(\d{2})\.(\d{4})',    # DD.MM.YYYY
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # D/M/YYYY ou DD/M/YYYY
            r'(\d{2})\s+(\d{2})\s+(\d{4})',  # DD MM YYYY (com espaços)
            r'(\d{2})(\d{2})(\d{4})',        # DDMMYYYY (sem separadores)
        ]
        
        # Padrões para valores monetários (mais robustos)
        self.value_patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',          # R$ 1.234,56
            r'R\$\s*(\d+,\d{2})',                               # R$ 123,45
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',                     # 1.234,56
            r'(\d+,\d{2})',                                     # 123,45
            r'(\d{1,3}(?:\.\d{3})*\.\d{2})',                    # 1.234.56 (formato americano)
            r'(\d+\.\d{2})',                                    # 123.45 (formato americano)
            r'(\d{1,3}(?:\s\d{3})*,\d{2})',                     # 1 234,56 (com espaços)
        ]
        
        # Palavras-chave para identificar créditos (mais abrangentes)
        self.credit_keywords = [
            'deposito', 'depósito', 'credito', 'crédito', 'entrada',
            'transferencia recebida', 'transferência recebida', 
            'pix recebido', 'ted recebida', 'doc recebido',
            'salario', 'salário', 'rendimento', 'aplicacao', 'aplicação',
            'resgate', 'estorno', 'devolucao', 'devolução',
            'receita', 'recebimento', 'pagamento recebido',
            'deposito em dinheiro', 'credito automatico', 'crédito automático'
        ]
        
        # Palavras-chave para identificar débitos (mais abrangentes)
        self.debit_keywords = [
            'debito', 'débito', 'saida', 'saída', 'saque',
            'transferencia enviada', 'transferência enviada',
            'pix enviado', 'ted enviada', 'doc enviado',
            'pagamento', 'compra', 'tarifa', 'taxa', 'juros',
            'anuidade', 'manutencao', 'manutenção', 'cobranca', 'cobrança',
            'debito automatico', 'débito automático', 'cartao',
            'cartão', 'financiamento', 'emprestimo', 'empréstimo'
        ]
        
        # Padrões de linha de extrato (para identificar linhas com transações)
        self.transaction_line_patterns = [
            r'\d{2}/\d{2}.*\d+[,\.]\d{2}',  # Data seguida de valor
            r'R\$.*\d+[,\.]\d{2}',          # Qualquer linha com R$ e valor
            r'\d+[,\.]\d{2}.*[CD]',         # Valor seguido de C ou D
        ]
    
    def extract_transactions(self, uploaded_file) -> List[Dict[str, Any]]:
        """Extrai transações do arquivo PDF com suporte a OCR para PDFs escaneados"""
        transactions = []
        
        try:
            # Mostrar progresso na interface
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text('📄 Analisando tipo de PDF...')
            progress_bar.progress(5)
            
            # Primeiro, tentar extração normal (texto selecionável)
            text_extracted = False
            total_text_length = 0
            
            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                
                # Testar se há texto selecionável nas primeiras páginas
                for i in range(min(3, total_pages)):
                    page_text = pdf.pages[i].extract_text()
                    if page_text and page_text.strip():
                        total_text_length += len(page_text.strip())
                
                text_extracted = total_text_length > 100  # Pelo menos 100 caracteres
            
            # Decidir método de extração
            if text_extracted:
                st.info("✅ **PDF com texto selecionável detectado** - usando extração direta")
                transactions = self._extract_with_text_method(uploaded_file, progress_bar, status_text)
            else:
                if OCR_AVAILABLE:
                    st.warning("📸 **PDF escaneado/imagem detectado** - usando OCR (mais lento)")
                    transactions = self._extract_with_ocr_method(uploaded_file, progress_bar, status_text)
                else:
                    st.error("❌ **PDF escaneado detectado mas OCR não disponível**")
                    st.markdown("""
                    **Para processar PDFs escaneados, instale as dependências OCR:**
                    ```bash
                    pip install pytesseract Pillow PyMuPDF
                    ```
                    
                    **No Windows, também instale o Tesseract:**
                    1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki
                    2. Instale o executável
                    3. Adicione ao PATH do sistema
                    """)
                    return []
                
        except Exception as e:
            st.error(f"❌ Erro ao processar o PDF: {str(e)}")
            
        return transactions
    
    def _extract_with_text_method(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Método de extração para PDFs com texto selecionável"""
        
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
            
            # Alerta para arquivos grandes
            if total_pages > 50:
                st.warning(f"⚠️ Arquivo grande detectado ({total_pages} páginas). O processamento pode levar alguns minutos...")
            elif total_pages > 20:
                st.info(f"📖 Processando arquivo médio ({total_pages} páginas)...")
            
            status_text.text(f'📖 Processando {total_pages} página(s)...')
            progress_bar.progress(10)
            
            # Processar páginas em lotes
            batch_size = 5
            all_transactions = []
            
            for batch_start in range(0, total_pages, batch_size):
                batch_end = min(batch_start + batch_size, total_pages)
                batch_text = ""
                
                # Processar lote atual
                for page_num in range(batch_start, batch_end):
                    try:
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            batch_text += page_text + "\n"
                    except Exception as e:
                        st.warning(f"⚠️ Erro na página {page_num + 1}: {str(e)}")
                        continue
                    
                    # Atualizar progresso
                    progress = 10 + (page_num + 1) * 70 // total_pages
                    progress_bar.progress(progress)
                    status_text.text(f'📖 Página {page_num + 1}/{total_pages}...')
                
                # Processar transações do lote atual
                if batch_text.strip():
                    batch_transactions = self._parse_transactions_batch(
                        batch_text, 
                        f"Lote {batch_start//batch_size + 1}"
                    )
                    all_transactions.extend(batch_transactions)
                
                # Limpar memória do lote
                del batch_text
            
            status_text.text('🔍 Finalizando análise...')
            progress_bar.progress(90)
            
            # Remover duplicatas e ordenar
            transactions = self._clean_and_sort_transactions(all_transactions)
            
            progress_bar.progress(100)
            status_text.success(f'🎉 Processamento concluído! {len(transactions)} transações encontradas')
            
            return transactions
    
    def _check_ocr_availability(self) -> bool:
        """Verifica se o OCR está disponível e exibe informações de diagnóstico"""
        if not OCR_AVAILABLE:
            st.error("🚫 **OCR (Reconhecimento Óptico) Indisponível**")
            
            # Verificar se pytesseract está instalado
            try:
                import pytesseract
                st.warning("⚡ pytesseract instalado, mas **Tesseract executável não encontrado**")
                
                if platform.system() == 'Windows':
                    st.info("� **Instalação Rápida do Tesseract (Windows):**")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown("""
                        **Método Recomendado:**
                        1. 📥 [Baixar Tesseract OCR](https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe)
                        2. ⚙️ Executar o instalador como **Administrador**
                        3. 🔄 Reiniciar esta aplicação
                        """)
                    
                    with col2:
                        if st.button("📋 Copiar Link", key="copy_tesseract_link"):
                            st.code("https://github.com/UB-Mannheim/tesseract/releases")
                    
                    st.warning("⏱️ **Enquanto isso:** Use apenas PDFs com **texto selecionável** (não escaneados)")
                    
                else:
                    st.info("🐧 **Para Linux/Mac:**")
                    st.code("sudo apt install tesseract-ocr tesseract-ocr-por  # Ubuntu/Debian")
                    st.code("brew install tesseract tesseract-lang  # macOS")
                    
            except ImportError:
                st.error("❌ **pytesseract não instalado**")
                st.code("pip install pytesseract")
                
            return False
        
        # Tesseract disponível - mostrar informação
        st.success("🤖 **OCR Ativo** - Suporte para PDFs escaneados habilitado!")
        return True

    def _extract_with_ocr_method(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Método de extração usando OCR com tratamento robusto de erros MuPDF"""
        
        if not self._check_ocr_availability():
            return []
        
        st.info("🤖 **Inicializando OCR com proteção contra erros MuPDF...**")
        
        # Múltiplas tentativas de abertura do PDF
        doc = None
        uploaded_file.seek(0)
        
        try:
            # Tentativa 1: Abertura padrão
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            st.success("✅ PDF aberto com método padrão")
        except Exception as e1:
            st.warning(f"⚠️ Método padrão falhou: {str(e1)}")
            
            try:
                # Tentativa 2: Forçar como documento
                uploaded_file.seek(0)
                doc = fitz.Document(stream=uploaded_file.read())
                st.success("✅ PDF aberto com método alternativo")
            except Exception as e2:
                st.error(f"❌ Não foi possível abrir o PDF: {str(e2)}")
                return []
        
        total_pages = len(doc)
        
        if total_pages > 20:
            st.warning(f"� **OCR em {total_pages} páginas** - isso pode levar vários minutos...")
        
        status_text.text(f'🖼️ Convertendo {total_pages} página(s) para imagem...')
        progress_bar.progress(10)
        
        all_transactions = []
        
        for page_num in range(total_pages):
            try:
                # Converter página para imagem com proteção contra erros MuPDF
                page = doc.load_page(page_num)
                
                # Múltiplas estratégias para contornar erro XObject
                img_data = None
                
                # Estratégia 1: Tentar com matriz padrão
                try:
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                except Exception as e1:
                    st.warning(f"⚠️ Estratégia 1 falhou página {page_num + 1}: {str(e1)[:50]}")
                    
                    # Estratégia 2: Sem matriz (resolução padrão)
                    try:
                        pix = page.get_pixmap()
                        img_data = pix.tobytes("png")
                    except Exception as e2:
                        st.warning(f"⚠️ Estratégia 2 falhou página {page_num + 1}: {str(e2)[:50]}")
                        
                        # Estratégia 3: Forçar RGB sem alpha
                        try:
                            pix = page.get_pixmap(alpha=False, colorspace=fitz.csRGB)
                            img_data = pix.tobytes("png")
                        except Exception as e3:
                            st.error(f"❌ Todas estratégias falharam página {page_num + 1}")
                            continue
                
                if not img_data:
                    st.error(f"❌ Impossível converter página {page_num + 1}")
                    continue
                
                # Converter para PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Aplicar OCR
                status_text.text(f'🤖 OCR página {page_num + 1}/{total_pages}...')
                
                # Configurar Tesseract para português
                custom_config = r'--oem 3 --psm 6 -l por'
                try:
                    ocr_text = pytesseract.image_to_string(image, config=custom_config)
                except:
                    # Fallback para inglês se português não estiver disponível
                    ocr_text = pytesseract.image_to_string(image)
                
                # Processar texto extraído por OCR
                if ocr_text.strip():
                    batch_transactions = self._parse_transactions_batch(
                        ocr_text, 
                        f"OCR Página {page_num + 1}"
                    )
                    all_transactions.extend(batch_transactions)
                
                # Atualizar progresso
                progress = 10 + (page_num + 1) * 70 // total_pages
                progress_bar.progress(progress)
                
            except Exception as e:
                st.warning(f"⚠️ Erro OCR na página {page_num + 1}: {str(e)}")
                continue
        
        doc.close()
        
        status_text.text('🔍 Finalizando análise OCR...')
        progress_bar.progress(90)
        
        # Remover duplicatas e ordenar
        transactions = self._clean_and_sort_transactions(all_transactions)
        
        progress_bar.progress(100)
        status_text.success(f'🎉 OCR concluído! {len(transactions)} transações encontradas')
        
        # Mostrar estatísticas OCR
        if total_pages > 10:
            st.info(f"🤖 **OCR Statistics:**\n"
                   f"- 📄 {total_pages} páginas processadas com OCR\n"
                   f"- 📋 {len(transactions)} transações extraídas\n"
                   f"- ⚡ Qualidade: {'Alta' if len(transactions) > total_pages else 'Média'}")
        
        return transactions
    
    def _parse_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Analisa o texto e extrai as transações"""
        transactions = []
        lines = text.split('\n')
        
        # Mostrar detalhes do processamento na interface
        st.write("🔍 **Detalhes do Processamento:**")
        
        # Container para mostrar transações encontradas em tempo real
        transaction_container = st.container()
        found_transactions = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Tentar extrair data da linha
            date = self._extract_date(line)
            if date:
                # Procurar informações da transação nas próximas linhas
                transaction_info = self._extract_transaction_info(
                    lines[i:i+5], date  # Analisar até 5 linhas seguintes
                )
                
                if transaction_info:
                    transactions.append(transaction_info)
                    found_transactions.append(transaction_info)
                    
                    # Mostrar transação encontrada na interface
                    with transaction_container:
                        cols = st.columns([2, 3, 1, 1])
                        with cols[0]:
                            st.write(f"📅 {transaction_info['data']}")
                        with cols[1]:
                            st.write(f"📝 {transaction_info['descricao'][:30]}...")
                        with cols[2]:
                            color = "🟢" if transaction_info['tipo'] == 'Crédito' else "🔴"
                            st.write(f"{color} {transaction_info['tipo']}")
                        with cols[3]:
                            st.write(f"💰 R$ {transaction_info['valor']:,.2f}")
        
        # Resumo final
        if transactions:
            st.success(f"✅ **Total de {len(transactions)} transações processadas com sucesso!**")
            
            # Mostrar resumo rápido
            total_credit = sum(t['valor'] for t in transactions if t['tipo'] == 'Crédito')
            total_debit = sum(t['valor'] for t in transactions if t['tipo'] == 'Débito')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💚 Total Créditos", f"R$ {total_credit:,.2f}")
            with col2:
                st.metric("🔴 Total Débitos", f"R$ {total_debit:,.2f}")
            with col3:
                st.metric("⚖️ Saldo Geral", f"R$ {total_credit - total_debit:,.2f}")
        else:
            st.warning("⚠️ Nenhuma transação foi encontrada no arquivo PDF.")
            st.info("💡 **Dicas:**\n- Verifique se o PDF contém dados de extrato bancário\n- Certifique-se de que o arquivo não está protegido por senha\n- Teste com um arquivo diferente")
        
        return transactions
    
    def _parse_transactions_batch(self, text: str, batch_name: str) -> List[Dict[str, Any]]:
        """Processa transações de um lote de páginas com diagnóstico detalhado"""
        transactions = []
        lines = text.split('\n')
        
        # Mostrar diagnóstico do conteúdo
        st.write(f"🔍 **Analisando {batch_name}:**")
        
        # Diagnóstico inicial
        diagnostic_container = st.container()
        with diagnostic_container:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Linhas", len(lines))
            with col2:
                non_empty_lines = len([l for l in lines if l.strip()])
                st.metric("📝 Linhas com conteúdo", non_empty_lines)
            with col3:
                st.metric("🔍 Datas encontradas", 0)  # Será atualizado
        
        # Mostrar amostra do conteúdo extraído
        if lines:
            with st.expander(f"� Amostra do conteúdo extraído ({batch_name})"):
                sample_lines = [line.strip() for line in lines[:20] if line.strip()]
                if sample_lines:
                    for i, line in enumerate(sample_lines):
                        st.text(f"{i+1:2d}: {line}")
                else:
                    st.warning("❌ Nenhum texto legível encontrado neste lote")
        
        # Contadores para diagnóstico
        dates_found = 0
        values_found = 0
        potential_transactions = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Debug: verificar se encontra datas
            date = self._extract_date(line)
            if date:
                dates_found += 1
                st.write(f"📅 **Data encontrada:** {date} na linha: `{line}`")
                
                # Procurar informações da transação nas próximas linhas
                context_lines = lines[i:i+5]
                transaction_info = self._extract_transaction_info(context_lines, date)
                
                if transaction_info:
                    transactions.append(transaction_info)
                    potential_transactions += 1
                    
                    # Mostrar transação encontrada
                    st.success(f"✅ **Transação {potential_transactions}:**\n"
                              f"📅 Data: {transaction_info['data']}\n"
                              f"📝 Descrição: {transaction_info['descricao']}\n"
                              f"💰 Valor: R$ {transaction_info['valor']:,.2f}\n"
                              f"🏷️ Tipo: {transaction_info['tipo']}")
                else:
                    st.warning(f"⚠️ Data encontrada mas sem informações de transação:\n"
                              f"Contexto: {' | '.join(context_lines)}")
            else:
                # Debug: verificar se há valores monetários na linha
                if self._extract_value(line) > 0:
                    values_found += 1
                    if values_found <= 5:  # Mostrar apenas os primeiros 5
                        st.info(f"💰 **Valor encontrado sem data:** R$ {self._extract_value(line):,.2f} na linha: `{line}`")
        
        # Atualizar métricas de diagnóstico
        with diagnostic_container:
            col1, col2, col3 = st.columns(3)
            with col3:
                st.metric("🔍 Datas encontradas", dates_found)
        
        # Resumo do diagnóstico
        if dates_found == 0:
            st.error("❌ **Problema identificado: Nenhuma data encontrada!**")
            st.markdown("""
            **Possíveis causas:**
            - Formato de data não reconhecido
            - PDF pode ser uma imagem escaneada
            - Texto não está em formato selecionável
            
            **Formatos de data suportados:**
            - DD/MM/AAAA (ex: 15/10/2024)
            - DD/MM/AA (ex: 15/10/24)  
            - DD-MM-AAAA (ex: 15-10-2024)
            - DD.MM.AAAA (ex: 15.10.2024)
            """)
            
            # Tentar método alternativo
            st.write("🔄 **Executando diagnóstico avançado...**")
            alternative_results = self._alternative_extraction(text)
            
        elif values_found == 0:
            st.error("❌ **Problema identificado: Nenhum valor monetário encontrado!**")
            st.markdown("""
            **Possíveis causas:**
            - Formato de valor não reconhecido
            - Valores podem estar em formato diferente
            
            **Formatos de valor suportados:**
            - R$ 1.234,56
            - 1.234,56
            - 123,45
            """)
            
            # Tentar método alternativo
            st.write("🔄 **Executando diagnóstico avançado...**")
            alternative_results = self._alternative_extraction(text)
            
        elif transactions:
            st.success(f"✅ **{len(transactions)} transações extraídas com sucesso neste lote!**")
        else:
            st.warning("⚠️ **Datas e valores encontrados, mas não foi possível formar transações completas**")
            
            # Tentar método alternativo
            st.write("🔄 **Executando diagnóstico avançado...**")
            alternative_results = self._alternative_extraction(text)
        
        return transactions
    
    def _alternative_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Método alternativo de extração usando diferentes abordagens"""
        transactions = []
        
        st.write("🔄 **Tentando métodos alternativos de extração...**")
        
        # Método 1: Buscar por linhas que parecem transações
        lines = text.split('\n')
        potential_transaction_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Verificar se a linha contém padrões de transação
            for pattern in self.transaction_line_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    potential_transaction_lines.append(line)
                    break
        
        st.info(f"📋 **Método 1:** Encontradas {len(potential_transaction_lines)} linhas com padrão de transação")
        
        if potential_transaction_lines:
            with st.expander("🔍 Linhas identificadas como possíveis transações"):
                for i, line in enumerate(potential_transaction_lines[:10]):
                    st.text(f"{i+1}: {line}")
        
        # Método 2: Buscar por qualquer sequência de data + texto + valor
        st.write("🔄 **Método 2:** Busca por padrões data-texto-valor")
        
        date_value_pairs = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Buscar data na linha
            date = self._extract_date(line)
            value = self._extract_value(line)
            
            if date and value > 0:
                date_value_pairs.append({
                    'linha': line,
                    'data': date,
                    'valor': value
                })
        
        st.info(f"💰 **Método 2:** Encontrados {len(date_value_pairs)} pares data-valor")
        
        if date_value_pairs:
            with st.expander("📊 Pares data-valor encontrados"):
                for pair in date_value_pairs[:10]:
                    st.text(f"📅 {pair['data']} - 💰 R$ {pair['valor']:,.2f} - {pair['linha']}")
        
        # Método 3: Análise de padrões por banco específico
        st.write("🔄 **Método 3:** Detectar formato de banco específico")
        
        # Detectar possível banco baseado em palavras-chave
        bank_patterns = {
            'Banco do Brasil': ['banco do brasil', 'bb ', 'conta corrente bb'],
            'Caixa': ['caixa economica', 'cef', 'caixa federal'],
            'Itaú': ['itau', 'itaú', 'banco itau'],
            'Bradesco': ['bradesco', 'banco bradesco'],
            'Santander': ['santander', 'banco santander'],
            'Nubank': ['nubank', 'nu pagamentos']
        }
        
        detected_bank = None
        text_lower = text.lower()
        
        for bank_name, keywords in bank_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_bank = bank_name
                break
        
        if detected_bank:
            st.success(f"🏦 **Banco detectado:** {detected_bank}")
        else:
            st.info("🏦 **Banco não identificado** - usando padrões genéricos")
        
        return transactions
    
    def _clean_and_sort_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas e ordena transações por data"""
        if not transactions:
            return []
        
        # Remover duplicatas baseado em data, valor e descrição
        unique_transactions = []
        seen = set()
        
        for transaction in transactions:
            key = (
                transaction['data'], 
                transaction['valor'], 
                transaction['descricao'][:20]  # Usar apenas parte da descrição
            )
            
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
        
        # Ordenar por data
        try:
            unique_transactions.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))
        except ValueError:
            # Se falhar, manter ordem original
            pass
        
        return unique_transactions
    
    def _extract_date(self, text: str) -> str:
        """Extrai data do texto"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                day, month, year = match.groups()
                
                # Ajustar ano se necessário (YY -> YYYY)
                if len(year) == 2:
                    current_year = datetime.now().year
                    year_int = int(year)
                    if year_int <= (current_year % 100):
                        year = f"20{year}"
                    else:
                        year = f"19{year}"
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def _extract_value(self, text: str) -> float:
        """Extrai valor monetário do texto com melhor tratamento"""
        found_values = []
        
        for pattern in self.value_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Limpar e normalizar o valor
                        clean_value = str(match).strip()
                        
                        # Remover caracteres não numéricos exceto vírgula e ponto
                        clean_value = re.sub(r'[^\d,.]', '', clean_value)
                        
                        # Tratar diferentes formatos
                        if ',' in clean_value and '.' in clean_value:
                            # Formato brasileiro: 1.234,56
                            if clean_value.rfind(',') > clean_value.rfind('.'):
                                clean_value = clean_value.replace('.', '').replace(',', '.')
                            # Formato americano: 1,234.56  
                            else:
                                clean_value = clean_value.replace(',', '')
                        elif ',' in clean_value:
                            # Apenas vírgula: assumir formato brasileiro
                            clean_value = clean_value.replace(',', '.')
                        
                        # Converter para float
                        value = float(clean_value)
                        if value > 0:  # Apenas valores positivos
                            found_values.append(value)
                            
                    except (ValueError, TypeError):
                        continue
        
        # Retornar o maior valor encontrado (mais provável de ser a transação principal)
        return max(found_values) if found_values else 0.0
    
    def _determine_transaction_type(self, text: str) -> str:
        """Determina se a transação é crédito ou débito"""
        text_lower = text.lower()
        
        # Verificar palavras-chave de crédito
        for keyword in self.credit_keywords:
            if keyword in text_lower:
                return 'Crédito'
        
        # Verificar palavras-chave de débito
        for keyword in self.debit_keywords:
            if keyword in text_lower:
                return 'Débito'
        
        # Verificar sinais específicos
        if any(sign in text for sign in ['+', 'C']):
            return 'Crédito'
        elif any(sign in text for sign in ['-', 'D']):
            return 'Débito'
        
        # Padrão: se não identificado, assumir débito
        return 'Débito'
    
    def _extract_description(self, lines: List[str]) -> str:
        """Extrai descrição da transação"""
        description_parts = []
        
        for line in lines:
            line = line.strip()
            if line and not re.search(r'\d{2}/\d{2}/\d{4}', line):
                # Remover valores monetários da descrição
                clean_line = re.sub(r'R\$\s*\d+[.,]\d+', '', line)
                clean_line = re.sub(r'\d+[.,]\d+', '', clean_line)
                clean_line = clean_line.strip()
                
                if clean_line and len(clean_line) > 3:
                    description_parts.append(clean_line)
        
        return ' '.join(description_parts[:3])  # Limitar a 3 partes
    
    def _extract_transaction_info(self, lines: List[str], date: str) -> Dict[str, Any]:
        """Extrai informações completas da transação"""
        combined_text = ' '.join(lines)
        
        # Extrair valor
        value = self._extract_value(combined_text)
        if value == 0.0:
            return None
        
        # Determinar tipo
        transaction_type = self._determine_transaction_type(combined_text)
        
        # Extrair descrição
        description = self._extract_description(lines[1:])  # Pular a primeira linha (data)
        
        return {
            'data': date,
            'descricao': description or 'Transação não identificada',
            'tipo': transaction_type,
            'valor': value
        }