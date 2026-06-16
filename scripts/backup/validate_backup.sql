-- ============================================================================
-- Script de Validação de Backup - Banco de Dados Inhire
-- ============================================================================
-- Autor: Auto-gerado
-- Data: 2026-03-23
-- Descrição: Validações pós-backup/restauração
-- ============================================================================

\echo '============================================================================'
\echo 'VALIDACAO DE BACKUP - BANCO DE DADOS INHIRE'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- VALIDAÇÃO 1: ESTRUTURA DO BANCO
-- ============================================================================

\echo '============================================================================'
\echo '1. VALIDACAO DA ESTRUTURA DO BANCO'
\echo '============================================================================'
\echo ''

\echo '[INFO] Contando objetos do banco...'
\echo ''

SELECT
    'Tabelas' as tipo_objeto,
    COUNT(*) as quantidade
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'

UNION ALL

SELECT
    'Views' as tipo_objeto,
    COUNT(*) as quantidade
FROM information_schema.views
WHERE table_schema = 'public'

UNION ALL

SELECT
    'Funcoes' as tipo_objeto,
    COUNT(*) as quantidade
FROM information_schema.routines
WHERE routine_schema = 'public'

UNION ALL

SELECT
    'Sequences' as tipo_objeto,
    COUNT(*) as quantidade
FROM information_schema.sequences
WHERE sequence_schema = 'public'

ORDER BY tipo_objeto;

\echo ''
\echo '[ESPERADO] Tabelas: ~17, Views: ~6, Funcoes: ~3, Sequences: ~15'
\echo ''

-- ============================================================================
-- VALIDAÇÃO 2: LISTA DE TABELAS
-- ============================================================================

\echo '============================================================================'
\echo '2. VALIDACAO DAS TABELAS PRINCIPAIS'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando existencia das tabelas principais...'
\echo ''

SELECT
    table_name as tabela,
    CASE
        WHEN table_name IN ('vagas', 'posicoes', 'position_timeline', 'candidaturas',
                           'candidatura_timeline', 'talentos', 'talento_arquivos',
                           'talento_tags', 'requisicoes', 'vaga_tags', 'clientes',
                           'custom_fields', 'sync_configuration', 'sync_log', 'feriados')
        THEN 'OK'
        ELSE 'VERIFICAR'
    END as status
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 3: VIEWS CRÍTICAS
-- ============================================================================

\echo '============================================================================'
\echo '3. VALIDACAO DAS VIEWS CRITICAS'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando existencia das views...'
\echo ''

SELECT
    table_name as view_name,
    CASE
        WHEN table_name IN ('vw_analise_posicoes', 'vw_funil_performance',
                           'vw_dados_jade', 'vw_analise_requisicoes',
                           'vw_performance_por_estagio', 'vw_transicoes_estagio')
        THEN 'OK - VIEW CRITICA'
        ELSE 'OK'
    END as status
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 4: FUNÇÕES CRÍTICAS
-- ============================================================================

\echo '============================================================================'
\echo '4. VALIDACAO DAS FUNCOES CRITICAS'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando existencia das funcoes...'
\echo ''

SELECT
    routine_name as funcao,
    data_type as tipo_retorno,
    CASE
        WHEN routine_name IN ('calcular_dias_uteis', 'update_updated_at_column',
                             'update_position_timeline_updated_at')
        THEN 'OK - FUNCAO CRITICA'
        ELSE 'OK'
    END as status
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 5: CONTAGEM DE REGISTROS
-- ============================================================================

\echo '============================================================================'
\echo '5. VALIDACAO DA CONTAGEM DE REGISTROS'
\echo '============================================================================'
\echo ''

\echo '[INFO] Contando registros nas tabelas principais...'
\echo ''

SELECT
    'vagas' as tabela,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE status = 'open') as registros_ativos,
    pg_size_pretty(pg_total_relation_size('vagas')) as tamanho_disco
FROM vagas

UNION ALL

SELECT
    'posicoes',
    COUNT(*),
    COUNT(*) FILTER (WHERE status = 'open'),
    pg_size_pretty(pg_total_relation_size('posicoes'))
FROM posicoes

UNION ALL

SELECT
    'candidaturas',
    COUNT(*),
    COUNT(*) FILTER (WHERE status NOT IN ('rejected', 'declined')),
    pg_size_pretty(pg_total_relation_size('candidaturas'))
FROM candidaturas

UNION ALL

SELECT
    'talentos',
    COUNT(*),
    NULL,
    pg_size_pretty(pg_total_relation_size('talentos'))
FROM talentos

UNION ALL

SELECT
    'position_timeline',
    COUNT(*),
    NULL,
    pg_size_pretty(pg_total_relation_size('position_timeline'))
FROM position_timeline

UNION ALL

SELECT
    'requisicoes',
    COUNT(*),
    COUNT(*) FILTER (WHERE status NOT IN ('approved', 'rejected', 'canceled')),
    pg_size_pretty(pg_total_relation_size('requisicoes'))
FROM requisicoes

ORDER BY tabela;

\echo ''
\echo '[REFERENCIA] Valores esperados (baseado em CLAUDE.md):'
\echo '  - Candidaturas: ~85.000'
\echo '  - Talentos: ~61.000-86.000'
\echo '  - Posicoes: ~1.400'
\echo ''

-- ============================================================================
-- VALIDAÇÃO 6: INTEGRIDADE REFERENCIAL
-- ============================================================================

\echo '============================================================================'
\echo '6. VALIDACAO DA INTEGRIDADE REFERENCIAL'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando constraints de chave estrangeira...'
\echo ''

SELECT
    tc.table_name as tabela,
    tc.constraint_name as constraint,
    kcu.column_name as coluna,
    ccu.table_name as tabela_referenciada,
    ccu.column_name as coluna_referenciada
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 7: ÍNDICES
-- ============================================================================

\echo '============================================================================'
\echo '7. VALIDACAO DOS INDICES'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando indices criados...'
\echo ''

SELECT
    schemaname as schema,
    tablename as tabela,
    indexname as indice,
    indexdef as definicao
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 8: TESTE DE FUNÇÕES
-- ============================================================================

\echo '============================================================================'
\echo '8. VALIDACAO FUNCIONAL - TESTE DE FUNCOES'
\echo '============================================================================'
\echo ''

\echo '[INFO] Testando funcao calcular_dias_uteis()...'
\echo ''

-- Teste 1: Janeiro de 2024 (deve retornar ~23 dias úteis)
SELECT
    'Teste 1: Janeiro 2024' as teste,
    calcular_dias_uteis('2024-01-01'::DATE, '2024-01-31'::DATE) as dias_uteis,
    'Esperado: ~23' as referencia;

-- Teste 2: Semana completa
SELECT
    'Teste 2: Semana Completa' as teste,
    calcular_dias_uteis('2025-01-13'::DATE, '2025-01-17'::DATE) as dias_uteis,
    'Esperado: 5' as referencia;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 9: TESTE DE VIEWS
-- ============================================================================

\echo '============================================================================'
\echo '9. VALIDACAO FUNCIONAL - TESTE DE VIEWS'
\echo '============================================================================'
\echo ''

\echo '[INFO] Testando view vw_analise_posicoes...'
\echo ''

-- Verificar se a view retorna dados
SELECT
    'vw_analise_posicoes' as view_testada,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE motivo_cancelamento_paralisacao IS NOT NULL) as com_motivo_cancelamento,
    COUNT(*) FILTER (WHERE sla_geral IS NOT NULL) as com_sla_calculado
FROM vw_analise_posicoes;

\echo ''

\echo '[INFO] Testando view vw_funil_performance...'
\echo ''

-- Verificar se a view de funil retorna dados
SELECT
    'vw_funil_performance' as view_testada,
    COUNT(*) as total_registros
FROM vw_funil_performance;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 10: DADOS RECENTES
-- ============================================================================

\echo '============================================================================'
\echo '10. VALIDACAO DE DADOS RECENTES'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando dados mais recentes...'
\echo ''

SELECT
    'vagas' as tabela,
    MAX(created_at) as ultimo_registro_criado,
    MAX(updated_at_inhire) as ultima_atualizacao_api
FROM vagas

UNION ALL

SELECT
    'posicoes',
    MAX(created_at),
    MAX(updated_at_inhire)
FROM posicoes

UNION ALL

SELECT
    'candidaturas',
    MAX(created_at),
    MAX(updated_at_inhire)
FROM candidaturas

UNION ALL

SELECT
    'talentos',
    MAX(created_at),
    MAX(updated_at_inhire)
FROM talentos

ORDER BY tabela;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 11: ÚLTIMAS SINCRONIZAÇÕES
-- ============================================================================

\echo '============================================================================'
\echo '11. VALIDACAO DAS ULTIMAS SINCRONIZACOES'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando log de sincronizacao...'
\echo ''

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
    records_failed as falhas
FROM sync_log
ORDER BY start_time DESC
LIMIT 10;

\echo ''

-- ============================================================================
-- VALIDAÇÃO 12: TAMANHO DO BANCO
-- ============================================================================

\echo '============================================================================'
\echo '12. VALIDACAO DO TAMANHO DO BANCO'
\echo '============================================================================'
\echo ''

\echo '[INFO] Verificando tamanho do banco de dados...'
\echo ''

SELECT
    pg_database.datname as database,
    pg_size_pretty(pg_database_size(pg_database.datname)) as tamanho_total
FROM pg_database
WHERE datname = 'inhire';

\echo ''

-- Tamanho por tabela (top 10)
\echo '[INFO] Top 10 maiores tabelas...'
\echo ''

SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho_total,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as tamanho_dados,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as tamanho_indices
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

\echo ''

-- ============================================================================
-- RESUMO FINAL
-- ============================================================================

\echo '============================================================================'
\echo 'RESUMO DA VALIDACAO'
\echo '============================================================================'
\echo ''
\echo '[OK] Validacoes concluidas!'
\echo ''
\echo 'Proximos passos:'
\echo '  1. Revisar os resultados acima'
\echo '  2. Verificar se os totais de registros estao corretos'
\echo '  3. Confirmar que as funcoes criticas funcionam'
\echo '  4. Testar a aplicacao com os dados restaurados'
\echo ''
\echo '============================================================================'
\echo ''
