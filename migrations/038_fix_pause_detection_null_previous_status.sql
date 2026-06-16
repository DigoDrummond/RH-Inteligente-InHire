/*
================================================================================
MIGRATION 038: Fix Pause Detection for NULL previous_status
================================================================================

Data: 2026-02-06
Descrição:
  Corrige detecção de pausas na view vw_analise_posicoes quando a posição
  inicia com previous_status = NULL

Problema identificado:
  - Posição 311: NULL → paused → canceled
  - A CTE eventos_pausa exigia: previous_status = 'open' AND new_status = 'paused'
  - Mas algumas posições começam direto em 'paused' com previous_status = NULL
  - Isso fazia com que o INICIO_PAUSA não fosse capturado

Solução:
  - Aceitar INICIO_PAUSA quando:
    (previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused'

Exemplo de caso corrigido:
  - Posição 311: Agora captura NULL → paused como INICIO_PAUSA

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com detecção de pausa corrigida
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
            -- CORRIGIDO: Aceita previous_status = NULL ou 'open'
            WHEN (pt.previous_status = 'open' OR pt.previous_status IS NULL)
                 AND pt.new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN pt.previous_status = 'paused'
                 AND pt.new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline pt
    WHERE
        -- CORRIGIDO: Aceita previous_status = NULL ou 'open'
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

    -- Informações de pausa/pendência cliente (CORRIGIDO)
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

ORDER BY p.id DESC;

-- Comentários
COMMENT ON VIEW vw_analise_posicoes IS
'View para análise de posições e requisições com métricas de SLA e pausas.
Atualizada em 2026-02-06:
- CORRIGIDO: Detecção de pausas agora aceita previous_status = NULL
- Captura corretamente posições que iniciam direto em paused
- Exemplo: Posição 311 (NULL → paused → canceled)';

-- Validação específica para posição 311
DO $$
DECLARE
    v_pos_311 RECORD;
    v_total_com_pausa INTEGER;
BEGIN
    -- Verificar posição 311
    SELECT
        id_position,
        status_atual,
        inicio_pendencia_cliente,
        fim_pendencia_cliente,
        sla_pendencia_cliente,
        num_ciclos_pausa,
        detalhamento_pausas
    INTO v_pos_311
    FROM vw_analise_posicoes
    WHERE id_position = 311;

    -- Contar total de posições com pausa
    SELECT COUNT(*) INTO v_total_com_pausa
    FROM vw_analise_posicoes
    WHERE inicio_pendencia_cliente IS NOT NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 038 - DETECÇÃO DE PAUSAS CORRIGIDA';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Mudança aplicada:';
    RAISE NOTICE '  - eventos_pausa CTE agora aceita: previous_status = NULL OR previous_status = ''open''';
    RAISE NOTICE '';
    RAISE NOTICE 'Validação da Posição 311:';

    IF v_pos_311.inicio_pendencia_cliente IS NOT NULL THEN
        RAISE NOTICE '  Status: %', v_pos_311.status_atual;
        RAISE NOTICE '  Início pendência: %', v_pos_311.inicio_pendencia_cliente;
        RAISE NOTICE '  Fim pendência: %', v_pos_311.fim_pendencia_cliente;
        RAISE NOTICE '  SLA pendência: % dias', v_pos_311.sla_pendencia_cliente;
        RAISE NOTICE '  Ciclos pausa: %', v_pos_311.num_ciclos_pausa;
        RAISE NOTICE '  [OK] Pausa CAPTURADA com sucesso!';
    ELSE
        RAISE NOTICE '  [!] PROBLEMA: Pausa ainda NÃO foi capturada';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE 'Total de posições com pausa registrada: %', v_total_com_pausa;
    RAISE NOTICE '================================================================================';
END $$;
