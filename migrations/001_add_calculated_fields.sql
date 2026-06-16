-- ========================================
-- Migration 001: Adicionar Campos Calculados
-- Data: 2025-11-19
-- Descrição: Adiciona campos calculados e triggers para métricas de candidaturas
-- ========================================

-- ========================================
-- 1. ADICIONAR NOVOS CAMPOS
-- ========================================

-- Adicionar campo created_at_inhire em candidaturas (originalmente missing)
ALTER TABLE candidaturas
ADD COLUMN IF NOT EXISTS created_at_inhire TIMESTAMP WITH TIME ZONE;

-- Adicionar campos calculados para performance
ALTER TABLE candidaturas
ADD COLUMN IF NOT EXISTS dias_no_processo DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS dias_no_stage_atual DECIMAL(10, 2);

-- Criar índice para otimizar queries por created_at_inhire
CREATE INDEX IF NOT EXISTS idx_candidatura_created_inhire
ON candidaturas(created_at_inhire);

-- Criar índice composto para análises de tempo
CREATE INDEX IF NOT EXISTS idx_candidatura_tempo_metricas
ON candidaturas(vaga_id, status, dias_no_processo);

-- ========================================
-- 2. POPULAR CAMPOS EXISTENTES
-- ========================================

-- Popular created_at_inhire com created_at para registros existentes (fallback)
UPDATE candidaturas
SET created_at_inhire = created_at
WHERE created_at_inhire IS NULL;

-- Calcular dias_no_processo para registros existentes
UPDATE candidaturas
SET dias_no_processo = EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400
WHERE dias_no_processo IS NULL;

-- Calcular dias_no_stage_atual para registros existentes
UPDATE candidaturas
SET dias_no_stage_atual = time_in_current_stage / 86400000.0
WHERE dias_no_stage_atual IS NULL
  AND time_in_current_stage IS NOT NULL;

-- ========================================
-- 3. FUNÇÃO PARA CALCULAR MÉTRICAS
-- ========================================

CREATE OR REPLACE FUNCTION update_candidatura_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular dias no processo (desde criação até agora)
    IF NEW.created_at IS NOT NULL THEN
        NEW.dias_no_processo = EXTRACT(EPOCH FROM (NOW() - NEW.created_at)) / 86400;
    END IF;

    -- Calcular dias no stage atual (time_in_current_stage está em milissegundos)
    IF NEW.time_in_current_stage IS NOT NULL THEN
        NEW.dias_no_stage_atual = NEW.time_in_current_stage / 86400000.0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 4. TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA
-- ========================================

-- Trigger para INSERT (nova candidatura)
DROP TRIGGER IF EXISTS trg_candidatura_insert_metrics ON candidaturas;
CREATE TRIGGER trg_candidatura_insert_metrics
    BEFORE INSERT ON candidaturas
    FOR EACH ROW
    EXECUTE FUNCTION update_candidatura_metrics();

-- Trigger para UPDATE (atualização de candidatura)
DROP TRIGGER IF EXISTS trg_candidatura_update_metrics ON candidaturas;
CREATE TRIGGER trg_candidatura_update_metrics
    BEFORE UPDATE ON candidaturas
    FOR EACH ROW
    WHEN (
        NEW.created_at IS DISTINCT FROM OLD.created_at OR
        NEW.time_in_current_stage IS DISTINCT FROM OLD.time_in_current_stage
    )
    EXECUTE FUNCTION update_candidatura_metrics();

-- ========================================
-- 5. ADICIONAR COMENTÁRIOS
-- ========================================

COMMENT ON COLUMN candidaturas.created_at_inhire IS 'Data de criação original na API InHire';
COMMENT ON COLUMN candidaturas.dias_no_processo IS 'Dias desde a criação da candidatura até agora (calculado automaticamente)';
COMMENT ON COLUMN candidaturas.dias_no_stage_atual IS 'Dias no stage atual (derivado de time_in_current_stage)';

-- ========================================
-- 6. VERIFICAÇÕES DE SUCESSO
-- ========================================

-- Verificar se os campos foram criados
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'candidaturas'
          AND column_name IN ('created_at_inhire', 'dias_no_processo', 'dias_no_stage_atual')
    ) THEN
        RAISE NOTICE 'SUCESSO: Campos calculados criados com sucesso!';
    ELSE
        RAISE WARNING 'AVISO: Alguns campos podem não ter sido criados.';
    END IF;
END $$;

-- Verificar se os índices foram criados
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'candidaturas'
          AND indexname IN ('idx_candidatura_created_inhire', 'idx_candidatura_tempo_metricas')
    ) THEN
        RAISE NOTICE 'SUCESSO: Índices criados com sucesso!';
    ELSE
        RAISE WARNING 'AVISO: Alguns índices podem não ter sido criados.';
    END IF;
END $$;

-- Verificar se os triggers foram criados
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname IN ('trg_candidatura_insert_metrics', 'trg_candidatura_update_metrics')
    ) THEN
        RAISE NOTICE 'SUCESSO: Triggers criados com sucesso!';
    ELSE
        RAISE WARNING 'AVISO: Alguns triggers podem não ter sido criados.';
    END IF;
END $$;

-- ========================================
-- 7. ESTATÍSTICAS
-- ========================================

-- Mostrar estatísticas dos novos campos
SELECT
    'Estatísticas dos Novos Campos' as titulo,
    COUNT(*) as total_candidaturas,
    COUNT(created_at_inhire) as com_created_at_inhire,
    COUNT(dias_no_processo) as com_dias_no_processo,
    COUNT(dias_no_stage_atual) as com_dias_no_stage_atual,
    ROUND(AVG(dias_no_processo), 2) as media_dias_processo,
    ROUND(AVG(dias_no_stage_atual), 2) as media_dias_stage_atual
FROM candidaturas;

RAISE NOTICE '';
RAISE NOTICE '========================================';
RAISE NOTICE 'Migration 001 concluída com sucesso!';
RAISE NOTICE '========================================';
