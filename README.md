# 📊 Leitor de PDF - Extrato Bancário Multibank

Uma aplicação web moderna para extrair e analisar transações de extratos bancários em PDF, com suporte específico para múltiplos bancos brasileiros.

## 🏦 **Bancos Suportados**

### ✅ **Processamento Específico Otimizado**
- 🟢 **Banco Santander (033)** - Processamento completo com padrões específicos
- 🔜 **Itaú (341)** - Em desenvolvimento
- 🔜 **Bradesco (237)** - Em desenvolvimento
- 🔜 **Banco do Brasil (001)** - Planejado
- 🔜 **Caixa Econômica Federal (104)** - Planejado

## ✨ **Principais Funcionalidades**

### 🎯 **Processamento Específico por Banco**
- **Seleção obrigatória do banco** para máxima precisão
- **Padrões otimizados** para cada instituição bancária
- **Reconhecimento inteligente** de formatos específicos
- **Classificação precisa** de tipos de transação

### 📊 **Análise Avançada**
- **Resumo diário** com créditos, débitos e saldo
- **Gráficos interativos** para visualização de dados
- **Estatísticas detalhadas** do período
- **Filtros e busca** nas transações

### ⚡ **Performance Otimizada**
- **Cache inteligente** para processamento rápido
- **Suporte a arquivos grandes** (múltiplas páginas)
- **Processamento em lote** otimizado
- **Interface responsiva** e moderna

## 🚀 **Como Usar**

### **Pré-requisitos**
- Python 3.8+
- pip (gerenciador de pacotes Python)

### **Instalação**
```bash
# Clone o repositório
git clone https://github.com/gabiissilvaa/Leitor_PDF.git
cd Leitor_PDF

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run app.py
```

### **Uso da Aplicação**
1. 🏦 **OBRIGATÓRIO:** Selecione seu banco na barra lateral
2. 📁 Faça upload do seu extrato bancário em PDF
3. ⚡ Sistema processa com padrões específicos do banco
4. 📊 Visualize resultados organizados e gráficos
5. 📈 Analise dados financeiros detalhados

## 🎯 **Por que a Seleção de Banco é Obrigatória?**

### **✅ Garantia de Máxima Precisão**
- **Cada banco tem formato único** - layouts, terminologias e padrões específicos
- **100% de confiabilidade** - sem erros de detecção automática
- **Processamento otimizado** - algoritmos específicos para cada banco
- **Resultados consistentes** - sempre use o melhor método disponível

### **🚫 Problemas da Detecção Automática**
- ❌ Pode identificar banco incorreto
- ❌ Reduz precisão da extração
- ❌ Gera resultados inconsistentes
- ❌ Processamento mais lento

## 🏗️ **Arquitetura Técnica**

### **📁 Estrutura do Projeto**
```
src/
├── banks/                          # Processadores específicos
│   ├── base_bank_processor.py      # Classe base abstrata
│   ├── santander_processor.py      # Processador Santander
│   └── bank_factory.py             # Factory pattern
├── multibank_pdf_processor.py      # Processador principal
├── data_analyzer.py                # Análise de dados
├── notification_manager.py         # Notificações
└── performance_manager.py          # Cache e performance
```

### **🏦 Adicionando Novos Bancos**
Para adicionar suporte a um novo banco:

1. **Criar processador específico:**
```python
class NovoBancoProcessor(BaseBankProcessor):
    def __init__(self, debug_mode: bool = False):
        super().__init__(debug_mode)
        self.bank_name = "Novo Banco"
        self.bank_code = "XXX"
    
    # Implementar métodos abstratos específicos
    @property
    def date_patterns(self) -> List[str]:
        return [...]  # Padrões específicos do banco
```

2. **Registrar no factory:**
```python
# Em bank_factory.py
AVAILABLE_BANKS = {
    'novo_banco': {
        'name': 'Novo Banco',
        'code': 'XXX',
        'processor_class': NovoBancoProcessor,
        'description': 'Novo Banco S.A.'
    }
}
```

## 📋 **Dependências Principais**

- **streamlit**: Interface web moderna
- **pdfplumber**: Extração de texto de PDFs
- **pandas**: Manipulação de dados
- **plotly**: Gráficos interativos
- **PyMuPDF** (opcional): PDFs complexos
- **easyocr** (opcional): PDFs escaneados

## 🔧 **Configuração Avançada**

### **Cache**
- Local: `cache/` (criado automaticamente)
- Validade: 24 horas
- Hash: baseado no conteúdo do arquivo

### **Performance**
- Processamento em páginas para arquivos grandes
- Otimizações específicas por banco

## 🤝 **Contribuição**

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovoRecurso`)
3. Commit suas mudanças (`git commit -am 'Adiciona novo recurso'`)
4. Push para a branch (`git push origin feature/NovoRecurso`)
5. Abra um Pull Request

## 📝 **Roadmap**

### **🔜 Próximas Versões**
- **v2.1**: Suporte ao Itaú
- **v2.2**: Suporte ao Bradesco
- **v2.3**: Banco do Brasil
- **v2.4**: Caixa Econômica Federal
- **v3.0**: API REST para integração

### **💡 Funcionalidades Futuras**
- Exportação para Excel/CSV
- Categorização automática de gastos
- Comparação entre períodos
- Dashboard executivo
- Alertas e notificações

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 **Suporte**

- **Issues**: Use o GitHub Issues para reportar bugs
- **Discussões**: GitHub Discussions para dúvidas

## 🎉 **Agradecimentos**

- Comunidade Streamlit pela excelente framework
- Contribuidores do pdfplumber
- Todos os testadores e usuários que ajudam a melhorar o projeto

---

**⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub!**