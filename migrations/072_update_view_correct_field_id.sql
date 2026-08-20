-- Migration 072: Atualizar view com ID correto do campo conhecia_framework
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição: Corrige ID do campo custom field 'Você conhecia a Framework Digital?'
--
-- ID ANTIGO (errado): 55282edb-bb11-4445-8cd6-3c0c6b9ddb9a
-- ID CORRETO (real):  58401823-2cf5-4e0c-93eb-07c46508eb3a

DROP VIEW IF EXISTS vw_relatorio_candidaturas;

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
    -- Formato: [{"id": "...", "label": "Sim", "value": "Sim"}]
    -- Extraímos o primeiro elemento do array e pegamos o 'label'
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '58401823-2cf5-4e0c-93eb-07c46508eb3a' THEN
            (c.custom_fields->'58401823-2cf5-4e0c-93eb-07c46508eb3a'->0->>'label')
        ELSE NULL
    END AS conhecia_framework,

    -- Extract "Tipo de contratação" (campo adicional identificado)
    -- ID: 745c6a26-c3fa-4389-9b1e-75f54934c9ae
    -- Valores: CLT Flex, CLT Full, PJ
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '745c6a26-c3fa-4389-9b1e-75f54934c9ae' THEN
            (c.custom_fields->'745c6a26-c3fa-4389-9b1e-75f54934c9ae'->0->>'label')
        ELSE NULL
    END AS tipo_contratacao,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas de 2026 com custom fields.

 Migration 072 (2026-07-22):
 - Corrigido ID do campo conhecia_framework
 - ID correto: 58401823-2cf5-4e0c-93eb-07c46508eb3a
 - Adicionado campo tipo_contratacao (745c6a26-c3fa-4389-9b1e-75f54934c9ae)
 - Extração usando formato correto: ->0->>''label''

 Campos disponíveis:
 - conhecia_framework: "Sim" ou "Não"
 - tipo_contratacao: "CLT Flex", "CLT Full", "PJ"';
