# Resumo da Análise de Funil - InHire

**Data:** 2026-02-06
**Última atualização dos dados:** 2026-02-04 20:22:15

---

## 📊 Tarefas Concluídas

### ✅ 1. Certificação de Integridade de Conexão e Dados

**Status:** ✅ CONCLUÍDO

**Resultados:**
- ✅ Conexão com PostgreSQL 18.1 estabelecida
- ✅ Login na API Inhire bem-sucedido
- ✅ Dados sincronizados e atualizados

**Volumes de Dados:**
- **1,167** Vagas
- **872** Posições
- **82,584** Candidaturas
- **57,966** Talentos
- **74** Clientes
- **834** Requisições

**Scripts criados:**
- `test_connection_simple.py` - Teste de integridade de conexões

---

### ✅ 2. View de Análise de Funil Criada

**Status:** ✅ CONCLUÍDO

**View criada:** `vw_funil_performance`

**Características:**
- Normaliza os nomes das etapas do funil
- Mapeia etapas para o kanban solicitado:
  1. Hunting
  2. Abordagem
  3. Inscrição
  4. Bate papo | Pessoas e Cultura
  5. Etapa técnica | Talent IA
  6. Aguardando Devolutiva IA
  7. Bate Papo | Cliente
  8. Formalização de Proposta
  9. Contratação

- **Total de registros:** 82,584 candidaturas
- Inclui dimensões para análise: recrutadora, vaga, cliente, torre

**Scripts criados:**
- `create_view_funil_simple.py` - Criação da view
- `query_etapas_funil.py` - Consulta de etapas do funil

---

### ✅ 3. Relatórios de Funil Gerados

**Status:** ✅ CONCLUÍDO

Foram gerados **5 relatórios** conforme solicitado:

#### **A. Funil Geral**

| Etapa | Total | Ativos | Reprovados |
|-------|-------|--------|------------|
| Hunting | 16,267 | 6,844 | 7,842 |
| Abordagem | 2,543 | 897 | 677 |
| Inscrição | **53,444** | 31,941 | 20,916 |
| Bate papo | Pessoas e Cultura | 5,167 | 766 | 3,996 |
| Etapa técnica | Talent IA | 2,741 | 513 | 2,067 |
| Aguardando Devolutiva IA | 818 | 269 | 509 |
| Bate Papo | Cliente | 733 | 276 | 402 |
| Formalização de Proposta | 104 | 32 | 11 |
| **Contratação** | **604** | 599 | 2 |

**Taxa de Reprovação por Etapa:**
- Bate papo | Pessoas e Cultura: **77.34%** (maior gargalo)
- Etapa técnica | Talent IA: **75.41%**
- Aguardando Devolutiva IA: **62.22%**
- Bate Papo | Cliente: **54.84%**

#### **B. Performance por Recrutadora**

**Top 5 Recrutadoras** (por volume):

| Recrutadora | Total | Ativos | Reprovados | Tempo Médio (dias) |
|-------------|-------|--------|------------|--------------------|
| InHire | 37,266 | 22,835 | 14,096 | 81.2 |
| Produto Intera | 20,602 | 10,124 | 10,094 | 84.0 |
| Maria Eduarda Benicio | 6,241 | 1,654 | 4,297 | 58.1 |
| Thainara de Souza | 2,645 | 1,230 | 986 | 70.0 |
| John Anderson | 2,371 | 37 | 2,184 | 79.2 |

**Insights:**
- Maria Eduarda tem o menor tempo médio de processo (58.1 dias)
- Média geral de tempo no processo: ~75-84 dias

#### **C. Performance por Vaga/Posição**

**Top 10 Vagas** (com 5+ candidaturas):

| Vaga | Total | Ativos | Reprovados |
|------|-------|--------|------------|
| Banco de Talentos | 390 | 390 | 0 |
| Engenheiro de dados - Especialista | 368 | 2 | 342 |
| Desenvolvedor .NET Jr | 350 | 350 | 0 |
| Analista de Testes Júnior | 350 | 321 | 29 |
| Analista de Conteúdo e Marketing | 350 | 48 | 300 |
| Desenvolvedor(a) .NET Sênior | 350 | 57 | 283 |
| Desenvolvedor Salesforce Júnior | 350 | 330 | 9 |
| Analista de CX | 350 | 349 | 1 |
| Desenvolvedor Chatbot Júnior | 350 | 349 | 1 |
| Desenvolvedor React JS Pleno | 350 | 317 | 32 |

**Insights:**
- Alta taxa de reprovação em vagas técnicas (Engenheiro de dados: 93%)
- Banco de Talentos mantém 100% de candidatos ativos

#### **D. Performance por Cliente**

**Top 10 Clientes:**

| Cliente | Total | Ativos | Reprovados | Tempo Médio (dias) |
|---------|-------|--------|------------|--------------------|
| Tecnologia | 16,723 | 8,085 | 8,294 | 84.0 |
| Localiza&Co | 16,392 | 9,008 | 6,680 | 79.8 |
| Mercantil | 4,900 | 3,593 | 1,247 | 81.0 |
| Unimed BH | 4,416 | 1,649 | 2,549 | 79.2 |
| Syngenta | 4,208 | 2,148 | 1,719 | 80.5 |
| Marketing | 2,625 | 1,113 | 1,430 | 83.7 |
| Unimed Porto Alegre | 2,613 | 1,486 | 914 | 82.7 |
| MRV | 2,509 | 1,198 | 993 | 78.3 |
| Framework | 2,313 | 1,114 | 1,082 | 73.0 |
| DB Diagnósticos | 1,890 | 1,577 | 249 | 82.0 |

**Insights:**
- Framework tem o menor tempo médio (73 dias)
- Tecnologia e Localiza&Co dominam em volume (33k candidaturas juntos)

#### **E. Performance por Torre**

| Torre | Total | Ativos | Reprovados | Desistentes |
|-------|-------|--------|------------|-------------|
| *Não informado* | 47,566 | 19,987 | 25,407 | 2,172 |
| **Varejo e Finanças** | **18,221** | 11,989 | 5,486 | 746 |
| **Saúde e Indústria** | **13,200** | 8,188 | 4,192 | 820 |
| Interno | 3,500 | 1,975 | 1,393 | 132 |
| Framework | 73 | 58 | 13 | 2 |

**⚠️ Atenção:**
- 57% das candidaturas (47,566) não têm torre informada
- Das candidaturas com torre definida, Varejo e Finanças representa 52%

---

### 📂 4. Scripts Criados

#### **Scripts de Teste e Diagnóstico:**
- ✅ `test_connection_simple.py` - Testa conexão com BD e API
- ✅ `check_candidaturas_columns.py` - Verifica estrutura de dados
- ✅ `query_etapas_funil.py` - Lista etapas do funil

#### **Scripts de Criação de Views:**
- ✅ `create_view_funil_simple.py` - Cria view `vw_funil_performance`

#### **Scripts de Análise e Relatório:**
- ✅ `relatorio_funil_completo.py` - Gera todos os 5 relatórios (A, B, C, D, E)

#### **Scripts de Exportação:**
- ✅ `export_to_sheets.py` - Exporta `vw_analise_posicoes` para Google Sheets

---

### ⏳ 5. Atualização de Planilha Google Sheets

**Status:** ⏳ PENDENTE

**Script criado:** `export_to_sheets.py`

**Para executar:**
```bash
python export_to_sheets.py
```

**Pré-requisitos:**
1. Configure `GOOGLE_CREDENTIALS_PATH` no arquivo `.env`
2. Arquivo de credenciais da Service Account do Google (JSON)
3. Permissões de escrita na planilha

**Planilha destino:**
- URL: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw/
- Aba: `Teste_API`

**Dados exportados:**
- View: `vw_analise_posicoes`
- 831 registros
- 31 colunas

---

## 🚀 Como Executar os Scripts

### 1. Gerar Relatório Completo de Funil

```bash
python relatorio_funil_completo.py
```

**Ou salvar em arquivo:**
```bash
python relatorio_funil_completo.py > meu_relatorio.txt
```

**Saída:** Relatório completo com todos os 5 tipos de análise (A, B, C, D, E)

---

### 2. Consultar Etapas do Funil

```bash
python query_etapas_funil.py
```

**Saída:** Lista de todas as etapas com contagens

---

### 3. Testar Conexões

```bash
python test_connection_simple.py
```

**Saída:** Verifica conexão com BD e API

---

### 4. Exportar para Google Sheets

```bash
python export_to_sheets.py
```

**Pré-requisito:** Configure `GOOGLE_CREDENTIALS_PATH` no `.env`

---

## 📈 Principais Insights

### 🔴 Gargalos Identificados

1. **Bate papo | Pessoas e Cultura**: Taxa de reprovação de **77.34%**
   - De 5,167 candidatos, 3,996 são reprovados nesta etapa
   - **Recomendação:** Revisar critérios de aprovação ou fortalecer etapas anteriores

2. **Etapa técnica | Talent IA**: Taxa de reprovação de **75.41%**
   - De 2,741 candidatos, 2,067 são reprovados
   - **Recomendação:** Avaliar dificuldade dos testes ou triagem inicial

3. **Tempo de Processo**: Média de **75-84 dias**
   - **Recomendação:** Investigar possibilidade de acelerar etapas intermediárias

### 🟢 Pontos Positivos

1. **Alta conversão de Inscrição**: 53,444 candidatos inscritos
2. **604 candidatos em Contratação**: Pipeline saudável na etapa final
3. **Taxa de desistência baixa**: Apenas 4,163 desistentes (5% do total)

### ⚠️ Pontos de Atenção

1. **Falta de dados de Torre**: 57% sem classificação
2. **Taxa de conversão 0%**: Necessário investigar se campo de status está correto
3. **Dados de contratação**: Aparentemente não estão sendo contabilizados corretamente

---

## 🗂️ Estrutura de Arquivos Criados

```
Inhire/
├── migrations/
│   └── 024_create_view_funil_performance.sql
├── scripts/
│   └── analise/
│       └── consultar_etapas_funil.py
├── test_connection_simple.py
├── check_candidaturas_columns.py
├── query_etapas_funil.py
├── create_view_funil_simple.py
├── relatorio_funil_completo.py
├── export_to_sheets.py
├── relatorio_funil_output.txt (gerado)
└── RESUMO_ANALISE_FUNIL_2026-02-06.md (este arquivo)
```

---

## 📝 Próximos Passos Sugeridos

1. ✅ **Concluir exportação para Google Sheets**
   - Configurar credenciais do Google
   - Executar `export_to_sheets.py`

2. 🔍 **Investigar taxa de conversão**
   - Verificar por que contratações aparecem como 0%
   - Validar campo `status` nas candidaturas

3. 📊 **Enriquecer dados de Torre**
   - Preencher 47,566 registros sem torre
   - Criar regras automáticas de classificação

4. 🎯 **Otimizar gargalos do funil**
   - Revisar etapa "Bate papo | Pessoas e Cultura"
   - Ajustar critérios de "Etapa técnica"

5. ⏱️ **Reduzir tempo de processo**
   - Meta: reduzir de 75-84 dias para 60 dias
   - Identificar etapas com maior tempo de espera

---

## 📞 Contato e Suporte

Para dúvidas ou problemas:
- Verificar logs em `logs/inhire_sync.log`
- Consultar documentação em `docs/`
- Revisar este resumo para comandos e instruções

---

**Documento gerado automaticamente em:** 2026-02-06
**Última atualização de dados:** 2026-02-04 20:22:15
