-- Migration 080: Atualizar filtros da view vw_relatorio_candidaturas
-- Data: 2026-08-05
-- Autor: Claude Code
-- Descrição:
--   1. Filtrar apenas empresa "Framework Digital"
--   2. Filtrar apenas requisições tipo "Posições Billable"
--   3. Remover filtro de ano (pegar todos os anos)
--   4. Resolver duplicação de registros usando DISTINCT ON

-- ============================================================================
-- VIEW DE CANDIDATURAS - FRAMEWORK DIGITAL - POSIÇÕES BILLABLE
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT DISTINCT ON (c.id)  -- ← Garante 1 linha por candidatura (remove duplicação)
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    cl.name AS cliente,
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,
    r.approval_workflow->>'name' AS nome_workflow_aprovacao,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- Extract "Você conhecia a Framework Digital?" from JSON
    -- ID CORRETO: 58401823-2cf5-4e0c-93eb-07c46508eb3a
    -- Formato: [{"id": "...", "label": "Sim", "value": "Sim"}]
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

WHERE
    -- Filtro 1: Apenas Framework Digital
    cl.name = 'Framework Digital'

    -- Filtro 2: Apenas requisições "Posições Billable"
    AND r.approval_workflow->>'name' = 'Posições Billable'

    -- Filtro 3: Removido filtro de ano (pega todos os anos)

ORDER BY
    c.id,                           -- ← Necessário para DISTINCT ON
    r.requested_at DESC NULLS LAST; -- ← Pega a requisição mais recente se houver múltiplas

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas - Framework Digital - Posições Billable (TODOS OS ANOS).

Filtros aplicados:
- Empresa: Framework Digital (via clientes.name)
- Tipo de requisição: Posições Billable (via requisicoes.approval_workflow->>"name")
- Anos: TODOS (sem filtro de ano)

Correções (Migration 080):
- DISTINCT ON para evitar duplicação por múltiplas requisições
- Removido filtro de ano (EXTRACT(YEAR FROM created_at) = 2026)
- Ordem garantida: candidatura + requisição mais recente

Custom fields extraídos:
- conhecia_framework (58401823-2cf5-4e0c-93eb-07c46508eb3a): "Sim" ou "Não"

Criado em: 2026-08-05';
