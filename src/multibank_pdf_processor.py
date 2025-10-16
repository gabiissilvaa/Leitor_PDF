import pdfplumber
import re
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
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

from .banks import BankProcessorFactory, BaseBankProcessor

class MultibankPDFProcessor:
    """Processador de PDF que suporta múltiplos bancos"""
    
    def __init__(self, bank_id: str = None, debug_mode: bool = False):
        self.bank_id = bank_id
        self.debug_mode = debug_mode
        self.bank_processor: Optional[BaseBankProcessor] = None
        self.detected_year = None
        self.last_date_context = None
        
        # Inicializar processador específico do banco se fornecido
        if bank_id:
            try:
                self.bank_processor = BankProcessorFactory.create_processor(bank_id, debug_mode)
                if self.debug_mode:
                    st.info(f"🏦 **Processador inicializado:** {self.bank_processor.bank_name}")
            except ValueError as e:
                st.error(f"❌ Erro ao inicializar processador: {str(e)}")
                self.bank_processor = None
    
    def set_bank_processor(self, bank_id: str):
        """Define o processador de banco a ser usado"""
        try:
            self.bank_id = bank_id
            self.bank_processor = BankProcessorFactory.create_processor(bank_id, self.debug_mode)
            if self.debug_mode:
                st.info(f"🏦 **Processador configurado para:** {self.bank_processor.bank_name}")
        except ValueError as e:
            st.error(f"❌ Erro ao configurar processador: {str(e)}")
            self.bank_processor = None
    
    def extract_transactions(self, uploaded_file, progress_bar, status_text, bank_id: str) -> List[Dict[str, Any]]:
        """Extrai transações do arquivo PDF usando processador específico do banco (obrigatório)"""
        
        # Verificar se bank_id foi fornecido
        if not bank_id:
            raise ValueError("bank_id é obrigatório. Selecione um banco antes de processar.")
        
        # Configurar o processador para o banco especificado
        if bank_id != self.bank_id:
            self.set_bank_processor(bank_id)
        
        # Verificar se temos processador válido
        if not self.bank_processor:
            raise ValueError(f"Não foi possível inicializar processador para o banco: {bank_id}")
        
        st.info(f"🏦 **Processando com {self.bank_processor.bank_name}**")
        st.success(f"🎯 **Usando padrões específicos otimizados do {self.bank_processor.bank_name}**")
        
        # Resetar posição do arquivo
        uploaded_file.seek(0)
        
        # Detectar ano do extrato usando o processador específico
        current_year = datetime.now().year
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                sample_text = ""
                for page_num in range(min(3, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        sample_text += page_text[:2000]
                
                self.detected_year = self.bank_processor.detect_statement_year(sample_text)
                self.bank_processor.detected_year = self.detected_year
                
                if self.detected_year < 2024:
                    st.warning(f"⚠️ Ano {self.detected_year} detectado parece muito antigo. Forçando para {current_year}.")
                    self.detected_year = current_year
                    self.bank_processor.detected_year = current_year
                
                st.info(f"📅 **Ano detectado do extrato:** {self.detected_year}")
                
        except Exception as e:
            st.warning(f"⚠️ Erro na detecção do ano: {str(e)}")
            self.detected_year = current_year
            if self.bank_processor:
                self.bank_processor.detected_year = current_year
        
        # Resetar posição após a detecção
        uploaded_file.seek(0)
        
        # Estratégia 1: Usar processador específico do banco
        try:
            status_text.text(f"📖 Processando com {self.bank_processor.bank_name}...")
            transactions = self._extract_with_bank_processor(uploaded_file, progress_bar, status_text)
            
            if transactions:
                st.success(f"✅ **Extração {self.bank_processor.bank_name} bem-sucedida!** {len(transactions)} transações encontradas")
                return transactions
            else:
                st.warning(f"⚠️ Nenhuma transação encontrada com processador {self.bank_processor.bank_name}")
                st.info("💡 Verifique se o arquivo é realmente um extrato deste banco")
                return []
                
        except Exception as e:
            st.error(f"❌ Erro na extração {self.bank_processor.bank_name}: {str(e)}")
            st.info("💡 Verifique se o arquivo é um extrato válido do banco selecionado")
            return []
    
    def _extract_with_bank_processor(self, uploaded_file, progress_bar, status_text) -> List[Dict[str, Any]]:
        """Extração usando processador específico do banco"""
        
        uploaded_file.seek(0)
        
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
            
            if total_pages > 10:
                st.info(f"📄 **Processando PDF {self.bank_processor.bank_name}** ({total_pages} páginas)")
            
            all_transactions = []
            self.bank_processor.last_date_context = None
            
            for page_num, page in enumerate(pdf.pages):
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"📖 {self.bank_processor.bank_name} - Página {page_num + 1}/{total_pages}...")
                
                try:
                    text = page.extract_text()
                    
                    if text and text.strip():
                        page_transactions = self._extract_transactions_from_text(
                            text, 
                            f"{self.bank_processor.bank_name} - Página {page_num + 1}"
                        )
                        all_transactions.extend(page_transactions)
                    
                except Exception as e:
                    st.warning(f"⚠️ Erro na página {page_num + 1}: {str(e)}")
                    continue
            
            return self.bank_processor.clean_and_sort_transactions(all_transactions)
    
    def _extract_transactions_from_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Extrai transações de um texto usando o processador específico"""
        
        if not self.bank_processor:
            return []
        
        transactions = []
        lines = text.split('\n')
        current_date = self.bank_processor.last_date_context
        
        if self.debug_mode:
            st.write(f"🔍 **Analisando {source}:** {len(lines)} linhas")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Verificar se é uma linha de data
            line_date = self.bank_processor.extract_date_from_line(line)
            if line_date:
                current_date = line_date
                self.bank_processor.last_date_context = current_date
                if self.debug_mode:
                    st.write(f"📅 **Data:** {current_date}")
                # Continuar para verificar se a linha também é uma transação
            
            # Se temos uma data atual, verificar se a linha é uma transação
            if current_date:
                transaction = self.bank_processor.parse_transaction_line(line, current_date)
                if transaction:
                    transaction['fonte'] = source
                    transaction['linha'] = line_num + 1
                    transactions.append(transaction)
                    
                    if self.debug_mode:
                        st.write(f"✅ **Transação:** {transaction['tipo']} R$ {transaction['valor']:.2f}")
        
        # Atualizar contexto global
        if current_date:
            self.bank_processor.last_date_context = current_date
        
        return transactions
    
    def get_supported_banks(self) -> dict:
        """Retorna lista de bancos suportados"""
        return BankProcessorFactory.get_available_banks()
    
    def get_current_bank_info(self) -> Optional[dict]:
        """Retorna informações do banco atualmente selecionado"""
        if self.bank_id:
            return BankProcessorFactory.get_bank_info(self.bank_id)
        return None