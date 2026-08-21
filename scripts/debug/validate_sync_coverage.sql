-- ===============================================================================
-- Script de Validação de Cobertura da Sincronização
-- ===============================================================================
--
-- Descrição: Identifica registros que podem estar desatualizados devido às
--            limitações da sincronização incremental
--
-- Data: 2026-03-02
-- Versão: 1.0
--
-- USO:
--   psql -U postgres -d inhire -f scripts/debug/validate_sync_coverage.sql
--
-- ===============================================================================

\echo ''
\echo '================================================================================'
\echo ' VALIDAÇÃO DE COBERTURA DA SINCRONIZAÇÃO INCREMENTAL'
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 1. POSITION TIMELINE - Verificar posições com timeline desatualizada
-- ===============================================================================

\echo '1. POSITION TIMELINE - Posições fechadas/canceladas com timeline antiga'
\echo '--------------------------------------------------------------------------------'

SELECT
    'POSITION_TIMELINE' as tabela,
    p.id as posicao_bd_id,
    p.inhire_id,
    p.job_title as cargo,
    p.status,
    p.updated_at_inhire as ultima_atualizacao_posicao,
    COUNT(pt.id) as total_eventos_timeline,
    MAX(pt.changed_at) as ultima_timeline,
    (NOW() - MAX(pt.changed_at)) as dias_desde_ultimo_evento
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
WHERE p.status IN ('closed', 'canceled')
GROUP BY p.id, p.inhire_id, p.job_title, p.status, p.updated_at_inhire
HAVING MAX(pt.changed_at) < NOW() - INTERVAL '30 days'
   OR MAX(pt.changed_at) IS NULL
ORDER BY dias_desde_ultimo_evento DESC NULLS FIRST
LIMIT 20;

\echo ''
\echo 'Total de posições fechadas/canceladas com timeline > 30 dias:'

SELECT
    COUNT(*) as total_posicoes_problema
FROM (
    SELECT p.id
    FROM posicoes p
    LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
    WHERE p.status IN ('closed', 'canceled')
    GROUP BY p.id
    HAVING MAX(pt.changed_at) < NOW() - INTERVAL '30 days'
       OR MAX(pt.changed_at) IS NULL
) sub;

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 2. VAGAS - Verificar vagas fechadas/canceladas
-- ===============================================================================

\echo '2. VAGAS - Vagas fechadas/canceladas antigas'
\echo '--------------------------------------------------------------------------------'

SELECT
    'VAGAS' as tabela,
    id as vaga_bd_id,
    inhire_id,
    name as nome_vaga,
    status,
    updated_at_inhire as ultima_atualizacao,
    (NOW() - updated_at_inhire) as dias_desde_atualizacao
FROM vagas
WHERE status IN ('CLOSED', 'CANCELED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days'
ORDER BY dias_desde_atualizacao DESC
LIMIT 20;

\echo ''
\echo 'Total de vagas fechadas/canceladas > 30 dias:'

SELECT COUNT(*) as total_vagas_problema
FROM vagas
WHERE status IN ('CLOSED', 'CANCELED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 3. POSIÇÕES - Verificar posições fechadas/canceladas
-- ===============================================================================

\echo '3. POSIÇÕES - Posições fechadas/canceladas antigas'
\echo '--------------------------------------------------------------------------------'

SELECT
    'POSICOES' as tabela,
    id as posicao_bd_id,
    inhire_id,
    job_title as cargo,
    status,
    updated_at_inhire as ultima_atualizacao,
    (NOW() - updated_at_inhire) as dias_desde_atualizacao
FROM posicoes
WHERE status IN ('closed', 'canceled')
  AND updated_at_inhire < NOW() - INTERVAL '30 days'
ORDER BY dias_desde_atualizacao DESC
LIMIT 20;

\echo ''
\echo 'Total de posições fechadas/canceladas > 30 dias:'

SELECT COUNT(*) as total_posicoes_problema
FROM posicoes
WHERE status IN ('closed', 'canceled')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 4. CANDIDATURAS - Verificar candidaturas rejeitadas/declinadas
-- ===============================================================================

\echo '4. CANDIDATURAS - Candidaturas rejeitadas/declinadas antigas'
\echo '--------------------------------------------------------------------------------'

SELECT
    'CANDIDATURAS' as tabela,
    id as candidatura_bd_id,
    inhire_id,
    talent_name as nome_talento,
    status,
    updated_at_inhire as ultima_atualizacao,
    (NOW() - updated_at_inhire) as dias_desde_atualizacao
FROM candidaturas
WHERE status IN ('REJECTED', 'DECLINED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days'
ORDER BY dias_desde_atualizacao DESC
LIMIT 20;

\echo ''
\echo 'Total de candidaturas rejeitadas/declinadas > 30 dias:'

SELECT COUNT(*) as total_candidaturas_problema
FROM candidaturas
WHERE status IN ('REJECTED', 'DECLINED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 5. REQUISIÇÕES - Verificar requisições aprovadas/canceladas/rejeitadas
-- ===============================================================================

\echo '5. REQUISIÇÕES - Requisições finalizadas antigas'
\echo '--------------------------------------------------------------------------------'

SELECT
    'REQUISICOES' as tabela,
    id as requisicao_bd_id,
    inhire_id,
    name as nome_requisicao,
    status,
    updated_at_inhire as ultima_atualizacao,
    (NOW() - updated_at_inhire) as dias_desde_atualizacao
FROM requisicoes
WHERE status IN ('approved', 'canceled', 'rejected')
  AND updated_at_inhire < NOW() - INTERVAL '30 days'
ORDER BY dias_desde_atualizacao DESC
LIMIT 20;

\echo ''
\echo 'Total de requisições finalizadas > 30 dias:'

SELECT COUNT(*) as total_requisicoes_problema
FROM requisicoes
WHERE status IN ('approved', 'canceled', 'rejected')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 6. RESUMO GERAL - Dashboard de cobertura
-- ===============================================================================

\echo '6. RESUMO GERAL - Dashboard de Cobertura'
\echo '--------------------------------------------------------------------------------'

SELECT
    'POSITION_TIMELINE' as entidade,
    (SELECT COUNT(*) FROM position_timeline) as total_registros,
    (
        SELECT COUNT(DISTINCT p.id)
        FROM posicoes p
        LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
        WHERE p.status IN ('closed', 'canceled')
        GROUP BY p.id
        HAVING MAX(pt.changed_at) < NOW() - INTERVAL '30 days'
           OR MAX(pt.changed_at) IS NULL
    ) as registros_problema,
    ROUND(
        (
            (SELECT COUNT(DISTINCT p.id)
            FROM posicoes p
            LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
            WHERE p.status IN ('closed', 'canceled')
            GROUP BY p.id
            HAVING MAX(pt.changed_at) < NOW() - INTERVAL '30 days'
               OR MAX(pt.changed_at) IS NULL
            )::numeric /
            NULLIF((SELECT COUNT(*) FROM position_timeline), 0) * 100
        ), 2
    ) as percentual_problema

UNION ALL

SELECT
    'VAGAS',
    (SELECT COUNT(*) FROM vagas),
    (SELECT COUNT(*) FROM vagas WHERE status IN ('CLOSED', 'CANCELED') AND updated_at_inhire < NOW() - INTERVAL '30 days'),
    ROUND(
        (SELECT COUNT(*) FROM vagas WHERE status IN ('CLOSED', 'CANCELED') AND updated_at_inhire < NOW() - INTERVAL '30 days')::numeric /
        NULLIF((SELECT COUNT(*) FROM vagas), 0) * 100,
        2
    )

UNION ALL

SELECT
    'POSICOES',
    (SELECT COUNT(*) FROM posicoes),
    (SELECT COUNT(*) FROM posicoes WHERE status IN ('closed', 'canceled') AND updated_at_inhire < NOW() - INTERVAL '30 days'),
    ROUND(
        (SELECT COUNT(*) FROM posicoes WHERE status IN ('closed', 'canceled') AND updated_at_inhire < NOW() - INTERVAL '30 days')::numeric /
        NULLIF((SELECT COUNT(*) FROM posicoes), 0) * 100,
        2
    )

UNION ALL

SELECT
    'CANDIDATURAS',
    (SELECT COUNT(*) FROM candidaturas),
    (SELECT COUNT(*) FROM candidaturas WHERE status IN ('REJECTED', 'DECLINED') AND updated_at_inhire < NOW() - INTERVAL '30 days'),
    ROUND(
        (SELECT COUNT(*) FROM candidaturas WHERE status IN ('REJECTED', 'DECLINED') AND updated_at_inhire < NOW() - INTERVAL '30 days')::numeric /
        NULLIF((SELECT COUNT(*) FROM candidaturas), 0) * 100,
        2
    )

UNION ALL

SELECT
    'REQUISICOES',
    (SELECT COUNT(*) FROM requisicoes),
    (SELECT COUNT(*) FROM requisicoes WHERE status IN ('approved', 'canceled', 'rejected') AND updated_at_inhire < NOW() - INTERVAL '30 days'),
    ROUND(
        (SELECT COUNT(*) FROM requisicoes WHERE status IN ('approved', 'canceled', 'rejected') AND updated_at_inhire < NOW() - INTERVAL '30 days')::numeric /
        NULLIF((SELECT COUNT(*) FROM requisicoes), 0) * 100,
        2
    );

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 7. ÚLTIMAS SINCRONIZAÇÕES - Log de sync
-- ===============================================================================

\echo '7. ÚLTIMAS SINCRONIZAÇÕES - Log de Sync'
\echo '--------------------------------------------------------------------------------'

SELECT
    sync_type,
    sync_entity,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duracao_minutos,
    records_processed as processados,
    records_created as criados,
    records_updated as atualizados,
    records_skipped as pulados,
    ROUND((records_skipped::numeric / NULLIF(records_processed, 0) * 100), 2) as skip_rate_pct
FROM sync_log
WHERE sync_type IN ('FULL', 'INCREMENTAL')
ORDER BY start_time DESC
LIMIT 15;

\echo ''
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- 8. POSIÇÃO ESPECÍFICA - Validar Position 1370
-- ===============================================================================

\echo '8. VALIDAÇÃO ESPECÍFICA - Position 1370 (Desenvolvedor .NET Senior)'
\echo '--------------------------------------------------------------------------------'

SELECT
    p.id as posicao_bd_id,
    p.inhire_id,
    p.job_title as cargo,
    p.status,
    p.updated_at_inhire as ultima_atualizacao_posicao,
    COUNT(pt.id) as total_eventos_timeline,
    MIN(pt.changed_at) as primeiro_evento,
    MAX(pt.changed_at) as ultimo_evento,
    (NOW() - MAX(pt.changed_at)) as tempo_desde_ultimo_evento
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
WHERE p.inhire_id = '1370'
GROUP BY p.id, p.inhire_id, p.job_title, p.status, p.updated_at_inhire;

\echo ''
\echo 'Últimos 10 eventos de timeline da position 1370:'

SELECT
    id,
    changed_at AT TIME ZONE 'America/Sao_Paulo' as data_evento,
    previous_status as status_anterior,
    new_status as novo_status,
    notes as observacoes
FROM position_timeline
WHERE posicao_id = (SELECT id FROM posicoes WHERE inhire_id = '1370')
ORDER BY changed_at DESC
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo ' FIM DA VALIDAÇÃO'
\echo '================================================================================'
\echo ''

-- ===============================================================================
-- INTERPRETAÇÃO DOS RESULTADOS
-- ===============================================================================
--
-- COBERTURA ESPERADA (sync incremental com otimização):
--   - Position Timeline: 60-80% (20-40% em status final)
--   - Vagas: 85-90% (10-15% em status final)
--   - Posições: 85-90% (10-15% em status final)
--   - Candidaturas: 90-95% (5-10% em status final)
--   - Requisições: 90-95% (5-10% em status final)
--
-- COBERTURA IDEAL (sync FULL ou incremental sem otimização):
--   - Todas as tabelas: 100%
--
-- AÇÃO RECOMENDADA:
--   - Se percentual_problema > 20%: Executar sync FULL imediatamente
--   - Se percentual_problema > 10%: Considerar remover otimização de status finais
--   - Se percentual_problema < 5%: Monitorar, situação aceitável
--
-- ===============================================================================
