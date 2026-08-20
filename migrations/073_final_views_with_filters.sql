-- Migration 073: Atualizar views com campos corretos e filtros
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição:
--   1. vw_relatorio_candidaturas: Remove duplicação, adiciona campo correto, filtros
--   2. vw_relatorio_requisicoes: Adiciona filtros

-- ============================================================================
-- 1. VIEW DE CANDIDATURAS
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    v.cliente_nome AS empresa,
    v.tipo_posicao,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,    -- FIXME: Removida duplicação

    -- Extract "Você conhecia a Framework Digital?" from JSON
    -- ID CORRETO: 58401823-2cf5-4e0c-93eb-07c46508eb3a
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '58401823-2cf5-4e0c-93eb-07c46508eb3a' THEN
            (c.custom_fields->'58401823-2cf5-4e0c-93eb-07c46508eb3a'->0->>'label')
        ELSE NULL
    END AS conhecia_framework,

    -- Extract "Tipo de contratação"
    -- ID: 745c6a26-c3fa-4389-9b1e-75f54934c9ae
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
  AND v.cliente_nome = 'Framework Digital'           -- Filtro: Framework
  AND v.tipo_posicao = 'Alocação Gerenciada'         -- Filtro: Alocação Gerenciada
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_relatorio_candidaturas IS
'Relatório de candidaturas de 2026 - Framework Digital - Alocação Gerenciada.

 Filtros aplicados:
 - Ano: 2026
 - Empresa: Framework Digital
 - Tipo de posição: Alocação Gerenciada

 Custom fields extraídos:
 - conhecia_framework (58401823-2cf5-4e0c-93eb-07c46508eb3a): "Sim" ou "Não"
 - tipo_contratacao (745c6a26-c3fa-4389-9b1e-75f54934c9ae): "CLT Flex", "CLT Full", "PJ"

 Migration 073 (2026-07-22):
 - Removida duplicação de status
 - ID correto de conhecia_framework
 - Adicionado tipo_contratacao
 - Filtros: Framework Digital + Alocação Gerenciada';


-- ============================================================================
-- 2. VIEW DE REQUISIÇÕES
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    r.id,
    r.inhire_id,
    v.name AS titulo,
    v.cliente_nome AS empresa,
    v.tipo_posicao,

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
WHERE r.requested_at IS NOT NULL
  AND v.name IS NOT NULL
  AND TRIM(v.name) != ''
  AND v.cliente_nome = 'Framework Digital'           -- Filtro: Framework
  AND v.tipo_posicao = 'Alocação Gerenciada'         -- Filtro: Alocação Gerenciada
ORDER BY r.requested_at DESC;

COMMENT ON VIEW vw_relatorio_requisicoes IS
'Relatório de requisições - Framework Digital - Alocação Gerenciada.

 Filtros aplicados:
 - Empresa: Framework Digital
 - Tipo de posição: Alocação Gerenciada
 - Apenas requisições com data de solicitação
 - Apenas vagas com título preenchido

 Migration 073 (2026-07-22):
 - Adicionados campos empresa e tipo_posicao
 - Filtros: Framework Digital + Alocação Gerenciada';
