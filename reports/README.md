# Relatórios Inhire

Este diretório contém os relatórios SQL e scripts Python para gerar análises de **Requisições** e **Candidaturas** do sistema Inhire.

## 📋 Conteúdo

### Arquivos SQL

1. **`relatorio_requisicoes.sql`**
   - Relatório completo de requisições
   - Campos principais: `description`, `name`, `requested_at`
   - Inclui queries auxiliares para análises estatísticas

2. **`relatorio_candidaturas.sql`**
   - Relatório completo de candidaturas
   - Campos principais: `vaga_id`, `status`, `talent_name`, `talent_email`
   - Inclui etapa, fase e custom fields
   - Extrai campo "Você conhecia a Framework?"

### Scripts Python

3. **`gerar_relatorios.py`**
   - Script principal para gerar relatórios automaticamente
   - Exporta em múltiplos formatos: Excel, CSV, JSON
   - Formatação automática do Excel

## 🚀 Como Usar

### Opção 1: Executar Queries SQL Diretamente

```bash
# Relatório de Requisições
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f relatorio_requisicoes.sql

# Relatório de Candidaturas
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f relatorio_candidaturas.sql
```

### Opção 2: Usar Script Python (Recomendado)

```bash
# Gerar todos os relatórios em Excel, CSV e JSON
python gerar_relatorios.py
```

Os arquivos serão salvos no diretório `exports/` com timestamp:
```
reports/exports/
├── relatorio_requisicoes_20260721_143022.xlsx
├── relatorio_requisicoes_20260721_143022.csv
├── relatorio_requisicoes_20260721_143022.json
├── relatorio_candidaturas_20260721_143022.xlsx
├── relatorio_candidaturas_20260721_143022.csv
└── relatorio_candidaturas_20260721_143022.json
```

## 📊 Relatório de Requisições

### Campos Principais

| Campo | Descrição |
|-------|-----------|
| `titulo_requisicao` | Nome/título da requisição |
| `descricao` | Descrição completa da requisição |
| `data_solicitacao` | Data em que foi solicitada |
| `status_requisicao` | Status atual (pending, approved, rejected) |
| `nome_vaga` | Nome da vaga relacionada |
| `solicitante_nome` | Nome do solicitante |
| `aprovador_nome` | Nome do aprovador (se aprovada) |
| `salario_minimo` | Salário mínimo oferecido |
| `salario_maximo` | Salário máximo oferecido |
| `quantidade_posicoes` | Número de posições solicitadas |

### Queries Auxiliares Disponíveis

- **Resumo Estatístico**: Estatísticas por status de requisição
- **Tempo de Aprovação**: Cálculo de dias para aprovação

## 📊 Relatório de Candidaturas

### Campos Principais

| Campo | Descrição |
|-------|-----------|
| `id_vaga` | ID da vaga |
| `nome_vaga` | Nome da vaga |
| `nome_candidato` | Nome do candidato |
| `email_candidato` | Email do candidato |
| `status_candidatura` | Status (active, hired, rejected, declined) |
| `etapa_atual` | Etapa atual da candidatura |
| `fase_atual` | Fase atual dentro da etapa |
| `dias_etapa_atual` | Dias na etapa atual |
| `origem_candidatura` | Fonte da candidatura |
| `conhecia_framework_stage` | Campo custom "Você conhecia a Framework?" |

### Queries Auxiliares Disponíveis

- **Resumo por Status e Etapa**: Estatísticas agrupadas
- **Timeline Completa**: Histórico de transições de cada candidatura
- **Diversidade**: Análise de diversidade dos candidatos
- **Exploração de Custom Fields**: Para descobrir estrutura de metadados

## 🔍 Campo Customizado "Você conhecia a Framework?"

Este campo está sendo extraído dos metadados JSON da candidatura. Existem duas colunas no relatório:

- `conhecia_framework_stage`: Extrai do `stage_metadata`
- `conhecia_framework_phase`: Extrai do `phase_metadata`

### ⚠️ Importante

A extração atual usa:
```sql
stage_metadata::jsonb->>'conhecia_framework'
```

**Você pode precisar ajustar o caminho JSON** conforme a estrutura real dos seus dados. Use a query auxiliar "Extrair Custom Fields" no arquivo SQL para explorar a estrutura:

```sql
SELECT
    c.id,
    c.talent_name,
    jsonb_pretty(c.stage_metadata::jsonb),
    jsonb_pretty(c.phase_metadata::jsonb)
FROM candidaturas c
WHERE c.stage_metadata IS NOT NULL
LIMIT 10;
```

Possíveis caminhos alternativos:
```sql
-- Se estiver dentro de customFields
stage_metadata::jsonb->'customFields'->>'conhecia_framework'

-- Se usar outro nome de chave
stage_metadata::jsonb->>'conheciaFramework'
stage_metadata::jsonb->>'conhecia_frwk'
```

## 📦 Dependências Python

Para usar o script Python, instale as dependências:

```bash
pip install pandas psycopg2-binary xlsxwriter openpyxl
```

Ou use o requirements.txt do projeto:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

### Conexão com Banco de Dados

O script Python usa as seguintes configurações (arquivo `gerar_relatorios.py:46-52`):

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', 'postgres')
}
```

Para maior segurança, defina a senha via variável de ambiente:

```bash
# Windows
set DB_PASSWORD=sua_senha_postgres

# Linux/Mac
export DB_PASSWORD=sua_senha_postgres
```

## 📈 Exemplos de Uso

### Filtrar por Vaga Específica

```sql
-- Candidaturas de uma vaga específica
SELECT * FROM (
    -- Cole aqui a query completa do relatorio_candidaturas.sql
) AS relatorio
WHERE id_vaga = 123;
```

### Filtrar por Período

```sql
-- Requisições dos últimos 30 dias
SELECT * FROM (
    -- Cole aqui a query completa do relatorio_requisicoes.sql
) AS relatorio
WHERE data_solicitacao >= CURRENT_DATE - INTERVAL '30 days';
```

### Exportar para CSV via psql

```bash
# Requisições
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire \
  -c "COPY (SELECT * FROM relatorio_requisicoes) TO STDOUT WITH CSV HEADER" \
  > requisicoes.csv

# Candidaturas
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire \
  -c "COPY (SELECT * FROM relatorio_candidaturas) TO STDOUT WITH CSV HEADER" \
  > candidaturas.csv
```

## 🛠️ Personalização

### Adicionar Campos ao Relatório

Para adicionar novos campos, edite os arquivos SQL:

1. Identifique a tabela/coluna na estrutura do banco
2. Adicione o campo na seção `SELECT` da query principal
3. Se necessário, adicione `LEFT JOIN` para relacionamentos

Exemplo:
```sql
SELECT
    -- Campos existentes...
    c.novo_campo AS meu_novo_campo,
    -- ...
FROM candidaturas c
```

### Modificar Formatação do Excel

Edite a função `exportar_para_excel()` em `gerar_relatorios.py:134-175`:

```python
# Exemplo: Mudar cor do cabeçalho
header_format = workbook.add_format({
    'bold': True,
    'bg_color': '#FF5733',  # Nova cor
    'font_color': 'white',
    # ...
})
```

## 🔄 Atualização dos Dados

Os relatórios sempre usam os dados mais atualizados do banco de dados no momento da execução.

Para garantir dados atualizados:

1. Execute a sincronização incremental:
```bash
python sync_incremental_completo.py --completa
```

2. Gere os relatórios:
```bash
python reports/gerar_relatorios.py
```

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs do script Python
2. Teste as queries SQL diretamente no psql
3. Use a query "Extrair Custom Fields" para explorar metadados
4. Consulte a documentação do banco em `models/database.py`

## 📝 Changelog

### 2026-07-21 - Versão Inicial
- ✅ Relatório de Requisições criado
- ✅ Relatório de Candidaturas criado
- ✅ Script Python para exportação automática
- ✅ Suporte a Excel, CSV e JSON
- ✅ Queries auxiliares para análises
- ✅ Documentação completa

---

**Última atualização:** 2026-07-21
