-- Migration 071: Corrigir view vw_relatorio_candidaturas
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição: Corrige duplicação do campo status e ajusta extração de custom_fields

-- 1. Corrigir duplicação de status
-- 2. Manter extração de conhecia_framework (mesmo que atualmente retorne NULL)
--    para quando o campo existir na API

DROP VIEW IF EXISTS vw_relatorio_candidaturas;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,    -- FIXME: Removida duplicação (era linha 19 + 23)

    -- Extract "Você conhecia a Framework Digital?" from JSON
    -- Nota: Campo ID '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' atualmente não existe nos dados
    -- Mantido para quando o campo for adicionado na API
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' THEN
            (c.custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a')::jsonb->>0
        ELSE NULL
    END AS conhecia_framework,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas de 2026 com custom fields.

 Correções (Migration 071):
 - Removida duplicação do campo status (estava nas linhas 19 e 23)
 - Mantida extração de conhecia_framework para compatibilidade futura

 Nota: Campo custom_field ''55282edb-bb11-4445-8cd6-3c0c6b9ddb9a'' (conhecia_framework)
 atualmente não existe nos dados retornados pela API. A query retornará NULL até
 que este campo seja adicionado aos custom_fields das candidaturas.';
