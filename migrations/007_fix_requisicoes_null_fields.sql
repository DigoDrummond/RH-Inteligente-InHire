-- ============================================
-- MIGRATION 007: Corrigir campos NULL em requisicoes
-- ============================================
-- Objetivo: Popular campos que estão NULL mas tem dados nos JSONs
-- Data: 2025-12-11
--
-- Campos corrigidos:
-- 1. approved_at - extrai de approvers[].statusUpdatedAt
-- 2. rejected_at - extrai de approvers[].statusUpdatedAt
-- 3. approver_name - extrai de approvers[].name
-- 4. requested_at - copia de created_at_inhire
-- 5. position_amount - conta elementos do array positions
-- ============================================

BEGIN;

-- ============================================
-- 1. POPULAR approved_at
-- ============================================
-- Extrair data de aprovação do JSON approvers para requisições aprovadas

UPDATE requisicoes
SET approved_at = (
    SELECT (elem->>'statusUpdatedAt')::timestamp
    FROM jsonb_array_elements(approvers::jsonb) AS elem
    WHERE elem->>'status' = 'approved'
    LIMIT 1
)
WHERE status = 'approved'
  AND approvers IS NOT NULL
  AND approved_at IS NULL
  AND jsonb_array_length(approvers::jsonb) > 0;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'approved_at: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 2. POPULAR rejected_at
-- ============================================
-- Extrair data de rejeição do JSON approvers para requisições rejeitadas

UPDATE requisicoes
SET rejected_at = (
    SELECT (elem->>'statusUpdatedAt')::timestamp
    FROM jsonb_array_elements(approvers::jsonb) AS elem
    WHERE elem->>'status' = 'rejected'
    LIMIT 1
)
WHERE status = 'rejected'
  AND approvers IS NOT NULL
  AND rejected_at IS NULL
  AND jsonb_array_length(approvers::jsonb) > 0;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'rejected_at: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 3. POPULAR approver_name
-- ============================================
-- Extrair nome do aprovador/rejeitador do JSON approvers

UPDATE requisicoes
SET approver_name = (
    SELECT elem->>'name'
    FROM jsonb_array_elements(approvers::jsonb) AS elem
    WHERE elem->>'status' IN ('approved', 'rejected')
    LIMIT 1
)
WHERE status IN ('approved', 'rejected')
  AND approvers IS NOT NULL
  AND approver_name IS NULL
  AND jsonb_array_length(approvers::jsonb) > 0;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'approver_name: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 4. POPULAR requested_at
-- ============================================
-- Usar created_at_inhire como data da solicitação

UPDATE requisicoes
SET requested_at = created_at_inhire
WHERE requested_at IS NULL
  AND created_at_inhire IS NOT NULL;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'requested_at: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 5. POPULAR position_amount
-- ============================================
-- Contar quantidade de elementos no array positions

UPDATE requisicoes
SET position_amount = (
    CASE
        WHEN positions IS NOT NULL
        THEN jsonb_array_length(positions::jsonb)
        ELSE 0
    END
)
WHERE position_amount IS NULL
  AND positions IS NOT NULL;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'position_amount: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 6. POPULAR status_updated_at (casos faltantes)
-- ============================================
-- Para requisições que não têm status_updated_at, usar do JSON ou updated_at_inhire

UPDATE requisicoes
SET status_updated_at = COALESCE(
    (
        SELECT (elem->>'statusUpdatedAt')::timestamp
        FROM jsonb_array_elements(approvers::jsonb) AS elem
        WHERE elem->>'statusUpdatedAt' IS NOT NULL
        LIMIT 1
    ),
    updated_at_inhire
)
WHERE status_updated_at IS NULL;

-- Log do resultado
DO $$
DECLARE
    rows_updated INTEGER;
BEGIN
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'status_updated_at: % requisicoes atualizadas', rows_updated;
END $$;


-- ============================================
-- 7. ESTATÍSTICAS FINAIS
-- ============================================

DO $$
DECLARE
    total_req INTEGER;
    approved_at_filled INTEGER;
    rejected_at_filled INTEGER;
    approver_name_filled INTEGER;
    requested_at_filled INTEGER;
    position_amount_filled INTEGER;
    status_updated_at_filled INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_req FROM requisicoes;
    SELECT COUNT(*) INTO approved_at_filled FROM requisicoes WHERE approved_at IS NOT NULL;
    SELECT COUNT(*) INTO rejected_at_filled FROM requisicoes WHERE rejected_at IS NOT NULL;
    SELECT COUNT(*) INTO approver_name_filled FROM requisicoes WHERE approver_name IS NOT NULL;
    SELECT COUNT(*) INTO requested_at_filled FROM requisicoes WHERE requested_at IS NOT NULL;
    SELECT COUNT(*) INTO position_amount_filled FROM requisicoes WHERE position_amount IS NOT NULL;
    SELECT COUNT(*) INTO status_updated_at_filled FROM requisicoes WHERE status_updated_at IS NOT NULL;

    RAISE NOTICE '';
    RAISE NOTICE '=== ESTATISTICAS FINAIS ===';
    RAISE NOTICE 'Total de requisicoes: %', total_req;
    RAISE NOTICE 'approved_at preenchido: % (%.1f%%)', approved_at_filled, (approved_at_filled::FLOAT / total_req * 100);
    RAISE NOTICE 'rejected_at preenchido: % (%.1f%%)', rejected_at_filled, (rejected_at_filled::FLOAT / total_req * 100);
    RAISE NOTICE 'approver_name preenchido: % (%.1f%%)', approver_name_filled, (approver_name_filled::FLOAT / total_req * 100);
    RAISE NOTICE 'requested_at preenchido: % (%.1f%%)', requested_at_filled, (requested_at_filled::FLOAT / total_req * 100);
    RAISE NOTICE 'position_amount preenchido: % (%.1f%%)', position_amount_filled, (position_amount_filled::FLOAT / total_req * 100);
    RAISE NOTICE 'status_updated_at preenchido: % (%.1f%%)', status_updated_at_filled, (status_updated_at_filled::FLOAT / total_req * 100);
END $$;

COMMIT;

-- ============================================
-- FIM DA MIGRATION 007
-- ============================================
