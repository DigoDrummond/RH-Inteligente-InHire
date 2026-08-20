-- ===============================================================
-- Migration 065: Corrigir View Requisições - Usar Nome da Vaga
-- ===============================================================
-- Correções FINAIS:
-- 1. Converter HTML da descrição para texto puro
-- 2. Usar nome da VAGA quando requisição não tem título
-- 3. Fallback para "Sem título" se não houver nem nome nem vaga
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
                    COALESCE(r.description, ''),
                    '<[^>]+>', '', 'g'  -- Remove todas as tags HTML
                ),
                '&nbsp;', ' ', 'g'  -- Substitui &nbsp; por espaço
            ),
            '\s+', ' ', 'g'  -- Remove múltiplos espaços
        )
    ) AS descricao,

    -- Usar nome da requisição, se não tiver usar nome da vaga, senão "Sem título"
    COALESCE(
        NULLIF(TRIM(r.name), ''),           -- Nome da requisição (se não vazio)
        NULLIF(TRIM(v.name), ''),           -- Nome da vaga (fallback)
        'Sem título'                         -- Último recurso
    ) AS titulo,

    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao

FROM requisicoes r
LEFT JOIN vagas v ON r.job_inhire_id = v.inhire_id
WHERE r.requested_at IS NOT NULL
ORDER BY r.requested_at DESC;

-- Comentários
COMMENT ON VIEW vw_relatorio_requisicoes IS 'Relatório de requisições - HTML convertido, título usa nome da vaga quando necessário';
COMMENT ON COLUMN vw_relatorio_requisicoes.descricao IS 'Descrição da requisição (HTML convertido para texto)';
COMMENT ON COLUMN vw_relatorio_requisicoes.titulo IS 'Título da requisição (usa nome da vaga como fallback)';
COMMENT ON COLUMN vw_relatorio_requisicoes.data_solicitacao IS 'Data da solicitação (timezone America/Sao_Paulo)';

-- Grant acesso
GRANT SELECT ON vw_relatorio_requisicoes TO PUBLIC;

-- Log de correção
DO $$
DECLARE
    v_total INTEGER;
    v_com_titulo INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_relatorio_requisicoes;
    SELECT COUNT(*) INTO v_com_titulo
    FROM vw_relatorio_requisicoes
    WHERE titulo != 'Sem título';

    RAISE NOTICE '✅ Migration 065: View vw_relatorio_requisicoes corrigida';
    RAISE NOTICE '   - Total de requisições: %', v_total;
    RAISE NOTICE '   - Com título válido: %', v_com_titulo;
    RAISE NOTICE '   - Descrição HTML convertida para texto';
END $$;
