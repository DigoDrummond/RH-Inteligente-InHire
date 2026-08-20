-- ===============================================================
-- RELATÓRIO DE CANDIDATURAS - VERSÃO SIMPLIFICADA
-- ===============================================================
-- Campos solicitados:
-- 1. vaga_id                    - ID da vaga
-- 2. status                     - Status da candidatura
-- 3. talent_name                - Nome do candidato
-- 4. talent_email               - Email do candidato
-- 5. Etapa da candidatura       - stage_name
-- 6. Status da candidatura      - status (mesmo que #2)
-- 7. "Você conhecia a Framework?" - Campo customizado
--
-- Data: 2026-07-21
-- ===============================================================

SELECT
    vaga_id,
    status AS status_candidatura,
    talent_name AS nome_candidato,
    talent_email AS email_candidato,
    stage_name AS etapa_candidatura,

    -- Tentativas de extração do campo "Você conhecia a Framework?"
    -- NOTA: Pode precisar ajuste baseado na estrutura real dos metadados
    CASE
        WHEN stage_metadata IS NOT NULL THEN
            COALESCE(
                stage_metadata::jsonb->>'conhecia_framework',
                stage_metadata::jsonb->>'conheciaFramework',
                stage_metadata::jsonb->>'voce_conhecia_framework',
                stage_metadata::jsonb->'customFields'->>'conhecia_framework',
                'N/A'
            )
        WHEN phase_metadata IS NOT NULL THEN
            COALESCE(
                phase_metadata::jsonb->>'conhecia_framework',
                phase_metadata::jsonb->>'conheciaFramework',
                phase_metadata::jsonb->>'voce_conhecia_framework',
                phase_metadata::jsonb->'customFields'->>'conhecia_framework',
                'N/A'
            )
        ELSE 'N/A'
    END AS conhecia_framework

FROM candidaturas
ORDER BY updated_at_inhire DESC NULLS LAST;
