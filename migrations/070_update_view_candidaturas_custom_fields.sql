-- ===============================================================
-- Migration 070: Atualizar view vw_relatorio_candidaturas
-- ===============================================================
-- Extrai o campo "Você conhecia a Framework Digital?" do JSON
-- custom_fields das candidaturas
--
-- ID do campo: 55282edb-bb11-4445-8cd6-3c0c6b9ddb9a
--
-- Data: 2026-07-21
-- ===============================================================

DROP VIEW IF EXISTS vw_relatorio_candidaturas;

CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    c.status,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- ✅ NOVO: Extrair "Você conhecia a Framework Digital?" do JSON custom_fields
    -- O campo retorna um array JSON, então pegamos o primeiro valor
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' THEN
            (c.custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a')::jsonb->>0
        ELSE NULL
    END AS conhecia_framework,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026
ORDER BY c.created_at DESC;

-- Comentário na view
COMMENT ON VIEW vw_relatorio_candidaturas IS 'Relatório de candidaturas 2026 com custom fields extraídos';

-- Log de validação
DO $$
DECLARE
    v_view_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.views
        WHERE table_name = 'vw_relatorio_candidaturas'
    ) INTO v_view_exists;

    IF v_view_exists THEN
        RAISE NOTICE '✅ Migration 070: View vw_relatorio_candidaturas atualizada';
        RAISE NOTICE '   - Campo custom "Você conhecia a Framework?" extraído';
        RAISE NOTICE '   - ID do campo: 55282edb-bb11-4445-8cd6-3c0c6b9ddb9a';
    ELSE
        RAISE EXCEPTION '❌ Falha ao atualizar view vw_relatorio_candidaturas';
    END IF;
END $$;
