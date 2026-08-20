-- Migration 077: Corrigir campos empresa e tipo_posicao (usar custom fields)
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição:
--   Corrigir campos que estavam usando as fontes erradas:
--   - empresa: deve vir de custom_fields da requisição, não de clientes.name
--   - tipo_posicao: deve vir de custom_fields 'Tipo de Serviço', não de approval_workflow
--   - cliente: adicionar coluna com clientes.name

-- ============================================================================
-- 1. VIEW DE CANDIDATURAS
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS cliente,                                      -- Cliente (tabela clientes)
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,              -- Empresa (custom field)
    get_custom_field_value(r.custom_fields, 'Tipo de Serviço') AS tipo_posicao, -- Tipo posição (custom field)
    r.approval_workflow->>'name' AS workflow_aprovacao,      -- Workflow de aprovação
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
'Relatório de candidaturas de 2026 - TODAS as empresas e tipos.

 Filtros aplicados:
 - Ano: 2026

 Colunas disponíveis para filtro:
 - cliente: Nome do cliente (via clientes.name)
 - empresa: Empresa da requisição (via requisicoes.custom_fields.Empresa)
 - tipo_posicao: Tipo de serviço (via requisicoes.custom_fields.Tipo de Serviço)
 - workflow_aprovacao: Nome do workflow (via requisicoes.approval_workflow)

 Custom fields extraídos:
 - conhecia_framework (58401823-2cf5-4e0c-93eb-07c46508eb3a): "Sim" ou "Não"

 Migration 077 (2026-07-22):
 - CORRIGIDO: empresa agora vem de custom_fields (não de clientes.name)
 - CORRIGIDO: tipo_posicao vem de custom_fields Tipo de Serviço (não de approval_workflow)
 - ADICIONADO: coluna cliente com clientes.name
 - ADICIONADO: coluna workflow_aprovacao com approval_workflow->>"name"';


-- ============================================================================
-- 2. VIEW DE REQUISIÇÕES
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    r.id,
    r.inhire_id,
    v.name AS titulo,
    cl.name AS cliente,                                      -- Cliente (tabela clientes)
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,              -- Empresa (custom field)
    get_custom_field_value(r.custom_fields, 'Tipo de Serviço') AS tipo_posicao, -- Tipo posição (custom field)
    r.approval_workflow->>'name' AS workflow_aprovacao,      -- Workflow de aprovação

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
'Relatório de requisições - TODAS as empresas e tipos.

 Colunas disponíveis para filtro:
 - cliente: Nome do cliente (via clientes.name)
 - empresa: Empresa da requisição (via requisicoes.custom_fields.Empresa)
 - tipo_posicao: Tipo de serviço (via requisicoes.custom_fields.Tipo de Serviço)
 - workflow_aprovacao: Nome do workflow (via requisicoes.approval_workflow)

 Filtros básicos:
 - Apenas requisições com data de solicitação
 - Apenas vagas com título preenchido

 Migration 077 (2026-07-22):
 - CORRIGIDO: empresa agora vem de custom_fields (não de clientes.name)
 - CORRIGIDO: tipo_posicao vem de custom_fields Tipo de Serviço (não de approval_workflow)
 - ADICIONADO: coluna cliente com clientes.name
 - ADICIONADO: coluna workflow_aprovacao com approval_workflow->>"name"';
