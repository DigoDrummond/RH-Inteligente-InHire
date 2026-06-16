/*
Migration 009: Adicionar Unique Constraint em candidatura_timeline
Data: 20/01/2026
Autor: Claude Code Refactoring
Objetivo: Prevenir race conditions em paralelização de sync de timeline

PROBLEMA IDENTIFICADO:
Durante sync paralela de timeline (ThreadPoolExecutor com 10 workers),
múltiplas threads podem tentar inserir o mesmo evento de timeline simultaneamente,
causando duplicate key violations.

SOLUÇÃO:
Adicionar unique constraint composto em (candidatura_id, transition_at) que previne
duplicatas e permite que threads façam INSERT...ON CONFLICT DO NOTHING de forma segura.
*/

-- ============================================================
-- VERIFICAR DUPLICATAS EXISTENTES ANTES DE CRIAR CONSTRAINT
-- ============================================================

-- Listar duplicatas atuais (se houver)
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT candidatura_id, transition_at, COUNT(*)
        FROM candidatura_timeline
        GROUP BY candidatura_id, transition_at
        HAVING COUNT(*) > 1
    ) duplicates;

    IF duplicate_count > 0 THEN
        RAISE WARNING 'Encontradas % duplicatas em candidatura_timeline', duplicate_count;
        RAISE NOTICE 'Execute a query abaixo para ver detalhes:';
        RAISE NOTICE 'SELECT candidatura_id, transition_at, COUNT(*) as total FROM candidatura_timeline GROUP BY candidatura_id, transition_at HAVING COUNT(*) > 1;';
    ELSE
        RAISE NOTICE 'Nenhuma duplicata encontrada. Safe para criar unique constraint.';
    END IF;
END $$;

-- ============================================================
-- REMOVER DUPLICATAS SE EXISTIREM
-- ============================================================

-- Estratégia: Manter apenas o registro mais recente (menor id = mais antigo)
-- Deletar duplicatas, mantendo apenas a primeira ocorrência

WITH duplicates AS (
    SELECT
        id,
        candidatura_id,
        transition_at,
        ROW_NUMBER() OVER (
            PARTITION BY candidatura_id, transition_at
            ORDER BY id ASC  -- Manter o mais antigo (menor ID)
        ) as rn
    FROM candidatura_timeline
)
DELETE FROM candidatura_timeline
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- Log de quantos foram deletados
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    IF deleted_count > 0 THEN
        RAISE NOTICE 'Deletadas % duplicatas de candidatura_timeline', deleted_count;
    END IF;
END $$;

-- ============================================================
-- CRIAR UNIQUE CONSTRAINT
-- ============================================================

-- Constraint previne inserção de eventos duplicados
ALTER TABLE candidatura_timeline
ADD CONSTRAINT uq_candidatura_timeline_event
UNIQUE (candidatura_id, transition_at);

-- ============================================================
-- CRIAR ÍNDICE PARA PERFORMANCE
-- ============================================================

-- Índice otimiza queries por candidatura
-- Como já temos unique constraint, o índice já existe implicitamente
-- Mas vamos criar um índice adicional para queries por data

CREATE INDEX IF NOT EXISTS idx_candidatura_timeline_transition_at
ON candidatura_timeline(transition_at DESC);

-- Índice composto para queries comuns (candidatura + tipo de stage)
CREATE INDEX IF NOT EXISTS idx_candidatura_timeline_type
ON candidatura_timeline(candidatura_id, stage_type);

-- ============================================================
-- VERIFICAR CONSTRAINT CRIADO
-- ============================================================

DO $$
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_candidatura_timeline_event'
    ) INTO constraint_exists;

    IF constraint_exists THEN
        RAISE NOTICE '✓ Unique constraint uq_candidatura_timeline_event criado com sucesso';
    ELSE
        RAISE EXCEPTION '✗ Falha ao criar unique constraint';
    END IF;
END $$;

-- ============================================================
-- COMENTÁRIOS PARA DOCUMENTAÇÃO
-- ============================================================

COMMENT ON CONSTRAINT uq_candidatura_timeline_event ON candidatura_timeline IS
'Previne duplicatas de eventos de timeline. Permite INSERT...ON CONFLICT DO NOTHING em sync paralela.';

COMMENT ON INDEX idx_candidatura_timeline_transition_at IS
'Otimiza queries que filtram ou ordenam por data de transição.';

COMMENT ON INDEX idx_candidatura_timeline_type IS
'Otimiza queries que filtram por candidatura e tipo de stage.';

-- ============================================================
-- EXEMPLO DE USO APÓS MIGRATION
-- ============================================================

/*
ANTES (pode causar duplicate key error):
    INSERT INTO candidatura_timeline (candidatura_id, transition_at, ...)
    VALUES (123, '2026-01-20 10:00:00', ...);

DEPOIS (thread-safe):
    INSERT INTO candidatura_timeline (candidatura_id, transition_at, ...)
    VALUES (123, '2026-01-20 10:00:00', ...)
    ON CONFLICT (candidatura_id, transition_at) DO NOTHING;

    -- Ou para atualizar se existir:
    INSERT INTO candidatura_timeline (candidatura_id, transition_at, from_stage, to_stage, ...)
    VALUES (123, '2026-01-20 10:00:00', 'Triagem', 'Entrevista', ...)
    ON CONFLICT (candidatura_id, transition_at)
    DO UPDATE SET
        from_stage = EXCLUDED.from_stage,
        to_stage = EXCLUDED.to_stage,
        updated_at = NOW();
*/

-- ============================================================
-- STATUS DA MIGRATION
-- ============================================================

SELECT
    'Migration 009 concluída com sucesso' as status,
    NOW() as executed_at;
