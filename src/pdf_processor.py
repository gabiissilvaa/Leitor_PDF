import pdfplumber
import re
import io
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st
import os

try:
    import fitz  # PyMuPDF para PDFs complexos
    from PIL import Image
    PDF_ADVANCED_AVAILABLE = True
except ImportError:
    PDF_ADVANCED_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

class PDFProcessor:
    """Classe responsável por processar PDFs e extrair transações bancárias"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.detected_year = None  # Ano detectado
        self.last_date_context = None  # Última data processada (para contexto entre páginas)
        # Padrões regex para diferentes formatos de data (melhorados para extratos bancários)
        self.date_patterns = [
            # Padrões prioritários - mais específicos para extratos
            r'^(\d{2})/(\d{2})/(\d{4})',            # DD/MM/YYYY no início da linha
            r'^(\d{2})/(\d{2})/(\d{2})',            # DD/MM/YY no início da linha
            r'^(\d{1,2})/(\d{1,2})/(\d{4})',        # D/M/YYYY no início da linha
            r'^(\d{2})/(\d{2})\s',                  # DD/MM seguido de espaço no início
            r'^(\d{1,2})/(\d{1,2})\s',              # D/M seguido de espaço no início
            
            # Padrões contextuais - com palavras ao redor
            r'data[:\s]+(\d{2})/(\d{2})/(\d{4})',   # "Data: 01/07/2025"
            r'em[:\s]+(\d{2})/(\d{2})/(\d{4})',     # "Em: 01/07/2025"
            
            # Padrões gerais (menor prioridade)
            r'(\d{2})/(\d{2})/(\d{4})',             # DD/MM/YYYY (geral)
            r'(\d{2})/(\d{2})/(\d{2})',             # DD/MM/YY (geral)
            r'(\d{1,2})/(\d{1,2})/(\d{4})',         # D/M/YYYY (geral)
            r'(\d{2})/(\d{2})\b',                   # DD/MM (geral)
            r'(\d{1,2})/(\d{1,2})\b',               # D/M (geral)
        ]
        
        # Padrões para valores monetários (mais abrangentes para capturar mais transações)
        self.value_patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',               # R$ 1.000,00 (obrigatório 2 decimais)
            r'(\d{1,3}(?:\.\d{3})*,\d{2})(?!\d)',               # 1.000,00 (obrigatório 2 decimais, não seguido de dígito)
            r'(\d{4,},\d{2})(?!\d)',                            # 491511,00 (valores grandes, não seguido de dígito)
            r'R\$\s*(\d+,\d{2})',                               # R$ 123,45 (formato simples)
            r'(\d+,\d{2})(?=\s|$)',                             # 123,45 (no final da linha ou seguido de espaço)
        ]
        
        # Palavras-chave para identificar tipos de transação
        self.credit_keywords = [
            'crédito', 'credito', 'entrada', 'depósito', 'deposito', 
            'transferência recebida', 'pix recebido', 'ted recebida',
            'doc recebido', 'salário', 'salario', 'rendimento'
        ]
        
        self.debit_keywords = [
            'débito', 'debito', 'saída', 'saque', 'pagamento',
            'transferência enviada', 'pix enviado', 'ted enviada',
            'doc enviado', 'compra', 'taxa', 'tarifa'
        ]

    def _detect_statement_year(self, text: str) -> int:
        """Detecta automaticamente o ano do extrato baseado em múltiplas estratégias"""
        
        current_year = datetime.now().year
        
        # Estratégia 1: Procurar por padrões específicos de cabeçalho de extrato
        header_patterns = [
            r'extrato.*?(\d{4})',                       # "Extrato ... 2025"
            r'período.*?(\d{1,2}/\d{1,2}/(\d{4}))',     # "Período: 01/07/2025"
            r'movimentação.*?(\d{4})',                  # "Movimentação 2025"
            r'julho.*?(\d{4})',                         # "Julho 2025"
            r'(\d{4}).*?julho',                         # "2025 Julho"
            r'(\d{4})\s*-\s*\d{1,2}',                   # "2025 - 07" (formato comum)
            r'(\d{1,2}/\d{1,2}/(\d{4}))\s*a\s*\d{1,2}/\d{1,2}/\d{4}',  # "01/07/2025 a 31/07/2025"
        ]
        
        # Tentar encontrar ano em cabeçalhos primeiro (mais confiável)
        for pattern in header_patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    # Se match é tupla, pegar o último elemento (ano)
                    year_candidate = match[-1] if isinstance(match, tuple) else match
                    year_int = int(year_candidate)
                    if 2020 <= year_int <= current_year + 1:
                        return year_int
                except (ValueError, IndexError):
                    continue
        
        # Estratégia 2: Analisar padrão de datas no documento
        # Procurar por datas completas e contar frequência de anos
        full_date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        date_matches = re.findall(full_date_pattern, text)
        
        year_frequency = {}
        recent_years_bonus = {}
        
        for day, month, year in date_matches:
            try:
                day_int, month_int, year_int = int(day), int(month), int(year)
                
                # Validar se é uma data real
                if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 2020 <= year_int <= current_year + 1:
                    year_frequency[year_int] = year_frequency.get(year_int, 0) + 1
                    
                    # Dar bônus para anos mais recentes (mais provável de ser o ano correto)
                    if year_int >= current_year - 1:
                        recent_years_bonus[year_int] = recent_years_bonus.get(year_int, 0) + 2
                        
            except ValueError:
                continue
        
        # Combinar frequência normal com bônus para anos recentes
        for year, bonus in recent_years_bonus.items():
            year_frequency[year] = year_frequency.get(year, 0) + bonus
        
        if year_frequency:
            # Pegar o ano com maior frequência (incluindo bônus)
            most_likely_year = max(year_frequency.items(), key=lambda x: x[1])[0]
            return most_likely_year
        
        # Estratégia 3: Se nada funcionou, assumir ano atual
        return current_year

    def extract_transactions(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Extrai transações do arquivo PDF usando múltiplas estratégias"""
        
        st.info("🔍 **Iniciando análise do PDF...**")
        
        # Resetar posição do arquivo
        uploaded_file.seek(0)
        
        # NOVO: Detectar o ano do extrato primeiro
        current_year = datetime.now().year
        try:
            # Ler uma amostra do PDF para detectar o ano
            with pdfplumber.open(uploaded_file) as pdf:
                sample_text = ""
                # Ler as primeiras 3 páginas para detectar o ano
                for page_num in range(min(3, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        sample_text += page_text[:2000]  # Primeiros 2000 caracteres de cada página
                
                # Detectar o ano do extrato
                self.detected_year = self._detect_statement_year(sample_text)
                
                # CORREÇÃO: Se detectou muitos anos antigos (como 2015), forçar ano atual
                # Isso acontece quando há muito texto informativo com datas antigas
                if self.detected_year < 2024:
                    st.warning(f"⚠️ Ano {self.detected_year} detectado parece muito antigo. Forçando para {current_year}.")
                    self.detected_year = current_year
                
                st.info(f"📅 **Ano detectado do extrato:** {self.detected_year}")
                
        except Exception as e:
            st.warning(f"⚠️ Erro na detecção do ano: {str(e)}")
            self.detected_year = datetime.now().year
        
        # Resetar posição após a detecção
        uploaded_file.seek(0)
        
        # Estratégia 1: Tentar com pdfplumber (mais confiável para texto)
        try:
            status_text.text("📖 Tentando extração de texto padrão...")
            transactions = self._extract_with_pdfplumber(uploaded_file, progress_bar, status_text)
            
            if transactions:
                st.success(f"✅ **Extração bem-sucedida!** {len(transactions)} transações encontradas")
                return transactions
            else:
                st.warning("⚠️ Nenhuma transação encontrada com método padrão")
                
        except Exception as e:
            st.warning(f"⚠️ Erro na extração padrão: {str(e)}")
        
        # Estratégia 2: Tentar extração avançada com PyMuPDF
        if PDF_ADVANCED_AVAILABLE:
            try:
                uploaded_file.seek(0)
                status_text.text("🔧 Tentando extração avançada...")
                transactions = self._extract_with_pymupdf(uploaded_file, progress_bar, status_text)
                
                if transactions:
                    st.success(f"✅ **Extração avançada bem-sucedida!** {len(transactions)} transações encontradas")
                    return transactions
                    
            except Exception as e:
                st.warning(f"⚠️ Erro na extração avançada: {str(e)}")
        
        # Estratégia 3: Tentar OCR com EasyOCR para PDFs escaneados
        if EASYOCR_AVAILABLE:
            try:
                uploaded_file.seek(0)
                status_text.text("🤖 Tentando OCR para PDF escaneado...")
                transactions = self._extract_with_easyocr(uploaded_file, progress_bar, status_text)
                
                if transactions:
                    st.success(f"✅ **OCR bem-sucedido!** {len(transactions)} transações encontradas")
                    return transactions
                    
            except Exception as e:
                st.warning(f"⚠️ Erro no OCR: {str(e)}")
        else:
            st.info("💡 **Para PDFs escaneados**: Instale `pip install easyocr` para ativar OCR automático")
        
        # Se chegou aqui, nenhum método funcionou
        self._show_pdf_help()
        return []

    def _extract_with_pdfplumber(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Extração usando pdfplumber (método principal)"""
        
        uploaded_file.seek(0)
        
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
            
            if total_pages > 10:
                st.info(f"📄 **Processando PDF grande** ({total_pages} páginas) - isso pode demorar...")
            
            all_transactions = []
            self.last_date_context = None  # Reset context for new document
            
            for page_num, page in enumerate(pdf.pages):
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"📖 Processando página {page_num + 1}/{total_pages}...")
                
                try:
                    # Extrair texto da página
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # Usar análise estruturada com contexto de data
                        page_transactions = self._extract_structured_data_with_context(
                            text, 
                            self.debug_mode
                        )
                        
                        # Se encontrou poucas transações, usar método original como fallback
                        if len(page_transactions) < 3:
                            if self.debug_mode:
                                st.write("🔄 **Usando método de fallback para esta página...**")
                            
                            fallback_transactions = self._parse_transactions_batch(
                                text, 
                                f"Página {page_num + 1}",
                                self.debug_mode
                            )
                            
                            # Se o fallback encontrou mais transações, usar ele
                            if len(fallback_transactions) > len(page_transactions):
                                page_transactions = fallback_transactions
                        
                        all_transactions.extend(page_transactions)
                    
                except Exception as e:
                    st.warning(f"⚠️ Erro na página {page_num + 1}: {str(e)}")
                    continue
            
            return self._clean_and_sort_transactions(all_transactions)

    def _extract_with_pymupdf(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Extração usando PyMuPDF para PDFs complexos"""
        
        if not PDF_ADVANCED_AVAILABLE:
            return []
            
        uploaded_file.seek(0)
        
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            
            all_transactions = []
            self.last_date_context = None  # Reset context for new document
            
            for page_num in range(total_pages):
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"🔧 Processando página {page_num + 1}/{total_pages} (avançado)...")
                
                try:
                    page = doc[page_num]
                    
                    # Tentar extrair texto
                    text = page.get_text()
                    
                    # Se não há texto ou muito pouco, tentar métodos alternativos
                    if not text or len(text.strip()) < 50:
                        # Tentar extrair texto com diferentes métodos
                        text = page.get_text("text")
                        
                        if not text or len(text.strip()) < 50:
                            # Informar que é provável PDF escaneado
                            st.warning(f"⚠️ Página {page_num + 1}: Pouco texto detectado - possível PDF escaneado")
                            continue
                    
                    if text and text.strip():
                        # Usar extração com contexto de data
                        page_transactions = self._extract_structured_data_with_context(
                            text, 
                            self.debug_mode
                        )
                        
                        # Se encontrou poucas transações, usar método de fallback  
                        if len(page_transactions) < 3:
                            fallback_transactions = self._parse_transactions_batch(
                                text, 
                                f"Página {page_num + 1} (Avançado)",
                                self.debug_mode
                            )
                            
                            if len(fallback_transactions) > len(page_transactions):
                                page_transactions = fallback_transactions
                        
                        all_transactions.extend(page_transactions)
                        
                except Exception as e:
                    st.warning(f"⚠️ Erro avançado na página {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()
            return self._clean_and_sort_transactions(all_transactions)
            
        except Exception as e:
            st.error(f"❌ Erro no processamento avançado: {str(e)}")
            return []

    def _extract_with_easyocr(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Extração usando EasyOCR para PDFs escaneados"""
        
        if not EASYOCR_AVAILABLE:
            st.warning("⚠️ EasyOCR não instalado. Execute: `pip install easyocr`")
            return []
            
        uploaded_file.seek(0)
        
        try:
            # Inicializar EasyOCR
            st.info("🤖 **Inicializando EasyOCR** (pode demorar na primeira vez)...")
            reader = easyocr.Reader(['pt', 'en'], gpu=False)  # Português e Inglês, sem GPU
            
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            
            st.info(f"📄 **Processando {total_pages} páginas com OCR** - isso pode demorar...")
            
            all_transactions = []
            
            for page_num in range(total_pages):
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"🤖 OCR página {page_num + 1}/{total_pages}...")
                
                try:
                    page = doc[page_num]
                    
                    # Converter página para imagem
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom para melhor qualidade OCR
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # Converter para PIL Image
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Aplicar OCR
                    results = reader.readtext(image)
                    
                    # Extrair texto das detecções
                    page_text = ""
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5:  # Filtrar detecções com baixa confiança
                            page_text += text + " "
                    
                    # Processar texto extraído
                    if page_text.strip():
                        page_transactions = self._parse_transactions_batch(
                            page_text, 
                            f"OCR Página {page_num + 1}",
                            self.debug_mode
                        )
                        all_transactions.extend(page_transactions)
                        
                        if page_transactions:
                            st.success(f"✅ Página {page_num + 1}: {len(page_transactions)} transações encontradas via OCR")
                    else:
                        st.warning(f"⚠️ Página {page_num + 1}: Nenhum texto detectado")
                        
                except Exception as e:
                    st.warning(f"⚠️ Erro OCR na página {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()
            
            transactions = self._clean_and_sort_transactions(all_transactions)
            
            if total_pages > 5:
                st.info(f"🤖 **OCR Concluído:** {total_pages} páginas processadas, {len(transactions)} transações encontradas")
                
            return transactions
            
        except Exception as e:
            st.error(f"❌ Erro geral no OCR: {str(e)}")
            return []

    def _extract_structured_data(self, text: str, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """Extrai dados estruturados do PDF usando análise posicional e contextual"""
        
        if debug_mode:
            st.write("🔍 **Análise estruturada do PDF:**")
        
        lines = text.split('\n')
        transactions = []
        current_date = None
        
        # Pré-processar linhas para identificar padrões de layout
        processed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            processed_lines.append({
                'index': i,
                'text': line,
                'has_date': bool(self._extract_date(line)),
                'has_value': bool(self._extract_all_values(line)),
                'length': len(line),
                'words': line.split()
            })
        
        if debug_mode:
            st.write(f"📝 **{len(processed_lines)} linhas processadas**")
        
        # Estratégia 1: Buscar por padrões de data no início das linhas
        for proc_line in processed_lines:
            line_text = proc_line['text']
            
            # Verificar se é uma linha de data (começa com data)
            date_at_start = self._extract_date_at_start(line_text)
            if date_at_start:
                current_date = date_at_start
                if debug_mode:
                    st.write(f"📅 **Data encontrada:** {current_date} na linha: `{line_text}`")
                continue
            
            # Se temos uma data atual, verificar se a linha é uma transação
            if current_date:
                transaction = self._parse_transaction_line(line_text, current_date)
                if transaction:
                    transactions.append(transaction)
                    if debug_mode:
                        st.write(f"✅ **Transação:** {transaction['tipo']} R$ {transaction['valor']:.2f}")
                        st.write(f"   Linha: `{line_text}`")
        
        # Estratégia 2: Se poucas transações foram encontradas, tentar análise por blocos
        if len(transactions) < 5:
            if debug_mode:
                st.write("🔄 **Poucas transações encontradas. Tentando análise por blocos...**")
            
            additional_transactions = self._extract_by_blocks(text, debug_mode)
            transactions.extend(additional_transactions)
        
        return transactions

    def _extract_structured_data_with_context(self, text: str, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """Extrai dados estruturados mantendo contexto de data entre páginas"""
        
        if debug_mode:
            st.write("🔍 **Análise estruturada com contexto:**")
        
        lines = text.split('\n')
        transactions = []
        current_date = self.last_date_context  # Usar último contexto de data
        
        # Pré-processar linhas para identificar padrões de layout
        processed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            processed_lines.append({
                'index': i,
                'text': line,
                'has_date': bool(self._extract_date(line)),
                'has_value': bool(self._extract_all_values(line)),
                'length': len(line),
                'words': line.split()
            })
        
        if debug_mode:
            st.write(f"📝 **{len(processed_lines)} linhas processadas**")
            if current_date:
                st.write(f"📅 **Contexto inicial:** {current_date}")
        
        # Estratégia 1: Buscar por padrões de data no início das linhas
        for proc_line in processed_lines:
            line_text = proc_line['text']
            
            # Verificar se é uma linha de data (começa com data)
            date_at_start = self._extract_date_at_start(line_text)
            if date_at_start:
                current_date = date_at_start
                self.last_date_context = current_date  # Atualizar contexto global
                if debug_mode:
                    st.write(f"📅 **Data encontrada:** {current_date} na linha: `{line_text}`")
                # NÃO fazer continue - verificar se a linha também é uma transação
            
            # Se temos uma data atual, verificar se a linha é uma transação
            if current_date:
                transaction = self._parse_transaction_line(line_text, current_date)
                if transaction:
                    transactions.append(transaction)
                    if debug_mode:
                        st.write(f"✅ **Transação:** {transaction['tipo']} R$ {transaction['valor']:.2f}")
                        st.write(f"   Linha: `{line_text}`")
        
        # Estratégia 2: Se poucas transações foram encontradas, tentar análise por blocos
        if len(transactions) < 5:
            if debug_mode:
                st.write("🔄 **Poucas transações encontradas. Tentando análise por blocos...**")
            
            additional_transactions = self._extract_by_blocks_with_context(text, current_date, debug_mode)
            transactions.extend(additional_transactions)
        
        # Atualizar contexto global com a última data usada
        if current_date:
            self.last_date_context = current_date
        
        return transactions

    def _extract_by_blocks_with_context(self, text: str, context_date: str, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """Extrai transações por blocos usando contexto de data"""
        
        transactions = []
        lines = text.split('\n')
        current_date = context_date
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verificar se linha tem nova data
            date_match = self._extract_date(line)
            if date_match:
                current_date = date_match
                self.last_date_context = current_date
                continue
            
            # Se tem data atual, tentar extrair transação
            if current_date:
                transaction = self._parse_transaction_line(line, current_date)
                if transaction:
                    transactions.append(transaction)
                    if debug_mode:
                        st.write(f"🔍 **Bloco:** {transaction['tipo']} R$ {transaction['valor']:.2f}")
        
        return transactions

    def _parse_with_date_context(self, text: str, context_date: str) -> List[Dict[str, Any]]:
        """Método auxiliar para parsing com contexto de data específico"""
        
        self.last_date_context = context_date
        return self._extract_structured_data_with_context(text, debug_mode=False)

    def _extract_date_at_start(self, line: str) -> str:
        """Extrai data especificamente do início da linha"""
        
        # Padrões para datas no início da linha
        start_patterns = [
            r'^(\d{2})/(\d{2})/(\d{4})',    # DD/MM/YYYY
            r'^(\d{2})/(\d{2})/(\d{2})',    # DD/MM/YY  
            r'^(\d{1,2})/(\d{1,2})/(\d{4})', # D/M/YYYY
            r'^(\d{2})/(\d{2})\s',          # DD/MM seguido de espaço
            r'^(\d{1,2})/(\d{1,2})\s',      # D/M seguido de espaço
        ]
        
        for pattern in start_patterns:
            match = re.search(pattern, line.strip())
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 2:
                        day, month = groups
                        statement_year = self.detected_year if self.detected_year else datetime.now().year
                        year = str(statement_year)
                    elif len(groups) == 3:
                        day, month, year = groups
                        if len(year) == 2:
                            year_int = int(year)
                            if year_int <= 50:
                                year = f"20{year}"
                            else:
                                year = f"19{year}"
                    
                    # Validar data
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    if 1 <= day_int <= 31 and 1 <= month_int <= 12:
                        try:
                            test_date = datetime(year_int, month_int, day_int)
                            return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                        except ValueError:
                            continue
                            
                except (ValueError, IndexError):
                    continue
        
        return None

    def _extract_by_blocks(self, text: str, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """Extrai transações analisando blocos de texto relacionados"""
        
        transactions = []
        
        # Dividir texto em blocos baseados em padrões de transação
        transaction_blocks = re.split(r'\n(?=\d{2}/\d{2})', text)
        
        for block in transaction_blocks:
            if not block.strip():
                continue
                
            # Tentar extrair data e transações do bloco
            lines = block.strip().split('\n')
            if not lines:
                continue
                
            first_line = lines[0].strip()
            block_date = self._extract_date_at_start(first_line)
            
            if block_date:
                # Analisar todas as linhas do bloco
                for line in lines:
                    transaction = self._parse_transaction_line(line.strip(), block_date)
                    if transaction:
                        transactions.append(transaction)
                        if debug_mode:
                            st.write(f"🔍 **Bloco:** {transaction['tipo']} R$ {transaction['valor']:.2f}")
        
        return transactions

    def _parse_transactions_batch(self, text: str, batch_name: str, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """Analisa um bloco de texto e extrai transações"""
        
        transactions = []
        lines = text.split('\n')
        
        if debug_mode:
            st.write(f"🔍 **Debug - {batch_name}:**")
            st.write(f"📄 Total de linhas encontradas: {len(lines)}")
        
        current_date = None
        processed_lines = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Armazenar linha para debug
            processed_lines.append(f"Linha {line_num + 1}: {line}")
            
            # Verificar se há uma data na linha
            date_found = self._extract_date(line)
            if date_found:
                current_date = date_found
                if debug_mode:
                    st.success(f"📅 Data encontrada na linha {line_num + 1}: {date_found}")
                    st.code(line)
            
            # Procurar por transações na linha
            transaction_info = self._parse_transaction_line(line, current_date)
            if transaction_info:
                transaction_info['fonte'] = batch_name
                transaction_info['linha'] = line_num + 1
                transactions.append(transaction_info)
                
                if debug_mode:
                    st.info(f"💰 Transação encontrada na linha {line_num + 1}:")
                    st.json(transaction_info)
                    st.code(line)
            elif debug_mode:
                # Mostrar por que a linha foi ignorada para debug
                has_values = bool(self._extract_all_values(line))
                has_date = bool(self._extract_date(line))
                if has_values or has_date or any(word in line.lower() for word in ['pix', 'ted', 'transferencia']):
                    st.warning(f"⚠️ Linha {line_num + 1} ignorada (valores: {has_values}, data: {has_date}):")
                    st.code(line)
        
        # Mostrar resumo do debug
        if debug_mode:
            st.write("📋 **Resumo da análise:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Linhas processadas", len(processed_lines))
                st.metric("Transações encontradas", len(transactions))
            with col2:
                if current_date:
                    st.metric("Última data detectada", current_date)
                else:
                    st.warning("Nenhuma data detectada")
            
            # Mostrar algumas linhas para análise
            with st.expander("🔍 Ver todas as linhas processadas"):
                for proc_line in processed_lines[:50]:  # Mostrar até 50 linhas
                    st.text(proc_line)
                if len(processed_lines) > 50:
                    st.info(f"... e mais {len(processed_lines) - 50} linhas")
        
        return transactions

    def _parse_transaction_line(self, line: str, current_date: str = None) -> Dict[str, Any]:
        """Analisa uma linha e tenta extrair informações de transação"""
        
        line_lower = line.lower()
        line_clean = line.strip()
        
        # Filtros mais rigorosos para ignorar linhas que claramente não são transações
        ignore_patterns = [
            r'página?\s*[:.]?\s*\d+',                    # "página: 66", "pagina:66/69", etc.
            r'pagina?\s*[:.]?\s*\d+',                    # "pagina: 66", "pagina:66/69", etc.
            r'\bpagina?\s*[:.]?\s*\d+/\d+',              # "pagina:66/69", "página 66/69"
            r'^\d+$',                                    # apenas números isolados
            r'^\d+/\d+$',                                # padrões como "66/69"
            r'banco\s+',                                 # cabeçalhos de banco
            r'extrato\s+',                               # cabeçalhos de extrato
            r'conta\s+corrente',                         # tipo de conta
            r'saldo\s+(anterior|atual)',                 # saldos
            r'total\s+',                                 # totais
            r'^\s*[-=]+\s*$',                           # linhas separadoras
            r'agencia\s*\d+',                            # informações de agência
            r'conta\s*\d+',                              # informações de conta
            r'cpf\s*[:.]?\s*\d',                        # informações de CPF
            r'cnpj\s*[:.]?\s*\d',                       # informações de CNPJ
            r'^\d+\s*$',                                # números isolados com espaços
            r'desconsidere\s+esta\s+informação',        # Texto informativo específico
            r'válido\s+para\s+clientes',                # Texto informativo específico
            r'se\s+o\s+limite\s+de\s+crédito',          # Texto informativo específico
            r'tarifa\s+pela\s+disponibilização',        # Texto informativo específico
            r'cheque\s+empresa\s+plus',                 # Texto informativo específico
            r'santander\s+master',                      # Texto informativo específico
            r'hipóteses?\s*:',                          # Listas de hipóteses
            r'durante\s+do\s+prazo',                    # Texto de termos e condições
            r'período\s+de\s+vigência',                 # Texto de termos e condições
            r'emitente',                                # Referências ao emitente
            r'ccgpj\s+\d+',                            # Códigos bancários específicos
            r'v\s+\d+,\d+\s+\d+',                     # Padrões de códigos "v 1,00 510.071,00"
            r'\d{12,}',                                # Números muito longos (códigos)
        ]
        
        # Verificar se a linha deve ser ignorada
        for pattern in ignore_patterns:
            if re.search(pattern, line_lower):
                return None
        
        # Verificar se a linha contém indicadores reais de transação bancária
        transaction_indicators = [
            'pix', 'ted', 'doc', 'transferencia', 'transferência',
            'saque', 'deposito', 'depósito', 'pagamento', 'recebimento',
            'debito', 'débito', 'credito', 'crédito', 'tarifa', 'taxa',
            'compra', 'fornec', 'checkout', 'talao', 'talão', 'ccgpj',
            'giro', 'cdc', 'fgi', 'peac', 'limite', 'certificação',
            # Adicionar mais indicadores comuns
            'enviado', 'recebido', 'cartao', 'cartão', 'conta',
            'banco', 'agencia', 'agência', 'compensacao', 'compensação',
            'cheque', 'boleto', 'fatura', 'parcela', 'juros',
            'multa', 'desconto', 'cashback', 'estorno', 'devolucao',
            'devolução', 'ordem', 'servico', 'serviço'
        ]
        
        has_transaction_indicator = any(indicator in line_lower for indicator in transaction_indicators)
        
        # Extrair valores da linha (deve ter pelo menos um valor válido)
        values = self._extract_all_values(line_clean)
        
        # Se não tem valores ou indicadores, ignorar
        if not values and not has_transaction_indicator:
            return None
            
        # Se tem valores, filtrar os significativos
        if values:
            # Filtrar valores muito pequenos ou muito grandes (possíveis códigos/erros)
            significant_values = [v for v in values if 1.0 <= v <= 50000000.0]
            
            if not significant_values:
                return None
            
            # Se não tem indicador de transação e valor parece suspeito, ignorar
            if not has_transaction_indicator:
                max_value = max(significant_values)
                # Valores redondos pequenos sem contexto são suspeitos (como página 69 = R$ 69,00)
                if max_value < 1000.0 and max_value == int(max_value):
                    return None
        else:
            # Se não tem valores mas tem indicadores, pode ser linha informativa
            return None
        
        # Extrair data da linha se disponível
        line_date = self._extract_date(line_clean)
        if line_date:
            current_date = line_date
        
        if not current_date:
            return None
        
        # Determinar tipo de transação baseado em palavras-chave mais específicas
        credit_keywords = ['recebido', 'recebimento', 'credito', 'crédito', 'depósito', 'deposito', 'entrada']
        debit_keywords = ['pago', 'pagamento', 'saque', 'debito', 'débito', 'tarifa', 'taxa', 'compra', 'saida']
        
        has_credit = any(keyword in line_lower for keyword in credit_keywords)
        has_debit = any(keyword in line_lower for keyword in debit_keywords)
        
        if has_credit:
            transaction_type = 'Crédito'
        elif has_debit:
            transaction_type = 'Débito'
        else:
            # Inferir pelo contexto da linha ou assumir crédito como padrão
            transaction_type = 'Crédito'
        
        # Usar o maior valor significativo encontrado
        value = max(significant_values)
        
        return {
            'data': current_date,
            'tipo': transaction_type,
            'valor': value,
            'descricao': line_clean,
            'linha_original': line_clean
        }

    def _extract_date(self, text: str) -> str:
        """Extrai data do texto usando múltiplos padrões melhorados com validação rigorosa"""
        
        # Limpar texto de caracteres especiais que podem interferir
        clean_text = re.sub(r'[^\w\s/.-]', ' ', text)
        
        # Verificar se a linha contém padrões que NÃO são datas válidas
        invalid_patterns = [
            r'pix\s+\d+',                        # "PIX 12345"
            r'\d{10,}',                          # Números muito longos
            r'conta\s+\d+',                      # "conta 12345"
            r'agencia\s+\d+',                    # "agencia 1234"
            r'codigo\s+\d+',                     # "codigo 123"
            r'ref\s*[:.]?\s*\d+',               # "ref: 12345"
            r'documento\s+\d+',                  # "documento 123"
            r'seq\s*[:.]?\s*\d+',               # "seq: 123"
            r'\b\d{6,}\b',                       # Códigos de 6+ dígitos
            r'valor\s+\d+',                      # "valor 12345"
            r'protocolo\s+\d+',                  # "protocolo 123"
            r'autenticacao\s+\d+',               # "autenticacao 123"
            r'comprovante\s+\d+',                # "comprovante 123"
        ]
        
        # Se contém padrões inválidos, não tentar extrair data
        for invalid_pattern in invalid_patterns:
            if re.search(invalid_pattern, clean_text.lower()):
                return None
        
        current_year = datetime.now().year
        
        for pattern in self.date_patterns:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    groups = match.groups()
                    
                    # Verificar se temos 2 ou 3 grupos (dia/mês ou dia/mês/ano)
                    if len(groups) == 2:
                        day, month = groups
                        # Usar o ano detectado do extrato
                        statement_year = self.detected_year if self.detected_year else current_year
                        year = str(statement_year)
                    elif len(groups) == 3:
                        day, month, year = groups
                        
                        # Converter ano de 2 dígitos para 4 dígitos
                        if len(year) == 2:
                            year_int = int(year)
                            # Para extratos bancários recentes, assumir 20XX
                            if year_int <= 50:
                                year = f"20{year}"
                            else:
                                year = f"19{year}"
                        else:
                            # Para anos de 4 dígitos, verificar consistência com ano detectado
                            year_int = int(year)
                            statement_year = self.detected_year if self.detected_year else current_year
                            # Se difere muito do ano detectado, usar o ano detectado
                            if abs(year_int - statement_year) > 1:
                                year = str(statement_year)
                    else:
                        continue
                    
                    # Validar valores de dia e mês
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    if not (1 <= day_int <= 31 and 1 <= month_int <= 12):
                        continue
                    
                    # Verificar se é uma data válida no calendário
                    try:
                        test_date = datetime(year_int, month_int, day_int)
                        
                        # Verificar se não é uma data muito no futuro ou passado
                        today = datetime.now()
                        if test_date.year < 2020 or test_date.year > today.year + 2:
                            continue
                            
                        formatted_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                        return formatted_date
                        
                    except ValueError:
                        # Data inválida (ex: 31/02)
                        continue
                        
                except (ValueError, IndexError):
                    continue
        
        return None

    def _extract_all_values(self, text: str) -> List[float]:
        """Extrai todos os valores monetários de uma linha"""
        
        values = []
        
        for pattern in self.value_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Limpar e converter valor
                    clean_value = match.replace('R$', '').replace(' ', '')
                    
                    # Converter formato brasileiro para float
                    if ',' in clean_value and '.' in clean_value:
                        # Formato: 1.000,00
                        clean_value = clean_value.replace('.', '').replace(',', '.')
                    elif ',' in clean_value:
                        # Formato: 1000,00
                        clean_value = clean_value.replace(',', '.')
                    
                    value = float(clean_value)
                    if value > 0:
                        values.append(value)
                        
                except (ValueError, AttributeError):
                    continue
        
        return values

    def _is_valid_date(self, date_str: str) -> bool:
        """Valida se uma string representa uma data válida"""
        try:
            # Tentar converter a data para verificar se é válida
            datetime.strptime(date_str, '%d/%m/%Y')
            return True
        except (ValueError, TypeError):
            return False

    def _clean_and_sort_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas e ordena transações por data, validando datas"""
        
        if not transactions:
            return []
        
        # Filtrar transações com datas válidas primeiro
        valid_transactions = []
        invalid_count = 0
        
        for transaction in transactions:
            if self._is_valid_date(transaction.get('data', '')):
                valid_transactions.append(transaction)
            else:
                invalid_count += 1
                if self.debug_mode:
                    try:
                        st.warning(f"⚠️ Data inválida ignorada: {transaction.get('data', 'N/A')}")
                    except NameError:
                        print(f"⚠️ Data inválida ignorada: {transaction.get('data', 'N/A')}")
        
        if invalid_count > 0:
            try:
                st.info(f"📅 {invalid_count} transação(ões) com datas inválidas foram ignoradas")
            except NameError:
                print(f"📅 {invalid_count} transação(ões) com datas inválidas foram ignoradas")
        
        # Remover duplicatas das transações válidas
        seen = set()
        unique_transactions = []
        
        for transaction in valid_transactions:
            key = (transaction['data'], transaction['tipo'], transaction['valor'])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
        
        # Ordenar por data (agora todas as datas são válidas)
        try:
            unique_transactions.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))
        except Exception as e:
            st.warning(f"⚠️ Erro na ordenação por data: {str(e)}")
            # Manter ordem original se não conseguir ordenar
        
        return unique_transactions

    def _show_pdf_help(self):
        """Mostra ajuda para PDFs que não puderam ser processados"""
        
        st.error("❌ **Não foi possível extrair transações do PDF**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔧 Possíveis soluções:**
            
            1. **PDF Escaneado:** 
               - Converta para PDF com texto selecionável
               - Use ferramentas: PDF24, SmallPDF, ILovePDF
            
            2. **Formato não padrão:**
               - Verifique se é um extrato bancário brasileiro
               - Confirme formato de data: DD/MM/AAAA
            """)
        
        with col2:
            st.markdown("""
            **✅ Formatos suportados:**
            
            - PDFs com texto selecionável
            - Extratos bancários brasileiros
            - Datas: DD/MM/AAAA
            - Valores: R$ 1.000,00 ou 1.000,00
            
            **❌ Não suportado:**
            - PDFs escaneados (imagens)
            - Formatos proprietários
            """)
        
        st.info("""
        **💡 Dica:** Teste selecionando texto no PDF. Se conseguir selecionar, 
        a aplicação deveria conseguir processar. Se não conseguir selecionar texto, 
        é um PDF escaneado que precisa ser convertido.
        """)