# Leitor de PDF - Extrato Bancário

Um sistema completo em Python com Streamlit para ler arquivos PDF de extratos bancários e organizar as transações por data, separando créditos e débitos.

## 🚀 Funcionalidades

- **📁 Upload de PDF**: Interface simples para carregar extratos bancários
- **🔍 Extração Automática**: Reconhece automaticamente datas, valores e tipos de transação
- **📊 Organização por Data**: Agrupa transações por dia com totais de crédito e débito
- **📈 Visualizações**: Gráficos interativos com Plotly
- **📋 Relatórios Detalhados**: Tabelas filtráveis e exportáveis
- **💾 Exportação**: Download dos dados em formato CSV

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Interface web interativa
- **pdfplumber**: Extração de texto de PDFs
- **Pandas**: Manipulação e análise de dados
- **Plotly**: Visualizações interativas
- **Regex**: Reconhecimento de padrões

## 📦 Instalação

1. **Clone o repositório**:
```bash
git clone https://github.com/gabiissilvaa/Leitor_PDF.git
cd Leitor_PDF
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Execute a aplicação**:
```bash
streamlit run app.py
```

4. **Acesse no navegador**:
```
http://localhost:8501
```

## 📁 Estrutura do Projeto

```
Leitor_PDF/
├── app.py                 # Aplicação principal Streamlit
├── requirements.txt       # Dependências do projeto
├── README.md             # Documentação
└── src/
    ├── pdf_processor.py  # Processamento de PDFs
    └── data_analyzer.py  # Análise de dados
```

## 🔧 Como Usar

1. **Upload**: Clique em "Browse files" e selecione seu PDF de extrato bancário
2. **Processamento**: O sistema extrairá automaticamente as transações
3. **Visualização**: Os dados serão organizados por data mostrando:
   - Data da transação
   - Total de créditos do dia
   - Total de débitos do dia
   - Saldo líquido do dia
4. **Análise**: Visualize gráficos e estatísticas detalhadas
5. **Exportação**: Baixe os dados processados em CSV

## 📊 Exemplo de Saída

```
01/08 Crédito: R$ 2.000,00 Débito: R$ 3.000,00 Saldo: -R$ 1.000,00
02/08 Crédito: R$ 1.500,00 Débito: R$ 800,00   Saldo: R$ 700,00
03/08 Crédito: R$ 0,00     Débito: R$ 1.200,00 Saldo: -R$ 1.200,00
```

## 🎯 Recursos Avançados

- **Filtros**: Filtre por data, tipo de transação ou valor mínimo
- **Busca**: Procure transações específicas por descrição
- **Estatísticas**: Visualize totais, maiores transações e saldos
- **Gráficos**: Análise visual com barras e linhas temporais

## 🔍 Formatos Suportados

O sistema reconhece automaticamente:

- **Datas**: DD/MM/YYYY, DD/MM/YY, DD-MM-YYYY, DD.MM.YYYY
- **Valores**: R$ 1.234,56, 1.234,56, 123,45
- **Tipos**: Identifica créditos e débitos por palavras-chave

## 🚨 Palavras-chave Reconhecidas

**Créditos**:
- Depósito, Crédito, Transferência recebida
- PIX recebido, TED recebida, DOC recebido
- Salário, Rendimento, Aplicação, Resgate
- Estorno, Devolução

**Débitos**:
- Débito, Saque, Transferência enviada
- PIX enviado, TED enviada, DOC enviado
- Pagamento, Compra, Tarifa, Taxa
- Juros, Anuidade

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Gabriela Silva**
- GitHub: [@gabiissilvaa](https://github.com/gabiissilvaa)

## 🆘 Suporte

Se você encontrar algum problema ou tiver sugestões, abra uma [issue](https://github.com/gabiissilvaa/Leitor_PDF/issues) no GitHub.

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no repositório!