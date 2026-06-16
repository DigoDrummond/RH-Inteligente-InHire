-- Migration 023: Remover tabelas obsoletas
-- Data: 2026-02-06
-- Descrição: Remove tabelas que não são mais utilizadas pelo sistema

-- Este script documenta a remoção de tabelas que foram excluídas por não trazerem
-- informações relevantes para análise de BI ou por serem dados redundantes/complexos

BEGIN;

-- 1. custom_fields (criada mas nunca populada)
DROP TABLE IF EXISTS custom_fields CASCADE;

-- 2. talento_arquivos (CVs em formato binário - não relevante para BI)
-- DROP TABLE IF EXISTS talento_arquivos CASCADE; -- Já foi removida

-- 3. talento_tags (sem dados ou obsoleto)
-- DROP TABLE IF EXISTS talento_tags CASCADE; -- Já foi removida

-- 4. scorecard_interviews (sem dados populados)
-- DROP TABLE IF EXISTS scorecard_interviews CASCADE; -- Já foi removida

-- 5. scorecard_jobs (sem dados populados)
-- DROP TABLE IF EXISTS scorecard_jobs CASCADE; -- Já foi removida

-- 6. scorecard_avaliacoes (sem dados populados)
-- DROP TABLE IF EXISTS scorecard_avaliacoes CASCADE; -- Já foi removida

-- 7. form_responses (dados complexos, baixo valor analítico)
-- DROP TABLE IF EXISTS form_responses CASCADE; -- Já foi removida

-- 8. automations (configuração do sistema, não dados de negócio)
-- DROP TABLE IF EXISTS automations CASCADE; -- Já foi removida

COMMIT;

-- ============================================================
-- TABELAS REMOVIDAS - REGISTRO HISTÓRICO
-- ============================================================
--
-- As seguintes tabelas foram removidas do banco de dados em 06/02/2026:
--
-- 1. custom_fields
--    - Motivo: Tabela vazia (0 registros), nunca foi populada
--
-- 2. talento_arquivos
--    - Motivo: CVs em formato binário, não relevante para análise de BI
--    - Acessar diretamente no ATS quando necessário
--
-- 3. talento_tags
--    - Motivo: Sem dados ou obsoleto
--
-- 4. scorecard_interviews
--    - Motivo: Sem dados populados, não relevante para BI
--
-- 5. scorecard_jobs
--    - Motivo: Sem dados populados, não relevante para BI
--
-- 6. scorecard_avaliacoes
--    - Motivo: Sem dados populados, não relevante para BI
--
-- 7. form_responses
--    - Motivo: Dados complexos e pouco estruturados, baixo valor analítico
--
-- 8. automations
--    - Motivo: Configuração do sistema, não dados de negócio para análise
--
-- ============================================================
-- IMPACTO
-- ============================================================
--
-- ANTES:  19 tabelas + 2 views
-- DEPOIS: 11 tabelas + 2 views
--
-- Redução: 8 tabelas obsoletas removidas (42%)
--
-- ============================================================
