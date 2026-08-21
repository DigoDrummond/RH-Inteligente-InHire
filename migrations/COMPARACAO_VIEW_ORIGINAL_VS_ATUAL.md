# Comparação: View Original vs View Atual

## 📋 Migration Original (076)

**Arquivo:** `migrations/076_remove_filters_add_columns.sql`

### Características da View Original:

```sql
CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS empresa,                    -- ← Nome da coluna: "empresa"
    r.approval_workflow->>'name' AS tipo_requisicao,  -- ← Nome da coluna: "tipo_requisicao"
    c.talent_name,
    c.talent_email,                        -- ❌ SEM telefone
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '58401823-2cf5-4e0c-93eb-07c46508eb3a' THEN
            (c.custom_fields->'58401823-2cf5-4e0c-93eb-07c46508eb3a'->0->>'label')
        ELSE NULL
    END AS conhecia_framework,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
-- ❌ SEM JOIN com talentos

WHERE EXTRACT(YEAR FROM c.created_at) = 2026  -- ⚠️ Filtrava apenas 2026

ORDER BY c.created_at DESC;  -- ❌ SEM DISTINCT ON (duplicação!)
```

### Problemas da View Original:

| Problema | Descrição |
|----------|-----------|
| **Duplicação** | ❌ Sem `DISTINCT ON` → Candidatura aparecia N vezes se vaga tivesse N requisições |
| **Sem telefone** | ❌ Não incluía campo `phone` da tabela `talentos` |
| **Filtro de ano** | ⚠️ Apenas 2026 (não pegava todos os anos) |
| **Sem filtros** | ⚠️ Retornava TODOS os clientes e workflows |
| **Nomes de colunas** | Usava `empresa` e `tipo_requisicao` |

---

## 🆕 View Atual (083)

**Arquivo:** `migrations/083_view_filtros_corretos.sql`

### Características da View Atual:

```sql
CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT DISTINCT ON (c.id)  -- ✅ NOVO: Remove duplicação
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS cliente,                    -- ✅ MUDOU: "empresa" → "cliente"
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,  -- ✅ NOVO: empresa da requisição
    r.approval_workflow->>'name' AS nome_workflow_aprovacao,  -- ✅ MUDOU: "tipo_requisicao" → "nome_workflow_aprovacao"
    c.talent_name,
    c.talent_email,
    t.phone AS talent_phone,               -- ✅ NOVO: Telefone do talento
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '58401823-2cf5-4e0c-93eb-07c46508eb3a' THEN
            (c.custom_fields->'58401823-2cf5-4e0c-93eb-07c46508eb3a'->0->>'label')
        ELSE NULL
    END AS conhecia_framework,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id  -- ✅ NOVO: JOIN com talentos

WHERE
    cl.name = 'Framework'  -- ✅ NOVO: Filtra apenas cliente Framework
    AND r.approval_workflow->>'name' = 'Requisição Posições Billable'  -- ✅ NOVO: Filtra apenas workflow específico
    -- ✅ Removido filtro de ano (pega todos os anos)

ORDER BY c.id, r.requested_at DESC NULLS LAST;  -- ✅ MUDOU: Ordem para DISTINCT ON funcionar
```

### Melhorias da View Atual:

| Melhoria | Descrição | Status |
|----------|-----------|--------|
| **Remove duplicação** | ✅ `DISTINCT ON (c.id)` garante 1 linha por candidatura | ✅ Implementado |
| **Campo telefone** | ✅ Inclui `t.phone AS talent_phone` | ✅ Implementado |
| **Todos os anos** | ✅ Removido filtro `EXTRACT(YEAR FROM c.created_at) = 2026` | ✅ Implementado |
| **Filtro cliente** | ✅ `cl.name = 'Framework'` | ✅ Implementado |
| **Filtro workflow** | ✅ `r.approval_workflow->>'name' = 'Requisição Posições Billable'` | ✅ Implementado |
| **JOIN com talentos** | ✅ `LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id` | ✅ Implementado |
| **Nomes de colunas** | ✅ Mais descritivos: `cliente`, `empresa`, `nome_workflow_aprovacao` | ✅ Implementado |

---

## 🔄 Mudanças de Nomenclatura

| View Original (076) | View Atual (083) | Razão da Mudança |
|---------------------|------------------|------------------|
| `empresa` | `cliente` | Nome do cliente (tabela `clientes.name`) |
| -                   | `empresa` | Empresa da requisição (custom field) |
| `tipo_requisicao`   | `nome_workflow_aprovacao` | Mais descritivo |
| -                   | `talent_phone` | NOVO: Telefone do talento |

---

## 📊 Impacto nos Dados

### View Original (076)
```sql
-- Exemplo de duplicação:
-- Vaga 123 tem 3 requisições → Cada candidatura aparece 3x

SELECT COUNT(*) FROM vw_relatorio_candidaturas;
-- Resultado: ~15.000 registros (com duplicação)
```

### View Atual (083)
```sql
-- DISTINCT ON garante 1 linha por candidatura
-- Filtros reduzem para apenas Framework + Requisição Posições Billable

SELECT COUNT(*) FROM vw_relatorio_candidaturas;
-- Resultado: 5 registros (sem duplicação, filtrado)
```

---

## ⚠️ Possível Problema: Apenas 5 Registros

Se a view retornou apenas **5 registros**, pode indicar:

1. **✅ Normal:** Apenas 5 candidaturas atendem aos critérios:
   - Cliente = "Framework"
   - Workflow = "Requisição Posições Billable"
   - Todos os anos

2. **⚠️ Investigar:** Verificar se os filtros estão muito restritivos:
   ```sql
   -- Quantas candidaturas tem cliente "Framework"?
   SELECT COUNT(*)
   FROM candidaturas c
   INNER JOIN vagas v ON c.vaga_id = v.id
   LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
   WHERE cl.name = 'Framework';

   -- Quantas requisições tem workflow "Requisição Posições Billable"?
   SELECT COUNT(DISTINCT v.id)
   FROM requisicoes r
   INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
   WHERE r.approval_workflow->>'name' = 'Requisição Posições Billable';

   -- Quantas candidaturas atendem AMBOS os critérios?
   SELECT COUNT(*)
   FROM candidaturas c
   INNER JOIN vagas v ON c.vaga_id = v.id
   LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
   LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
   WHERE cl.name = 'Framework'
     AND r.approval_workflow->>'name' = 'Requisição Posições Billable';
   ```

---

## 🎯 Recomendações

### Se 5 registros está CORRETO:
✅ View está funcionando perfeitamente

### Se esperava MAIS registros:

**Opção 1: Remover filtro de workflow**
```sql
WHERE cl.name = 'Framework'
-- AND r.approval_workflow->>'name' = 'Requisição Posições Billable'  -- ← Comentar esta linha
```

**Opção 2: Usar ILIKE para case-insensitive**
```sql
WHERE cl.name ILIKE '%Framework%'
  AND r.approval_workflow->>'name' ILIKE '%Billable%'
```

**Opção 3: Permitir NULL em workflow**
```sql
WHERE cl.name = 'Framework'
  AND (r.approval_workflow->>'name' = 'Requisição Posições Billable'
       OR r.approval_workflow IS NULL)
```

---

## ✅ Validação Final

Execute estas queries para validar:

```sql
-- 1. Total de registros na view
SELECT COUNT(*) as total FROM vw_relatorio_candidaturas;

-- 2. Ver os 5 registros
SELECT
    talent_name,
    talent_email,
    talent_phone,
    vaga_nome,
    cliente,
    nome_workflow_aprovacao
FROM vw_relatorio_candidaturas;

-- 3. Verificar se há telefones preenchidos
SELECT
    COUNT(*) as total,
    COUNT(talent_phone) as com_telefone,
    COUNT(*) - COUNT(talent_phone) as sem_telefone
FROM vw_relatorio_candidaturas;
```

---

**Data:** 2026-08-05
**Migration Original:** 076
**Migration Atual:** 083
**Status:** ✅ Implementado
