-- Análise Comparativa: Talentos PostgreSQL vs Inhire API
-- Data: 2026-06-23

\echo '================================================================================'
\echo 'ANÁLISE DE TALENTOS - BANCO DE DADOS POSTGRESQL'
\echo '================================================================================'
\echo ''

-- 1. Total de Talentos no BD
\echo '1. TOTAL DE TALENTOS NO BANCO DE DADOS'
\echo '--------------------------------------------------------------------------------'
SELECT
    COUNT(*) as total_talentos_bd,
    COUNT(DISTINCT inhire_id) as talentos_unicos_inhire_id
FROM talentos;

\echo ''
\echo '2. TALENTOS COM E SEM CANDIDATURAS'
\echo '--------------------------------------------------------------------------------'

-- Talentos COM candidaturas
SELECT
    'COM candidaturas' as tipo,
    COUNT(DISTINCT t.id) as total_talentos
FROM talentos t
WHERE EXISTS (
    SELECT 1
    FROM candidaturas c
    WHERE c.talent_inhire_id = t.inhire_id
);

-- Talentos SEM candidaturas
SELECT
    'SEM candidaturas' as tipo,
    COUNT(DISTINCT t.id) as total_talentos
FROM talentos t
WHERE NOT EXISTS (
    SELECT 1
    FROM candidaturas c
    WHERE c.talent_inhire_id = t.inhire_id
);

\echo ''
\echo '3. DISTRIBUIÇÃO POR DATA DE ATUALIZAÇÃO'
\echo '--------------------------------------------------------------------------------'
SELECT
    CASE
        WHEN updated_at_inhire >= NOW() - INTERVAL '7 days' THEN 'Última semana'
        WHEN updated_at_inhire >= NOW() - INTERVAL '30 days' THEN 'Último mês'
        WHEN updated_at_inhire >= NOW() - INTERVAL '90 days' THEN 'Últimos 3 meses'
        WHEN updated_at_inhire >= NOW() - INTERVAL '180 days' THEN 'Últimos 6 meses'
        ELSE 'Mais de 6 meses'
    END as periodo,
    COUNT(*) as total_talentos
FROM talentos
GROUP BY
    CASE
        WHEN updated_at_inhire >= NOW() - INTERVAL '7 days' THEN 'Última semana'
        WHEN updated_at_inhire >= NOW() - INTERVAL '30 days' THEN 'Último mês'
        WHEN updated_at_inhire >= NOW() - INTERVAL '90 days' THEN 'Últimos 3 meses'
        WHEN updated_at_inhire >= NOW() - INTERVAL '180 days' THEN 'Últimos 6 meses'
        ELSE 'Mais de 6 meses'
    END
ORDER BY
    CASE
        WHEN periodo = 'Última semana' THEN 1
        WHEN periodo = 'Último mês' THEN 2
        WHEN periodo = 'Últimos 3 meses' THEN 3
        WHEN periodo = 'Últimos 6 meses' THEN 4
        ELSE 5
    END;

\echo ''
\echo '4. ÚLTIMAS SINCRONIZAÇÕES DE TALENTOS'
\echo '--------------------------------------------------------------------------------'
SELECT
    sync_type,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duracao_minutos,
    records_processed,
    records_created,
    records_updated,
    records_skipped,
    records_failed
FROM sync_log
WHERE sync_entity = 'TALENTOS'
ORDER BY start_time DESC
LIMIT 5;

\echo ''
\echo '5. TOTAL DE CANDIDATURAS ÚNICAS (TALENT_INHIRE_ID)'
\echo '--------------------------------------------------------------------------------'
SELECT
    COUNT(DISTINCT talent_inhire_id) as talentos_unicos_em_candidaturas
FROM candidaturas
WHERE talent_inhire_id IS NOT NULL;

\echo ''
\echo '================================================================================'
\echo 'FIM DA ANÁLISE'
\echo '================================================================================'
