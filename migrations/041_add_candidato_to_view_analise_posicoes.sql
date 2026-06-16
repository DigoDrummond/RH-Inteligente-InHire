/*
================================================================================
MIGRATION 041: Adicionar Candidato Contratado na View Análise Posições
================================================================================

Data: 2026-02-06
Descrição:
  Atualiza vw_analise_posicoes para incluir:
  - candidato_nome (talentos.name via stage_name = 'Contratação')
  - candidato_email (talentos.email via stage_name = 'Contratação')

  Mesma lógica utilizada em vw_dados_jade.

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com dados do candidato contratado
CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultimo_status_posicao AS (
    SELECT DISTINCT ON (pt.posicao_id)
        pt.posicao_id,
        pt.new_status AS status_atual,
        pt.changed_at AS data_ultima_mudanca
    FROM position_timeline pt
    ORDER BY pt.posicao_id, pt.changed_at DESC
),
eventos_pausa AS (
    SELECT DISTINCT
        pt.posicao_id,
        pt.changed_at,
        pt.previous_status,
        pt.new_status,
        CASE
            WHEN (pt.previous_status = 'open' OR pt.previous_status IS NULL)
                 AND pt.new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN pt.previous_status = 'paused'
                 AND pt.new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline pt
    WHERE
        ((pt.previous_status = 'open' OR pt.previous_status IS NULL) AND pt.new_status = 'paused')
        OR (pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS inicio_pausa,
        MIN(fim.changed_at) AS fim_pausa,
        CASE
            WHEN MIN(fim.changed_at) IS NOT NULL THEN
                (DATE(MIN(fim.changed_at)) - DATE(inicio.changed_at))::INTEGER
            ELSE NULL
        END AS dias_pausa
    FROM eventos_pausa inicio
    LEFT JOIN eventos_pausa fim
        ON fim.posicao_id = inicio.posicao_id
        AND fim.tipo_evento = 'FIM_PAUSA'
        AND fim.changed_at > inicio.changed_at
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
    GROUP BY inicio.posicao_id, inicio.changed_at
),
periodos_numerados AS (
    SELECT
        posicao_id,
        inicio_pausa,
        fim_pausa,
        dias_pausa,
        ROW_NUMBER() OVER (PARTITION BY posicao_id ORDER BY inicio_pausa) AS numero_pausa
    FROM periodos_pausa
),
agregacao_pausas AS (
    SELECT
        posicao_id,
        MIN(inicio_pausa) AS primeira_pausa,
        MAX(fim_pausa) AS ultima_retomada,
        SUM(dias_pausa) AS total_dias_pausa,
        COUNT(*) AS num_ciclos,
        STRING_AGG(
            'Pausa ' || numero_pausa ||
            ': ' || TO_CHAR(inicio_pausa, 'DD/MM/YYYY') ||
            ' a ' || COALESCE(TO_CHAR(fim_pausa, 'DD/MM/YYYY'), 'Em pausa') ||
            COALESCE(' (' || dias_pausa || ' dias)', ''),
            '; ' ORDER BY inicio_pausa
        ) AS detalhamento
    FROM periodos_numerados
    GROUP BY posicao_id
),
candidatos_contratados AS (
    -- Pega candidatos na etapa Contratação (mesma lógica da vw_dados_jade)
    SELECT DISTINCT ON (c.vaga_id)
        c.vaga_id,
        t.name as candidato_nome,
        t.email as candidato_email,
        c.updated_at_inhire
    FROM candidaturas c
    INNER JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.stage_name = 'Contratação'
    ORDER BY c.vaga_id, c.updated_at_inhire DESC
)
SELECT
    -- Identificação
    p.id AS id_position,
    p.vaga_id,
    v.inhire_id AS vaga_inhire_id,
    v.name AS cargo,

    -- Status (prioriza timeline, fallback para posicoes.status)
    COALESCE(usp.status_atual, p.status) AS status_atual,

    -- Datas principais
    DATE(COALESCE(r.requested_at, p.opened_at)) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,

    -- Data de encerramento/atualização (SEM fallback para CURRENT_DATE)
    COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) AS data_encerramento_ou_atualizacao,

    -- Informações da requisição
    r.id AS requisicao_id,
    r.inhire_id AS requisicao_inhire_id,

    -- Dimensões de análise
    v.user_name AS recrutadora,
    cl.name AS cliente,
    v.custom_fields->>'Torre' AS torre,

    -- Status de preenchimento
    DATE(p.hired_at) AS data_contratacao,

    -- NOVO: Dados do candidato contratado
    cc.candidato_nome,
    cc.candidato_email,

    -- Métricas de SLA (em dias - SEM usar CURRENT_DATE)
    CASE
        WHEN usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL THEN
            (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,

    CASE
        WHEN p.opened_at IS NOT NULL AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL) THEN
            (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(p.opened_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,

    -- Prazo do processo seletivo (custom_field)
    (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER AS prazo_processo_seletivo,

    -- Indicador de prazo
    CASE
        WHEN (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER IS NOT NULL
             AND p.hired_at IS NOT NULL THEN
            CASE
                WHEN (DATE(p.hired_at) - DATE(p.opened_at))::INTEGER <=
                     (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER
                THEN 'Dentro do prazo'
                ELSE 'Fora do prazo'
            END
        ELSE NULL
    END AS indicador_prazo,

    -- Informações de pausa/pendência cliente
    DATE(ap.primeira_pausa) AS inicio_pendencia_cliente,
    DATE(ap.ultima_retomada) AS fim_pendencia_cliente,
    ap.total_dias_pausa AS sla_pendencia_cliente,
    ap.num_ciclos AS num_ciclos_pausa,
    ap.detalhamento AS detalhamento_pausas,

    -- Datas de criação/atualização
    DATE(p.created_at) AS created_at,
    DATE(p.updated_at) AS updated_at

FROM posicoes p
INNER JOIN vagas v ON p.vaga_id = v.id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
LEFT JOIN agregacao_pausas ap ON ap.posicao_id = p.id
LEFT JOIN candidatos_contratados cc ON cc.vaga_id = v.id

ORDER BY p.id DESC;

-- Comentários
COMMENT ON VIEW vw_analise_posicoes IS
'View para análise de posições e requisições com métricas de SLA e pausas.
Atualizada em 2026-02-06 (Migration 041):
- Adicionado: candidato_nome
- Adicionado: candidato_email
- Mesma lógica de vw_dados_jade para identificar candidato contratado';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_candidato INTEGER;
    v_contratadas INTEGER;
BEGIN
    -- Total geral
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    -- Com candidato
    SELECT COUNT(*) INTO v_com_candidato
    FROM vw_analise_posicoes
    WHERE candidato_nome IS NOT NULL;

    -- Contratadas (hired_at preenchido)
    SELECT COUNT(*) INTO v_contratadas
    FROM vw_analise_posicoes
    WHERE data_contratacao IS NOT NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 041 - CANDIDATO ADICIONADO NA VIEW ANÁLISE POSIÇÕES';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Posições contratadas: %', v_contratadas;
    RAISE NOTICE 'Com candidato identificado: %', v_com_candidato;
    RAISE NOTICE '';
    RAISE NOTICE 'Novos campos:';
    RAISE NOTICE '  - candidato_nome (talentos.name)';
    RAISE NOTICE '  - candidato_email (talentos.email)';
    RAISE NOTICE '';
    RAISE NOTICE 'Campos existentes mantidos:';
    RAISE NOTICE '  - data_contratacao (p.hired_at)';
    RAISE NOTICE '  - data_encerramento_ou_atualizacao';
    RAISE NOTICE '================================================================================';
END $$;
