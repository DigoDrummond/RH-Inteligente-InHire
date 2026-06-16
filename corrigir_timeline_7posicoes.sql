/*
 * Correção de Timeline - 7 Posições com Problemas
 * Data: 2026-03-03
 *
 * Problemas:
 * 1. Eventos duplicados (9 eventos aparecem 2x)
 * 2. Inversão de status (previous_status e new_status trocados)
 */

BEGIN;

-- ========================================
-- ETAPA 1: Remover Eventos Duplicados
-- ========================================

-- Identificar duplicados e manter apenas o primeiro registro (menor ID)
DELETE FROM position_timeline
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            ROW_NUMBER() OVER (
                PARTITION BY posicao_id, changed_at, previous_status, new_status
                ORDER BY id
            ) as rn
        FROM position_timeline
        WHERE posicao_id IN (
            SELECT id FROM posicoes
            WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
        )
    ) t
    WHERE t.rn > 1
);

-- ========================================
-- ETAPA 2: Inverter previous_status ↔ new_status
-- ========================================

-- Inverter os status (trocar previous_status e new_status)
UPDATE position_timeline
SET
    previous_status = new_status,
    new_status = previous_status
WHERE posicao_id IN (
    SELECT id FROM posicoes
    WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
);

-- ========================================
-- ETAPA 3: Validação
-- ========================================

-- Verificar se ainda há duplicados
SELECT
    'DUPLICADOS' as tipo,
    COUNT(*) as total
FROM (
    SELECT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        COUNT(*) as total
    FROM position_timeline
    WHERE posicao_id IN (
        SELECT id FROM posicoes
        WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
    )
    GROUP BY posicao_id, changed_at, previous_status, new_status
    HAVING COUNT(*) > 1
) t;

-- Verificar consistência: status atual deve bater com último evento da timeline
SELECT
    'CONSISTENCIA' as tipo,
    COUNT(*) as inconsistencias
FROM (
    SELECT DISTINCT ON (pt.posicao_id)
        pt.posicao_id,
        p.status as status_bd,
        pt.new_status as status_timeline
    FROM position_timeline pt
    JOIN posicoes p ON pt.posicao_id = p.id
    WHERE p.id IN (1303, 1264, 120, 425, 1308, 759, 1261)
    ORDER BY pt.posicao_id, pt.changed_at DESC
) t
WHERE t.status_bd != t.status_timeline;

-- Mostrar resultado final
SELECT
    p.id as posicao_id,
    v.name as vaga_nome,
    p.status as status_atual,
    pt.ultimo_evento_data,
    pt.transicao
FROM posicoes p
JOIN vagas v ON p.vaga_id = v.id
LEFT JOIN LATERAL (
    SELECT
        changed_at as ultimo_evento_data,
        previous_status || ' -> ' || new_status as transicao
    FROM position_timeline
    WHERE posicao_id = p.id
    ORDER BY changed_at DESC
    LIMIT 1
) pt ON true
WHERE p.id IN (1303, 1264, 120, 425, 1308, 759, 1261)
ORDER BY p.id;

COMMIT;

-- ========================================
-- RESULTADO ESPERADO:
-- ========================================
-- DUPLICADOS: 0
-- CONSISTENCIA: 0 inconsistências
-- Todas as 7 posições com transição "open -> canceled"
