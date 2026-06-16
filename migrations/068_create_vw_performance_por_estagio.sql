/*
================================================================================
MIGRATION 068: Criar view vw_performance_por_estagio (Análise Agregada)
================================================================================

Data: 2026-02-24
Descrição:
  Cria view para análise agregada de performance por estágio do funil.
  Complementa vw_funil_performance com métricas de gargalos e conversões.

Objetivo:
  - Identificar estágios mais demorados (gargalos)
  - Analisar taxa de conversão entre estágios
  - Calcular tempo médio, mediano e p90 por estágio
  - Comparar performance entre recrutadoras/torres/clientes

Métricas Incluídas:
  1. Volume de candidatos por estágio
  2. Taxa de conversão para próximo estágio
  3. Taxa de aprovação/reprovação/desistência
  4. Tempo médio, mediano, p90 no estágio
  5. Identificação de gargalos

Uso no Power BI:
  - Dashboard de gargalos do funil
  - Benchmark entre recrutadoras
  - Análise de tempo por etapa
  - Identificação de pontos de melhoria

================================================================================
*/

-- Remove view se existir
DROP VIEW IF EXISTS vw_performance_por_estagio CASCADE;

-- Cria view de performance agregada por estágio
CREATE OR REPLACE VIEW vw_performance_por_estagio AS
WITH candidatos_por_estagio AS (
    -- Agrega dados por etapa do funil
    SELECT
        etapa_funil,
        ordem_etapa,

        -- Dimensões de análise
        recrutadora,
        cliente,
        torre,

        -- Contadores
        COUNT(*) AS total_candidatos,
        COUNT(*) FILTER (WHERE foi_contratado = 1) AS total_contratados,
        COUNT(*) FILTER (WHERE foi_reprovado = 1) AS total_reprovados,
        COUNT(*) FILTER (WHERE foi_desistente = 1) AS total_desistentes,
        COUNT(*) FILTER (WHERE esta_ativo = 1) AS total_ativos,

        -- Métricas de timeline (apenas candidatos com dados)
        COUNT(*) FILTER (WHERE tem_dados_timeline) AS candidatos_com_timeline,

        -- Durações agregadas
        AVG(duracao_media_por_estagio_dias) FILTER (WHERE tem_dados_timeline AND duracao_media_por_estagio_dias > 0) AS tempo_medio_estagio,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duracao_media_por_estagio_dias) FILTER (WHERE tem_dados_timeline AND duracao_media_por_estagio_dias > 0) AS tempo_mediano_estagio,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duracao_media_por_estagio_dias) FILTER (WHERE tem_dados_timeline AND duracao_media_por_estagio_dias > 0) AS tempo_p90_estagio,

        -- Total de transições
        SUM(total_transicoes) FILTER (WHERE tem_dados_timeline) AS total_transicoes_estagio

    FROM vw_funil_performance
    GROUP BY etapa_funil, ordem_etapa, recrutadora, cliente, torre
),
conversao_entre_estagios AS (
    -- Calcula taxa de conversão para próximo estágio
    SELECT
        c1.etapa_funil,
        c1.ordem_etapa,
        c1.recrutadora,
        c1.cliente,
        c1.torre,
        c1.total_candidatos AS candidatos_estagio_atual,

        -- Candidatos que avançaram para próximo estágio
        (
            SELECT COUNT(DISTINCT f2.candidatura_id)
            FROM vw_funil_performance f2
            WHERE f2.recrutadora = c1.recrutadora
            AND COALESCE(f2.cliente, 'NULL') = COALESCE(c1.cliente, 'NULL')
            AND COALESCE(f2.torre, 'NULL') = COALESCE(c1.torre, 'NULL')
            AND f2.ordem_etapa = c1.ordem_etapa + 1
        ) AS candidatos_proximo_estagio

    FROM candidatos_por_estagio c1
)
SELECT
    -- Identificação do Estágio
    cpe.etapa_funil,
    cpe.ordem_etapa,

    -- Dimensões de Análise
    cpe.recrutadora,
    cpe.cliente,
    cpe.torre,

    -- ===========================
    -- VOLUME
    -- ===========================
    cpe.total_candidatos,
    cpe.candidatos_com_timeline,
    ROUND(100.0 * cpe.candidatos_com_timeline / NULLIF(cpe.total_candidatos, 0), 1) AS cobertura_timeline_pct,

    -- ===========================
    -- CONVERSÃO
    -- ===========================
    cee.candidatos_proximo_estagio,
    ROUND(100.0 * cee.candidatos_proximo_estagio / NULLIF(cee.candidatos_estagio_atual, 0), 1) AS taxa_conversao_proximo_estagio,

    -- ===========================
    -- STATUS FINAIS
    -- ===========================
    cpe.total_contratados,
    cpe.total_reprovados,
    cpe.total_desistentes,
    cpe.total_ativos,

    -- Taxas percentuais
    ROUND(100.0 * cpe.total_contratados / NULLIF(cpe.total_candidatos, 0), 1) AS taxa_contratacao_pct,
    ROUND(100.0 * cpe.total_reprovados / NULLIF(cpe.total_candidatos, 0), 1) AS taxa_reprovacao_pct,
    ROUND(100.0 * cpe.total_desistentes / NULLIF(cpe.total_candidatos, 0), 1) AS taxa_desistencia_pct,
    ROUND(100.0 * cpe.total_ativos / NULLIF(cpe.total_candidatos, 0), 1) AS taxa_ativos_pct,

    -- ===========================
    -- TEMPO / DURAÇÃO (GARGALOS)
    -- ===========================
    ROUND(cpe.tempo_medio_estagio::numeric, 1) AS tempo_medio_dias,
    ROUND(cpe.tempo_mediano_estagio::numeric, 1) AS tempo_mediano_dias,
    ROUND(cpe.tempo_p90_estagio::numeric, 1) AS tempo_p90_dias,

    -- Indicador de gargalo (estágios com p90 > 7 dias)
    CASE
        WHEN cpe.tempo_p90_estagio > 7 THEN TRUE
        ELSE FALSE
    END AS e_gargalo,

    -- ===========================
    -- MÉTRICAS AUXILIARES
    -- ===========================
    cpe.total_transicoes_estagio

FROM candidatos_por_estagio cpe
LEFT JOIN conversao_entre_estagios cee
    ON cpe.etapa_funil = cee.etapa_funil
    AND cpe.ordem_etapa = cee.ordem_etapa
    AND cpe.recrutadora = cee.recrutadora
    AND COALESCE(cpe.cliente, 'NULL') = COALESCE(cee.cliente, 'NULL')
    AND COALESCE(cpe.torre, 'NULL') = COALESCE(cee.torre, 'NULL')
ORDER BY cpe.ordem_etapa, cpe.recrutadora, cpe.cliente, cpe.torre;

-- Comentário
COMMENT ON VIEW vw_performance_por_estagio IS
'View para análise agregada de performance por estágio do funil.

CRIADA EM: 2026-02-24 (Migration 068)

MÉTRICAS INCLUÍDAS:

1. VOLUME:
   - total_candidatos: Total de candidatos no estágio
   - candidatos_com_timeline: Candidatos com dados de timeline
   - cobertura_timeline_pct: Percentual de cobertura de dados

2. CONVERSÃO:
   - candidatos_proximo_estagio: Quantos avançaram para próximo estágio
   - taxa_conversao_proximo_estagio: Percentual que avançou

3. STATUS FINAIS:
   - total_contratados/reprovados/desistentes/ativos
   - taxa_*_pct: Percentuais de cada status

4. TEMPO / GARGALOS:
   - tempo_medio_dias: Tempo médio no estágio
   - tempo_mediano_dias: Tempo mediano (menos afetado por outliers)
   - tempo_p90_dias: Percentil 90 (outliers lentos)
   - e_gargalo: TRUE se p90 > 7 dias (estágio lento)

USO RECOMENDADO:

-- Identificar gargalos gerais
SELECT * FROM vw_performance_por_estagio
WHERE e_gargalo = TRUE
ORDER BY tempo_p90_dias DESC;

-- Benchmark entre recrutadoras em estágio específico
SELECT recrutadora, total_candidatos, taxa_conversao_proximo_estagio, tempo_medio_dias
FROM vw_performance_por_estagio
WHERE etapa_funil = ''Etapa técnica | Talent IA''
ORDER BY taxa_conversao_proximo_estagio DESC;

-- Análise de conversão por estágio (visão geral)
SELECT
    etapa_funil,
    ordem_etapa,
    SUM(total_candidatos) AS total,
    ROUND(AVG(taxa_conversao_proximo_estagio), 1) AS taxa_conversao_media
FROM vw_performance_por_estagio
GROUP BY etapa_funil, ordem_etapa
ORDER BY ordem_etapa;

-- Gargalos por torre
SELECT torre, etapa_funil, tempo_p90_dias, e_gargalo
FROM vw_performance_por_estagio
WHERE torre IS NOT NULL
ORDER BY tempo_p90_dias DESC
LIMIT 10;

COMPLEMENTA:
- vw_funil_performance (dados por candidato)
- vw_transicoes_estagio (fluxo Sankey entre estágios)
';

-- Validação
DO $$
DECLARE
    v_total_linhas INTEGER;
    v_estagios_unicos INTEGER;
    v_gargalos INTEGER;
    v_taxa_conversao_media NUMERIC;
BEGIN
    SELECT COUNT(*) INTO v_total_linhas FROM vw_performance_por_estagio;
    SELECT COUNT(DISTINCT etapa_funil) INTO v_estagios_unicos FROM vw_performance_por_estagio;
    SELECT COUNT(*) INTO v_gargalos FROM vw_performance_por_estagio WHERE e_gargalo = TRUE;

    SELECT ROUND(AVG(taxa_conversao_proximo_estagio), 1) INTO v_taxa_conversao_media
    FROM vw_performance_por_estagio
    WHERE taxa_conversao_proximo_estagio IS NOT NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 068 - VIEW vw_performance_por_estagio CREATED';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'SUMMARY:';
    RAISE NOTICE '  Total rows: %', v_total_linhas;
    RAISE NOTICE '  Unique stages: %', v_estagios_unicos;
    RAISE NOTICE '  Bottlenecks identified: %', v_gargalos;
    RAISE NOTICE '  Average conversion rate: %', v_taxa_conversao_media;
    RAISE NOTICE '';
    RAISE NOTICE 'KEY METRICS AVAILABLE:';
    RAISE NOTICE '  - total_candidatos (volume per stage)';
    RAISE NOTICE '  - taxa_conversao_proximo_estagio (conversion rate)';
    RAISE NOTICE '  - tempo_medio_dias / tempo_mediano_dias / tempo_p90_dias';
    RAISE NOTICE '  - e_gargalo (bottleneck indicator)';
    RAISE NOTICE '  - taxa_contratacao_pct / taxa_reprovacao_pct / taxa_desistencia_pct';
    RAISE NOTICE '';
    RAISE NOTICE 'USE CASES:';
    RAISE NOTICE '  1. Identify bottlenecks: WHERE e_gargalo = TRUE';
    RAISE NOTICE '  2. Benchmark recruiters: GROUP BY recrutadora';
    RAISE NOTICE '  3. Analyze conversion funnel: ORDER BY ordem_etapa';
    RAISE NOTICE '  4. Compare towers/clients: GROUP BY torre, cliente';
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEP:';
    RAISE NOTICE '  Create vw_transicoes_estagio for Sankey diagram data';
    RAISE NOTICE '================================================================================';
END $$;
