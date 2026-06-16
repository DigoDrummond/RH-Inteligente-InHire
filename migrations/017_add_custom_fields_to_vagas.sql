-- Migration 017: Adicionar campo custom_fields à tabela vagas
-- Data: 2026-01-24
-- Descrição: Adiciona coluna custom_fields (JSONB) para armazenar campos personalizados das vagas

BEGIN;

-- Adicionar campo custom_fields à tabela vagas
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS custom_fields JSONB;

-- Criar índice GIN para permitir queries eficientes no JSONB
CREATE INDEX IF NOT EXISTS idx_vagas_custom_fields ON vagas USING GIN (custom_fields);

-- Comentário
COMMENT ON COLUMN vagas.custom_fields IS 'Campos personalizados da vaga (formulário customizado)';

COMMIT;

SELECT 'Migration 017 executada com sucesso!' as status;
SELECT 'Coluna custom_fields adicionada à tabela vagas' as info;
