/*
================================================================================
MIGRATION 043: Corrigir Referência de Torre na View vw_analise_posicoes
================================================================================

Data: 2026-02-10
Descrição:
  Corrige referência incorreta do campo "Torre" que estava buscando de
  requisições quando na verdade o campo está em vagas.

PROBLEMA IDENTIFICADO:
  Linha 153 da migration 036:
    r.custom_fields->>'Torre' AS torre

  Problemas:
  1. Torre está em vagas.custom_fields, NÃO em requisicoes.custom_fields
  2. requisicoes.custom_fields é um ARRAY, não um OBJETO (operador ->> não funciona)
  3. A query funciona "por acidente" porque busca campo inexistente (sempre NULL)

SOLUÇÃO:
  v.custom_fields->>'Torre' AS torre

  Busca corretamente de vagas onde o campo existe e é acessível via ->>'

IMPACTO:
  - Código correto e manutenível
  - Funcionalidade mantida (campo já era NULL em requisições)
  - Se Torre for removido de vagas no futuro, view fica clara sobre origem

ESTRUTURA DOS CUSTOM FIELDS:
  - vagas.custom_fields:       JSONB tipo OBJETO  {key: value}  → ->> funciona
  - requisicoes.custom_fields: JSON  tipo ARRAY   [{name, value}] → ->> NÃO funciona

CAMPOS EM VAGAS:    Torre, Área, Senioridade, Modalidade, Tipo, Gestor, etc
CAMPOS EM REQUISIÇÕES: Cliente, Área, Senioridade, Modalidade (apenas 4 campos)

================================================================================
*/

-- Remover view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recriar view com correção
CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL AND cd.stage_order IS NOT NULL
),
pessoa_contratada AS (
    SELECT
        cd.vaga_id,
        cd.talent_inhire_id,
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
),
ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
eventos_pausa AS (
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            WHEN previous_status = 'open' AND new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE (previous_status = 'open' AND new_status = 'paused')
       OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS data_inicio,
        COALESCE(
            (SELECT MIN(fim.changed_at)
             FROM eventos_pausa fim
             WHERE fim.posicao_id = inicio.posicao_id
               AND fim.tipo_evento = 'FIM_PAUSA'
               AND fim.changed_at > inicio.changed_at
            ),
            CURRENT_TIMESTAMP
        ) AS data_fim
    FROM eventos_pausa inicio
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
),
periodos_unicos AS (
    SELECT DISTINCT
        posicao_id,
        data_inicio,
        data_fim
    FROM periodos_pausa
),
pendencias_posicao AS (
    SELECT
        posicao_id,
        SUM(DATE(data_fim) - DATE(data_inicio)) AS total_dias_pausado,
        MIN(data_inicio) AS primeira_pausa,
        MAX(data_fim) AS ultima_retomada,
        COUNT(*) AS num_ciclos,
        STRING_AGG(TO_CHAR(data_inicio, 'DD/MM/YYYY'), '; ' ORDER BY data_inicio) AS datas_inicio_pausa,
        STRING_AGG(
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Em andamento'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END,
            '; '
            ORDER BY data_inicio
        ) AS datas_fim_pausa,
        STRING_AGG(
            TO_CHAR(data_inicio, 'DD/MM/YYYY') || ' a ' ||
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Hoje'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END ||
            ' (' || (DATE(data_fim) - DATE(data_inicio))::text || 'd)',
            '; '
            ORDER BY data_inicio
        ) AS detalhamento_periodos
    FROM periodos_unicos
    GROUP BY posicao_id
),
source_posicao AS (
    SELECT
        p.id AS posicao_id,
        COALESCE(
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             GROUP BY cd.source
             ORDER BY COUNT(*) DESC
             LIMIT 1)
        ) AS source
    FROM posicoes p
)
SELECT
    p.id AS id_position,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    v.custom_fields->>'Torre' AS torre,  -- ✅ CORRIGIDO: era r.custom_fields, agora v.custom_fields
    COALESCE(usp.new_status, p.status) AS status_atual,
    COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) AS data_encerramento_ou_atualizacao,
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    p.reason AS motivo_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,
    v.user_name AS recrutador_vaga,
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,
    pp.datas_fim_pausa AS fim_pendencia_cliente,
    pp.total_dias_pausado AS sla_pendencia_cliente,
    pp.num_ciclos AS num_ciclos_pausa,
    pp.detalhamento_periodos AS detalhamento_pausas,
    -- SLA Recrutamento em DIAS CORRIDOS
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    -- SLA Geral CORRIGIDO - usa data_ultima_mudanca ou hired_at, NÃO usa CURRENT_DATE
    CASE
        WHEN usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL THEN
            (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,
    CASE
        WHEN v.sla_days_goal IS NOT NULL
            AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL) THEN
            CASE
                WHEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,
    sp.source AS source_candidato,
    CASE
        WHEN sp.source IN ('referral', 'direct-referral', 'employee') THEN TRUE
        ELSE FALSE
    END AS is_referral

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN source_posicao sp ON sp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

COMMENT ON VIEW vw_analise_posicoes IS 'View analítica com correção da referência de Torre (migration 043). SLAs em dias corridos. Torre agora busca corretamente de vagas.custom_fields.';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_torre_preenchido INTEGER;
    v_torre_null INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    SELECT COUNT(*) INTO v_torre_preenchido
    FROM vw_analise_posicoes
    WHERE torre IS NOT NULL;

    SELECT COUNT(*) INTO v_torre_null
    FROM vw_analise_posicoes
    WHERE torre IS NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 043 - CORREÇÃO DE TORRE';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Torre preenchido:  % (%% )', v_torre_preenchido, ROUND((v_torre_preenchido::numeric / v_total * 100), 1);
    RAISE NOTICE 'Torre NULL:        % (%% )', v_torre_null, ROUND((v_torre_null::numeric / v_total * 100), 1);
    RAISE NOTICE '';
    RAISE NOTICE 'CORREÇÃO APLICADA:';
    RAISE NOTICE '  - Antes: r.custom_fields->>''Torre'' (sempre NULL - campo não existe)';
    RAISE NOTICE '  - Depois: v.custom_fields->>''Torre'' (campo existe e é acessível)';
    RAISE NOTICE '';
    RAISE NOTICE 'OBSERVAÇÃO:';
    RAISE NOTICE '  - vagas.custom_fields é JSONB tipo OBJETO';
    RAISE NOTICE '  - requisicoes.custom_fields é JSON tipo ARRAY';
    RAISE NOTICE '  - Torre está em vagas, não em requisições';
    RAISE NOTICE '================================================================================';
END $$;
