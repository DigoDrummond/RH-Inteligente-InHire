-- =====================================================
-- Migration: 020_fix_invalid_posicoes_status.sql
-- Descrição: Remove registros com status inválidos na tabela posicoes
--           (filled e archived não existem na API InHire)
-- Data: 2026-02-04
-- =====================================================

-- IMPORTANTE: Status válidos para posições segundo a API InHire:
-- - open
-- - closed
-- - paused
-- - canceled
--
-- Registros com status 'filled' e 'archived' são dados incorretos
-- que não correspondem à API e devem ser EXCLUÍDOS.

-- Ver quantos registros serão EXCLUÍDOS
SELECT
    'REGISTROS QUE SERÃO EXCLUÍDOS' as acao,
    status,
    COUNT(*) as quantidade
FROM posicoes
WHERE status IN ('filled', 'archived')
GROUP BY status
ORDER BY quantidade DESC;

-- Ver exemplos dos registros que serão excluídos
SELECT
    'AMOSTRA DOS REGISTROS' as tipo,
    inhire_id,
    vaga_id,
    status,
    requisition_id,
    talent_id,
    hired_at,
    opened_at,
    created_at_inhire,
    updated_at_inhire
FROM posicoes
WHERE status IN ('filled', 'archived')
ORDER BY updated_at_inhire DESC
LIMIT 10;

-- EXCLUIR registros com status 'filled' (654 registros)
-- Esses registros não existem na API e são dados incorretos
DELETE FROM posicoes
WHERE status = 'filled';

-- EXCLUIR registros com status 'archived' (12 registros)
-- Esses registros não existem na API e são dados incorretos
DELETE FROM posicoes
WHERE status = 'archived';

-- Verificar resultado após exclusão
SELECT
    'APÓS EXCLUSÃO - DISTRIBUIÇÃO DE STATUS' as momento,
    status,
    COUNT(*) as quantidade
FROM posicoes
WHERE status IS NOT NULL
GROUP BY status
ORDER BY quantidade DESC;

-- Verificar se ainda existem status inválidos
SELECT
    'STATUS INVÁLIDOS RESTANTES' as verificacao,
    COUNT(*) as total
FROM posicoes
WHERE status NOT IN ('open', 'closed', 'paused', 'canceled')
  AND status IS NOT NULL;

-- Estatísticas finais
SELECT
    'ESTATÍSTICAS FINAIS' as relatorio,
    COUNT(*) as total_posicoes,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as abertas,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as fechadas,
    COUNT(CASE WHEN status = 'paused' THEN 1 END) as pausadas,
    COUNT(CASE WHEN status = 'canceled' THEN 1 END) as canceladas
FROM posicoes;
