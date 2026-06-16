-- Migration 014: Adicionar valor EXPRESS ao ENUM SyncTypeEnum
-- Descrição: Adiciona suporte ao novo modo de sincronização EXPRESS no banco de dados
-- Data: 2026-01-21

-- Adicionar novo valor ao ENUM
ALTER TYPE synctypeenum ADD VALUE IF NOT EXISTS 'EXPRESS';

-- Confirmar adição
SELECT 'Migration 014: EXPRESS adicionado ao SyncTypeEnum' AS status;
