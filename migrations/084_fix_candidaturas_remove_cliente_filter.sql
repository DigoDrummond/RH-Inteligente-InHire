-- Migration 084: Corrigir filtros da view vw_relatorio_candidaturas
-- EXECUÇÃO MANUAL
-- Data: 2026-08-05
-- Autor: Claude Code

-- ============================================================================
-- CORREÇÃO DE FILTROS:
-- ============================================================================
-- ANTES (Migration 083):
--   - Cliente: 'Framework'
--   - Workflow: 'Requisição Posições Billable'
--   - Ano: TODOS
--   - Resultado: 5 registros
--
-- DEPOIS (Migration 084):
--   - Cliente: REMOVIDO (todos os clientes)
--   - Workflow: 'Requisição Posições Billable' (MANTIDO)
--   - Ano: 2026 (ADICIONADO)
--   - Resultado esperado: ~5.389 registros
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT DISTINCT ON (c.id)
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS cliente,
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,
    r.approval_workflow->>'name' AS nome_workflow_aprovacao,
    c.talent_name,
    c.talent_email,
    t.phone AS talent_phone,                  -- ✅ Telefone incluído
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- Extract "Você conhecia a Framework Digital?" from JSON
    -- ID: 58401823-2cf5-4e0c-93eb-07c46508eb3a
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
LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id   -- ✅ JOIN para telefone

WHERE
    -- Filtro 1: Apenas ano 2026
    EXTRACT(YEAR FROM c.created_at) = 2026

    -- Filtro 2: Apenas workflow "Requisição Posições Billable"
    AND r.approval_workflow->>'name' = 'Requisição Posições Billable'

    -- ❌ REMOVIDO: Filtro de cliente (cl.name = 'Framework')
    --    Agora retorna TODOS os clientes

ORDER BY c.id, r.requested_at DESC NULLS LAST;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas 2026 - Requisição Posições Billable - TODOS OS CLIENTES.

Filtros aplicados:
- Ano: 2026 (via EXTRACT(YEAR FROM c.created_at))
- Workflow: Requisição Posições Billable (via requisicoes.approval_workflow->>"name")
- Clientes: TODOS (sem filtro - inclui Framework, clientes externos, etc.)

Campos incluídos:
- id: ID da candidatura
- vaga_id: ID da vaga
- vaga_nome: Nome da vaga
- cliente: Nome do cliente (Framework, clientes externos, etc.)
- empresa: Empresa da requisição (custom field)
- nome_workflow_aprovacao: Nome do workflow de aprovação
- talent_name: Nome do talento
- talent_email: E-mail do talento
- talent_phone: Telefone do talento (via talentos.phone) ✅ NOVO
- etapa_candidatura: Etapa/stage atual
- status_candidatura: Status atual
- conhecia_framework: Custom field "Você conhecia a Framework?" (Sim/Não)
- created_at: Data de criação da candidatura
- ultima_atualizacao: Última atualização (via updated_at_inhire)

Correções (Migration 084 - 2026-08-05):
- REMOVIDO: Filtro de cliente (cl.name = "Framework")
- ADICIONADO: Filtro de ano (EXTRACT(YEAR FROM c.created_at) = 2026)
- MANTIDO: Filtro de workflow (Requisição Posições Billable)
- MANTIDO: Campo talent_phone da tabela talentos
- MANTIDO: DISTINCT ON (c.id) para evitar duplicação por múltiplas requisições

Resultado esperado: ~5.389 registros (todas as candidaturas de 2026 com workflow "Requisição Posições Billable")';

-- ============================================================================
-- QUERIES DE VALIDAÇÃO (executar após aplicar a migration):
-- ============================================================================

-- 1. Verificar total de registros
-- SELECT COUNT(*) as total_registros FROM vw_relatorio_candidaturas;
-- Resultado esperado: ~5.389

-- 2. Verificar telefones preenchidos
-- SELECT
--     COUNT(*) as total,
--     COUNT(talent_phone) as com_telefone,
--     COUNT(*) - COUNT(talent_phone) as sem_telefone,
--     ROUND(COUNT(talent_phone)::numeric / COUNT(*) * 100, 2) as pct_com_telefone
-- FROM vw_relatorio_candidaturas;

-- 3. Ver clientes incluídos
-- SELECT DISTINCT cliente, COUNT(*) as total
-- FROM vw_relatorio_candidaturas
-- WHERE cliente IS NOT NULL
-- GROUP BY cliente
-- ORDER BY total DESC
-- LIMIT 10;

-- 4. Ver amostra de dados
-- SELECT
--     talent_name,
--     talent_email,
--     talent_phone,
--     vaga_nome,
--     cliente,
--     nome_workflow_aprovacao
-- FROM vw_relatorio_candidaturas
-- LIMIT 10;
