-- ===============================================================
-- Migration 064: Corrigir View de Relatório de Requisições
-- ===============================================================
-- Correções:
-- 1. Filtrar requisições sem título (name IS NOT NULL)
-- 2. Converter HTML da descrição para texto puro
--
-- Data: 2026-07-21
-- ===============================================================

-- Drop view existente
DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

-- Criar view corrigida
CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    -- Remover tags HTML da descrição e limpar espaços
    TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    COALESCE(description, ''),
                    '<[^>]+>', '', 'g'  -- Remove todas as tags HTML
                ),
                '&nbsp;', ' ', 'g'  -- Substitui &nbsp; por espaço
            ),
            '\s+', ' ', 'g'  -- Remove múltiplos espaços
        )
    ) AS descricao,

    name AS titulo,

    requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao

FROM requisicoes
WHERE requested_at IS NOT NULL
  AND name IS NOT NULL           -- Filtrar títulos nulos
  AND TRIM(name) != ''            -- Filtrar títulos vazios
ORDER BY requested_at DESC;

-- Comentários
COMMENT ON VIEW vw_relatorio_requisicoes IS 'Relatório de requisições - descrição convertida de HTML para texto';
COMMENT ON COLUMN vw_relatorio_requisicoes.descricao IS 'Descrição da requisição (HTML convertido para texto)';
COMMENT ON COLUMN vw_relatorio_requisicoes.titulo IS 'Título/Nome da requisição (apenas não vazios)';
COMMENT ON COLUMN vw_relatorio_requisicoes.data_solicitacao IS 'Data da solicitação (timezone America/Sao_Paulo)';

-- Grant acesso
GRANT SELECT ON vw_relatorio_requisicoes TO PUBLIC;

-- Log
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 064: View vw_relatorio_requisicoes corrigida (HTML -> texto, filtro título)';
END $$;
