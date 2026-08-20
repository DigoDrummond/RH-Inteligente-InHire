-- ===============================================================
-- Migration 063: Criar View de Relatório de Candidaturas
-- ===============================================================
-- Cria view simplificada com os 7 campos solicitados:
-- 1. vaga_id
-- 2. status
-- 3. talent_name
-- 4. talent_email
-- 5. Etapa da candidatura
-- 6. Status da candidatura (duplicado do #2)
-- 7. "Você conhecia a Framework?" (campo customizado)
--
-- Data: 2026-07-21
-- ===============================================================

-- Drop view se existir
DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

-- Criar view
CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    vaga_id,
    status AS status_candidatura,
    talent_name AS nome_candidato,
    talent_email AS email_candidato,
    stage_name AS etapa_candidatura,

    -- Extração do campo customizado "Você conhecia a Framework?"
    -- Tenta múltiplas variações possíveis de chave JSON
    CASE
        WHEN stage_metadata IS NOT NULL THEN
            COALESCE(
                stage_metadata::jsonb->>'conhecia_framework',
                stage_metadata::jsonb->>'conheciaFramework',
                stage_metadata::jsonb->>'voce_conhecia_framework',
                stage_metadata::jsonb->>'Você conhecia a Framework?',
                stage_metadata::jsonb->'customFields'->>'conhecia_framework',
                stage_metadata::jsonb->'customFields'->>'conheciaFramework',
                stage_metadata::jsonb->'customFields'->>'Você conhecia a Framework?',
                'N/A'
            )
        WHEN phase_metadata IS NOT NULL THEN
            COALESCE(
                phase_metadata::jsonb->>'conhecia_framework',
                phase_metadata::jsonb->>'conheciaFramework',
                phase_metadata::jsonb->>'voce_conhecia_framework',
                phase_metadata::jsonb->>'Você conhecia a Framework?',
                phase_metadata::jsonb->'customFields'->>'conhecia_framework',
                phase_metadata::jsonb->'customFields'->>'conheciaFramework',
                phase_metadata::jsonb->'customFields'->>'Você conhecia a Framework?',
                'N/A'
            )
        ELSE 'N/A'
    END AS conhecia_framework

FROM candidaturas
ORDER BY updated_at_inhire DESC NULLS LAST;

-- Comentários
COMMENT ON VIEW vw_relatorio_candidaturas IS 'Relatório simplificado de candidaturas - campos essenciais + campo customizado';
COMMENT ON COLUMN vw_relatorio_candidaturas.vaga_id IS 'ID da vaga à qual o candidato se inscreveu';
COMMENT ON COLUMN vw_relatorio_candidaturas.status_candidatura IS 'Status atual da candidatura (active, hired, rejected, declined)';
COMMENT ON COLUMN vw_relatorio_candidaturas.nome_candidato IS 'Nome do candidato no momento da candidatura';
COMMENT ON COLUMN vw_relatorio_candidaturas.email_candidato IS 'Email do candidato no momento da candidatura';
COMMENT ON COLUMN vw_relatorio_candidaturas.etapa_candidatura IS 'Etapa/stage atual da candidatura';
COMMENT ON COLUMN vw_relatorio_candidaturas.conhecia_framework IS 'Resposta do candidato à pergunta "Você conhecia a Framework?"';

-- Grant acesso
GRANT SELECT ON vw_relatorio_candidaturas TO PUBLIC;

-- Log
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 063: View vw_relatorio_candidaturas criada com sucesso';
END $$;
