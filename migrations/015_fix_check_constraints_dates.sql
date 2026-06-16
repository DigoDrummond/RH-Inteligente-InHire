-- Migration 015: Corrigir check constraints de datas
-- Data: 2026-01-22
--
-- Problema: Os check constraints estavam comparando timestamps da API (updated_at_inhire)
-- com timestamps locais do banco (created_at), causando falhas quando inseríamos novos registros.
--
-- Solução: Modificar os constraints para comparar apenas timestamps da mesma origem:
-- - created_at_inhire vs updated_at_inhire (ambos da API)

-- ==========================================
-- VAGAS
-- ==========================================
ALTER TABLE vagas
DROP CONSTRAINT IF EXISTS chk_vaga_dates_logical;

ALTER TABLE vagas
ADD CONSTRAINT chk_vaga_dates_logical
CHECK (
    created_at_inhire IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at_inhire
);

-- ==========================================
-- POSIÇÕES
-- ==========================================
ALTER TABLE posicoes
DROP CONSTRAINT IF EXISTS chk_posicao_dates_logical;

ALTER TABLE posicoes
ADD CONSTRAINT chk_posicao_dates_logical
CHECK (
    created_at_inhire IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at_inhire
);

-- ==========================================
-- CANDIDATURAS
-- ==========================================
-- NOTA: Candidaturas não tem created_at_inhire, apenas updated_at_inhire
-- Removendo constraint antigo se existir, mas não adicionando novo
ALTER TABLE candidaturas
DROP CONSTRAINT IF EXISTS chk_candidatura_dates_logical;

-- ==========================================
-- TALENTOS
-- ==========================================
ALTER TABLE talentos
DROP CONSTRAINT IF EXISTS chk_talento_dates_logical;

ALTER TABLE talentos
ADD CONSTRAINT chk_talento_dates_logical
CHECK (
    created_at_inhire IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at_inhire
);

-- ==========================================
-- REQUISIÇÕES
-- ==========================================
ALTER TABLE requisicoes
DROP CONSTRAINT IF EXISTS chk_requisicao_dates_logical;

ALTER TABLE requisicoes
ADD CONSTRAINT chk_requisicao_dates_logical
CHECK (
    created_at_inhire IS NULL OR
    updated_at_inhire IS NULL OR
    updated_at_inhire >= created_at_inhire
);

-- ==========================================
-- POSITION_TIMELINE
-- ==========================================
-- NOTA: position_timeline não tem colunas *_inhire, apenas created_at/updated_at locais
-- Removendo constraint antigo se existir, mas não adicionando novo
ALTER TABLE position_timeline
DROP CONSTRAINT IF EXISTS chk_position_timeline_dates_logical;

-- Verificar se os constraints foram aplicados corretamente
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conname LIKE '%dates_logical%'
ORDER BY table_name, constraint_name;
