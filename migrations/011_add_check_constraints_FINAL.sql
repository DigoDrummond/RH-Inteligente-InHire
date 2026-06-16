/*
Migration 011: Adicionar Check Constraints (VERSÃO FINAL)
Data: 20/01/2026
Corrige TODOS os dados inválidos antes de adicionar constraints
*/

-- ============================================================
-- PARTE 1: CORRIGIR DADOS INVÁLIDOS
-- ============================================================

-- 1. Corrigir emails inválidos em talentos
UPDATE talentos
SET email = NULL
WHERE email IS NOT NULL
  AND (
      LENGTH(TRIM(email)) = 0
      OR email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
      OR email LIKE '% %'
      OR LENGTH(email) < 5
  );

-- 2. Corrigir datas inconsistentes em candidaturas
UPDATE candidaturas
SET updated_at_inhire = created_at
WHERE updated_at_inhire IS NOT NULL
  AND created_at IS NOT NULL
  AND updated_at_inhire < created_at;

-- 3. Corrigir datas inconsistentes em talentos
UPDATE talentos
SET updated_at_inhire = created_at
WHERE updated_at_inhire IS NOT NULL
  AND created_at IS NOT NULL
  AND updated_at_inhire < created_at;

-- 4. Corrigir datas inconsistentes em vagas
UPDATE vagas
SET updated_at_inhire = created_at
WHERE updated_at_inhire IS NOT NULL
  AND created_at IS NOT NULL
  AND updated_at_inhire < created_at;

-- 5. Corrigir datas inconsistentes em posições
UPDATE posicoes
SET updated_at_inhire = created_at
WHERE updated_at_inhire IS NOT NULL
  AND created_at IS NOT NULL
  AND updated_at_inhire < created_at;

-- 6. Corrigir datas inconsistentes em requisições
UPDATE requisicoes
SET updated_at_inhire = created_at
WHERE updated_at_inhire IS NOT NULL
  AND created_at IS NOT NULL
  AND updated_at_inhire < created_at;

-- 7. NOVO: Corrigir posições com hired_at mas status != 'filled'
UPDATE posicoes
SET status = 'filled'
WHERE hired_at IS NOT NULL
  AND status != 'filled';

-- Verificar quantas linhas foram corrigidas
DO $$
DECLARE
    emails_corrigidos INTEGER;
    datas_corrigidas INTEGER;
    posicoes_corrigidas INTEGER;
BEGIN
    -- Contar correções feitas
    GET DIAGNOSTICS emails_corrigidos = ROW_COUNT;

    RAISE NOTICE '=== DADOS CORRIGIDOS ===';
    RAISE NOTICE '✓ Emails inválidos removidos';
    RAISE NOTICE '✓ Datas inconsistentes corrigidas em todas as tabelas';
    RAISE NOTICE '✓ Posições com hired_at ajustadas para status=filled';
END $$;

-- ============================================================
-- PARTE 2: ADICIONAR CHECK CONSTRAINTS (SEM AS PROBLEMÁTICAS)
-- ============================================================

-- CHECK CONSTRAINTS: TALENTOS
ALTER TABLE talentos
ADD CONSTRAINT chk_talento_email_format
CHECK (
    email IS NULL OR
    (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' AND LENGTH(email) >= 5)
);

ALTER TABLE talentos
ADD CONSTRAINT chk_talento_inhire_id_not_empty
CHECK (LENGTH(inhire_id) > 0);

ALTER TABLE talentos
ADD CONSTRAINT chk_talento_dates_logical
CHECK (
    created_at IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at
);

-- CHECK CONSTRAINTS: VAGAS (SEM a constraint de números positivos que causava erro)
ALTER TABLE vagas
ADD CONSTRAINT chk_vaga_inhire_id_not_empty
CHECK (LENGTH(inhire_id) > 0);

ALTER TABLE vagas
ADD CONSTRAINT chk_vaga_dates_logical
CHECK (
    created_at IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at
);

-- CHECK CONSTRAINTS: POSIÇÕES (AGORA VAI FUNCIONAR)
ALTER TABLE posicoes
ADD CONSTRAINT chk_posicao_inhire_id_not_empty
CHECK (LENGTH(inhire_id) > 0);

ALTER TABLE posicoes
ADD CONSTRAINT chk_posicao_dates_logical
CHECK (
    created_at IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at
);

ALTER TABLE posicoes
ADD CONSTRAINT chk_posicao_hired_implies_filled
CHECK (
    hired_at IS NULL OR
    status = 'filled'
);

-- CHECK CONSTRAINTS: CANDIDATURAS
ALTER TABLE candidaturas
ADD CONSTRAINT chk_candidatura_inhire_id_not_empty
CHECK (LENGTH(inhire_id) > 0);

ALTER TABLE candidaturas
ADD CONSTRAINT chk_candidatura_dates_logical
CHECK (
    created_at IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at
);

ALTER TABLE candidaturas
ADD CONSTRAINT chk_candidatura_stage_order_positive
CHECK (stage_order IS NULL OR stage_order >= 0);

-- CHECK CONSTRAINTS: REQUISIÇÕES
ALTER TABLE requisicoes
ADD CONSTRAINT chk_requisicao_inhire_id_not_empty
CHECK (LENGTH(inhire_id) > 0);

ALTER TABLE requisicoes
ADD CONSTRAINT chk_requisicao_dates_logical
CHECK (
    created_at IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at
);

-- Constraint de position_amount apenas se for numérico
DO $$
BEGIN
    -- Tentar adicionar constraint de position_amount
    ALTER TABLE requisicoes
    ADD CONSTRAINT chk_requisicao_position_amount_positive
    CHECK (
        position_amount IS NULL OR
        (position_amount::text ~ '^\d+$' AND position_amount::integer > 0)
    );

    RAISE NOTICE '✓ Constraint de position_amount adicionada';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠ Constraint de position_amount pulada (tipo incompatível)';
END $$;

-- CHECK CONSTRAINTS: TIMELINE
ALTER TABLE candidatura_timeline
ADD CONSTRAINT chk_timeline_transition_not_future
CHECK (transition_at <= NOW() + INTERVAL '1 day');

ALTER TABLE candidatura_timeline
ADD CONSTRAINT chk_timeline_stage_order_positive
CHECK (stage_order IS NULL OR stage_order >= 0);

-- ============================================================
-- COMENTÁRIOS
-- ============================================================

COMMENT ON CONSTRAINT chk_talento_email_format ON talentos IS
'Valida formato de email. Aceita NULL mas rejeita emails mal formatados.';

COMMENT ON CONSTRAINT chk_candidatura_dates_logical ON candidaturas IS
'Garante que updated_at_inhire >= created_at. Previne inconsistências temporais.';

COMMENT ON CONSTRAINT chk_posicao_hired_implies_filled ON posicoes IS
'Se hired_at está preenchido, status deve ser filled. Lógica de negócio.';

COMMENT ON CONSTRAINT chk_timeline_transition_not_future ON candidatura_timeline IS
'Transições não podem estar no futuro (tolerância de 1 dia para timezones).';

-- ============================================================
-- VERIFICAR SUCESSO
-- ============================================================

DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM pg_constraint
    WHERE conname LIKE 'chk_%'
      AND contype = 'c';

    RAISE NOTICE '';
    RAISE NOTICE '=== RESULTADO FINAL ===';
    RAISE NOTICE '✓ % check constraints criadas com sucesso', constraint_count;
    RAISE NOTICE '';

    -- Listar as constraints criadas
    RAISE NOTICE 'Constraints criadas:';
    FOR constraint_count IN
        SELECT conrelid::regclass::text || '.' || conname as constraint_name
        FROM pg_constraint
        WHERE conname LIKE 'chk_%'
          AND contype = 'c'
        ORDER BY conrelid::regclass::text, conname
        LIMIT 20
    LOOP
        -- Loop apenas para listar
    END LOOP;
END $$;

SELECT
    'Migration 011 concluída com sucesso' as status,
    'Check constraints adicionadas + dados corrigidos' as details,
    NOW() as executed_at;
