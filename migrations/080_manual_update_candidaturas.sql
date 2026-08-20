-- Migration 080: Atualizar filtros da view vw_relatorio_candidaturas
-- EXECUÇÃO MANUAL
-- Data: 2026-08-05

-- ============================================================================
-- INSTRUÇÕES DE EXECUÇÃO:
-- ============================================================================
-- 1. Abrir psql ou PgAdmin
-- 2. Conectar ao banco "inhire"
-- 3. Executar o comando abaixo
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
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- Extract "Você conhecia a Framework Digital?" from JSON
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
    -- Filtro: Apenas Framework Digital
    cl.name = 'Framework Digital'

    -- Filtro: Apenas Posições Billable
    AND r.approval_workflow->>'name' = 'Posições Billable'

ORDER BY c.id, r.requested_at DESC NULLS LAST;

-- ============================================================================
-- Verificar resultado:
-- ============================================================================
-- SELECT COUNT(*) FROM vw_relatorio_candidaturas;
-- SELECT * FROM vw_relatorio_candidaturas LIMIT 10;
