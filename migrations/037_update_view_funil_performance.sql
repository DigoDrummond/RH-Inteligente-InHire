/*
================================================================================
MIGRATION 037: Atualizar View vw_funil_performance
================================================================================

Data: 2026-02-06
Descrição:
  Adiciona 3 novos campos e corrige cálculo de dias_no_processo

Mudanças:
  1. Adiciona: nome_talento (JOIN com talentos)
  2. Adiciona: data_criacao_vaga
  3. Adiciona: data_encerramento_vaga (última mudança de status)
  4. CORRIGE: dias_no_processo (estava usando CURRENT_DATE incorretamente)

  Campo recrutadora: usa v.user_name (mesmo da view de posições)

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_funil_performance CASCADE;

-- Recria view com melhorias
CREATE OR REPLACE VIEW vw_funil_performance AS
WITH etapas_normalizadas AS (
    -- Normaliza os nomes das etapas do funil
    SELECT
        c.id,
        c.vaga_id,
        c.talent_inhire_id,
        c.status,
        c.stage_order,
        c.created_at,
        c.updated_at,

        -- Normaliza o nome da etapa
        CASE
            WHEN c.stage_name ILIKE '%hunting%' THEN 'Hunting'
            WHEN c.stage_name ILIKE '%abordagem%' THEN 'Abordagem'
            WHEN c.stage_name ILIKE '%inscri%' THEN 'Inscrição'
            WHEN c.stage_name ILIKE '%bate%papo%pessoas%cultura%' OR c.stage_name ILIKE '%bate%papo%time%gente%' THEN 'Bate papo | Pessoas e Cultura'
            WHEN c.stage_name ILIKE '%etapa%t%cnica%' THEN 'Etapa técnica | Talent IA'
            WHEN c.stage_name ILIKE '%aguardando%devolutiva%ia%' OR c.stage_name ILIKE '%aguardando%devolutiva%' THEN 'Aguardando Devolutiva IA'
            WHEN c.stage_name ILIKE '%bate%papo%cliente%' OR c.stage_name ILIKE '%bate%papo%gestor%' THEN 'Bate Papo | Cliente'
            WHEN c.stage_name ILIKE '%formaliza%' THEN 'Formalização de Proposta'
            WHEN c.stage_name ILIKE '%contrata%' THEN 'Contratação'
            WHEN c.stage_name ILIKE '%aguardando%agenda%' THEN 'Aguardando Agenda'
            ELSE c.stage_name
        END AS etapa_funil_normalizada,

        -- Ordem padrão das etapas no funil
        CASE
            WHEN c.stage_name ILIKE '%hunting%' THEN 1
            WHEN c.stage_name ILIKE '%abordagem%' THEN 2
            WHEN c.stage_name ILIKE '%inscri%' THEN 3
            WHEN c.stage_name ILIKE '%bate%papo%pessoas%cultura%' OR c.stage_name ILIKE '%bate%papo%time%gente%' THEN 4
            WHEN c.stage_name ILIKE '%etapa%t%cnica%' THEN 5
            WHEN c.stage_name ILIKE '%aguardando%devolutiva%ia%' OR c.stage_name ILIKE '%aguardando%devolutiva%' THEN 6
            WHEN c.stage_name ILIKE '%bate%papo%cliente%' OR c.stage_name ILIKE '%bate%papo%gestor%' THEN 7
            WHEN c.stage_name ILIKE '%formaliza%' THEN 8
            WHEN c.stage_name ILIKE '%contrata%' THEN 9
            ELSE 99
        END AS ordem_funil_padrao,

        v.name AS nome_vaga,
        v.area AS area_vaga,
        v.custom_fields->>'Torre' AS torre,
        v.user_name AS recrutadora,
        cl.name AS cliente,

        -- NOVOS CAMPOS
        t.name AS nome_talento,
        DATE(v.created_at) AS data_criacao_vaga,

        -- Data de encerramento da vaga (última mudança de status da posição)
        (SELECT MAX(pt.changed_at)
         FROM position_timeline pt
         INNER JOIN posicoes p ON p.id = pt.posicao_id
         WHERE p.vaga_id = v.id
         AND pt.new_status IN ('closed', 'canceled')
        )::date AS data_encerramento_vaga,

        -- Status da candidatura
        c.status::text AS status_candidatura,

        -- Indicadores binários
        CASE WHEN c.status::text = 'HIRED' THEN 1 ELSE 0 END AS foi_contratado,
        CASE WHEN c.status::text = 'REJECTED' THEN 1 ELSE 0 END AS foi_reprovado,
        CASE WHEN c.status::text = 'DECLINED' THEN 1 ELSE 0 END AS foi_desistente,
        CASE WHEN c.status::text = 'ACTIVE' THEN 1 ELSE 0 END AS esta_ativo

    FROM candidaturas c
    INNER JOIN vagas v ON c.vaga_id = v.id
    LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
    LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.stage_name IS NOT NULL
)
SELECT
    -- Identificação
    id AS candidatura_id,
    vaga_id,
    talent_inhire_id,
    nome_vaga,
    area_vaga,

    -- NOVO: Nome do Talento
    nome_talento,

    -- Etapa do Funil
    etapa_funil_normalizada AS etapa_funil,
    ordem_funil_padrao AS ordem_etapa,
    stage_order AS ordem_stage_original,

    -- Dimensões de Análise
    recrutadora,
    cliente,
    torre,

    -- Status
    status_candidatura,
    foi_contratado,
    foi_reprovado,
    foi_desistente,
    esta_ativo,

    -- Datas
    created_at AS data_criacao_candidatura,
    updated_at AS data_atualizacao_candidatura,

    -- NOVOS: Datas da vaga
    data_criacao_vaga,
    data_encerramento_vaga,

    -- Tempo no processo CORRIGIDO (dias entre criação e última atualização da candidatura)
    (updated_at::date - created_at::date)::int AS dias_no_processo

FROM etapas_normalizadas
ORDER BY created_at DESC;

-- Comentários
COMMENT ON VIEW vw_funil_performance IS
'View para análise de funil de performance das candidaturas.
Atualizada em 2026-02-06 com:
- Nome do talento
- Data de criação da vaga
- Data de encerramento da vaga
- Correção do cálculo de dias_no_processo (agora usa updated_at - created_at)
- Campo recrutadora usa v.user_name (mesmo campo da view de posições)';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_nome INTEGER;
    v_com_data_enc INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_funil_performance;
    SELECT COUNT(nome_talento) INTO v_com_nome FROM vw_funil_performance;
    SELECT COUNT(data_encerramento_vaga) INTO v_com_data_enc FROM vw_funil_performance;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 037 - VIEW FUNIL PERFORMANCE ATUALIZADA';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de candidaturas: %', v_total;
    RAISE NOTICE 'Com nome do talento: %', v_com_nome;
    RAISE NOTICE 'Com data de encerramento: %', v_com_data_enc;
    RAISE NOTICE '';
    RAISE NOTICE 'Mudanças aplicadas:';
    RAISE NOTICE '  1. Adicionado: nome_talento';
    RAISE NOTICE '  2. Adicionado: data_criacao_vaga';
    RAISE NOTICE '  3. Adicionado: data_encerramento_vaga';
    RAISE NOTICE '  4. CORRIGIDO: dias_no_processo (agora usa updated_at - created_at)';
    RAISE NOTICE '  5. Campo recrutadora usa v.user_name (mesmo da view de posições)';
    RAISE NOTICE '================================================================================';
END $$;
