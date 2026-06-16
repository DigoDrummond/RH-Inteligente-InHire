/*
================================================================================
MIGRATION 051: Adicionar Campos Opcionais Faltantes
================================================================================

Data: 2026-02-13
Descrição:
  Adiciona todos os campos opcionais faltantes das entidades para garantir
  captura completa de dados da API InHire.

Campos adicionados:
  - VAGAS: specialization, metadata (duplicateFrom, duplication)
  - CANDIDATURAS: stage_metadata, phase_metadata (objetos completos)

================================================================================
*/

-- ============================================================================
-- 1. ADICIONAR CAMPOS EM VAGAS
-- ============================================================================

-- Specialization (back-end, devops, front-end, full-stack)
ALTER TABLE vagas
ADD COLUMN IF NOT EXISTS specialization VARCHAR(50);

-- Metadata para armazenar duplicateFrom e duplication objects
ALTER TABLE vagas
ADD COLUMN IF NOT EXISTS metadata JSONB;

COMMENT ON COLUMN vagas.specialization IS 'Especialização da vaga (back-end, devops, front-end, full-stack)';
COMMENT ON COLUMN vagas.metadata IS 'Metadados adicionais: duplicateFrom, duplication, etc.';

-- ============================================================================
-- 2. ADICIONAR CAMPOS EM CANDIDATURAS
-- ============================================================================

-- Stage metadata completo (type, createdAt, updatedAt, userId, userName)
ALTER TABLE candidaturas
ADD COLUMN IF NOT EXISTS stage_metadata JSONB;

-- Phase metadata completo (type, createdAt, updatedAt, userId, userName)
ALTER TABLE candidaturas
ADD COLUMN IF NOT EXISTS phase_metadata JSONB;

COMMENT ON COLUMN candidaturas.stage_metadata IS 'Metadados completos do stage (type, createdAt, updatedAt, userId, userName)';
COMMENT ON COLUMN candidaturas.phase_metadata IS 'Metadados completos da phase (type, createdAt, updatedAt, userId, userName)';

-- ============================================================================
-- 3. CRIAR ÍNDICES
-- ============================================================================

-- Índice GIN para busca em metadata de vagas
CREATE INDEX IF NOT EXISTS idx_vagas_metadata
ON vagas USING GIN (metadata);

-- Índice para specialization
CREATE INDEX IF NOT EXISTS idx_vagas_specialization
ON vagas (specialization)
WHERE specialization IS NOT NULL;

-- Índices GIN para candidaturas
CREATE INDEX IF NOT EXISTS idx_candidaturas_stage_metadata
ON candidaturas USING GIN (stage_metadata);

CREATE INDEX IF NOT EXISTS idx_candidaturas_phase_metadata
ON candidaturas USING GIN (phase_metadata);

-- ============================================================================
-- VALIDAÇÃO
-- ============================================================================

DO $$
DECLARE
    v_vagas_columns INTEGER;
    v_candidaturas_columns INTEGER;
BEGIN
    -- Contar colunas em vagas
    SELECT COUNT(*) INTO v_vagas_columns
    FROM information_schema.columns
    WHERE table_name = 'vagas'
      AND column_name IN ('specialization', 'metadata');

    -- Contar colunas em candidaturas
    SELECT COUNT(*) INTO v_candidaturas_columns
    FROM information_schema.columns
    WHERE table_name = 'candidaturas'
      AND column_name IN ('stage_metadata', 'phase_metadata');

    RAISE NOTICE '===============================================================================';
    RAISE NOTICE 'MIGRATION 051 - CAMPOS OPCIONAIS ADICIONADOS';
    RAISE NOTICE '===============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'VAGAS:';
    RAISE NOTICE '  Novos campos: % / 2', v_vagas_columns;
    IF v_vagas_columns = 2 THEN
        RAISE NOTICE '  - specialization (VARCHAR)';
        RAISE NOTICE '  - metadata (JSONB)';
        RAISE NOTICE '  Status: OK';
    ELSE
        RAISE WARNING '  Status: ERRO - Campos faltando';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE 'CANDIDATURAS:';
    RAISE NOTICE '  Novos campos: % / 2', v_candidaturas_columns;
    IF v_candidaturas_columns = 2 THEN
        RAISE NOTICE '  - stage_metadata (JSONB)';
        RAISE NOTICE '  - phase_metadata (JSONB)';
        RAISE NOTICE '  Status: OK';
    ELSE
        RAISE WARNING '  Status: ERRO - Campos faltando';
    END IF;

    RAISE NOTICE '===============================================================================';

    IF v_vagas_columns <> 2 OR v_candidaturas_columns <> 2 THEN
        RAISE EXCEPTION 'Migration 051 falhou - verifique os erros acima';
    END IF;
END $$;
