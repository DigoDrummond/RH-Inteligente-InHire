-- ========================================
-- Migration 002: Criar Views Materializadas
-- Data: 2025-11-19
-- Descrição: Cria views materializadas para análises de funil, kanban, SLA e métricas
-- ========================================

-- ========================================
-- 1. VIEW: FUNIL DE CONVERSÃO
-- ========================================

DROP MATERIALIZED VIEW IF EXISTS mv_funil_conversao CASCADE;

CREATE MATERIALIZED VIEW mv_funil_conversao AS
WITH funil AS (
    SELECT
        stage_order,
        stage_name,
        status,
        COUNT(*) as total_candidatos,
        AVG(time_in_current_stage / 86400000.0) as media_dias_stage,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time_in_current_stage / 86400000.0) as mediana_dias_stage
    FROM candidaturas
    WHERE stage_order IS NOT NULL
    GROUP BY stage_order, stage_name, status
),
funil_agregado AS (
    SELECT
        stage_order,
        stage_name,
        SUM(total_candidatos) as total_candidatos,
        SUM(CASE WHEN status = 'ACTIVE' THEN total_candidatos ELSE 0 END) as ativos,
        SUM(CASE WHEN status = 'REJECTED' THEN total_candidatos ELSE 0 END) as rejeitados,
        SUM(CASE WHEN status = 'DECLINED' THEN total_candidatos ELSE 0 END) as desistentes,
        SUM(CASE WHEN status = 'HIRED' THEN total_candidatos ELSE 0 END) as contratados,
        AVG(media_dias_stage) as media_dias_stage,
        AVG(mediana_dias_stage) as mediana_dias_stage
    FROM funil
    GROUP BY stage_order, stage_name
)
SELECT
    f.stage_order,
    f.stage_name,
    f.total_candidatos,
    f.ativos,
    f.rejeitados,
    f.desistentes,
    f.contratados,
    ROUND(f.media_dias_stage, 2) as media_dias_no_stage,
    ROUND(f.mediana_dias_stage, 2) as mediana_dias_no_stage,
    -- Taxa de conversão (para próximo stage)
    LAG(f.total_candidatos) OVER (ORDER BY f.stage_order DESC) as candidatos_stage_anterior,
    ROUND(
        f.total_candidatos * 100.0 /
        NULLIF(LAG(f.total_candidatos) OVER (ORDER BY f.stage_order DESC), 0),
        2
    ) as taxa_conversao_pct,
    -- Taxa de rejeição no stage
    ROUND(f.rejeitados * 100.0 / NULLIF(f.total_candidatos, 0), 2) as taxa_rejeicao_pct,
    -- Taxa de desistência no stage
    ROUND(f.desistentes * 100.0 / NULLIF(f.total_candidatos, 0), 2) as taxa_desistencia_pct
FROM funil_agregado f
ORDER BY f.stage_order;

-- Criar índices na view materializada
CREATE INDEX IF NOT EXISTS idx_mv_funil_stage_order ON mv_funil_conversao(stage_order);
CREATE INDEX IF NOT EXISTS idx_mv_funil_stage_name ON mv_funil_conversao(stage_name);

COMMENT ON MATERIALIZED VIEW mv_funil_conversao IS 'Funil de conversão com taxas e métricas por stage';

-- ========================================
-- 2. VIEW: KANBAN DASHBOARD
-- ========================================

DROP MATERIALIZED VIEW IF EXISTS mv_kanban_dashboard CASCADE;

CREATE MATERIALIZED VIEW mv_kanban_dashboard AS
WITH vagas_stats AS (
    SELECT
        status,
        COUNT(*) as total_vagas,
        SUM(active_talents) as total_talentos_ativos,
        SUM(open_positions) as total_posicoes_abertas,
        AVG(active_talents) as media_talentos_por_vaga
    FROM vagas
    GROUP BY status
),
posicoes_stats AS (
    SELECT
        status,
        COUNT(*) as total_posicoes,
        COUNT(DISTINCT vaga_id) as vagas_envolvidas,
        COUNT(CASE WHEN talent_id IS NOT NULL THEN 1 END) as posicoes_preenchidas
    FROM posicoes
    GROUP BY status
),
candidaturas_por_stage AS (
    SELECT
        stage_name,
        stage_order,
        COUNT(*) as total_candidaturas,
        COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as ativas,
        COUNT(CASE WHEN status = 'REJECTED' THEN 1 END) as rejeitadas,
        COUNT(CASE WHEN status = 'DECLINED' THEN 1 END) as desistidas,
        AVG(dias_no_stage_atual) as media_dias_no_stage
    FROM candidaturas
    WHERE stage_name IS NOT NULL
    GROUP BY stage_name, stage_order
)
SELECT
    'VAGAS' as entidade,
    v.status as status,
    v.total_vagas as quantidade,
    v.total_talentos_ativos as metrica_1,
    v.total_posicoes_abertas as metrica_2,
    ROUND(v.media_talentos_por_vaga, 2) as metrica_3,
    NULL::decimal as metrica_4
FROM vagas_stats v
UNION ALL
SELECT
    'POSICOES' as entidade,
    p.status as status,
    p.total_posicoes as quantidade,
    p.vagas_envolvidas as metrica_1,
    p.posicoes_preenchidas as metrica_2,
    NULL as metrica_3,
    NULL as metrica_4
FROM posicoes_stats p
UNION ALL
SELECT
    'CANDIDATURAS' as entidade,
    c.stage_name as status,
    c.total_candidaturas as quantidade,
    c.ativas as metrica_1,
    c.rejeitadas as metrica_2,
    c.desistidas as metrica_3,
    ROUND(c.media_dias_no_stage, 2) as metrica_4
FROM candidaturas_por_stage c
ORDER BY entidade, status;

CREATE INDEX IF NOT EXISTS idx_mv_kanban_entidade ON mv_kanban_dashboard(entidade);
CREATE INDEX IF NOT EXISTS idx_mv_kanban_status ON mv_kanban_dashboard(status);

COMMENT ON MATERIALIZED VIEW mv_kanban_dashboard IS 'Visão consolidada de kanban para vagas, posições e candidaturas';

-- ========================================
-- 3. VIEW: MÉTRICAS DE SLA
-- ========================================

DROP MATERIALIZED VIEW IF EXISTS mv_sla_metrics CASCADE;

CREATE MATERIALIZED VIEW mv_sla_metrics AS
WITH candidaturas_com_timeline AS (
    SELECT
        c.id,
        c.inhire_id,
        c.vaga_id,
        c.talento_id,
        c.talent_name,
        c.status,
        c.stage_name,
        c.dias_no_processo,
        c.dias_no_stage_atual,
        c.created_at,
        v.name as vaga_name,
        v.sla_days_goal,
        MIN(t.transition_at) as primeira_transicao,
        MAX(t.transition_at) as ultima_transicao,
        COUNT(t.id) as total_transicoes
    FROM candidaturas c
    LEFT JOIN candidatura_timeline t ON c.id = t.candidatura_id
    LEFT JOIN vagas v ON c.vaga_id = v.id
    GROUP BY c.id, c.inhire_id, c.vaga_id, c.talento_id, c.talent_name,
             c.status, c.stage_name, c.dias_no_processo, c.dias_no_stage_atual,
             c.created_at, v.name, v.sla_days_goal
)
SELECT
    ct.id as candidatura_id,
    ct.inhire_id as candidatura_inhire_id,
    ct.vaga_id,
    ct.vaga_name,
    ct.talento_id,
    ct.talent_name,
    ct.status,
    ct.stage_name,
    ROUND(ct.dias_no_processo, 2) as dias_no_processo,
    ROUND(ct.dias_no_stage_atual, 2) as dias_no_stage_atual,
    ct.sla_days_goal,
    CASE
        WHEN ct.sla_days_goal IS NOT NULL AND ct.dias_no_processo > ct.sla_days_goal
        THEN ROUND(ct.dias_no_processo - ct.sla_days_goal, 2)
        ELSE NULL
    END as dias_atraso_sla,
    CASE
        WHEN ct.sla_days_goal IS NULL THEN 'SEM_SLA'
        WHEN ct.dias_no_processo > ct.sla_days_goal THEN 'ATRASADO'
        WHEN ct.dias_no_processo > (ct.sla_days_goal * 0.8) THEN 'EM_ALERTA'
        ELSE 'OK'
    END as status_sla,
    ct.total_transicoes,
    ct.primeira_transicao,
    ct.ultima_transicao,
    CASE
        WHEN ct.primeira_transicao IS NOT NULL AND ct.ultima_transicao IS NOT NULL
        THEN ROUND(EXTRACT(EPOCH FROM (ct.ultima_transicao - ct.primeira_transicao)) / 86400, 2)
        ELSE NULL
    END as dias_timeline_total,
    ct.created_at
FROM candidaturas_com_timeline ct
WHERE ct.status = 'ACTIVE'  -- Apenas candidaturas ativas
ORDER BY ct.dias_no_processo DESC;

CREATE INDEX IF NOT EXISTS idx_mv_sla_status ON mv_sla_metrics(status_sla);
CREATE INDEX IF NOT EXISTS idx_mv_sla_vaga ON mv_sla_metrics(vaga_id);
CREATE INDEX IF NOT EXISTS idx_mv_sla_dias ON mv_sla_metrics(dias_no_processo);

COMMENT ON MATERIALIZED VIEW mv_sla_metrics IS 'Métricas de SLA e tempo para candidaturas ativas';

-- ========================================
-- 4. VIEW: RESUMO DE CANDIDATURAS
-- ========================================

DROP MATERIALIZED VIEW IF EXISTS mv_candidaturas_summary CASCADE;

CREATE MATERIALIZED VIEW mv_candidaturas_summary AS
WITH candidaturas_metricas AS (
    SELECT
        v.id as vaga_id,
        v.inhire_id as vaga_inhire_id,
        v.name as vaga_name,
        v.status as vaga_status,
        v.area as vaga_area,
        v.seniority as vaga_seniority,
        v.sla_days_goal,
        COUNT(c.id) as total_candidaturas,
        COUNT(CASE WHEN c.status = 'ACTIVE' THEN 1 END) as ativas,
        COUNT(CASE WHEN c.status = 'REJECTED' THEN 1 END) as rejeitadas,
        COUNT(CASE WHEN c.status = 'DECLINED' THEN 1 END) as desistidas,
        COUNT(CASE WHEN c.status = 'HIRED' THEN 1 END) as contratadas,
        COUNT(CASE WHEN c.status = 'INACTIVE' THEN 1 END) as inativas,
        AVG(c.dias_no_processo) as media_dias_processo,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY c.dias_no_processo) as mediana_dias_processo,
        MAX(c.dias_no_processo) as max_dias_processo,
        AVG(c.dias_no_stage_atual) as media_dias_stage,
        COUNT(DISTINCT c.stage_name) as total_stages_utilizados
    FROM vagas v
    LEFT JOIN candidaturas c ON v.id = c.vaga_id
    GROUP BY v.id, v.inhire_id, v.name, v.status, v.area, v.seniority, v.sla_days_goal
)
SELECT
    cm.vaga_id,
    cm.vaga_inhire_id,
    cm.vaga_name,
    cm.vaga_status,
    cm.vaga_area,
    cm.vaga_seniority,
    cm.sla_days_goal,
    cm.total_candidaturas,
    cm.ativas,
    cm.rejeitadas,
    cm.desistidas,
    cm.contratadas,
    cm.inativas,
    -- Taxas calculadas
    ROUND(cm.ativas * 100.0 / NULLIF(cm.total_candidaturas, 0), 2) as taxa_ativas_pct,
    ROUND(cm.rejeitadas * 100.0 / NULLIF(cm.total_candidaturas, 0), 2) as taxa_rejeicao_pct,
    ROUND(cm.desistidas * 100.0 / NULLIF(cm.total_candidaturas, 0), 2) as taxa_desistencia_pct,
    ROUND(cm.contratadas * 100.0 / NULLIF(cm.total_candidaturas, 0), 2) as taxa_contratacao_pct,
    -- Métricas de tempo
    ROUND(cm.media_dias_processo, 2) as media_dias_processo,
    ROUND(cm.mediana_dias_processo, 2) as mediana_dias_processo,
    ROUND(cm.max_dias_processo, 2) as max_dias_processo,
    ROUND(cm.media_dias_stage, 2) as media_dias_stage,
    cm.total_stages_utilizados,
    -- Indicador de performance
    CASE
        WHEN cm.total_candidaturas = 0 THEN 'SEM_CANDIDATOS'
        WHEN cm.vaga_status = 'CLOSED' AND cm.contratadas > 0 THEN 'SUCESSO'
        WHEN cm.vaga_status = 'CLOSED' AND cm.contratadas = 0 THEN 'FECHADA_SEM_SUCESSO'
        WHEN cm.vaga_status = 'CANCELED' THEN 'CANCELADA'
        WHEN cm.ativas > 0 THEN 'EM_ANDAMENTO'
        ELSE 'OUTROS'
    END as status_performance
FROM candidaturas_metricas cm
ORDER BY cm.total_candidaturas DESC;

CREATE INDEX IF NOT EXISTS idx_mv_summary_vaga ON mv_candidaturas_summary(vaga_id);
CREATE INDEX IF NOT EXISTS idx_mv_summary_status ON mv_candidaturas_summary(vaga_status);
CREATE INDEX IF NOT EXISTS idx_mv_summary_area ON mv_candidaturas_summary(vaga_area);
CREATE INDEX IF NOT EXISTS idx_mv_summary_performance ON mv_candidaturas_summary(status_performance);

COMMENT ON MATERIALIZED VIEW mv_candidaturas_summary IS 'Resumo analítico de candidaturas agrupadas por vaga';

-- ========================================
-- 5. FUNÇÃO PARA REFRESH AUTOMÁTICO
-- ========================================

CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_funil_conversao;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_kanban_dashboard;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sla_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_candidaturas_summary;

    RAISE NOTICE 'Todas as views materializadas foram atualizadas com sucesso!';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views() IS 'Atualiza todas as views materializadas de uma vez';

-- ========================================
-- 6. VERIFICAÇÕES DE SUCESSO
-- ========================================

DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM pg_matviews
    WHERE schemaname = 'public'
      AND matviewname IN ('mv_funil_conversao', 'mv_kanban_dashboard', 'mv_sla_metrics', 'mv_candidaturas_summary');

    IF v_count = 4 THEN
        RAISE NOTICE 'SUCESSO: Todas as 4 views materializadas foram criadas!';
    ELSE
        RAISE WARNING 'AVISO: Apenas % de 4 views materializadas foram criadas.', v_count;
    END IF;
END $$;

-- ========================================
-- 7. ESTATÍSTICAS DAS VIEWS
-- ========================================

SELECT 'mv_funil_conversao' as view_name, COUNT(*) as registros FROM mv_funil_conversao
UNION ALL
SELECT 'mv_kanban_dashboard' as view_name, COUNT(*) as registros FROM mv_kanban_dashboard
UNION ALL
SELECT 'mv_sla_metrics' as view_name, COUNT(*) as registros FROM mv_sla_metrics
UNION ALL
SELECT 'mv_candidaturas_summary' as view_name, COUNT(*) as registros FROM mv_candidaturas_summary
ORDER BY view_name;

RAISE NOTICE '';
RAISE NOTICE '========================================';
RAISE NOTICE 'Migration 002 concluída com sucesso!';
RAISE NOTICE 'Use: SELECT refresh_all_materialized_views(); para atualizar todas as views';
RAISE NOTICE '========================================';
