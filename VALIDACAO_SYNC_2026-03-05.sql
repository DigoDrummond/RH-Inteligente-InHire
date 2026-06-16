/*
================================================================================
VALIDAÇÃO DE SINCRONIZAÇÃO INCREMENTAL - 05/03/2026
================================================================================

Sincronização executada: 13:38:41 → 14:11:41 (33 minutos)
Credenciais: localhost:5432/inhire (postgres/postgres)

ESTRUTURA CORRIGIDA:
- position_timeline: NÃO tem "updated_at_inhire", "status"
- position_timeline: TEM "new_status", "previous_status", "changed_at"
- sync_entity: enum não aceita "position_timeline" (verificar valores válidos)

================================================================================
*/

-- ============================================================================
-- VALIDAÇÃO 1: CONTAGEM RÁPIDA DE REGISTROS
-- ============================================================================

SELECT 'vagas' as tabela, COUNT(*) as registros FROM vagas
UNION ALL SELECT 'posicoes', COUNT(*) FROM posicoes
UNION ALL SELECT 'candidaturas', COUNT(*) FROM candidaturas
UNION ALL SELECT 'talentos', COUNT(*) FROM talentos
UNION ALL SELECT 'position_timeline', COUNT(*) FROM position_timeline
UNION ALL SELECT 'requisicoes', COUNT(*) FROM requisicoes
ORDER BY tabela;

/*
✅ RESULTADO VALIDADO:
candidaturas        | 85,664
posicoes            | 1,439
position_timeline   | 3,654  ← ⚠️ MUITO BAIXO (esperava 15k+)
requisicoes         | 892
talentos            | 59,884
vagas               | 1,212
*/


-- ============================================================================
-- VALIDAÇÃO 2: ÚLTIMA ATUALIZAÇÃO (TIMESTAMP CHECK)
-- ============================================================================

SELECT
    'vagas' as tabela,
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo' as ultima_atualizacao_brt,
    CASE
        WHEN MAX(updated_at) >= '2026-03-05 14:00:00'::timestamp
        THEN '✅ Atualizado Hoje'
        ELSE '❌ Desatualizado'
    END as status
FROM vagas

UNION ALL

SELECT 'posicoes',
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo',
    CASE WHEN MAX(updated_at) >= '2026-03-05 14:00:00'::timestamp THEN '✅ Atualizado Hoje' ELSE '❌ Desatualizado' END
FROM posicoes

UNION ALL

SELECT 'candidaturas',
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo',
    CASE WHEN MAX(updated_at) >= '2026-03-05 14:00:00'::timestamp THEN '✅ Atualizado Hoje' ELSE '❌ Desatualizado' END
FROM candidaturas

UNION ALL

SELECT 'talentos',
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo',
    CASE WHEN MAX(updated_at) >= '2026-03-05 14:00:00'::timestamp THEN '✅ Atualizado Hoje' ELSE '❌ Desatualizado' END
FROM talentos

UNION ALL

SELECT 'position_timeline',
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo',
    CASE WHEN MAX(updated_at) >= '2026-03-05 14:00:00'::timestamp THEN '✅ Atualizado Hoje' ELSE '❌ Desatualizado' END
FROM position_timeline

ORDER BY tabela;

/*
✅ RESULTADO VALIDADO:
candidaturas     | 2026-03-05 14:09:42 | ✅ Atualizado Hoje
posicoes         | 2026-03-05 13:49:33 | ❌ Desatualizado
position_timeline| 2026-03-03 12:08:49 | ❌ Desatualizado  ← 🔴 2 DIAS ATRÁS!
talentos         | 2026-03-05 14:11:06 | ✅ Atualizado Hoje
vagas            | 2026-03-05 13:38:51 | ❌ Desatualizado
*/


-- ============================================================================
-- VALIDAÇÃO 3: LOG DE SINCRONIZAÇÃO
-- ============================================================================

SELECT
    sync_entity as entidade,
    records_created as criados,
    records_updated as atualizados,
    records_skipped as pulados,
    records_failed as falhas,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim
FROM sync_log
WHERE sync_type = 'INCREMENTAL'
    AND start_time >= '2026-03-05 13:00:00'::timestamp
ORDER BY start_time DESC
LIMIT 15;

/*
✅ RESULTADO VALIDADO:
ALL | 316 | 71 | 86065 | 4 | 2026-03-05 13:38:39 | 2026-03-05 14:11:40
*/


-- ============================================================================
-- VALIDAÇÃO 4: IDENTIFICAR FALHAS (CORRIGIDA)
-- ============================================================================

SELECT
    sync_entity as entidade,
    records_failed as num_falhas,
    error_messages as erros,  -- ← CORRIGIDO: era "error_message"
    start_time AT TIME ZONE 'America/Sao_Paulo' as quando
FROM sync_log
WHERE sync_type = 'INCREMENTAL'
    AND start_time >= '2026-03-05 13:00:00'::timestamp
    AND records_failed > 0
ORDER BY records_failed DESC;

/*
✅ RESULTADO VALIDADO:
ALL | 4 | NULL | 2026-03-05 13:38:39
*/


-- ============================================================================
-- VALIDAÇÃO 5: VERIFICAR VALORES VÁLIDOS DE sync_entity
-- ============================================================================

-- Descobrir quais valores são aceitos pelo enum sync_entity
SELECT DISTINCT sync_entity
FROM sync_log
ORDER BY sync_entity;

/*
EXECUTAR ESTA QUERY PARA DESCOBRIR OS VALORES VÁLIDOS DO ENUM!
Precisamos saber se é "position_timeline", "POSITION_TIMELINE", ou outro nome.
*/


-- ============================================================================
-- VALIDAÇÃO 6: STRUCTURE CHECK - position_timeline
-- ============================================================================

-- Listar colunas da tabela position_timeline
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'position_timeline'
ORDER BY ordinal_position;

/*
COLUNAS CONFIRMADAS (migration 013):
- id, inhire_id, posicao_id, vaga_id
- previous_status, new_status  ← NÃO É "status"!
- changed_at  ← Data do evento
- changed_by, changed_by_name, reason, notes
- metadata
- created_at, updated_at  ← NÃO TEM "updated_at_inhire"!
*/


-- ============================================================================
-- VALIDAÇÃO 7: VERIFICAR POSITION_TIMELINE POR POSIÇÃO
-- ============================================================================

-- Contar eventos de timeline por posição (top 20)
SELECT
    posicao_id,
    COUNT(*) as eventos,
    MIN(changed_at) AT TIME ZONE 'America/Sao_Paulo' as primeiro_evento,
    MAX(changed_at) AT TIME ZONE 'America/Sao_Paulo' as ultimo_evento,
    MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo' as ultima_atualizacao_bd
FROM position_timeline
GROUP BY posicao_id
ORDER BY eventos DESC
LIMIT 20;


-- ============================================================================
-- VALIDAÇÃO 8: POSIÇÃO 1561 - TIMELINE (CORRIGIDA)
-- ============================================================================

-- Verificar timeline da posição 1561 (monitorada anteriormente)
SELECT
    pt.id,
    pt.changed_at AT TIME ZONE 'America/Sao_Paulo' as data_evento,
    pt.previous_status as status_anterior,
    pt.new_status as status_novo,  -- ← CORRIGIDO: era "status"
    pt.updated_at AT TIME ZONE 'America/Sao_Paulo' as updated_bd,
    pt.notes
FROM position_timeline pt
WHERE pt.posicao_id = 1561
ORDER BY pt.changed_at DESC
LIMIT 10;


-- ============================================================================
-- VALIDAÇÃO 9: VERIFICAR SE POSITION_TIMELINE FOI SINCRONIZADO
-- ============================================================================

-- Buscar sync_log para descobrir nome correto da entidade position_timeline
SELECT
    sync_entity,
    records_processed,
    records_created,
    records_updated,
    records_skipped,
    records_failed,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio
FROM sync_log
WHERE sync_type = 'INCREMENTAL'
    AND start_time >= '2026-03-05 13:00:00'::timestamp
    -- Buscar qualquer entidade que contenha "timeline" no nome
    AND LOWER(sync_entity::text) LIKE '%timeline%'
ORDER BY start_time DESC;

/*
SE RETORNAR VAZIO: position_timeline NÃO foi sincronizado!
SE RETORNAR ALGO: verificar estatísticas
*/


-- ============================================================================
-- VALIDAÇÃO 10: ANÁLISE DE EVENTOS POR DATA
-- ============================================================================

-- Verificar quando foram criados os eventos de timeline
SELECT
    DATE(changed_at) as data_evento,
    COUNT(*) as eventos,
    COUNT(DISTINCT posicao_id) as posicoes_afetadas,
    STRING_AGG(DISTINCT new_status, ', ') as status_usados
FROM position_timeline
GROUP BY DATE(changed_at)
ORDER BY data_evento DESC
LIMIT 30;

/*
OBJETIVO: Verificar se há eventos recentes (05/03/2026)
Se não houver eventos de 05/03: timeline NÃO foi sincronizado
*/


-- ============================================================================
-- VALIDAÇÃO 11: COMPARAR POSIÇÕES COM TIMELINE
-- ============================================================================

-- Identificar posições sem timeline
SELECT
    p.id as posicao_id,
    p.inhire_id,
    p.status,
    p.titulo,
    COUNT(pt.id) as eventos_timeline
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
GROUP BY p.id, p.inhire_id, p.status, p.titulo
HAVING COUNT(pt.id) = 0
ORDER BY p.id DESC
LIMIT 20;

/*
ESPERADO: Posições criadas recentemente (após 03/03) não terão timeline
Se houver MUITAS posições sem timeline: problema de sincronização
*/


-- ============================================================================
-- VALIDAÇÃO 12: VIEW ANALÍTICA
-- ============================================================================

SELECT COUNT(*) as total_posicoes FROM vw_analise_posicoes;

/*
ESPERADO: ~1.383-1.439 registros
*/


-- ============================================================================
-- VALIDAÇÃO 13: RESUMO EXECUTIVO (QUERY ÚNICA)
-- ============================================================================

SELECT
    (SELECT COUNT(*) FROM vagas) as total_vagas,
    (SELECT COUNT(*) FROM posicoes) as total_posicoes,
    (SELECT COUNT(*) FROM candidaturas) as total_candidaturas,
    (SELECT COUNT(*) FROM position_timeline) as total_timeline,
    (SELECT MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo' FROM vagas) as vagas_ultima_atualizacao,
    (SELECT MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo' FROM posicoes) as posicoes_ultima_atualizacao,
    (SELECT MAX(updated_at) AT TIME ZONE 'America/Sao_Paulo' FROM position_timeline) as timeline_ultima_atualizacao,
    (SELECT SUM(records_created) FROM sync_log WHERE sync_type = 'INCREMENTAL' AND start_time >= '2026-03-05 13:00:00') as sync_criados,
    (SELECT SUM(records_updated) FROM sync_log WHERE sync_type = 'INCREMENTAL' AND start_time >= '2026-03-05 13:00:00') as sync_atualizados,
    (SELECT SUM(records_failed) FROM sync_log WHERE sync_type = 'INCREMENTAL' AND start_time >= '2026-03-05 13:00:00') as sync_falhas,
    (SELECT COUNT(*) FROM vw_analise_posicoes) as view_analise_posicoes_count;


-- ============================================================================
-- DIAGNÓSTICO E CONCLUSÕES
-- ============================================================================

/*
🔴 PROBLEMAS IDENTIFICADOS:

1. position_timeline NÃO FOI SINCRONIZADO
   - Última atualização: 03/03/2026 (2 dias atrás)
   - Apenas 3.654 eventos (esperava 15k+)
   - Impacto: SLAs incorretos, pausas não contabilizadas

2. Tabelas pararam de atualizar durante a sync
   - vagas: parou às 13:38 (início da sync)
   - posicoes: parou às 13:49 (meio da sync)
   - position_timeline: nem foi tocado

3. Sync reportou sucesso mas dados não atualizaram
   - Sync_log mostra: 316 criados, 71 atualizados
   - Mas timestamps das tabelas não refletem isso

PRÓXIMAS AÇÕES:

1. Execute VALIDAÇÃO 5 para descobrir valores válidos de sync_entity
2. Execute VALIDAÇÃO 9 para verificar se position_timeline foi sincronizado
3. Execute VALIDAÇÃO 10 para ver distribuição de eventos por data
4. Execute VALIDAÇÃO 11 para identificar posições sem timeline

HIPÓTESES:

A) position_timeline não está configurado no sync incremental
   → Verificar services/sync_service.py

B) Nome da entidade está errado no código
   → "position_timeline" vs "POSITION_TIMELINE" vs outro

C) Sync foi interrompido antes de chegar em position_timeline
   → Mas sync_log mostra sucesso...

D) Há um bug na sincronização de position_timeline
   → Precisa investigar código
*/

================================================================================
-- FIM DO ARQUIVO DE VALIDAÇÃO
================================================================================
