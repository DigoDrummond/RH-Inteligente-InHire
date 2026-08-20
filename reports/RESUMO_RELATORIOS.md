# ✅ Relatórios Criados - Resumo Final

## 📊 Views Criadas no Banco de Dados

### 1. **vw_relatorio_requisicoes**

Contém **apenas os 3 campos solicitados**:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `descricao` | TEXT | Descrição da requisição |
| `titulo` | VARCHAR | Título/Nome da requisição |
| `data_solicitacao` | TIMESTAMP | Data da solicitação (timezone America/Sao_Paulo) |

**Estatísticas:**
- ✅ **356 requisições** encontradas em 2026
- ✅ Ordenadas por data mais recente primeiro

**Como usar:**
```sql
-- Ver todas as requisições de 2026
SELECT * FROM vw_relatorio_requisicoes
WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026;

-- Ver últimas 10 requisições
SELECT * FROM vw_relatorio_requisicoes LIMIT 10;

-- Exportar para CSV (via psql)
COPY (SELECT * FROM vw_relatorio_requisicoes
      WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026)
TO 'C:\requisicoes_2026.csv'
WITH CSV HEADER;
```

---

### 2. **vw_relatorio_candidaturas**

Contém **os 6 campos solicitados**:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `vaga_id` | BIGINT | ID da vaga |
| `status_candidatura` | VARCHAR | Status (active, hired, rejected, declined) |
| `nome_candidato` | VARCHAR | Nome do candidato |
| `email_candidato` | VARCHAR | Email do candidato |
| `etapa_candidatura` | VARCHAR | Etapa/stage atual |
| `conhecia_framework` | TEXT | Resposta "Você conhecia a Framework?" |

**Estatísticas:**
- ✅ **108.262 candidaturas** no total
- ⚠️ Campo `conhecia_framework` retornando `N/A` (precisa ajuste)

**Como usar:**
```sql
-- Ver todas as candidaturas
SELECT * FROM vw_relatorio_candidaturas LIMIT 100;

-- Ver candidaturas ativas
SELECT * FROM vw_relatorio_candidaturas
WHERE status_candidatura = 'active';

-- Exportar para CSV
COPY (SELECT * FROM vw_relatorio_candidaturas)
TO 'C:\candidaturas.csv'
WITH CSV HEADER;
```

---

## 📁 Arquivos Criados

### Scripts SQL
1. **`relatorio_requisicoes_simples.sql`** - Query simplificada de requisições
2. **`relatorio_candidaturas_simples.sql`** - Query simplificada de candidaturas

### Migrations (Views Permanentes)
3. **`062_create_view_relatorio_requisicoes.sql`** - Cria view de requisições
4. **`063_create_view_relatorio_candidaturas.sql`** - Cria view de candidaturas

### Scripts Python
5. **`criar_views.py`** - Script para criar e testar as views
6. **`gerar_relatorios.py`** - Script para exportar relatórios (Excel, CSV, JSON)
7. **`testar_relatorios.py`** - Script de testes

### Documentação
8. **`README.md`** - Documentação completa
9. **`GUIA_INTEGRACAO.md`** - Integração com Power BI, Excel, etc.
10. **`RESUMO_RELATORIOS.md`** - Este arquivo

---

## 🚀 Como Usar

### Opção 1: Consultar Views Diretamente (Mais Simples)

```bash
# Via psql
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire

# Dentro do psql
SELECT * FROM vw_relatorio_requisicoes WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026;
SELECT * FROM vw_relatorio_candidaturas LIMIT 100;
```

### Opção 2: Exportar para Excel/CSV (Python)

```bash
cd reports
python gerar_relatorios.py
```

Arquivos gerados em `reports/exports/`:
- `relatorio_requisicoes_YYYYMMDD_HHMMSS.xlsx`
- `relatorio_candidaturas_YYYYMMDD_HHMMSS.xlsx`

### Opção 3: Power BI

1. **Obter Dados** → **PostgreSQL**
2. Servidor: `localhost:5432`, Database: `inhire`
3. Na janela de navegador, selecione:
   - `vw_relatorio_requisicoes`
   - `vw_relatorio_candidaturas`

---

## ⚠️ IMPORTANTE: Campo "Você conhecia a Framework?"

Atualmente o campo **`conhecia_framework`** está retornando `N/A` para todas as candidaturas.

### Por quê?

O campo está tentando extrair de múltiplas variações de chaves JSON:
- `stage_metadata->>'conhecia_framework'`
- `stage_metadata->>'conheciaFramework'`
- `stage_metadata->'customFields'->>'conhecia_framework'`
- Etc.

### Como Encontrar a Chave Correta?

Execute este SQL para explorar a estrutura dos metadados:

```sql
-- Ver estrutura dos metadados de candidaturas
SELECT
    id,
    nome_candidato,
    -- Ver metadados formatados
    jsonb_pretty(stage_metadata::jsonb) AS stage_metadata,
    jsonb_pretty(phase_metadata::jsonb) AS phase_metadata
FROM candidaturas
WHERE stage_metadata IS NOT NULL
   OR phase_metadata IS NOT NULL
LIMIT 10;
```

### Depois de Identificar a Chave

Edite a view (arquivo `063_create_view_relatorio_candidaturas.sql:21-41`) e ajuste o caminho JSON:

```sql
-- Exemplo: Se a chave for 'framework_conhecimento'
stage_metadata::jsonb->>'framework_conhecimento'

-- Ou se estiver dentro de um array customFields
stage_metadata::jsonb->'customFields'->0->>'conhecia_framework'
```

Depois recrie a view:
```bash
python reports/criar_views.py
```

---

## 📊 Dados de 2026 Disponíveis

### Requisições
✅ **356 requisições** de 2026 encontradas

**Exemplos:**
- Desenvolvedor(a) Fullstack Senior (.NET/React)
- Desenvolvedor React Pleno
- Agile Master Jr.
- Delivery Manager
- Analista de BI - Sênior
- Full Stack IA Senior
- Tech Lead Senior
- Arquiteto(a) de Solução e Integrações

### Candidaturas
✅ **108.262 candidaturas** no total

**Etapas mais comuns:**
- Etapa técnica | Talent IA
- Bate papo | Pessoas e Gestão
- Inscrição
- Bate Papo | Cliente
- Aguardando Devolutiva IA
- Abordagem

**Status:**
- ACTIVE (ativas)
- REJECTED (rejeitadas)
- HIRED (contratadas)
- DECLINED (recusadas)

---

## 🔧 Troubleshooting

### 1. Views não existem

```bash
# Recriar views
python reports/criar_views.py
```

### 2. Erro de permissão

```sql
-- Conceder acesso
GRANT SELECT ON vw_relatorio_requisicoes TO seu_usuario;
GRANT SELECT ON vw_relatorio_candidaturas TO seu_usuario;
```

### 3. Campo "conhecia_framework" retorna N/A

Siga os passos em **"Como Encontrar a Chave Correta?"** acima.

### 4. Dados desatualizados

```bash
# Sincronizar dados
python sync_incremental_completo.py --completa
```

---

## 📈 Próximos Passos

1. ✅ Views criadas e testadas
2. ⚠️ **Ajustar campo `conhecia_framework`** (pendente)
3. ✅ Documentação completa
4. ✅ Scripts de exportação prontos
5. ⚠️ **Integrar com Power BI/Excel** (opcional)

---

## 📞 Consultas Úteis

### Estatísticas de Requisições 2026

```sql
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE titulo LIKE '%Desenvolvedor%') AS devs,
    COUNT(*) FILTER (WHERE titulo LIKE '%Senior%' OR titulo LIKE '%Sênior%') AS seniors,
    MIN(data_solicitacao) AS primeira,
    MAX(data_solicitacao) AS ultima
FROM vw_relatorio_requisicoes
WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026;
```

### Estatísticas de Candidaturas por Status

```sql
SELECT
    status_candidatura,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentual
FROM vw_relatorio_candidaturas
GROUP BY status_candidatura
ORDER BY total DESC;
```

### Candidaturas por Etapa

```sql
SELECT
    etapa_candidatura,
    COUNT(*) AS total
FROM vw_relatorio_candidaturas
GROUP BY etapa_candidatura
ORDER BY total DESC
LIMIT 10;
```

---

**Última atualização:** 2026-07-21
**Status:** ✅ Views criadas e funcionando
**Pendência:** ⚠️ Ajustar extração do campo "Você conhecia a Framework?"
