-- Migration 006: Remover tabelas vazias sem dados na API
-- Data: 2025-12-03
-- Descrição: Remove 4 tabelas que não possuem dados na API InHire

-- 1. Tabela custom_fields (0 registros)
DROP TABLE IF EXISTS custom_fields CASCADE;

-- 2. Tabela requisicoes (0 registros)
DROP TABLE IF EXISTS requisicoes CASCADE;

-- 3. Tabela scorecard_avaliacoes (0 registros)
DROP TABLE IF EXISTS scorecard_avaliacoes CASCADE;

-- 4. Tabela talento_tags (0 registros)
DROP TABLE IF EXISTS talento_tags CASCADE;

-- Confirmação
SELECT 'Migration 006 executada com sucesso - 4 tabelas vazias removidas' AS status;
