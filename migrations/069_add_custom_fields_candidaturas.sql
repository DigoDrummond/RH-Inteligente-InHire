-- ===============================================================
-- Migration 069: Adicionar custom_fields em Candidaturas
-- ===============================================================
-- Adiciona coluna JSON para armazenar custom fields responses
-- das candidaturas (JOB_TALENTS entity)
--
-- Data: 2026-07-21
-- ===============================================================

-- Adicionar coluna custom_fields
ALTER TABLE candidaturas
ADD COLUMN IF NOT EXISTS custom_fields JSON;

-- Comentário
COMMENT ON COLUMN candidaturas.custom_fields IS 'Custom fields responses (JOB_TALENTS) - formato: {"field_id": ["valor1", "valor2"]}';

-- Criar índice GIN para busca eficiente em JSON
CREATE INDEX IF NOT EXISTS idx_candidaturas_custom_fields
ON candidaturas USING GIN (custom_fields);

-- Log de validação
DO $$
DECLARE
    v_column_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'candidaturas'
        AND column_name = 'custom_fields'
    ) INTO v_column_exists;

    IF v_column_exists THEN
        RAISE NOTICE '✅ Migration 069: Coluna custom_fields adicionada com sucesso';
        RAISE NOTICE '   - Tabela: candidaturas';
        RAISE NOTICE '   - Tipo: JSON';
        RAISE NOTICE '   - Índice GIN criado para busca eficiente';
    ELSE
        RAISE EXCEPTION '❌ Falha ao criar coluna custom_fields';
    END IF;
END $$;
