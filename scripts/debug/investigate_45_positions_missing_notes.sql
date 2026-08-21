-- ============================================================================
-- Script de Diagnóstico: 45 Posições sem Motivos de Cancelamento
-- Data: 2026-03-20
-- Objetivo: Investigar por que motivos de cancelamento estão ausentes
-- ============================================================================

-- Lista de posições a investigar
\echo '===================================================================================='
\echo 'INVESTIGAÇÃO: 45 Posições sem Motivos de Cancelamento'
\echo '===================================================================================='
\echo ''

-- ---------------------------------------------------------------------------
-- 1. ESTATÍSTICAS GERAIS
-- ---------------------------------------------------------------------------
\echo '[1] ESTATÍSTICAS GERAIS'
\echo '------------------------------------------------------------------------------------'

WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
)
SELECT
    'Total de posições investigadas' AS metrica,
    COUNT(*)::text AS valor
FROM posicoes_investigadas

UNION ALL

SELECT
    'Posições existentes no BD' AS metrica,
    COUNT(DISTINCT p.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN posicoes p ON p.id = pi.posicao_id

UNION ALL

SELECT
    'Posições com eventos de timeline' AS metrica,
    COUNT(DISTINCT pt.posicao_id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id

UNION ALL

SELECT
    'Total de eventos de timeline' AS metrica,
    COUNT(pt.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id

UNION ALL

SELECT
    'Eventos COM notes/reason' AS metrica,
    COUNT(pt.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
WHERE pt.notes IS NOT NULL AND TRIM(pt.notes) != ''

UNION ALL

SELECT
    'Eventos SEM notes/reason' AS metrica,
    COUNT(pt.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
WHERE pt.notes IS NULL OR TRIM(pt.notes) = ''

UNION ALL

SELECT
    'Eventos canceled/paused COM notes' AS metrica,
    COUNT(pt.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
WHERE pt.new_status IN ('canceled', 'paused')
  AND pt.notes IS NOT NULL AND TRIM(pt.notes) != ''

UNION ALL

SELECT
    'Eventos canceled/paused SEM notes' AS metrica,
    COUNT(pt.id)::text AS valor
FROM posicoes_investigadas pi
INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
WHERE pt.new_status IN ('canceled', 'paused')
  AND (pt.notes IS NULL OR TRIM(pt.notes) = '');

\echo ''

-- ---------------------------------------------------------------------------
-- 2. DETECÇÃO DE DUPLICATAS
-- ---------------------------------------------------------------------------
\echo '[2] DETECÇÃO DE DUPLICATAS (Padrão: mesma posição, data, status)'
\echo '------------------------------------------------------------------------------------'

WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
),
duplicates AS (
    SELECT
        pt.posicao_id,
        DATE(pt.changed_at) as event_date,
        pt.new_status,
        COUNT(*) as dup_count,
        SUM(CASE WHEN pt.notes IS NOT NULL AND TRIM(pt.notes) != '' THEN 1 ELSE 0 END) as with_notes,
        SUM(CASE WHEN pt.notes IS NULL OR TRIM(pt.notes) = '' THEN 1 ELSE 0 END) as without_notes
    FROM posicoes_investigadas pi
    INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
    GROUP BY pt.posicao_id, DATE(pt.changed_at), pt.new_status
    HAVING COUNT(*) > 1
)
SELECT
    'Total de grupos de duplicatas' AS metrica,
    COUNT(*)::text AS valor
FROM duplicates

UNION ALL

SELECT
    'Total de eventos duplicados' AS metrica,
    SUM(dup_count)::text AS valor
FROM duplicates

UNION ALL

SELECT
    'Duplicatas COM padrão notes (1 COM, 1 SEM)' AS metrica,
    COUNT(*)::text AS valor
FROM duplicates
WHERE with_notes > 0 AND without_notes > 0;

\echo ''

-- ---------------------------------------------------------------------------
-- 3. AMOSTRA DE DUPLICATAS (Top 10)
-- ---------------------------------------------------------------------------
\echo '[3] AMOSTRA DE DUPLICATAS (Top 10 grupos)'
\echo '------------------------------------------------------------------------------------'

WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
),
duplicates AS (
    SELECT
        pt.posicao_id,
        DATE(pt.changed_at) as event_date,
        pt.new_status,
        COUNT(*) as dup_count
    FROM posicoes_investigadas pi
    INNER JOIN position_timeline pt ON pt.posicao_id = pi.posicao_id
    GROUP BY pt.posicao_id, DATE(pt.changed_at), pt.new_status
    HAVING COUNT(*) > 1
)
SELECT
    d.posicao_id,
    p.inhire_id,
    v.nome as vaga_nome,
    d.event_date,
    d.new_status,
    d.dup_count as total_eventos
FROM duplicates d
INNER JOIN posicoes p ON p.id = d.posicao_id
INNER JOIN vagas v ON v.id = p.vaga_id
ORDER BY d.dup_count DESC, d.posicao_id
LIMIT 10;

\echo ''

-- ---------------------------------------------------------------------------
-- 4. COMPARAÇÃO COM AS 85 POSIÇÕES CORRIGIDAS ANTERIORMENTE
-- ---------------------------------------------------------------------------
\echo '[4] COMPARAÇÃO: 45 posições vs 85 corrigidas anteriormente'
\echo '------------------------------------------------------------------------------------'

-- Lista das 85 posições corrigidas em 2026-03-20
WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
),
posicoes_corrigidas_anteriormente AS (
    SELECT unnest(ARRAY[
        386, 311, 85, 935, 240, 254, 516, 1274, 1238, 639,
        1202, 598, 265, 1129, 1180, 956, 1100, 1167, 1168, 1169,
        1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179,
        1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190,
        1191, 1192, 1193, 1194, 1196, 1197, 1198, 1199, 1200, 1201,
        1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212,
        1213, 1214, 1215, 1216, 1217, 1218, 1219, 1221, 1222, 1223,
        1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233,
        1234, 1235, 1236, 1237, 1239
    ]) AS posicao_id
)
SELECT
    'Posições que ESTAVAM nas 85 anteriores' AS categoria,
    COUNT(*)::text AS total
FROM posicoes_investigadas pi
WHERE pi.posicao_id IN (SELECT posicao_id FROM posicoes_corrigidas_anteriormente)

UNION ALL

SELECT
    'Posições NOVAS (não estavam nas 85)' AS categoria,
    COUNT(*)::text AS total
FROM posicoes_investigadas pi
WHERE pi.posicao_id NOT IN (SELECT posicao_id FROM posicoes_corrigidas_anteriormente);

\echo ''

-- ---------------------------------------------------------------------------
-- 5. STATUS ATUAL DAS POSIÇÕES
-- ---------------------------------------------------------------------------
\echo '[5] STATUS ATUAL DAS POSIÇÕES'
\echo '------------------------------------------------------------------------------------'

WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
)
SELECT
    p.status,
    COUNT(*) as total_posicoes
FROM posicoes_investigadas pi
INNER JOIN posicoes p ON p.id = pi.posicao_id
GROUP BY p.status
ORDER BY total_posicoes DESC;

\echo ''

-- ---------------------------------------------------------------------------
-- 6. DETALHAMENTO DE POSIÇÕES SEM NOTES (Top 10)
-- ---------------------------------------------------------------------------
\echo '[6] DETALHAMENTO: Top 10 posições SEM notes em eventos canceled/paused'
\echo '------------------------------------------------------------------------------------'

WITH posicoes_investigadas AS (
    SELECT unnest(ARRAY[
        386, 1220, 201, 1235, 935, 1228, 1221, 1237, 636, 637,
        273, 643, 514, 902, 336, 687, 177, 789, 738, 707,
        650, 1195, 915, 232, 213, 657, 349, 182, 711, 994,
        334, 1035, 945, 676, 1580, 483, 1601, 591, 586, 587,
        588, 1551, 2090, 2087, 2122, 2141
    ]) AS posicao_id
)
SELECT
    p.id as posicao_id,
    p.inhire_id,
    v.nome as vaga_nome,
    p.status as status_atual,
    COUNT(pt.id) as total_eventos,
    SUM(CASE WHEN pt.new_status IN ('canceled', 'paused') AND (pt.notes IS NULL OR TRIM(pt.notes) = '') THEN 1 ELSE 0 END) as eventos_cancelpaused_sem_notes,
    MAX(pt.changed_at) as ultimo_evento
FROM posicoes_investigadas pi
INNER JOIN posicoes p ON p.id = pi.posicao_id
INNER JOIN vagas v ON v.id = p.vaga_id
LEFT JOIN position_timeline pt ON pt.posicao_id = p.id
GROUP BY p.id, p.inhire_id, v.nome, p.status
HAVING SUM(CASE WHEN pt.new_status IN ('canceled', 'paused') AND (pt.notes IS NULL OR TRIM(pt.notes) = '') THEN 1 ELSE 0 END) > 0
ORDER BY eventos_cancelpaused_sem_notes DESC, total_eventos DESC
LIMIT 10;

\echo ''
\echo '===================================================================================='
\echo 'FIM DO DIAGNÓSTICO'
\echo '===================================================================================='
