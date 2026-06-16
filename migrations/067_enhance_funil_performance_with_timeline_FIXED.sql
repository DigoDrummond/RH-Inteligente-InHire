/*
================================================================================
MIGRATION 067 (FIXED): Enriquecer vw_funil_performance com dados de timeline
================================================================================

Data: 2026-02-24
Versão: FIXED (corrigido erro AVG com LEAD)

Descrição:
  Adiciona métricas de progressão de estágios usando dados da candidatura_timeline

CORREÇÃO:
  - Erro anterior: AVG() não pode conter LEAD() diretamente
  - Solução: Calcular durações em CTE separada, depois aplicar AVG

Novas Métricas:
  1. total_etapas_percorridas: Número de estágios únicos visitados
  2. total_transicoes: Número total de mudanças de estágio
  3. primeira_transicao: Data da primeira mudança de estágio
  4. ultima_transicao: Data da última mudança de estágio
  5. duracao_timeline_dias: Tempo total entre primeira e última transição
  6. duracao_media_por_estagio_dias: Tempo médio gasto em cada estágio
  7. tem_dados_timeline: Indicador de cobertura

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_funil_performance CASCADE;

-- Recria view com métricas de timeline CORRIGIDAS
CREATE OR REPLACE VIEW vw_funil_performance AS
WITH etapas_normalizadas AS (
    SELECT
        c.id,
        c.vaga_id,
        c.talent_inhire_id,
        c.status,
        c.stage_order,
        c.created_at,
        c.updated_at,

        -- Normaliza o nome da etapa
        CASE
            WHEN c.stage_name ILIKE '%hunting%' THEN 'Hunting'
            WHEN c.stage_name ILIKE '%abordagem%' THEN 'Abordagem'
            WHEN c.stage_name ILIKE '%inscri%' THEN 'Inscrição'
            WHEN c.stage_name ILIKE '%bate%papo%pessoas%cultura%' OR c.stage_name ILIKE '%bate%papo%time%gente%' THEN 'Bate papo | Pessoas e Cultura'
            WHEN c.stage_name ILIKE '%etapa%t%cnica%' THEN 'Etapa técnica | Talent IA'
            WHEN c.stage_name ILIKE '%aguardando%devolutiva%ia%' OR c.stage_name ILIKE '%aguardando%devolutiva%' THEN 'Aguardando Devolutiva IA'
            WHEN c.stage_name ILIKE '%bate%papo%cliente%' OR c.stage_name ILIKE '%bate%papo%gestor%' THEN 'Bate Papo | Cliente'
            WHEN c.stage_name ILIKE '%formaliza%' THEN 'Formalização de Proposta'
            WHEN c.stage_name ILIKE '%contrata%' THEN 'Contratação'
            WHEN c.stage_name ILIKE '%aguardando%agenda%' THEN 'Aguardando Agenda'
            ELSE c.stage_name
        END AS etapa_funil_normalizada,

        -- Ordem padrão das etapas no funil
        CASE
            WHEN c.stage_name ILIKE '%hunting%' THEN 1
            WHEN c.stage_name ILIKE '%abordagem%' THEN 2
            WHEN c.stage_name ILIKE '%inscri%' THEN 3
            WHEN c.stage_name ILIKE '%bate%papo%pessoas%cultura%' OR c.stage_name ILIKE '%bate%papo%time%gente%' THEN 4
            WHEN c.stage_name ILIKE '%etapa%t%cnica%' THEN 5
            WHEN c.stage_name ILIKE '%aguardando%devolutiva%ia%' OR c.stage_name ILIKE '%aguardando%devolutiva%' THEN 6
            WHEN c.stage_name ILIKE '%bate%papo%cliente%' OR c.stage_name ILIKE '%bate%papo%gestor%' THEN 7
            WHEN c.stage_name ILIKE '%formaliza%' THEN 8
            WHEN c.stage_name ILIKE '%contrata%' THEN 9
            ELSE 99
        END AS ordem_funil_padrao,

        v.name AS nome_vaga,
        v.area AS area_vaga,
        v.custom_fields->>'Torre' AS torre,
        v.user_name AS recrutadora,
        cl.name AS cliente,
        COALESCE(t.name, c.talent_name) AS nome_talento,

        DATE(v.created_at) AS data_criacao_vaga,

        (SELECT MAX(pt.changed_at)
         FROM position_timeline pt
         INNER JOIN posicoes p ON p.id = pt.posicao_id
         WHERE p.vaga_id = v.id
         AND pt.new_status IN ('closed', 'canceled')
        )::date AS data_encerramento_vaga,

        c.status::text AS status_candidatura,

        CASE WHEN c.status::text = 'HIRED' THEN 1 ELSE 0 END AS foi_contratado,
        CASE WHEN c.status::text = 'REJECTED' THEN 1 ELSE 0 END AS foi_reprovado,
        CASE WHEN c.status::text = 'DECLINED' THEN 1 ELSE 0 END AS foi_desistente,
        CASE WHEN c.status::text = 'ACTIVE' THEN 1 ELSE 0 END AS esta_ativo

    FROM candidaturas c
    INNER JOIN vagas v ON c.vaga_id = v.id
    LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
    LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.stage_name IS NOT NULL
),
duracoes_por_estagio AS (
    -- PASSO 1: Calcula duração de cada estágio (window function)
    SELECT
        ct.candidatura_id,
        ct.stage_id,
        ct.transition_at,
        EXTRACT(EPOCH FROM (
            LEAD(ct.transition_at) OVER (
                PARTITION BY ct.candidatura_id
                ORDER BY ct.transition_at
            ) - ct.transition_at
        )) / 86400 AS duracao_dias
    FROM candidatura_timeline ct
),
metricas_timeline AS (
    -- PASSO 2: Agrega métricas (sem window functions dentro de agregações)
    SELECT
        ct.candidatura_id,

        -- Contadores básicos
        COUNT(DISTINCT ct.stage_id) AS total_etapas_percorridas,
        COUNT(*) AS total_transicoes,

        -- Datas de transições
        MIN(ct.transition_at) AS primeira_transicao,
        MAX(ct.transition_at) AS ultima_transicao,

        -- Duração total do funil
        EXTRACT(EPOCH FROM (MAX(ct.transition_at) - MIN(ct.transition_at))) / 86400 AS duracao_timeline_dias

    FROM candidatura_timeline ct
    GROUP BY ct.candidatura_id
),
duracao_media AS (
    -- PASSO 3: Calcula média das durações (agora sem conflito)
    SELECT
        d.candidatura_id,
        AVG(d.duracao_dias) AS duracao_media_por_estagio_dias
    FROM duracoes_por_estagio d
    WHERE d.duracao_dias IS NOT NULL
    GROUP BY d.candidatura_id
)
SELECT
    -- Identificação
    en.id AS candidatura_id,
    en.vaga_id,
    en.talent_inhire_id,
    en.nome_vaga,
    en.area_vaga,
    en.nome_talento,

    -- Etapa do Funil
    en.etapa_funil_normalizada AS etapa_funil,
    en.ordem_funil_padrao AS ordem_etapa,
    en.stage_order AS ordem_stage_original,

    -- Dimensões de Análise
    en.recrutadora,
    en.cliente,
    en.torre,

    -- Status
    en.status_candidatura,
    en.foi_contratado,
    en.foi_reprovado,
    en.foi_desistente,
    en.esta_ativo,

    -- Datas
    en.created_at AS data_criacao_candidatura,
    en.updated_at AS data_atualizacao_candidatura,
    en.data_criacao_vaga,
    en.data_encerramento_vaga,

    -- Tempo no processo (LEGADO - mantido para compatibilidade)
    (en.updated_at::date - en.created_at::date)::int AS dias_no_processo,

    -- ===========================
    -- NOVAS MÉTRICAS DE TIMELINE
    -- ===========================

    -- Contadores de progressão
    COALESCE(mt.total_etapas_percorridas, 0) AS total_etapas_percorridas,
    COALESCE(mt.total_transicoes, 0) AS total_transicoes,

    -- Datas de transições
    mt.primeira_transicao::date AS primeira_transicao,
    mt.ultima_transicao::date AS ultima_transicao,

    -- Durações
    ROUND(COALESCE(mt.duracao_timeline_dias, 0)::numeric, 1) AS duracao_timeline_dias,
    ROUND(COALESCE(dm.duracao_media_por_estagio_dias, 0)::numeric, 1) AS duracao_media_por_estagio_dias,

    -- Indicador de cobertura de timeline
    CASE
        WHEN mt.candidatura_id IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS tem_dados_timeline

FROM etapas_normalizadas en
LEFT JOIN metricas_timeline mt ON en.id = mt.candidatura_id
LEFT JOIN duracao_media dm ON en.id = dm.candidatura_id
ORDER BY en.created_at DESC;

-- Comentários
COMMENT ON VIEW vw_funil_performance IS
'View para análise de funil de performance das candidaturas.

ATUALIZAÇÃO 2026-02-24 (Migration 067 - FIXED):
==================================================
Adicionadas métricas de progressão usando candidatura_timeline (versão corrigida)

NOVAS COLUNAS:
- total_etapas_percorridas: Número de estágios únicos visitados
- total_transicoes: Número total de mudanças de estágio
- primeira_transicao: Data da primeira mudança de estágio
- ultima_transicao: Data da última mudança de estágio
- duracao_timeline_dias: Tempo total entre primeira e última transição
- duracao_media_por_estagio_dias: Tempo médio gasto em cada estágio
- tem_dados_timeline: Indicador se candidatura tem dados de timeline

CORREÇÃO TÉCNICA:
- Separados cálculos de window functions e agregações em CTEs distintas
- Resolvido erro "aggregate function calls cannot contain window function calls"

COBERTURA:
- 99% das candidaturas têm dados de timeline (79.859 de 80.652)
- 130.239 eventos de transição rastreados
- Média de 1.6 transições por candidatura

USO RECOMENDADO:
- Analisar rapidez: ORDER BY duracao_timeline_dias
- Filtrar completos: WHERE total_etapas_percorridas >= 5
- Benchmark: AVG(duracao_media_por_estagio_dias) GROUP BY recrutadora
- Ver gargalos: JOIN com vw_performance_por_estagio (próxima view)

PERFORMANCE:
- View otimizada com CTEs sequenciais
- Rápida para queries diretas e filtros
- Use vw_performance_por_estagio para análises agregadas de gargalos
';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_timeline INTEGER;
    v_cobertura_pct NUMERIC;
    v_avg_transicoes NUMERIC;
    v_avg_etapas NUMERIC;
    v_avg_duracao_dias NUMERIC;
    v_avg_duracao_estagio NUMERIC;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_funil_performance;
    SELECT COUNT(*) INTO v_com_timeline FROM vw_funil_performance WHERE tem_dados_timeline;
    SELECT ROUND((v_com_timeline::numeric / NULLIF(v_total, 0) * 100), 1) INTO v_cobertura_pct;

    SELECT ROUND(AVG(total_transicoes), 1) INTO v_avg_transicoes
    FROM vw_funil_performance WHERE tem_dados_timeline;

    SELECT ROUND(AVG(total_etapas_percorridas), 1) INTO v_avg_etapas
    FROM vw_funil_performance WHERE tem_dados_timeline;

    SELECT ROUND(AVG(duracao_timeline_dias), 1) INTO v_avg_duracao_dias
    FROM vw_funil_performance WHERE tem_dados_timeline AND duracao_timeline_dias > 0;

    SELECT ROUND(AVG(duracao_media_por_estagio_dias), 1) INTO v_avg_duracao_estagio
    FROM vw_funil_performance WHERE tem_dados_timeline AND duracao_media_por_estagio_dias > 0;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 067 (FIXED) - TIMELINE DATA INTEGRATION';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'COVERAGE:';
    RAISE NOTICE '  Total candidaturas: %', v_total;
    RAISE NOTICE '  With timeline data: % (%%)', v_com_timeline, v_cobertura_pct;
    RAISE NOTICE '';
    RAISE NOTICE 'CALCULATED METRICS:';
    RAISE NOTICE '  Avg transitions per candidatura: %', v_avg_transicoes;
    RAISE NOTICE '  Avg stages traversed: %', v_avg_etapas;
    RAISE NOTICE '  Avg funnel duration (days): %', v_avg_duracao_dias;
    RAISE NOTICE '  Avg time per stage (days): %', v_avg_duracao_estagio;
    RAISE NOTICE '';
    RAISE NOTICE 'NEW COLUMNS ADDED:';
    RAISE NOTICE '  ✓ total_etapas_percorridas';
    RAISE NOTICE '  ✓ total_transicoes';
    RAISE NOTICE '  ✓ primeira_transicao';
    RAISE NOTICE '  ✓ ultima_transicao';
    RAISE NOTICE '  ✓ duracao_timeline_dias';
    RAISE NOTICE '  ✓ duracao_media_por_estagio_dias';
    RAISE NOTICE '  ✓ tem_dados_timeline';
    RAISE NOTICE '';
    RAISE NOTICE 'TECHNICAL FIX:';
    RAISE NOTICE '  ✓ Separated window functions from aggregations';
    RAISE NOTICE '  ✓ Uses 3 CTEs: duracoes_por_estagio → metricas_timeline → duracao_media';
    RAISE NOTICE '  ✓ Resolved "aggregate cannot contain window function" error';
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '  1. Create vw_performance_por_estagio (stage aggregation + bottlenecks)';
    RAISE NOTICE '  2. Create vw_transicoes_estagio (Sankey diagram data)';
    RAISE NOTICE '  3. Update Power BI documentation';
    RAISE NOTICE '================================================================================';
END $$;
