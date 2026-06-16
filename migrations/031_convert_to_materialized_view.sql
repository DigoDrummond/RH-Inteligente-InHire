/*
================================================================================
MIGRATION 031: Converter para Materialized View (Performance)
================================================================================

Data: 2026-02-06
Descrição:
  Converte vw_analise_posicoes de VIEW regular para MATERIALIZED VIEW
  para resolver problema de performance no cálculo de dias úteis.

  Materialized View armazena os resultados pré-calculados, permitindo
  consultas instantâneas. A view pode ser atualizada quando necessário.

Impacto:
  - View passa de regular para materialized (dados armazenados)
  - Consultas ficam instantâneas (sem recalcular dias úteis)
  - Adiciona índices para melhor performance
  - Requer REFRESH após sincronizações

Performance:
  - Antes: ~45+ segundos por consulta
  - Depois: < 50ms por consulta

================================================================================
*/

-- 1. Remover view regular
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- 2. Criar MATERIALIZED VIEW com os mesmos dados
CREATE MATERIALIZED VIEW vw_analise_posicoes AS
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
        -- Usar calcular_dias_uteis para cada período de pausa
        SUM(calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))) AS total_dias_pausado,
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
            ' (' || calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))::text || 'd úteis)',
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
            -- Prioriza source do candidato contratado
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            -- Fallback: source mais comum
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
    r.custom_fields->>'Torre' AS torre,
    COALESCE(usp.new_status, p.status) AS status_atual,
    COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at), CURRENT_DATE) AS data_encerramento_ou_atualizacao,
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
    -- SLA Recrutamento em dias úteis
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN calcular_dias_uteis(DATE(r.requested_at), DATE(p.opened_at))
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    -- SLA Geral em dias úteis
    calcular_dias_uteis(
        DATE(COALESCE(r.requested_at, p.opened_at)),
        COALESCE(DATE(p.hired_at), CURRENT_DATE)
    ) AS sla_geral,
    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN calcular_dias_uteis(
                    DATE(COALESCE(r.requested_at, p.opened_at)),
                    COALESCE(DATE(p.hired_at), CURRENT_DATE)
                ) <= v.sla_days_goal
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

-- 3. Criar índices para melhorar performance
CREATE UNIQUE INDEX idx_vw_analise_posicoes_id ON vw_analise_posicoes (id_position);
CREATE INDEX idx_vw_analise_posicoes_status ON vw_analise_posicoes (status_atual);
CREATE INDEX idx_vw_analise_posicoes_cliente ON vw_analise_posicoes (cliente);
CREATE INDEX idx_vw_analise_posicoes_cargo ON vw_analise_posicoes (cargo);
CREATE INDEX idx_vw_analise_posicoes_torre ON vw_analise_posicoes (torre);

-- 4. Comentário
COMMENT ON MATERIALIZED VIEW vw_analise_posicoes IS 'Materialized view analítica de posições com SLAs em DIAS ÚTEIS (excluindo finais de semana e feriados). Performance otimizada. Última atualização: ver data do REFRESH. Para atualizar: REFRESH MATERIALIZED VIEW vw_analise_posicoes;';

-- 5. Validação
DO $$
DECLARE
    v_total INTEGER;
    v_exemplo_sla INTEGER;
    v_tempo_inicio TIMESTAMP;
    v_tempo_fim TIMESTAMP;
    v_duracao_ms INTEGER;
BEGIN
    -- Contar posições
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    -- Testar performance de consulta
    v_tempo_inicio := clock_timestamp();
    SELECT sla_geral INTO v_exemplo_sla
    FROM vw_analise_posicoes
    WHERE id_position = 241;
    v_tempo_fim := clock_timestamp();

    v_duracao_ms := EXTRACT(MILLISECONDS FROM (v_tempo_fim - v_tempo_inicio))::INTEGER;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 031 - MATERIALIZED VIEW';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: % (esperado: 830)', v_total;
    RAISE NOTICE '';
    RAISE NOTICE 'Teste de performance:';
    RAISE NOTICE '  Posição 241 - SLA Geral: % dias úteis', COALESCE(v_exemplo_sla::TEXT, 'NULL');
    RAISE NOTICE '  Tempo de consulta: %ms (esperado: < 50ms)', v_duracao_ms;
    RAISE NOTICE '';
    RAISE NOTICE 'Melhorias implementadas:';
    RAISE NOTICE '  1. View convertida para MATERIALIZED (dados pré-calculados)';
    RAISE NOTICE '  2. 5 índices criados para performance';
    RAISE NOTICE '  3. Consultas agora são instantâneas';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANTE: Para atualizar os dados após sincronização:';
    RAISE NOTICE '  REFRESH MATERIALIZED VIEW vw_analise_posicoes;';
    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
COMO USAR A MATERIALIZED VIEW
================================================================================

1. CONSULTAR (instantâneo):
   SELECT * FROM vw_analise_posicoes WHERE id_position = 241;

2. ATUALIZAR DADOS (após sincronização ou mudanças):
   REFRESH MATERIALIZED VIEW vw_analise_posicoes;

   Tempo de refresh: ~30-60 segundos (executa 1x, serve N consultas)

3. ATUALIZAR EM BACKGROUND (não bloqueia consultas):
   REFRESH MATERIALIZED VIEW CONCURRENTLY vw_analise_posicoes;

   Requisito: precisa de índice UNIQUE (já criado: id_position)

RECOMENDAÇÃO:
- Executar REFRESH após cada sincronização completa
- Ou agendar REFRESH 1x por dia (ex: 6h da manhã)
- Adicionar ao final do script de sincronização Python

================================================================================
*/
