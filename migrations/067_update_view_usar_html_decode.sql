-- ===============================================================
-- Migration 067: Atualizar View para Usar html_decode()
-- ===============================================================
-- Atualiza view vw_relatorio_requisicoes para converter
-- entidades HTML diretamente na view
--
-- Data: 2026-07-21
-- ===============================================================

-- Drop view existente
DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

-- Criar view com html_decode()
CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    -- Remover tags HTML e converter entidades HTML
    html_decode(
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        COALESCE(r.description, ''),
                        '<[^>]+>', '', 'g'  -- Remove tags HTML
                    ),
                    '&nbsp;', ' ', 'g'  -- Substitui &nbsp; (antes do html_decode)
                ),
                '\s+', ' ', 'g'  -- Remove múltiplos espaços
            )
        )
    ) AS descricao,

    -- Usar nome da requisição, senão nome da vaga, senão "Sem título"
    COALESCE(
        NULLIF(TRIM(r.name), ''),
        NULLIF(TRIM(v.name), ''),
        'Sem título'
    ) AS titulo,

    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao

FROM requisicoes r
LEFT JOIN vagas v ON r.job_inhire_id = v.inhire_id
WHERE r.requested_at IS NOT NULL
ORDER BY r.requested_at DESC;

-- Comentários
COMMENT ON VIEW vw_relatorio_requisicoes IS 'Relatório de requisições - HTML e entidades convertidos para texto puro';
COMMENT ON COLUMN vw_relatorio_requisicoes.descricao IS 'Descrição em texto puro (HTML e entidades convertidos)';
COMMENT ON COLUMN vw_relatorio_requisicoes.titulo IS 'Título da requisição (usa nome da vaga como fallback)';
COMMENT ON COLUMN vw_relatorio_requisicoes.data_solicitacao IS 'Data da solicitação (timezone America/Sao_Paulo)';

-- Grant acesso
GRANT SELECT ON vw_relatorio_requisicoes TO PUBLIC;

-- Log de teste
DO $$
DECLARE
    v_total INTEGER;
    v_exemplo TEXT;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_relatorio_requisicoes;

    SELECT SUBSTRING(descricao, 1, 100) INTO v_exemplo
    FROM vw_relatorio_requisicoes
    WHERE LENGTH(descricao) > 0
    LIMIT 1;

    RAISE NOTICE '✅ Migration 067: View vw_relatorio_requisicoes atualizada';
    RAISE NOTICE '   - Total de registros: %', v_total;
    RAISE NOTICE '   - Exemplo de descrição: %...', v_exemplo;
END $$;
