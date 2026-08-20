-- Migration 082: View SEM FILTROS para debug
-- EXECUÇÃO MANUAL
-- Data: 2026-08-05

-- ============================================================================
-- VIEW TEMPORÁRIA SEM FILTROS - PARA DEBUG
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
    t.phone AS talent_phone,
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
LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id

-- ⚠️ SEM FILTROS - RETORNA TUDO
-- WHERE cl.name = 'Framework Digital'
--   AND r.approval_workflow->>'name' = 'Posições Billable'

ORDER BY c.id, r.requested_at DESC NULLS LAST;

-- ============================================================================
-- Queries para diagnóstico:
-- ============================================================================

-- Ver total de registros
-- SELECT COUNT(*) FROM vw_relatorio_candidaturas;

-- Ver clientes disponíveis
-- SELECT DISTINCT cliente FROM vw_relatorio_candidaturas WHERE cliente IS NOT NULL ORDER BY cliente LIMIT 20;

-- Ver workflows disponíveis
-- SELECT DISTINCT nome_workflow_aprovacao FROM vw_relatorio_candidaturas WHERE nome_workflow_aprovacao IS NOT NULL ORDER BY nome_workflow_aprovacao LIMIT 20;

-- Ver combinações cliente + workflow
-- SELECT DISTINCT cliente, nome_workflow_aprovacao, COUNT(*) as total
-- FROM vw_relatorio_candidaturas
-- WHERE cliente IS NOT NULL AND nome_workflow_aprovacao IS NOT NULL
-- GROUP BY cliente, nome_workflow_aprovacao
-- ORDER BY cliente, nome_workflow_aprovacao;
