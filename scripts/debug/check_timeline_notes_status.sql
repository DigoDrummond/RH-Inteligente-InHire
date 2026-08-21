-- Diagnostic Query: Check current state of notes/reason in position_timeline
-- Purpose: Determine if ANY positions have notes populated
-- Date: 2026-03-20

-- ============================================================================
-- 1. Overall Statistics
-- ============================================================================
SELECT
    'OVERALL STATISTICS' as section,
    COUNT(*) as total_timeline_events,
    COUNT(*) FILTER (WHERE reason IS NOT NULL AND reason != '') as events_with_reason,
    COUNT(*) FILTER (WHERE notes IS NOT NULL AND notes != '') as events_with_notes,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reason IS NOT NULL AND reason != '') / COUNT(*), 2) as pct_with_reason,
    ROUND(100.0 * COUNT(*) FILTER (WHERE notes IS NOT NULL AND notes != '') / COUNT(*), 2) as pct_with_notes
FROM position_timeline;

-- ============================================================================
-- 2. Check for cancellation/pause events specifically
-- ============================================================================
SELECT
    'CANCELLATION/PAUSE EVENTS' as section,
    COUNT(*) as total_cancel_pause_events,
    COUNT(*) FILTER (WHERE reason IS NOT NULL AND reason != '') as cancel_with_reason,
    COUNT(*) FILTER (WHERE notes IS NOT NULL AND notes != '') as cancel_with_notes,
    ROUND(100.0 * COUNT(*) FILTER (WHERE notes IS NOT NULL AND notes != '') / COUNT(*), 2) as pct_with_notes
FROM position_timeline
WHERE new_status IN ('canceled', 'paused', 'closed');

-- ============================================================================
-- 3. Sample positions from the provided list
-- ============================================================================
SELECT
    'SAMPLE FROM PROVIDED LIST (First 10)' as section,
    p.id as position_id,
    p.vaga_id,
    v.name as vaga_nome,
    pt.new_status,
    pt.changed_at,
    CASE
        WHEN pt.reason IS NOT NULL AND pt.reason != '' THEN '✅ HAS REASON'
        ELSE '❌ NO REASON'
    END as reason_status,
    CASE
        WHEN pt.notes IS NOT NULL AND pt.notes != '' THEN '✅ HAS NOTES'
        ELSE '❌ NO NOTES'
    END as notes_status,
    LEFT(COALESCE(pt.notes, '(empty)'), 50) as notes_preview
FROM posicoes p
INNER JOIN vagas v ON p.vaga_id = v.id
LEFT JOIN position_timeline pt ON pt.posicao_id = p.id
WHERE p.id IN (386, 311, 85, 935, 240, 254, 516, 1274, 1238, 639)
  AND pt.new_status IN ('canceled', 'paused', 'closed')
ORDER BY p.id, pt.changed_at DESC;

-- ============================================================================
-- 4. Check if ANY positions have notes (find examples)
-- ============================================================================
SELECT
    'EXAMPLES WITH NOTES (if any)' as section,
    p.id as position_id,
    p.vaga_id,
    v.name as vaga_nome,
    pt.new_status,
    pt.changed_at,
    LEFT(pt.notes, 100) as notes_preview,
    LEFT(COALESCE(pt.reason, '(empty)'), 50) as reason_preview
FROM position_timeline pt
INNER JOIN posicoes p ON pt.posicao_id = p.id
INNER JOIN vagas v ON p.vaga_id = v.id
WHERE pt.notes IS NOT NULL AND pt.notes != ''
ORDER BY pt.changed_at DESC
LIMIT 10;

-- ============================================================================
-- 5. Detailed view of Position 386 (first from the list)
-- ============================================================================
SELECT
    'POSITION 386 DETAILED VIEW' as section,
    pt.id,
    pt.inhire_id,
    pt.previous_status,
    pt.new_status,
    pt.changed_at,
    pt.changed_by_name,
    COALESCE(pt.reason, '(empty)') as reason,
    COALESCE(pt.notes, '(empty)') as notes,
    pt.metadata
FROM position_timeline pt
WHERE pt.posicao_id = 386
ORDER BY pt.changed_at;

-- ============================================================================
-- 6. All 85 positions from the list - summary
-- ============================================================================
SELECT
    'ALL 85 POSITIONS SUMMARY' as section,
    p.id as position_id,
    p.vaga_id,
    v.name as vaga_nome,
    p.status as current_status,
    COUNT(pt.id) as timeline_events,
    COUNT(*) FILTER (WHERE pt.new_status IN ('canceled', 'paused', 'closed')) as cancel_events,
    COUNT(*) FILTER (WHERE pt.notes IS NOT NULL AND pt.notes != '') as events_with_notes,
    COUNT(*) FILTER (WHERE pt.reason IS NOT NULL AND pt.reason != '') as events_with_reason
FROM posicoes p
INNER JOIN vagas v ON p.vaga_id = v.id
LEFT JOIN position_timeline pt ON pt.posicao_id = p.id
WHERE p.id IN (
    386, 311, 85, 935, 240, 254, 516, 1274, 1238, 639, 638, 1236, 307, 193, 914, 647,
    629, 768, 110, 378, 353, 389, 19, 643, 514, 1320, 1231, 200, 93, 197, 1257, 1245,
    278, 884, 862, 992, 782, 858, 462, 152, 263, 68, 130, 869, 339, 710, 708, 905, 223,
    88, 831, 1139, 798, 188, 876, 796, 395, 974, 137, 329, 812, 209, 77, 724, 185, 1580,
    417, 896, 1601, 1, 583, 355, 420, 204, 592, 479, 597, 600, 1332, 1337, 1551, 2090,
    2087, 2122, 2141
)
GROUP BY p.id, p.vaga_id, v.name, p.status
ORDER BY
    CASE WHEN events_with_notes > 0 THEN 1 ELSE 0 END DESC,
    p.id;
