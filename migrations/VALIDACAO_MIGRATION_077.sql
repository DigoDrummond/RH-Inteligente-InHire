/*
================================================================================
VALIDAÇÃO DA MIGRATION 077
================================================================================

Execute estas queries no pgAdmin para validar se a migration foi aplicada
corretamente e se as posições pausadas estão usando CURRENT_DATE.

Data: 2026-03-04
================================================================================
*/

-- ============================================================================
-- QUERY 1: Verificar se a view existe e qual é a definição ativa
-- ============================================================================
SELECT
    viewname,
    LEFT(definition, 200) as definicao_inicio
FROM pg_views
WHERE viewname = 'vw_analise_posicoes';

-- RESULTADO ESPERADO: Deve retornar 1 linha com o nome da view


-- ============================================================================
-- QUERY 2: Validar posição 1561 especificamente
-- ============================================================================
SELECT
    id_position,
    cargo,
    status_atual,
    TO_CHAR(data_publicacao, 'YYYY-MM-DD') as data_publicacao,
    TO_CHAR(data_encerramento_ou_atualizacao, 'YYYY-MM-DD') as data_encerramento,
    TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD') as data_esperada,
    CASE
        WHEN data_encerramento_ou_atualizacao = CURRENT_DATE
        THEN '✅ OK'
        ELSE '❌ ERRO - Usando ' || TO_CHAR(data_encerramento_ou_atualizacao, 'YYYY-MM-DD')
    END as validacao,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    num_ciclos_pausa,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE id_position = 1561;

-- RESULTADO ESPERADO:
-- status_atual: paused
-- data_encerramento: 2026-03-04 (deve ser igual a data_esperada)
-- validacao: ✅ OK


-- ============================================================================
-- QUERY 3: Verificar TODAS as posições pausadas
-- ============================================================================
SELECT
    id_position,
    LEFT(cargo, 40) as cargo,
    TO_CHAR(data_publicacao, 'YYYY-MM-DD') as data_pub,
    TO_CHAR(data_encerramento_ou_atualizacao, 'YYYY-MM-DD') as data_enc,
    CASE
        WHEN data_encerramento_ou_atualizacao = CURRENT_DATE
        THEN '✅'
        ELSE '❌'
    END as ok,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento
FROM vw_analise_posicoes
WHERE status_atual = 'paused'
ORDER BY id_position;

-- RESULTADO ESPERADO:
-- Todas as linhas devem ter ok = '✅'
-- Se houver '❌', a migration não foi aplicada corretamente


-- ============================================================================
-- QUERY 4: Contar posições com problema
-- ============================================================================
SELECT
    COUNT(*) as total_pausadas,
    COUNT(*) FILTER (WHERE data_encerramento_ou_atualizacao = CURRENT_DATE) as corretas,
    COUNT(*) FILTER (WHERE data_encerramento_ou_atualizacao <> CURRENT_DATE) as com_problema,
    ROUND(100.0 * COUNT(*) FILTER (WHERE data_encerramento_ou_atualizacao = CURRENT_DATE) / COUNT(*), 2) as percentual_ok
FROM vw_analise_posicoes
WHERE status_atual = 'paused';

-- RESULTADO ESPERADO:
-- total_pausadas: ~10-15
-- corretas: (igual a total_pausadas)
-- com_problema: 0
-- percentual_ok: 100.00


-- ============================================================================
-- QUERY 5: Verificar último status na position_timeline (posição 1561)
-- ============================================================================
SELECT
    pt.posicao_id,
    pt.new_status,
    TO_CHAR(pt.changed_at, 'YYYY-MM-DD HH24:MI:SS') as data_mudanca,
    pt.notes
FROM position_timeline pt
WHERE pt.posicao_id = 1561
ORDER BY pt.changed_at DESC
LIMIT 5;

-- RESULTADO ESPERADO:
-- Primeira linha deve ter new_status = 'paused'


-- ============================================================================
-- QUERY 6: Verificar CTE ultimo_status_posicao (isolado)
-- ============================================================================
WITH ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
)
SELECT
    usp.posicao_id,
    usp.new_status,
    TO_CHAR(usp.data_ultima_mudanca, 'YYYY-MM-DD HH24:MI:SS') as data_mudanca,
    p.status as status_tabela_posicoes,
    COALESCE(usp.new_status, p.status) as status_final
FROM ultimo_status_posicao usp
INNER JOIN posicoes p ON p.id = usp.posicao_id
WHERE usp.posicao_id = 1561;

-- RESULTADO ESPERADO:
-- new_status: paused
-- status_tabela_posicoes: paused
-- status_final: paused


-- ============================================================================
-- QUERY 7: Simular o CASE de data_encerramento_ou_atualizacao (posição 1561)
-- ============================================================================
WITH ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
)
SELECT
    p.id as posicao_id,
    p.status,
    usp.new_status,
    COALESCE(usp.new_status, p.status) as status_coalesce,
    -- Simular o CASE completo
    CASE
        WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
            THEN DATE(p.hired_at)
        WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
             AND usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        WHEN COALESCE(usp.new_status, p.status) = 'open'
            THEN CURRENT_DATE
        WHEN COALESCE(usp.new_status, p.status) = 'paused'
            THEN CURRENT_DATE
        WHEN usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        ELSE NULL
    END AS data_encerramento_calculada,
    CURRENT_DATE as data_esperada
FROM posicoes p
LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.id = 1561;

-- RESULTADO ESPERADO:
-- status_coalesce: paused
-- data_encerramento_calculada: 2026-03-04 (CURRENT_DATE)
-- data_esperada: 2026-03-04


-- ============================================================================
-- QUERY 8: Comparar view com simulação
-- ============================================================================
WITH ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
simulacao AS (
    SELECT
        p.id as posicao_id,
        CASE
            WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                THEN DATE(p.hired_at)
            WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                 AND usp.data_ultima_mudanca IS NOT NULL
                 AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                THEN DATE(usp.data_ultima_mudanca)
            WHEN COALESCE(usp.new_status, p.status) = 'open'
                THEN CURRENT_DATE
            WHEN COALESCE(usp.new_status, p.status) = 'paused'
                THEN CURRENT_DATE
            WHEN usp.data_ultima_mudanca IS NOT NULL
                 AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                THEN DATE(usp.data_ultima_mudanca)
            ELSE NULL
        END AS data_encerramento_simulada
    FROM posicoes p
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
    WHERE p.id = 1561
)
SELECT
    v.id_position,
    v.data_encerramento_ou_atualizacao as data_na_view,
    s.data_encerramento_simulada as data_simulada,
    CASE
        WHEN v.data_encerramento_ou_atualizacao = s.data_encerramento_simulada
        THEN '✅ MATCH'
        ELSE '❌ DIFERENTE'
    END as comparacao
FROM vw_analise_posicoes v
INNER JOIN simulacao s ON s.posicao_id = v.id_position
WHERE v.id_position = 1561;

-- RESULTADO ESPERADO:
-- data_na_view: 2026-03-04
-- data_simulada: 2026-03-04
-- comparacao: ✅ MATCH


-- ============================================================================
-- DIAGNÓSTICO
-- ============================================================================

/*
INTERPRETAÇÃO DOS RESULTADOS:

1. Se QUERY 2 retorna data_encerramento = 2026-03-04:
   ✅ Migration 077 está funcionando corretamente
   ✅ Problema pode ser dados em cache no Google Sheets
   → Ação: Executar export_views_oauth.py

2. Se QUERY 2 retorna data_encerramento = 2026-02-26:
   ❌ Migration 077 NÃO foi aplicada ou tem erro
   ❌ View ainda usa lógica antiga
   → Ação: Reexecutar Migration 077 STEP1 + STEP2

3. Se QUERY 7 retorna data_encerramento_calculada = 2026-03-04
   mas QUERY 2 retorna 2026-02-26:
   ❌ View está compilada com código antigo
   → Ação: Forçar recompilação da view (DROP + CREATE)

4. Se QUERY 3 mostra algumas posições ✅ e outras ❌:
   ❌ Lógica condicional tem problema
   ❌ Alguma condição anterior no CASE está pegando
   → Ação: Investigar ordem dos CASEs e criar Migration 078

5. Se QUERY 4 mostra percentual_ok < 100:
   ❌ Há posições pausadas com problema
   → Ação: Identificar padrão e corrigir
*/


-- ============================================================================
-- AÇÕES CORRETIVAS
-- ============================================================================

/*
CENÁRIO A: View não foi atualizada (reexecutar migration)
---------------------------------------------------------
1. Abrir pgAdmin
2. Executar: migrations/077_fix_pausas_em_andamento_STEP1_DROP.sql
3. Executar: migrations/077_fix_pausas_em_andamento_STEP2_CREATE.sql
4. Validar com QUERY 2


CENÁRIO B: View está correta mas dados estão em cache
------------------------------------------------------
1. Executar: python scripts/export/export_views_oauth.py
2. Atualizar Google Sheets
3. Validar com QUERY 2


CENÁRIO C: Lógica tem problema (criar Migration 078)
-----------------------------------------------------
1. Criar 078_fix_data_encerramento_paused_STEP1_DROP.sql
2. Criar 078_fix_data_encerramento_paused_STEP2_CREATE.sql
3. Modificar ordem dos CASEs:
   - Mover WHEN paused PARA ANTES de WHEN canceled/closed
4. Executar migration 078
5. Validar com QUERY 2
*/
