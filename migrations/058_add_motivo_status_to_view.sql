/*
================================================================================
MIGRATION 058: Adiciona coluna motivo_status à vw_analise_posicoes
================================================================================

Data: 2026-02-19
Descrição:
  Adiciona o campo 'motivo_status' à view vw_analise_posicoes.

  Este campo traz o motivo (notes) da última mudança de status da posição,
  vindo de position_timeline.notes.

CAMPO ADICIONADO:
  - motivo_status: Código do motivo da última mudança de status
    Exemplos de valores:
      - 'waiting_schedule' (Cartas enviadas, aguardando retorno de agenda)
      - 'feedback_received_from_client' (Feedback recebido do cliente)
      - 'strategy_change' (Mudança de estratégia)
      - 'closed_other_vendor' (Fechado com outro fornecedor)
      - E outros 325 códigos distintos

FONTE DOS DADOS:
  - Tabela: position_timeline
  - Campo: notes
  - Cobertura: 66.8% dos eventos (2.418 de 3.618)

INTEGRAÇÃO:
  - O campo já estava sendo usado na CTE ultimo_status_posicao
  - Apenas faltava incluir no SELECT final da view

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view COM motivo_status
CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    -- Última etapa do funil alcançada por candidatos da vaga
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL AND cd.stage_order IS NOT NULL
),
pessoa_contratada AS (
    -- Pessoa contratada para a posição
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
    -- Último status da posição (da timeline) + MOTIVO (notes)
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes AS motivo  -- ✅ ADICIONADO: motivo da última mudança
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
eventos_pausa AS (
    -- Identifica eventos de INÍCIO e FIM de pausa
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            -- Início de pausa: de 'open' (ou NULL) para 'paused'
            WHEN (previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused'
                THEN 'INICIO_PAUSA'
            -- Fim de pausa: de 'paused' para 'open', 'canceled' ou 'closed'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed')
                THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE
        -- Início de pausa
        ((previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused')
        -- Fim de pausa
        OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    -- Calcula períodos de pausa (data início → data fim)
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
            CURRENT_TIMESTAMP  -- Se ainda está pausado
        ) AS data_fim
    FROM eventos_pausa inicio
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
),
periodos_unicos AS (
    -- Remove duplicatas de períodos
    SELECT DISTINCT
        posicao_id,
        data_inicio,
        data_fim
    FROM periodos_pausa
),
pendencias_posicao AS (
    -- Agrega todas as pausas por posição
    SELECT
        posicao_id,
        SUM(DATE(data_fim) - DATE(data_inicio)) AS total_dias_pausado,
        MIN(data_inicio) AS primeira_pausa,
        MAX(data_fim) AS ultima_retomada,
        COUNT(*) AS num_ciclos,
        -- Lista de datas de início
        STRING_AGG(TO_CHAR(data_inicio, 'DD/MM/YYYY'), '; ' ORDER BY data_inicio) AS datas_inicio_pausa,
        -- Lista de datas de fim
        STRING_AGG(
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Em andamento'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END,
            '; '
            ORDER BY data_inicio
        ) AS datas_fim_pausa,
        -- Detalhamento completo de cada período
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
    -- Identifica a origem do candidato contratado (ou mais comum)
    SELECT
        p.id AS posicao_id,
        COALESCE(
            -- Prioridade 1: Source do candidato contratado
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            -- Prioridade 2: Source mais comum entre candidatos
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
    -- ========================================
    -- 📋 IDENTIFICAÇÃO
    -- ========================================
    p.id AS id_position,
    v.name AS cargo,
    c.name AS cliente,
    v.custom_fields->>'Torre' AS torre,

    -- ========================================
    -- 📅 DATAS PRINCIPAIS
    -- ========================================
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,

    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
        THEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- ========================================
    -- 📊 STATUS E CONTEXTO
    -- ========================================
    COALESCE(usp.new_status, p.status) AS status_atual,
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    usp.motivo AS motivo_status,  -- ✅ NOVO: motivo da última mudança de status

    -- ========================================
    -- 👔 PERFIL DA VAGA
    -- ========================================
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- ========================================
    -- 👥 RESPONSÁVEIS
    -- ========================================
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,
    v.user_name AS recrutador_vaga,

    -- ========================================
    -- ⏸️ PAUSAS E PENDÊNCIAS
    -- ========================================
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,
    pp.datas_fim_pausa AS fim_pendencia_cliente,
    pp.total_dias_pausado AS sla_pendencia_cliente,
    pp.num_ciclos AS num_ciclos_pausa,
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- ========================================
    -- ⏱️ MÉTRICAS DE SLA (DIAS CORRIDOS)
    -- ========================================
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,

    v.sla_days_goal AS prazo_processo_seletivo,

    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,

    CASE
        WHEN v.sla_days_goal IS NOT NULL
            AND p.hired_at IS NOT NULL
            AND DATE(p.hired_at) >= DATE(p.opened_at)
        THEN
            CASE
                WHEN (DATE(p.hired_at) - DATE(p.opened_at))::INTEGER <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    -- ========================================
    -- 👤 PESSOA CONTRATADA
    -- ========================================
    p.reason AS motivo_contratacao,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,

    -- ========================================
    -- 🔍 ORIGEM DO CANDIDATO
    -- ========================================
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

-- Filtros
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')

ORDER BY p.opened_at DESC NULLS LAST;

-- ================================================================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- ================================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View COMPLETA para análise de posições - Migration 058 (2026-02-19)

ATUALIZAÇÃO: Adicionado campo motivo_status

VERSÃO DEFINITIVA que combina:
✅ Campos completos da migration 036 (11 campos de análise)
✅ Correções de bugs da migration 042 (validações de integridade)
✅ Correção de Torre da migration 043 (busca do local correto)
✅ Custom fields funcionando (bug corrigido em 2026-02-10)
✅ Campo motivo_status adicionado (migration 058, 2026-02-19)

CAMPOS DE NEGÓCIO:
- Motivo de cancelamento/paralisação
- Etapa do funil (última alcançada)
- Modalidade de contratação (CLT/PJ)
- Responsável/Gestor
- Informações de substituição
- Source/Indicação de candidatos
- Motivo do status atual (novo)

VALIDAÇÕES DE INTEGRIDADE:
- Data de encerramento >= data de publicação
- SLA só calculado se datas consistentes
- Indicador de prazo validado
- Torre busca de vagas (não requisições)

SLAs calculados em DIAS CORRIDOS (não úteis).';

COMMENT ON COLUMN vw_analise_posicoes.motivo_status IS
'Código do motivo da última mudança de status da posição. Vem de position_timeline.notes. Exemplos: waiting_schedule, feedback_received_from_client, strategy_change, closed_other_vendor. Cobertura: ~67% das posições.';
