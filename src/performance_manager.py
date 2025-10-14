import streamlit as st
import hashlib
import pickle
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class CacheManager:
    """Gerencia cache para melhorar performance com arquivos grandes"""
    
    def __init__(self, cache_dir: str = "cache"):
        # Você pode personalizar o local do cache aqui:
        # cache_dir = "C:/MeuCache"              # Pasta específica
        # cache_dir = "cache"                    # Pasta local (padrão)
        # cache_dir = os.path.expanduser("~/Documents/LeitorPDF_Cache")  # Documentos do usuário
        
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        self.max_cache_age = timedelta(hours=24)  # Cache válido por 24 horas
    
    def ensure_cache_dir(self):
        """Cria diretório de cache se não existir"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_file_hash(self, file_content: bytes) -> str:
        """Gera hash único para o conteúdo do arquivo"""
        return hashlib.md5(file_content).hexdigest()
    
    def get_cache_path(self, file_hash: str) -> str:
        """Retorna caminho do arquivo de cache"""
        return os.path.join(self.cache_dir, f"{file_hash}.pkl")
    
    def is_cache_valid(self, cache_path: str) -> bool:
        """Verifica se o cache ainda é válido"""
        if not os.path.exists(cache_path):
            return False
        
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - cache_time < self.max_cache_age
    
    def save_to_cache(self, file_hash: str, transactions: List[Dict[str, Any]]):
        """Salva transações no cache"""
        try:
            cache_path = self.get_cache_path(file_hash)
            cache_data = {
                'transactions': transactions,
                'timestamp': datetime.now(),
                'version': '1.0'
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            # Mostrar detalhes do cache salvo
            file_size = os.path.getsize(cache_path) / 1024  # KB
            st.success(
                f"💾 **Cache salvo com sucesso!**\n"
                f"📁 **Local:** `{cache_path}`\n"
                f"📊 **Tamanho:** {file_size:.1f} KB\n"
                f"⏱️ **Válido por:** 24 horas\n"
                f"🚀 **Próximas consultas:** Instantâneas"
            )
            
        except Exception as e:
            st.warning(f"⚠️ Não foi possível salvar cache: {str(e)}")
    
    def load_from_cache(self, file_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Carrega transações do cache"""
        try:
            cache_path = self.get_cache_path(file_hash)
            
            if not self.is_cache_valid(cache_path):
                return None
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            return cache_data.get('transactions', [])
            
        except Exception:
            return None
    
    def clear_old_cache(self):
        """Remove arquivos de cache antigos"""
        try:
            current_time = datetime.now()
            files_removed = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    file_path = os.path.join(self.cache_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if current_time - file_time > self.max_cache_age:
                        os.remove(file_path)
                        files_removed += 1
            
            if files_removed > 0:
                st.info(f"🧹 {files_removed} arquivo(s) de cache antigo removido(s)")
                
        except Exception as e:
            st.warning(f"⚠️ Erro ao limpar cache: {str(e)}")

class PerformanceOptimizer:
    """Otimiza performance para arquivos grandes"""
    
    @staticmethod
    def should_use_fast_mode(total_pages: int) -> bool:
        """Determina se deve usar modo rápido baseado no tamanho"""
        return total_pages > 30
    
    @staticmethod
    def get_batch_size(total_pages: int) -> int:
        """Calcula tamanho ideal do lote baseado no número de páginas"""
        if total_pages <= 10:
            return 5
        elif total_pages <= 50:
            return 8
        elif total_pages <= 100:
            return 10
        else:
            return 15
    
    @staticmethod
    def estimate_processing_time(total_pages: int) -> str:
        """Estima tempo de processamento"""
        # Baseado em testes empíricos: ~0.5s por página
        seconds_per_page = 0.5
        total_seconds = total_pages * seconds_per_page
        
        if total_seconds < 60:
            return f"~{int(total_seconds)} segundos"
        else:
            minutes = int(total_seconds // 60)
            return f"~{minutes} minuto(s)"
    
    @staticmethod
    def show_performance_tips(total_pages: int):
        """Mostra dicas de performance"""
        if total_pages > 50:
            with st.expander("⚡ Dicas de Performance"):
                st.markdown("""
                **Para arquivos grandes:**
                - ✅ Processamento otimizado ativado automaticamente
                - ✅ Cache habilitado para consultas futuras
                - ✅ Processamento em lotes para economizar memória
                - ⏱️ Tempo estimado: """ + PerformanceOptimizer.estimate_processing_time(total_pages) + """
                
                **Próximas vezes:**
                - 🚀 Se processar o mesmo arquivo, será muito mais rápido (cache)
                - 💾 Dados ficam salvos temporariamente
                """)

class ProgressTracker:
    """Gerencia progresso detalhado para arquivos grandes"""
    
    def __init__(self, total_pages: int):
        self.total_pages = total_pages
        self.current_page = 0
        self.transactions_found = 0
        self.start_time = datetime.now()
        
        # Elementos da interface
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.metrics_container = st.container()
        
        # Mostrar métricas iniciais
        self._show_metrics()
    
    def update_page(self, page_num: int):
        """Atualiza progresso da página"""
        self.current_page = page_num
        progress = min(90, (page_num / self.total_pages) * 90)
        
        self.progress_bar.progress(int(progress))
        self.status_text.text(f'📖 Processando página {page_num}/{self.total_pages}...')
        
        # Atualizar métricas a cada 10 páginas
        if page_num % 10 == 0 or page_num == self.total_pages:
            self._show_metrics()
    
    def add_transaction(self):
        """Incrementa contador de transações"""
        self.transactions_found += 1
    
    def complete(self, total_transactions: int):
        """Finaliza o progresso"""
        self.transactions_found = total_transactions
        self.progress_bar.progress(100)
        
        elapsed_time = datetime.now() - self.start_time
        self.status_text.success(
            f'🎉 Concluído! {total_transactions} transações em {elapsed_time.seconds}s'
        )
        
        self._show_final_metrics()
    
    def _show_metrics(self):
        """Mostra métricas em tempo real"""
        elapsed = datetime.now() - self.start_time
        
        with self.metrics_container:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Páginas", f"{self.current_page}/{self.total_pages}")
            
            with col2:
                st.metric("📋 Transações", self.transactions_found)
            
            with col3:
                progress_percent = (self.current_page / self.total_pages) * 100
                st.metric("⚡ Progresso", f"{progress_percent:.1f}%")
            
            with col4:
                st.metric("⏱️ Tempo", f"{elapsed.seconds}s")
    
    def _show_final_metrics(self):
        """Mostra métricas finais"""
        elapsed = datetime.now() - self.start_time
        
        st.success(f"""
        ✅ **Processamento Finalizado!**
        - 📄 {self.total_pages} páginas processadas
        - 📋 {self.transactions_found} transações encontradas  
        - ⏱️ Tempo total: {elapsed.seconds} segundos
        - ⚡ Velocidade: {self.total_pages/elapsed.seconds:.1f} páginas/segundo
        """)