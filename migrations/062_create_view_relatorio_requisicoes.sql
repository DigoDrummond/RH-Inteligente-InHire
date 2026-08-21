-- ===============================================================
-- Migration 062: Criar View de Relatório de Requisições
-- ===============================================================
-- Cria view simplificada com apenas os 3 campos solicitados
--
-- Data: 2026-07-21
-- ===============================================================

-- Drop view se existir
DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

-- Criar view
CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    description AS descricao,
    name AS titulo,
    requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao
FROM requisicoes
WHERE requested_at IS NOT NULL
ORDER BY requested_at DESC;

-- Comentários
COMMENT ON VIEW vw_relatorio_requisicoes IS 'Relatório simplificado de requisições - apenas campos essenciais';
COMMENT ON COLUMN vw_relatorio_requisicoes.descricao IS 'Descrição da requisição';
COMMENT ON COLUMN vw_relatorio_requisicoes.titulo IS 'Título/Nome da requisição';
COMMENT ON COLUMN vw_relatorio_requisicoes.data_solicitacao IS 'Data da solicitação (timezone America/Sao_Paulo)';

-- Grant acesso
GRANT SELECT ON vw_relatorio_requisicoes TO PUBLIC;

-- Log
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 062: View vw_relatorio_requisicoes criada com sucesso';
END $$;
