-- ===============================================================
-- RELATÓRIO DE CANDIDATURAS
-- ===============================================================
-- Relatório completo de candidaturas com todas as informações
-- solicitadas: vaga_id, status, talent_name, talent_email,
-- etapa, status, e campo customizado "Você conhecia a Framework?"
--
-- Data de criação: 2026-07-21
-- ===============================================================

SELECT
    c.id AS id_candidatura,
    c.inhire_id AS inhire_id_candidatura,

    -- Informações da vaga
    c.vaga_id AS id_vaga,
    v.inhire_id AS inhire_id_vaga,
    v.name AS nome_vaga,
    v.status AS status_vaga,
    v.area AS area_vaga,
    v.seniority AS senioridade_vaga,

    -- Informações do candidato (solicitado)
    c.talent_name AS nome_candidato,
    c.talent_email AS email_candidato,
    c.talent_headline AS headline_candidato,
    c.talent_company AS empresa_candidato,
    c.talent_location AS localizacao_candidato,

    -- Status da candidatura (solicitado)
    c.status AS status_candidatura,

    -- Etapa da candidatura (solicitado)
    c.stage_name AS etapa_atual,
    c.stage_order AS ordem_etapa,
    c.phase_name AS fase_atual,
    c.phase_order AS ordem_fase,

    -- Tempo na etapa atual
    ROUND(c.time_in_current_stage / 86400000.0, 2) AS dias_etapa_atual,

    -- Fonte da candidatura
    c.source AS origem_candidatura,

    -- Informações do talento completo
    t.id AS id_talento_bd,
    t.inhire_id AS inhire_id_talento,
    t.phone AS telefone_talento,
    t.linkedin_username AS linkedin_talento,
    t.contact_method AS metodo_contato,

    -- Informações de diversidade do talento
    t.diversity_black AS diversidade_negro,
    t.diversity_woman AS diversidade_mulher,
    t.diversity_lgbt AS diversidade_lgbt,
    t.diversity_disability AS diversidade_deficiencia,
    t.diversity_trans AS diversidade_trans,

    -- Responsável pela candidatura
    c.user_name AS responsavel_nome,
    c.user_id AS responsavel_id,

    -- Extração do custom field "Você conhecia a Framework?"
    -- (Nota: Este campo pode estar na tabela custom_fields ou diretamente
    -- na candidatura. Adapte conforme a estrutura real dos dados)
    --
    -- Opção 1: Se estiver em um JSON no stage_metadata ou phase_metadata
    CASE
        WHEN c.stage_metadata IS NOT NULL THEN
            c.stage_metadata::jsonb->>'conhecia_framework'
        ELSE NULL
    END AS conhecia_framework_stage,

    CASE
        WHEN c.phase_metadata IS NOT NULL THEN
            c.phase_metadata::jsonb->>'conhecia_framework'
        ELSE NULL
    END AS conhecia_framework_phase,

    -- Metadata completa (caso precise extrair outros campos)
    c.stage_metadata AS metadata_etapa,
    c.phase_metadata AS metadata_fase,

    -- Auditoria
    c.updated_at_inhire AT TIME ZONE 'America/Sao_Paulo' AS atualizado_em_inhire,
    c.created_at AT TIME ZONE 'America/Sao_Paulo' AS criado_em_bd,
    c.updated_at AT TIME ZONE 'America/Sao_Paulo' AS atualizado_em_bd,

    -- IDs de referência
    c.talent_inhire_id AS talent_inhire_id,
    c.stage_id AS stage_id,
    c.phase_id AS phase_id

FROM candidaturas c
LEFT JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN talentos t ON c.talento_id = t.id

-- Ordenar por data de atualização mais recente
ORDER BY c.updated_at_inhire DESC NULLS LAST, c.created_at DESC;


-- ===============================================================
-- QUERY ALTERNATIVA: Resumo por Status e Etapa
-- ===============================================================

SELECT
    v.name AS vaga_nome,
    c.status AS status_candidatura,
    c.stage_name AS etapa,
    c.phase_name AS fase,
    COUNT(*) AS total_candidaturas,
    COUNT(DISTINCT c.talent_inhire_id) AS candidatos_unicos,
    AVG(c.time_in_current_stage / 86400000.0) AS media_dias_etapa,
    MIN(c.created_at AT TIME ZONE 'America/Sao_Paulo') AS primeira_candidatura,
    MAX(c.updated_at_inhire AT TIME ZONE 'America/Sao_Paulo') AS ultima_atualizacao

FROM candidaturas c
LEFT JOIN vagas v ON c.vaga_id = v.id

GROUP BY v.name, c.status, c.stage_name, c.phase_name
ORDER BY total_candidaturas DESC;


-- ===============================================================
-- QUERY AUXILIAR: Candidaturas com Timeline Completa
-- ===============================================================
-- Esta query mostra a evolução completa de cada candidatura
-- através das etapas/fases ao longo do tempo

SELECT
    c.id AS id_candidatura,
    c.talent_name AS candidato,
    c.talent_email AS email,
    v.name AS vaga,

    -- Estado atual
    c.status AS status_atual,
    c.stage_name AS etapa_atual,
    c.phase_name AS fase_atual,

    -- Timeline de transições
    ct.stage_name AS etapa_historico,
    ct.phase_name AS fase_historico,
    ct.transition_at AT TIME ZONE 'America/Sao_Paulo' AS data_transicao,
    ct.user_name AS responsavel_transicao,

    -- Tempo na etapa/fase
    LEAD(ct.transition_at) OVER (
        PARTITION BY ct.candidatura_id
        ORDER BY ct.transition_at
    ) - ct.transition_at AS tempo_na_etapa

FROM candidaturas c
LEFT JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN candidatura_timeline ct ON c.id = ct.candidatura_id

WHERE ct.transition_at IS NOT NULL

ORDER BY
    c.id,
    ct.transition_at;


-- ===============================================================
-- QUERY AUXILIAR: Candidaturas por Diversidade
-- ===============================================================

SELECT
    v.name AS vaga,
    c.status AS status_candidatura,

    -- Contadores de diversidade
    COUNT(*) AS total_candidaturas,
    COUNT(*) FILTER (WHERE t.diversity_black = true) AS candidatos_negros,
    COUNT(*) FILTER (WHERE t.diversity_woman = true) AS candidatas_mulheres,
    COUNT(*) FILTER (WHERE t.diversity_lgbt = true) AS candidatos_lgbt,
    COUNT(*) FILTER (WHERE t.diversity_disability = true) AS candidatos_pcd,
    COUNT(*) FILTER (WHERE t.diversity_trans = true) AS candidatos_trans,

    -- Percentuais
    ROUND(100.0 * COUNT(*) FILTER (WHERE t.diversity_black = true) / NULLIF(COUNT(*), 0), 2) AS perc_negros,
    ROUND(100.0 * COUNT(*) FILTER (WHERE t.diversity_woman = true) / NULLIF(COUNT(*), 0), 2) AS perc_mulheres,
    ROUND(100.0 * COUNT(*) FILTER (WHERE t.diversity_lgbt = true) / NULLIF(COUNT(*), 0), 2) AS perc_lgbt,
    ROUND(100.0 * COUNT(*) FILTER (WHERE t.diversity_disability = true) / NULLIF(COUNT(*), 0), 2) AS perc_pcd

FROM candidaturas c
LEFT JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN talentos t ON c.talento_id = t.id

GROUP BY v.name, c.status
ORDER BY total_candidaturas DESC;


-- ===============================================================
-- QUERY AUXILIAR: Extrair Custom Fields de Candidaturas
-- ===============================================================
-- Caso os custom fields estejam armazenados em outro formato,
-- use esta query para explorar a estrutura dos dados

SELECT
    c.id AS id_candidatura,
    c.talent_name AS candidato,
    v.name AS vaga,

    -- Extrair todos os campos do stage_metadata
    jsonb_pretty(c.stage_metadata::jsonb) AS metadata_etapa_formatado,

    -- Extrair todos os campos do phase_metadata
    jsonb_pretty(c.phase_metadata::jsonb) AS metadata_fase_formatado

FROM candidaturas c
LEFT JOIN vagas v ON c.vaga_id = v.id

WHERE c.stage_metadata IS NOT NULL
   OR c.phase_metadata IS NOT NULL

LIMIT 10;


-- ===============================================================
-- NOTAS IMPORTANTES
-- ===============================================================
--
-- 1. Custom Field "Você conhecia a Framework?":
--    - Os campos conhecia_framework_stage e conhecia_framework_phase
--      tentam extrair este valor dos metadados JSON
--    - Você pode precisar ajustar o caminho JSON conforme a estrutura
--      real dos dados (ex: stage_metadata->'customFields'->>'conhecia_framework')
--    - Use a query auxiliar "Extrair Custom Fields" para explorar
--      a estrutura exata dos metadados
--
-- 2. Timeline de Candidaturas:
--    - A tabela candidatura_timeline armazena o histórico completo
--      de transições entre etapas/fases
--    - Use a query "Candidaturas com Timeline Completa" para ver
--      a evolução de cada candidatura ao longo do tempo
--
-- 3. Performance:
--    - As queries com JOINs podem ser lentas para grandes volumes
--    - Considere adicionar filtros (WHERE vaga_id = X, WHERE status = 'active')
--    - Use LIMIT para testar queries antes de rodar completo
--
-- ===============================================================
