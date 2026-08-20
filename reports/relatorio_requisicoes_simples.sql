-- ===============================================================
-- RELATÓRIO DE REQUISIÇÕES - VERSÃO SIMPLIFICADA
-- ===============================================================
-- Apenas os 3 campos solicitados:
-- 1. description  - Descrição da requisição
-- 2. name         - Título/Nome da requisição
-- 3. requested_at - Data da solicitação
--
-- Data: 2026-07-21
-- ===============================================================

SELECT
    description,
    name,
    requested_at AT TIME ZONE 'America/Sao_Paulo' AS requested_at
FROM requisicoes
WHERE requested_at IS NOT NULL
ORDER BY requested_at DESC;
