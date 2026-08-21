-- ===============================================================
-- Migration 068: Adicionar Nome da Vaga na View de Candidaturas
-- ===============================================================
-- Adiciona o nome da vaga (coluna "vaga_nome") na view de
-- relatório de candidaturas.
--
-- Data: 2026-07-21
-- ===============================================================

-- Drop view existente
DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

-- Criar view com nome da vaga
CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,  -- ✅ NOVO: Nome da vaga
    c.status,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- Placeholder para campo customizado (ainda não encontrado)
    NULL::text AS conhecia_framework,

    -- Datas
    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026  -- Filtrar apenas 2026
ORDER BY c.created_at DESC;

-- Comentários
COMMENT ON VIEW vw_relatorio_candidaturas IS 'Relatório de candidaturas 2026 com nome da vaga';
COMMENT ON COLUMN vw_relatorio_candidaturas.vaga_nome IS 'Nome da vaga';
COMMENT ON COLUMN vw_relatorio_candidaturas.etapa_candidatura IS 'Nome do stage atual da candidatura';
COMMENT ON COLUMN vw_relatorio_candidaturas.status_candidatura IS 'Status da candidatura (APPLIED, IN_PROCESS, etc)';
COMMENT ON COLUMN vw_relatorio_candidaturas.conhecia_framework IS 'Resposta à pergunta "Você conhecia a Framework?" - PENDENTE LOCALIZAÇÃO';

-- Grant acesso
GRANT SELECT ON vw_relatorio_candidaturas TO PUBLIC;

-- Log de teste
DO $$
DECLARE
    v_total INTEGER;
    v_exemplo_vaga VARCHAR;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_relatorio_candidaturas;

    SELECT vaga_nome INTO v_exemplo_vaga
    FROM vw_relatorio_candidaturas
    WHERE vaga_nome IS NOT NULL
    LIMIT 1;

    RAISE NOTICE '✅ Migration 068: View vw_relatorio_candidaturas atualizada';
    RAISE NOTICE '   - Total de registros: %', v_total;
    RAISE NOTICE '   - Exemplo de vaga: %', v_exemplo_vaga;
    RAISE NOTICE '   - Campo conhecia_framework: PENDENTE (ainda não localizado)';
END $$;
