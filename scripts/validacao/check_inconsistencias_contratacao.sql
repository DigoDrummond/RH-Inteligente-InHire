/*
================================================================================
Query de Monitoramento: Inconsistências em Posições com Etapa "Contratação"
================================================================================

OBJETIVO:
  Identificar posições onde a etapa do funil indica "Contratação" mas:
  - Status da posição não é "closed" ou "filled"
  - Campo hired_at está NULL (não foi preenchido)
  - Outras inconsistências de dados

USO:
  psql -U postgres -d inhire -f scripts/validacao/check_inconsistencias_contratacao.sql

RESULTADO:
  Lista de posições inconsistentes com classificação de severidade

================================================================================
*/

-- ============================================================================
-- CTE 1: Última etapa alcançada por vaga
-- ============================================================================
WITH ultima_etapa_por_vaga AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        cd.updated_at_inhire,
        COUNT(*) as num_candidatos_nesta_etapa,
        ROW_NUMBER() OVER (
            PARTITION BY cd.vaga_id
            ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC
        ) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL
      AND cd.stage_order IS NOT NULL
    GROUP BY cd.vaga_id, cd.stage_name, cd.stage_order, cd.updated_at_inhire
),

-- ============================================================================
-- CTE 2: Dados das posições com informações da etapa
-- ============================================================================
posicoes_com_etapa AS (
    SELECT
        p.id AS posicao_id,
        p.vaga_id,
        p.inhire_id AS posicao_inhire_id,
        p.status AS status_posicao,
        p.hired_at,
        p.opened_at,
        p.created_at,
        p.updated_at,
        p.reason,
        ue.stage_name AS etapa_funil,
        ue.stage_order,
        ue.updated_at_inhire AS data_ultima_candidatura_etapa,
        ue.num_candidatos_nesta_etapa,
        v.title AS vaga_titulo,
        v.status AS vaga_status
    FROM posicoes p
    LEFT JOIN ultima_etapa_por_vaga ue
        ON ue.vaga_id = p.vaga_id
        AND ue.rn = 1
    LEFT JOIN vagas v
        ON v.id = p.vaga_id
    WHERE ue.stage_name IS NOT NULL  -- Apenas posições com candidaturas
),

-- ============================================================================
-- CTE 3: Classificação de inconsistências
-- ============================================================================
classificacao AS (
    SELECT
        *,
        CASE
            -- CRÍTICO: Candidato em "Contratação" mas posição aberta e sem hired_at
            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('open', 'paused', 'pending')
                 AND hired_at IS NULL
            THEN 'CRÍTICO'

            -- ALTO: Candidato em "Contratação" mas apenas sem hired_at (status fechado)
            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('closed', 'filled', 'canceled')
                 AND hired_at IS NULL
            THEN 'ALTO'

            -- MÉDIO: Candidato em "Contratação" mas posição aberta (mas tem hired_at)
            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('open', 'paused', 'pending')
                 AND hired_at IS NOT NULL
            THEN 'MÉDIO'

            -- BAIXO: Etapa avançada (>= 9) mas não é "Contratação" e posição está aberta
            WHEN stage_order >= 9
                 AND etapa_funil != 'Contratação'
                 AND status_posicao IN ('open', 'paused')
            THEN 'BAIXO'

            -- OK: Tudo consistente
            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('closed', 'filled')
                 AND hired_at IS NOT NULL
            THEN 'OK'

            ELSE 'OUTROS'
        END AS severidade,

        CASE
            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('open', 'paused', 'pending')
                 AND hired_at IS NULL
            THEN 'Candidato em Contratação mas posição ABERTA e SEM hired_at'

            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('closed', 'filled', 'canceled')
                 AND hired_at IS NULL
            THEN 'Posição FECHADA mas hired_at não foi preenchido'

            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('open', 'paused', 'pending')
                 AND hired_at IS NOT NULL
            THEN 'Posição foi contratada (hired_at preenchido) mas status não foi atualizado para closed'

            WHEN stage_order >= 9
                 AND etapa_funil != 'Contratação'
                 AND status_posicao IN ('open', 'paused')
            THEN 'Candidato em etapa final (order >= 9) mas posição ainda aberta'

            WHEN etapa_funil = 'Contratação'
                 AND status_posicao IN ('closed', 'filled')
                 AND hired_at IS NOT NULL
            THEN 'Dados consistentes - Contratação OK'

            ELSE 'Outras situações'
        END AS descricao_problema
    FROM posicoes_com_etapa
)

-- ============================================================================
-- RESULTADO FINAL
-- ============================================================================
SELECT
    severidade,
    posicao_id,
    vaga_id,
    vaga_titulo,
    status_posicao,
    etapa_funil,
    stage_order,
    hired_at,
    num_candidatos_nesta_etapa,
    data_ultima_candidatura_etapa,
    updated_at AS posicao_updated_at,
    descricao_problema
FROM classificacao
WHERE severidade IN ('CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO')  -- Excluir apenas "OK" e "OUTROS"
ORDER BY
    CASE severidade
        WHEN 'CRÍTICO' THEN 1
        WHEN 'ALTO' THEN 2
        WHEN 'MÉDIO' THEN 3
        WHEN 'BAIXO' THEN 4
        ELSE 5
    END,
    posicao_id DESC;

-- ============================================================================
-- ESTATÍSTICAS RESUMIDAS
-- ============================================================================

\echo
\echo '================================================================================'
\echo 'ESTATÍSTICAS RESUMIDAS'
\echo '================================================================================'

SELECT
    severidade,
    COUNT(*) as quantidade,
    ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM classificacao
GROUP BY severidade
ORDER BY
    CASE severidade
        WHEN 'CRÍTICO' THEN 1
        WHEN 'ALTO' THEN 2
        WHEN 'MÉDIO' THEN 3
        WHEN 'BAIXO' THEN 4
        WHEN 'OK' THEN 5
        ELSE 6
    END;

\echo
\echo '================================================================================'
\echo 'RESUMO POR DESCRIÇÃO DO PROBLEMA'
\echo '================================================================================'

SELECT
    descricao_problema,
    COUNT(*) as quantidade
FROM classificacao
WHERE severidade IN ('CRÍTICO', 'ALTO', 'MÉDIO')
GROUP BY descricao_problema
ORDER BY quantidade DESC;

-- ============================================================================
-- AÇÕES RECOMENDADAS
-- ============================================================================

\echo
\echo '================================================================================'
\echo 'AÇÕES RECOMENDADAS'
\echo '================================================================================'
\echo
\echo 'CRÍTICO (Candidato em Contratação + Posição Aberta + Sem hired_at):'
\echo '  1. Verificar se contratação foi confirmada'
\echo '  2. Se SIM: Atualizar hired_at e status para closed'
\echo '  3. Se NÃO: Mover candidato para etapa anterior ou declinar'
\echo
\echo 'ALTO (Posição Fechada + Sem hired_at):'
\echo '  1. Preencher hired_at com data de contratação'
\echo '  2. Se não houve contratação, ajustar status para cancelado'
\echo
\echo 'MÉDIO (Contratação OK + Status não atualizado):'
\echo '  1. Atualizar status da posição para closed/filled'
\echo '  2. Verificar se há processo automatizado falhando'
\echo
\echo 'BAIXO (Etapa final + Posição aberta):'
\echo '  1. Monitorar - pode ser processo em andamento'
\echo '  2. Verificar após 7 dias se status foi atualizado'
\echo
\echo '================================================================================'
