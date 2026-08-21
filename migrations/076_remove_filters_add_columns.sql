-- Migration 076: Remover filtros e adicionar colunas empresa e workflow
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição:
--   1. vw_relatorio_candidaturas: Remove filtros, adiciona colunas empresa e workflow
--   2. vw_relatorio_requisicoes: Remove filtros, adiciona coluna empresa

-- ============================================================================
-- 1. VIEW DE CANDIDATURAS
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS empresa,                                      -- NOVO: Nome da empresa
    r.approval_workflow->>'name' AS tipo_requisicao,         -- NOVO: Tipo de requisição
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
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas de 2026 - TODAS as empresas e workflows.

 Filtros aplicados:
 - Ano: 2026

 Colunas disponíveis para filtro:
 - empresa: Nome da empresa/cliente (via clientes.name)
 - tipo_requisicao: Nome do workflow de aprovação (via requisicoes.approval_workflow)

 Custom fields extraídos:
 - conhecia_framework (58401823-2cf5-4e0c-93eb-07c46508eb3a): "Sim" ou "Não"

 Migration 076 (2026-07-22):
 - Removidos filtros de empresa e workflow
 - Adicionadas colunas: empresa, tipo_requisicao
 - Permite filtrar posteriormente via SQL ou aplicação';


-- ============================================================================
-- 2. VIEW DE REQUISIÇÕES
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    r.id,
    r.inhire_id,
    v.name AS titulo,
    cl.name AS empresa,                                      -- NOVO: Nome da empresa
    r.approval_workflow->>'name' AS tipo_requisicao,         -- NOVO: Tipo de requisição

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
ORDER BY r.requested_at DESC;

COMMENT ON VIEW vw_relatorio_requisicoes IS
'Relatório de requisições - TODAS as empresas e workflows.

 Colunas disponíveis para filtro:
 - empresa: Nome da empresa/cliente (via clientes.name)
 - tipo_requisicao: Nome do workflow de aprovação (via requisicoes.approval_workflow)

 Filtros básicos:
 - Apenas requisições com data de solicitação
 - Apenas vagas com título preenchido

 Migration 076 (2026-07-22):
 - Removidos filtros de empresa e workflow
 - Adicionadas colunas: empresa, tipo_requisicao
 - Permite filtrar posteriormente via SQL ou aplicação';
