-- Migration 083: View com filtros CORRETOS
-- EXECUÇÃO MANUAL
-- Data: 2026-08-05

-- ============================================================================
-- VALORES CORRETOS IDENTIFICADOS:
-- - Cliente: "Framework" (não "Framework Digital")
-- - Workflow: "Requisição Posições Billable" (não "Posições Billable")
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
LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id

WHERE
    -- Filtro 1: Cliente "Framework" (VALOR CORRETO)
    cl.name = 'Framework'

    -- Filtro 2: Workflow "Requisição Posições Billable" (VALOR CORRETO)
    AND r.approval_workflow->>'name' = 'Requisição Posições Billable'

ORDER BY c.id, r.requested_at DESC NULLS LAST;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas - Framework - Requisição Posições Billable (TODOS OS ANOS).

Filtros aplicados:
- Cliente: Framework (via clientes.name)
- Workflow: Requisição Posições Billable (via requisicoes.approval_workflow->>"name")
- Anos: TODOS (sem filtro de ano)

Campos incluídos:
- id: ID da candidatura
- vaga_id: ID da vaga
- vaga_nome: Nome da vaga
- cliente: Nome do cliente (Framework)
- empresa: Empresa da requisição (custom field)
- nome_workflow_aprovacao: Nome do workflow
- talent_name: Nome do talento
- talent_email: E-mail do talento
- talent_phone: Telefone do talento
- etapa_candidatura: Etapa atual
- status_candidatura: Status atual
- conhecia_framework: Custom field (Sim/Não)
- created_at: Data de criação
- ultima_atualizacao: Última atualização

Migration 083 (2026-08-05):
- CORRIGIDO: Cliente = "Framework" (não "Framework Digital")
- CORRIGIDO: Workflow = "Requisição Posições Billable" (não "Posições Billable")
- Inclui campo talent_phone da tabela talentos
- DISTINCT ON para evitar duplicação';

-- ============================================================================
-- Verificar resultado:
-- ============================================================================
-- SELECT COUNT(*) FROM vw_relatorio_candidaturas;
-- SELECT talent_name, talent_email, talent_phone, vaga_nome FROM vw_relatorio_candidaturas LIMIT 10;
