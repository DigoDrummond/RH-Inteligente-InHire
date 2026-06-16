/*
================================================================================
MIGRATION 069: Criar view vw_transicoes_estagio (Dados para Sankey Diagram)
================================================================================

Data: 2026-02-24
Descrição:
  Cria view com matriz de transições entre estágios do funil.
  Dados prontos para visualização Sankey Diagram no Power BI.

Objetivo:
  - Visualizar fluxo de candidatos entre estágios
  - Identificar caminhos mais comuns no funil
  - Analisar onde candidatos saem do processo
  - Tempo médio de cada transição

Estrutura Sankey:
  - Origem: Estágio inicial
  - Destino: Estágio seguinte
  - Valor: Quantidade de candidatos
  - Tempo: Duração média da transição

Uso no Power BI:
  - Sankey Diagram visual
  - Análise de fluxo do funil
  - Identificação de drop-offs
  - Benchmark de caminhos

================================================================================
*/

-- Remove view se existir
DROP VIEW IF EXISTS vw_transicoes_estagio CASCADE;

-- Cria view de transições entre estágios
CREATE OR REPLACE VIEW vw_transicoes_estagio AS
WITH transicoes_raw AS (
    -- Captura cada transição individual de estágio
    SELECT
        ct.candidatura_id,
        ct.stage_name AS estagio_origem,
        ct.stage_order AS ordem_origem,
        ct.transition_at AS data_entrada,

        -- Próximo estágio usando LEAD
        LEAD(ct.stage_name) OVER (
            PARTITION BY ct.candidatura_id
            ORDER BY ct.transition_at
        ) AS estagio_destino,

        LEAD(ct.stage_order) OVER (
            PARTITION BY ct.candidatura_id
            ORDER BY ct.transition_at
        ) AS ordem_destino,

        LEAD(ct.transition_at) OVER (
            PARTITION BY ct.candidatura_id
            ORDER BY ct.transition_at
        ) AS data_saida,

        -- Duração no estágio (em dias)
        EXTRACT(EPOCH FROM (
            LEAD(ct.transition_at) OVER (
                PARTITION BY ct.candidatura_id
                ORDER BY ct.transition_at
            ) - ct.transition_at
        )) / 86400 AS duracao_dias

    FROM candidatura_timeline ct
    WHERE ct.stage_name IS NOT NULL
),
transicoes_com_contexto AS (
    -- Adiciona contexto de vaga/candidatura
    SELECT
        tr.*,
        c.vaga_id,
        v.user_name AS recrutadora,
        cl.name AS cliente,
        v.custom_fields->>'Torre' AS torre,

        -- Normaliza nomes dos estágios
        CASE
            WHEN tr.estagio_origem ILIKE '%hunting%' THEN 'Hunting'
            WHEN tr.estagio_origem ILIKE '%abordagem%' THEN 'Abordagem'
            WHEN tr.estagio_origem ILIKE '%inscri%' THEN 'Inscrição'
            WHEN tr.estagio_origem ILIKE '%bate%papo%pessoas%cultura%' OR tr.estagio_origem ILIKE '%bate%papo%time%gente%' THEN 'Bate papo | Pessoas e Cultura'
            WHEN tr.estagio_origem ILIKE '%etapa%t%cnica%' THEN 'Etapa técnica | Talent IA'
            WHEN tr.estagio_origem ILIKE '%aguardando%devolutiva%ia%' OR tr.estagio_origem ILIKE '%aguardando%devolutiva%' THEN 'Aguardando Devolutiva IA'
            WHEN tr.estagio_origem ILIKE '%bate%papo%cliente%' OR tr.estagio_origem ILIKE '%bate%papo%gestor%' THEN 'Bate Papo | Cliente'
            WHEN tr.estagio_origem ILIKE '%formaliza%' THEN 'Formalização de Proposta'
            WHEN tr.estagio_origem ILIKE '%contrata%' THEN 'Contratação'
            WHEN tr.estagio_origem ILIKE '%aguardando%agenda%' THEN 'Aguardando Agenda'
            ELSE tr.estagio_origem
        END AS estagio_origem_normalizado,

        CASE
            WHEN tr.estagio_destino ILIKE '%hunting%' THEN 'Hunting'
            WHEN tr.estagio_destino ILIKE '%abordagem%' THEN 'Abordagem'
            WHEN tr.estagio_destino ILIKE '%inscri%' THEN 'Inscrição'
            WHEN tr.estagio_destino ILIKE '%bate%papo%pessoas%cultura%' OR tr.estagio_destino ILIKE '%bate%papo%time%gente%' THEN 'Bate papo | Pessoas e Cultura'
            WHEN tr.estagio_destino ILIKE '%etapa%t%cnica%' THEN 'Etapa técnica | Talent IA'
            WHEN tr.estagio_destino ILIKE '%aguardando%devolutiva%ia%' OR tr.estagio_destino ILIKE '%aguardando%devolutiva%' THEN 'Aguardando Devolutiva IA'
            WHEN tr.estagio_destino ILIKE '%bate%papo%cliente%' OR tr.estagio_destino ILIKE '%bate%papo%gestor%' THEN 'Bate Papo | Cliente'
            WHEN tr.estagio_destino ILIKE '%formaliza%' THEN 'Formalização de Proposta'
            WHEN tr.estagio_destino ILIKE '%contrata%' THEN 'Contratação'
            WHEN tr.estagio_destino ILIKE '%aguardando%agenda%' THEN 'Aguardando Agenda'
            ELSE tr.estagio_destino
        END AS estagio_destino_normalizado

    FROM transicoes_raw tr
    INNER JOIN candidaturas c ON c.id = tr.candidatura_id
    INNER JOIN vagas v ON v.id = c.vaga_id
    LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
    WHERE tr.estagio_destino IS NOT NULL  -- Remove última transição (sem destino)
)
SELECT
    -- ===========================
    -- IDENTIFICAÇÃO DA TRANSIÇÃO
    -- ===========================
    estagio_origem_normalizado AS estagio_origem,
    ordem_origem,
    estagio_destino_normalizado AS estagio_destino,
    ordem_destino,

    -- Label para Sankey (Origem → Destino)
    estagio_origem_normalizado || ' → ' || estagio_destino_normalizado AS transicao_label,

    -- ===========================
    -- DIMENSÕES DE ANÁLISE
    -- ===========================
    recrutadora,
    cliente,
    torre,

    -- ===========================
    -- MÉTRICAS DE VOLUME
    -- ===========================
    COUNT(DISTINCT candidatura_id) AS total_candidatos,
    COUNT(*) AS total_transicoes,

    -- ===========================
    -- MÉTRICAS DE TEMPO
    -- ===========================
    ROUND(AVG(duracao_dias)::numeric, 1) AS duracao_media_dias,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duracao_dias)::numeric, 1) AS duracao_mediana_dias,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duracao_dias)::numeric, 1) AS duracao_p90_dias,
    ROUND(MIN(duracao_dias)::numeric, 1) AS duracao_minima_dias,
    ROUND(MAX(duracao_dias)::numeric, 1) AS duracao_maxima_dias,

    -- ===========================
    -- ANÁLISE DE FLUXO
    -- ===========================

    -- Tipo de transição
    CASE
        WHEN ordem_destino > ordem_origem THEN 'Avanço'
        WHEN ordem_destino < ordem_origem THEN 'Retrocesso'
        ELSE 'Lateral'
    END AS tipo_transicao,

    -- Magnitude do avanço/retrocesso
    ordem_destino - ordem_origem AS distancia_estagios

FROM transicoes_com_contexto
GROUP BY
    estagio_origem_normalizado,
    ordem_origem,
    estagio_destino_normalizado,
    ordem_destino,
    recrutadora,
    cliente,
    torre
ORDER BY
    ordem_origem,
    ordem_destino,
    total_candidatos DESC;

-- Comentário
COMMENT ON VIEW vw_transicoes_estagio IS
'View para análise de transições entre estágios do funil (Sankey Diagram).

CRIADA EM: 2026-02-24 (Migration 069)

ESTRUTURA SANKEY:
- estagio_origem: Ponto de partida
- estagio_destino: Próximo estágio
- total_candidatos: Volume de transições (espessura da linha no Sankey)
- duracao_media_dias: Tempo médio da transição

MÉTRICAS INCLUÍDAS:

1. IDENTIFICAÇÃO:
   - estagio_origem / estagio_destino
   - transicao_label (formato: "Origem → Destino")
   - ordem_origem / ordem_destino

2. VOLUME:
   - total_candidatos: Candidatos únicos nesta transição
   - total_transicoes: Total de ocorrências

3. TEMPO:
   - duracao_media_dias / duracao_mediana_dias / duracao_p90_dias
   - duracao_minima_dias / duracao_maxima_dias

4. ANÁLISE DE FLUXO:
   - tipo_transicao: Avanço, Retrocesso ou Lateral
   - distancia_estagios: Quantos estágios avançou/retrocedeu

USO RECOMENDADO:

-- Transições mais comuns (Top 20)
SELECT transicao_label, total_candidatos, duracao_media_dias
FROM vw_transicoes_estagio
ORDER BY total_candidatos DESC
LIMIT 20;

-- Identificar retrocessos no funil
SELECT transicao_label, total_candidatos, tipo_transicao
FROM vw_transicoes_estagio
WHERE tipo_transicao = ''Retrocesso''
ORDER BY total_candidatos DESC;

-- Transições mais lentas
SELECT transicao_label, duracao_media_dias, total_candidatos
FROM vw_transicoes_estagio
WHERE duracao_media_dias > 7
ORDER BY duracao_media_dias DESC;

-- Dados para Sankey (agregado geral)
SELECT
    estagio_origem,
    estagio_destino,
    SUM(total_candidatos) AS valor
FROM vw_transicoes_estagio
GROUP BY estagio_origem, estagio_destino
ORDER BY valor DESC;

POWER BI - SANKEY VISUAL:
1. Source: estagio_origem
2. Destination: estagio_destino
3. Weight: total_candidatos
4. Tooltips: duracao_media_dias, tipo_transicao

COMPLEMENTA:
- vw_funil_performance (dados por candidato)
- vw_performance_por_estagio (agregado por estágio)
';

-- Validação
DO $$
DECLARE
    v_total_transicoes INTEGER;
    v_transicoes_unicas INTEGER;
    v_retrocessos INTEGER;
    v_duracao_media NUMERIC;
BEGIN
    SELECT COUNT(*) INTO v_total_transicoes FROM vw_transicoes_estagio;

    SELECT COUNT(DISTINCT transicao_label) INTO v_transicoes_unicas
    FROM vw_transicoes_estagio;

    SELECT SUM(total_candidatos) INTO v_retrocessos
    FROM vw_transicoes_estagio
    WHERE tipo_transicao = 'Retrocesso';

    SELECT ROUND(AVG(duracao_media_dias), 1) INTO v_duracao_media
    FROM vw_transicoes_estagio;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 069 - VIEW vw_transicoes_estagio CREATED';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'SUMMARY:';
    RAISE NOTICE '  Total transition combinations: %', v_total_transicoes;
    RAISE NOTICE '  Unique transitions: %', v_transicoes_unicas;
    RAISE NOTICE '  Candidates with backward transitions: %', v_retrocessos;
    RAISE NOTICE '  Average transition duration: % days', v_duracao_media;
    RAISE NOTICE '';
    RAISE NOTICE 'KEY METRICS:';
    RAISE NOTICE '  - estagio_origem / estagio_destino (Sankey source/target)';
    RAISE NOTICE '  - total_candidatos (Sankey weight/value)';
    RAISE NOTICE '  - duracao_media_dias (tooltip/analysis)';
    RAISE NOTICE '  - tipo_transicao (Avanco/Retrocesso/Lateral)';
    RAISE NOTICE '';
    RAISE NOTICE 'POWER BI SANKEY SETUP:';
    RAISE NOTICE '  1. Source: estagio_origem';
    RAISE NOTICE '  2. Destination: estagio_destino';
    RAISE NOTICE '  3. Weight: total_candidatos';
    RAISE NOTICE '  4. Tooltips: duracao_media_dias, tipo_transicao';
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '  1. Test view performance';
    RAISE NOTICE '  2. Update Power BI documentation';
    RAISE NOTICE '  3. Create Sankey visualization in Power BI';
    RAISE NOTICE '================================================================================';
END $$;
