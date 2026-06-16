-- ========================================
-- Migration 003: Criar Tabela de Métricas
-- Data: 2025-11-19
-- Descrição: Cria tabela para armazenar métricas pré-calculadas de candidaturas
-- ========================================

-- ========================================
-- 1. CRIAR TABELA DE MÉTRICAS
-- ========================================

DROP TABLE IF EXISTS candidatura_metrics CASCADE;

CREATE TABLE candidatura_metrics (
    id BIGSERIAL PRIMARY KEY,
    candidatura_id BIGINT NOT NULL,
    candidatura_inhire_id VARCHAR(255) NOT NULL,
    vaga_id BIGINT,
    talento_id BIGINT,

    -- Métricas de Tempo
    dias_no_processo DECIMAL(10, 2),
    dias_no_stage_atual DECIMAL(10, 2),
    total_transicoes INTEGER DEFAULT 0,
    primeira_transicao_at TIMESTAMP WITH TIME ZONE,
    ultima_transicao_at TIMESTAMP WITH TIME ZONE,
    dias_timeline_total DECIMAL(10, 2),

    -- Métricas de Performance
    stages_percorridos INTEGER DEFAULT 0,
    stages_rejeitados INTEGER DEFAULT 0,
    tempo_medio_por_stage DECIMAL(10, 2),
    stage_com_maior_tempo VARCHAR(255),
    tempo_maior_stage DECIMAL(10, 2),

    -- SLA
    sla_days_goal INTEGER,
    dias_atraso_sla DECIMAL(10, 2),
    status_sla VARCHAR(50), -- OK, EM_ALERTA, ATRASADO, SEM_SLA

    -- Status e Classificação
    status_candidatura VARCHAR(50),
    velocidade_processo VARCHAR(50), -- RAPIDO, NORMAL, LENTO
    risco_abandono VARCHAR(50), -- BAIXO, MEDIO, ALTO

    -- Timestamps
    calculado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_candidatura_metrics_candidatura FOREIGN KEY (candidatura_id) REFERENCES candidaturas(id) ON DELETE CASCADE,
    CONSTRAINT fk_candidatura_metrics_vaga FOREIGN KEY (vaga_id) REFERENCES vagas(id) ON DELETE SET NULL,
    CONSTRAINT fk_candidatura_metrics_talento FOREIGN KEY (talento_id) REFERENCES talentos(id) ON DELETE SET NULL,
    CONSTRAINT uq_candidatura_metrics_candidatura UNIQUE (candidatura_id)
);

-- ========================================
-- 2. CRIAR ÍNDICES
-- ========================================

CREATE INDEX idx_candidatura_metrics_candidatura ON candidatura_metrics(candidatura_id);
CREATE INDEX idx_candidatura_metrics_vaga ON candidatura_metrics(vaga_id);
CREATE INDEX idx_candidatura_metrics_talento ON candidatura_metrics(talento_id);
CREATE INDEX idx_candidatura_metrics_status_sla ON candidatura_metrics(status_sla);
CREATE INDEX idx_candidatura_metrics_velocidade ON candidatura_metrics(velocidade_processo);
CREATE INDEX idx_candidatura_metrics_risco ON candidatura_metrics(risco_abandono);
CREATE INDEX idx_candidatura_metrics_calculado ON candidatura_metrics(calculado_em);

-- Índice composto para queries de dashboard
CREATE INDEX idx_candidatura_metrics_dashboard ON candidatura_metrics(vaga_id, status_sla, velocidade_processo);

-- ========================================
-- 3. PROCEDURE PARA CALCULAR MÉTRICAS
-- ========================================

CREATE OR REPLACE FUNCTION calculate_candidatura_metrics(p_candidatura_id BIGINT)
RETURNS void AS $$
DECLARE
    v_candidatura RECORD;
    v_timeline RECORD;
    v_metrics RECORD;
BEGIN
    -- Buscar dados da candidatura
    SELECT
        c.id,
        c.inhire_id,
        c.vaga_id,
        c.talento_id,
        c.status,
        c.dias_no_processo,
        c.dias_no_stage_atual,
        c.stage_name,
        v.sla_days_goal
    INTO v_candidatura
    FROM candidaturas c
    LEFT JOIN vagas v ON c.vaga_id = v.id
    WHERE c.id = p_candidatura_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Candidatura % não encontrada', p_candidatura_id;
        RETURN;
    END IF;

    -- Calcular métricas do timeline
    SELECT
        COUNT(*) as total_transicoes,
        MIN(transition_at) as primeira_transicao,
        MAX(transition_at) as ultima_transicao,
        EXTRACT(EPOCH FROM (MAX(transition_at) - MIN(transition_at))) / 86400 as dias_timeline_total,
        COUNT(DISTINCT stage_id) as stages_percorridos,
        AVG(EXTRACT(EPOCH FROM (
            LEAD(transition_at) OVER (ORDER BY transition_at) - transition_at
        )) / 86400) as tempo_medio_por_stage
    INTO v_timeline
    FROM candidatura_timeline
    WHERE candidatura_id = p_candidatura_id;

    -- Calcular stage com maior tempo
    SELECT
        stage_name,
        MAX(tempo_no_stage) as tempo_maior_stage
    INTO v_metrics
    FROM (
        SELECT
            stage_name,
            EXTRACT(EPOCH FROM (
                LEAD(transition_at) OVER (ORDER BY transition_at) - transition_at
            )) / 86400 as tempo_no_stage
        FROM candidatura_timeline
        WHERE candidatura_id = p_candidatura_id
    ) sub
    GROUP BY stage_name
    ORDER BY tempo_maior_stage DESC NULLS LAST
    LIMIT 1;

    -- Calcular dias de atraso SLA
    DECLARE
        v_dias_atraso DECIMAL(10, 2);
        v_status_sla VARCHAR(50);
        v_velocidade VARCHAR(50);
        v_risco VARCHAR(50);
    BEGIN
        -- SLA
        IF v_candidatura.sla_days_goal IS NOT NULL THEN
            v_dias_atraso := v_candidatura.dias_no_processo - v_candidatura.sla_days_goal;
            IF v_candidatura.dias_no_processo > v_candidatura.sla_days_goal THEN
                v_status_sla := 'ATRASADO';
            ELSIF v_candidatura.dias_no_processo > (v_candidatura.sla_days_goal * 0.8) THEN
                v_status_sla := 'EM_ALERTA';
            ELSE
                v_status_sla := 'OK';
            END IF;
        ELSE
            v_dias_atraso := NULL;
            v_status_sla := 'SEM_SLA';
        END IF;

        -- Velocidade do processo
        IF v_candidatura.dias_no_processo < 7 THEN
            v_velocidade := 'RAPIDO';
        ELSIF v_candidatura.dias_no_processo < 30 THEN
            v_velocidade := 'NORMAL';
        ELSE
            v_velocidade := 'LENTO';
        END IF;

        -- Risco de abandono (baseado em tempo no stage atual)
        IF v_candidatura.dias_no_stage_atual > 30 THEN
            v_risco := 'ALTO';
        ELSIF v_candidatura.dias_no_stage_atual > 14 THEN
            v_risco := 'MEDIO';
        ELSE
            v_risco := 'BAIXO';
        END IF;

        -- Inserir ou atualizar métricas
        INSERT INTO candidatura_metrics (
            candidatura_id,
            candidatura_inhire_id,
            vaga_id,
            talento_id,
            dias_no_processo,
            dias_no_stage_atual,
            total_transicoes,
            primeira_transicao_at,
            ultima_transicao_at,
            dias_timeline_total,
            stages_percorridos,
            tempo_medio_por_stage,
            stage_com_maior_tempo,
            tempo_maior_stage,
            sla_days_goal,
            dias_atraso_sla,
            status_sla,
            status_candidatura,
            velocidade_processo,
            risco_abandono,
            calculado_em,
            updated_at
        ) VALUES (
            v_candidatura.id,
            v_candidatura.inhire_id,
            v_candidatura.vaga_id,
            v_candidatura.talento_id,
            v_candidatura.dias_no_processo,
            v_candidatura.dias_no_stage_atual,
            COALESCE(v_timeline.total_transicoes, 0),
            v_timeline.primeira_transicao,
            v_timeline.ultima_transicao,
            ROUND(v_timeline.dias_timeline_total, 2),
            COALESCE(v_timeline.stages_percorridos, 0),
            ROUND(v_timeline.tempo_medio_por_stage, 2),
            v_metrics.stage_name,
            ROUND(v_metrics.tempo_maior_stage, 2),
            v_candidatura.sla_days_goal,
            ROUND(v_dias_atraso, 2),
            v_status_sla,
            v_candidatura.status,
            v_velocidade,
            v_risco,
            NOW(),
            NOW()
        )
        ON CONFLICT (candidatura_id)
        DO UPDATE SET
            dias_no_processo = EXCLUDED.dias_no_processo,
            dias_no_stage_atual = EXCLUDED.dias_no_stage_atual,
            total_transicoes = EXCLUDED.total_transicoes,
            primeira_transicao_at = EXCLUDED.primeira_transicao_at,
            ultima_transicao_at = EXCLUDED.ultima_transicao_at,
            dias_timeline_total = EXCLUDED.dias_timeline_total,
            stages_percorridos = EXCLUDED.stages_percorridos,
            tempo_medio_por_stage = EXCLUDED.tempo_medio_por_stage,
            stage_com_maior_tempo = EXCLUDED.stage_com_maior_tempo,
            tempo_maior_stage = EXCLUDED.tempo_maior_stage,
            sla_days_goal = EXCLUDED.sla_days_goal,
            dias_atraso_sla = EXCLUDED.dias_atraso_sla,
            status_sla = EXCLUDED.status_sla,
            status_candidatura = EXCLUDED.status_candidatura,
            velocidade_processo = EXCLUDED.velocidade_processo,
            risco_abandono = EXCLUDED.risco_abandono,
            updated_at = NOW();
    END;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_candidatura_metrics(BIGINT) IS 'Calcula e armazena métricas completas para uma candidatura';

-- ========================================
-- 4. PROCEDURE PARA RECALCULAR TODAS AS MÉTRICAS
-- ========================================

CREATE OR REPLACE FUNCTION refresh_all_candidatura_metrics()
RETURNS TABLE(total_processadas BIGINT, total_sucesso BIGINT, total_erro BIGINT) AS $$
DECLARE
    v_candidatura_id BIGINT;
    v_total_processadas BIGINT := 0;
    v_total_sucesso BIGINT := 0;
    v_total_erro BIGINT := 0;
BEGIN
    RAISE NOTICE 'Iniciando recálculo de métricas para todas as candidaturas...';

    FOR v_candidatura_id IN SELECT id FROM candidaturas LOOP
        BEGIN
            PERFORM calculate_candidatura_metrics(v_candidatura_id);
            v_total_processadas := v_total_processadas + 1;
            v_total_sucesso := v_total_sucesso + 1;

            -- Log a cada 1000 registros
            IF v_total_processadas % 1000 = 0 THEN
                RAISE NOTICE 'Processadas: % candidaturas', v_total_processadas;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            v_total_erro := v_total_erro + 1;
            RAISE WARNING 'Erro ao calcular métricas para candidatura %: %', v_candidatura_id, SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE 'Recálculo concluído! Total: %, Sucesso: %, Erros: %',
                 v_total_processadas, v_total_sucesso, v_total_erro;

    RETURN QUERY SELECT v_total_processadas, v_total_sucesso, v_total_erro;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_candidatura_metrics() IS 'Recalcula métricas para todas as candidaturas (usar com cautela em produção)';

-- ========================================
-- 5. TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA
-- ========================================

CREATE OR REPLACE FUNCTION trigger_update_candidatura_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Atualizar métricas quando candidatura for modificada
    PERFORM calculate_candidatura_metrics(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_candidatura_update_metrics_table ON candidaturas;
CREATE TRIGGER trg_candidatura_update_metrics_table
    AFTER INSERT OR UPDATE ON candidaturas
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_candidatura_metrics();

COMMENT ON TRIGGER trg_candidatura_update_metrics_table ON candidaturas IS 'Atualiza tabela de métricas automaticamente quando candidatura é modificada';

-- ========================================
-- 6. POPULAR MÉTRICAS PARA CANDIDATURAS EXISTENTES
-- ========================================

-- NOTA: Este processo pode demorar. Execute com cuidado em produção.
-- Para amostra de 100 candidaturas:
DO $$
DECLARE
    v_candidatura_id BIGINT;
    v_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Calculando métricas para primeiras 100 candidaturas (amostra)...';

    FOR v_candidatura_id IN
        SELECT id FROM candidaturas ORDER BY updated_at DESC LIMIT 100
    LOOP
        PERFORM calculate_candidatura_metrics(v_candidatura_id);
        v_count := v_count + 1;
    END LOOP;

    RAISE NOTICE 'Métricas calculadas para % candidaturas (amostra)', v_count;
    RAISE NOTICE 'Para calcular TODAS as métricas, execute: SELECT * FROM refresh_all_candidatura_metrics();';
END $$;

-- ========================================
-- 7. VERIFICAÇÕES DE SUCESSO
-- ========================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'candidatura_metrics') THEN
        RAISE NOTICE 'SUCESSO: Tabela candidatura_metrics criada!';
    ELSE
        RAISE WARNING 'ERRO: Tabela candidatura_metrics não foi criada!';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'calculate_candidatura_metrics'
    ) THEN
        RAISE NOTICE 'SUCESSO: Function calculate_candidatura_metrics criada!';
    ELSE
        RAISE WARNING 'ERRO: Function calculate_candidatura_metrics não foi criada!';
    END IF;
END $$;

-- ========================================
-- 8. ESTATÍSTICAS
-- ========================================

SELECT
    'Métricas Calculadas' as titulo,
    COUNT(*) as total_metricas,
    COUNT(CASE WHEN status_sla = 'ATRASADO' THEN 1 END) as atrasados,
    COUNT(CASE WHEN status_sla = 'EM_ALERTA' THEN 1 END) as em_alerta,
    COUNT(CASE WHEN velocidade_processo = 'LENTO' THEN 1 END) as processos_lentos,
    COUNT(CASE WHEN risco_abandono = 'ALTO' THEN 1 END) as alto_risco_abandono,
    ROUND(AVG(dias_no_processo), 2) as media_dias_processo,
    ROUND(AVG(total_transicoes), 2) as media_transicoes
FROM candidatura_metrics;

RAISE NOTICE '';
RAISE NOTICE '========================================';
RAISE NOTICE 'Migration 003 concluída com sucesso!';
RAISE NOTICE 'Use: SELECT * FROM refresh_all_candidatura_metrics(); para recalcular todas';
RAISE NOTICE '========================================';
