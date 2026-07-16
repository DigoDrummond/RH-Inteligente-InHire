/*
================================================================================
TESTE: Queries da Sincronização Incremental Otimizada
================================================================================

Este script testa as queries que identificam registros modificados
para a nova sincronização incremental otimizada.

Execução:
  psql -U postgres -d inhire -f test_sync_queries.sql
================================================================================
*/

\echo '================================================================================'
\echo 'TESTE: Sincronização Incremental Otimizada - Queries de Identificação'
\echo '================================================================================'
\echo ''

-- Obter última sincronização incremental
\echo '1. Obtendo data da última sincronização incremental...'
\echo '--------------------------------------------------------------------------------'

SELECT
    tenant_id,
    last_incremental_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_sync_incremental,
    last_full_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_sync_completa,
    CASE
        WHEN last_incremental_sync IS NULL THEN 'NENHUMA SYNC INCREMENTAL ANTERIOR'
        ELSE 'OK'
    END as status
FROM sync_configuration
WHERE tenant_id = (SELECT DISTINCT tenant_id FROM sync_configuration LIMIT 1);

\echo ''

-- Query 1: Vagas modificadas
\echo '2. Vagas modificadas/criadas desde última sync...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(*) as total_vagas_modificadas,
    COUNT(CASE WHEN v.created_at > us.data_ref THEN 1 END) as vagas_novas,
    COUNT(CASE WHEN v.updated_at_inhire > us.data_ref AND v.created_at <= us.data_ref THEN 1 END) as vagas_atualizadas
FROM vagas v
CROSS JOIN ultima_sync us
WHERE v.updated_at_inhire > us.data_ref
   OR v.created_at > us.data_ref;

\echo ''

-- Query 2: Posições modificadas
\echo '3. Posições modificadas desde última sync...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(*) as total_posicoes_modificadas,
    MIN(p.updated_at_inhire) as primeira_modificacao,
    MAX(p.updated_at_inhire) as ultima_modificacao
FROM posicoes p
CROSS JOIN ultima_sync us
WHERE p.updated_at_inhire > us.data_ref;

\echo ''

-- Query 3: Candidaturas modificadas
\echo '4. Candidaturas modificadas desde última sync...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(*) as total_candidaturas_modificadas,
    MIN(c.updated_at_inhire) as primeira_modificacao,
    MAX(c.updated_at_inhire) as ultima_modificacao
FROM candidaturas c
CROSS JOIN ultima_sync us
WHERE c.updated_at_inhire > us.data_ref;

\echo ''

-- Query 4: Talentos modificados
\echo '5. Talentos modificados desde última sync...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(*) as total_talentos_modificados,
    MIN(t.updated_at_inhire) as primeira_modificacao,
    MAX(t.updated_at_inhire) as ultima_modificacao
FROM talentos t
CROSS JOIN ultima_sync us
WHERE t.updated_at_inhire > us.data_ref;

\echo ''

-- Query 5: Posições com mudança de status (via timeline)
\echo '6. Posições com mudança de status (timeline)...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(DISTINCT pt.posicao_id) as posicoes_com_mudanca_status,
    COUNT(*) as total_eventos_timeline,
    MIN(pt.changed_at) as primeira_mudanca,
    MAX(pt.changed_at) as ultima_mudanca
FROM position_timeline pt
CROSS JOIN ultima_sync us
WHERE pt.changed_at > us.data_ref;

\echo ''

-- Query 6: Candidaturas com mudança de stage (via timeline)
\echo '7. Candidaturas com mudança de stage (timeline)...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
)
SELECT
    COUNT(DISTINCT ct.candidatura_id) as candidaturas_com_mudanca_stage,
    COUNT(*) as total_eventos_timeline,
    MIN(ct.stage_updated_at) as primeira_mudanca,
    MAX(ct.stage_updated_at) as ultima_mudanca
FROM candidatura_timeline ct
CROSS JOIN ultima_sync us
WHERE ct.stage_updated_at > us.data_ref;

\echo ''

-- Query 7: Análise de Eficiência
\echo '8. Análise de Eficiência Esperada...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
),
totais AS (
    SELECT
        (SELECT COUNT(*) FROM vagas) as total_vagas,
        (SELECT COUNT(*) FROM posicoes) as total_posicoes,
        (SELECT COUNT(*) FROM candidaturas) as total_candidaturas,
        (SELECT COUNT(*) FROM talentos) as total_talentos
),
modificados AS (
    SELECT
        COUNT(DISTINCT v.id) as vagas_mod,
        COUNT(DISTINCT p.id) as posicoes_mod,
        COUNT(DISTINCT c.id) as candidaturas_mod,
        COUNT(DISTINCT t.id) as talentos_mod
    FROM ultima_sync us
    LEFT JOIN vagas v ON v.updated_at_inhire > us.data_ref OR v.created_at > us.data_ref
    LEFT JOIN posicoes p ON p.updated_at_inhire > us.data_ref
    LEFT JOIN candidaturas c ON c.updated_at_inhire > us.data_ref
    LEFT JOIN talentos t ON t.updated_at_inhire > us.data_ref
)
SELECT
    'Vagas' as entidade,
    t.total_vagas as total_registros,
    m.vagas_mod as modificados,
    ROUND((m.vagas_mod::NUMERIC / NULLIF(t.total_vagas, 0)) * 100, 2) as percentual_modificado,
    ROUND((1 - (m.vagas_mod::NUMERIC / NULLIF(t.total_vagas, 0))) * 100, 2) as percentual_skip
FROM totais t, modificados m

UNION ALL

SELECT
    'Posições',
    t.total_posicoes,
    m.posicoes_mod,
    ROUND((m.posicoes_mod::NUMERIC / NULLIF(t.total_posicoes, 0)) * 100, 2),
    ROUND((1 - (m.posicoes_mod::NUMERIC / NULLIF(t.total_posicoes, 0))) * 100, 2)
FROM totais t, modificados m

UNION ALL

SELECT
    'Candidaturas',
    t.total_candidaturas,
    m.candidaturas_mod,
    ROUND((m.candidaturas_mod::NUMERIC / NULLIF(t.total_candidaturas, 0)) * 100, 2),
    ROUND((1 - (m.candidaturas_mod::NUMERIC / NULLIF(t.total_candidaturas, 0))) * 100, 2)
FROM totais t, modificados m

UNION ALL

SELECT
    'Talentos',
    t.total_talentos,
    m.talentos_mod,
    ROUND((m.talentos_mod::NUMERIC / NULLIF(t.total_talentos, 0)) * 100, 2),
    ROUND((1 - (m.talentos_mod::NUMERIC / NULLIF(t.total_talentos, 0))) * 100, 2)
FROM totais t, modificados m;

\echo ''

-- Query 8: Estimativa de chamadas à API
\echo '9. Estimativa de Chamadas à API...'
\echo '--------------------------------------------------------------------------------'

WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
),
vagas_modificadas AS (
    SELECT COUNT(DISTINCT v.id) as total
    FROM vagas v
    CROSS JOIN ultima_sync us
    WHERE v.updated_at_inhire > us.data_ref
       OR v.created_at > us.data_ref
)
SELECT
    'GET /jobs/paginated/lean' as endpoint,
    1 as chamadas,
    'Buscar todas as vagas (detectar novas)' as descricao

UNION ALL

SELECT
    'GET /positions/get-all-from-job',
    vm.total,
    'Buscar posições apenas de vagas modificadas'
FROM vagas_modificadas vm

UNION ALL

SELECT
    'GET /talent/get-applications-from-job',
    vm.total,
    'Buscar candidaturas apenas de vagas modificadas'
FROM vagas_modificadas vm

UNION ALL

SELECT
    'GET /talents/list (filtrado)',
    1,
    'Buscar talentos modificados (filtro API)'

UNION ALL

SELECT
    '*** TOTAL ESTIMADO ***',
    3 + (2 * vm.total),
    'Total de chamadas à API'
FROM vagas_modificadas vm;

\echo ''

-- Query 9: Comparação com estratégia atual
\echo '10. Comparação: Estratégia Atual vs Otimizada...'
\echo '--------------------------------------------------------------------------------'

WITH totais AS (
    SELECT
        (SELECT COUNT(*) FROM vagas) as total_vagas,
        (SELECT COUNT(*) FROM posicoes) as total_posicoes,
        (SELECT COUNT(*) FROM candidaturas) as total_candidaturas
),
ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
),
vagas_modificadas AS (
    SELECT COUNT(DISTINCT v.id) as total
    FROM vagas v
    CROSS JOIN ultima_sync us
    WHERE v.updated_at_inhire > us.data_ref
       OR v.created_at > us.data_ref
)
SELECT
    'Estratégia Atual' as estrategia,
    1 + t.total_vagas + t.total_vagas + 1 as chamadas_api,
    '10-20 min' as tempo_estimado,
    'Busca TUDO e compara datas' as observacao
FROM totais t

UNION ALL

SELECT
    'Estratégia Otimizada',
    3 + (2 * vm.total),
    '2-5 min',
    'Busca apenas vagas modificadas'
FROM vagas_modificadas vm;

\echo ''
\echo '================================================================================'
\echo 'TESTE CONCLUÍDO'
\echo '================================================================================'
\echo ''
\echo 'Se percentual_skip > 90%: EXCELENTE eficiência'
\echo 'Se percentual_skip > 70%: BOA eficiência'
\echo 'Se percentual_skip > 50%: RAZOÁVEL eficiência'
\echo 'Se percentual_skip < 50%: Muitas mudanças, considerar sync completa'
\echo ''
