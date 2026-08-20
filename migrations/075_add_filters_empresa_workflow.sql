-- Migration 075: Adicionar filtros empresa e workflow de aprovação
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição:
--   1. vw_relatorio_candidaturas: Adiciona filtros e remove tipo_contratacao
--   2. vw_relatorio_requisicoes: Adiciona filtros
--
--   FILTROS:
--   - empresa = 'Framework' (via clientes.name)
--   - workflow != 'Requisição Posições Non Billable' (via requisicoes.approval_workflow->>'name')

-- ============================================================================
-- 1. VIEW DE CANDIDATURAS
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- Extract "Você conhecia a Framework Digital?" from JSON
    -- ID CORRETO: 58401823-2cf5-4e0c-93eb-07c46508eb3a
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
WHERE EXTRACT(YEAR FROM c.created_at) = 2026
  AND cl.name = 'Framework'                                 -- Filtro: Framework
  AND (r.approval_workflow->>'name' IS NULL OR r.approval_workflow->>'name' != 'Requisição Posições Non Billable')  -- Excluir Non Billable
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas de 2026 - Framework (exceto Non Billable).

 Filtros aplicados:
 - Ano: 2026
 - Empresa: Framework (via clientes.name)
 - Workflow de aprovação: Excluir "Requisição Posições Non Billable" (via requisicoes.approval_workflow)

 Custom fields extraídos:
 - conhecia_framework (58401823-2cf5-4e0c-93eb-07c46508eb3a): "Sim" ou "Não"

 Migration 075 (2026-07-22):
 - Removido campo tipo_contratacao (não necessário)
 - Adicionado JOIN com clientes para filtro de empresa
 - Adicionado JOIN com requisicoes para filtro de workflow
 - Filtros: Framework Digital + Requisição Posições Billable';


-- ============================================================================
-- 2. VIEW DE REQUISIÇÕES
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    r.id,
    r.inhire_id,
    v.name AS titulo,

    -- Descrição limpa (sem HTML)
    TRIM(REGEXP_REPLACE(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                COALESCE(r.description, ''),
                '<[^>]+>', '', 'g'
            ),
            '&nbsp;', ' ', 'g'
        ),
        '\s+', ' ', 'g'
    )) AS descricao,

    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao,
    r.status,
    r.created_at,
    r.updated_at

FROM requisicoes r
INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
WHERE r.requested_at IS NOT NULL
  AND v.name IS NOT NULL
  AND TRIM(v.name) != ''
  AND cl.name = 'Framework'                                 -- Filtro: Framework
  AND (r.approval_workflow->>'name' IS NULL OR r.approval_workflow->>'name' != 'Requisição Posições Non Billable')  -- Excluir Non Billable
ORDER BY r.requested_at DESC;

COMMENT ON VIEW vw_relatorio_requisicoes IS
'Relatório de requisições - Framework (exceto Non Billable).

 Filtros aplicados:
 - Empresa: Framework (via clientes.name)
 - Workflow de aprovação: Excluir "Requisição Posições Non Billable" (via requisicoes.approval_workflow)
 - Apenas requisições com data de solicitação
 - Apenas vagas com título preenchido

 Migration 075 (2026-07-22):
 - Adicionado JOIN com clientes para filtro de empresa
 - Filtros: Framework Digital + Requisição Posições Billable';
