/*
================================================================================
MIGRATION 048: Adicionar Email do Responsável nas Views
================================================================================

Data: 2026-02-13
Descrição:
  Adiciona o campo "Email do responsável por parte do cliente" extraído dos
  custom_fields da tabela requisicoes em duas views:

  1. vw_dados_jade - após campo responsavel_requisicao (posição 15)
  2. vw_analise_posicoes - após campo responsavel (posição 17)

  IMPORTANTE: Como o email deve ficar AO LADO do campo responsavel (não no final),
  é necessário usar DROP VIEW para permitir a reordenação das colunas.

Campo no custom_fields:
  - Nome: "Email do responsável por parte do cliente"
  - Fonte: requisicoes.custom_fields (JSONB dict)

================================================================================
*/

-- ============================================================================
-- 1. ATUALIZAR VIEW vw_dados_jade
-- ============================================================================

DROP VIEW IF EXISTS vw_dados_jade CASCADE;

CREATE OR REPLACE VIEW vw_dados_jade AS
WITH candidatos_contratados AS (
    -- Pega candidatos na etapa Contratação
    SELECT DISTINCT ON (c.vaga_id)
        c.vaga_id,
        t.name as candidato_nome,
        t.email as candidato_email,
        c.updated_at_inhire
    FROM candidaturas c
    INNER JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.stage_name = 'Contratação'
    ORDER BY c.vaga_id, c.updated_at_inhire DESC
)
SELECT
    -- Identificação da posição
    p.id AS posicao_id,
    p.inhire_id AS posicao_inhire_id,
    v.id AS vaga_id,
    v.name AS cargo,

    -- Informações salariais e de valores
    r.custom_fields->>'Custo Hora (ideal) - Ex. R$ xx,xx' AS salario_min,
    v.salary_max,
    r.custom_fields->>'Valor da venda' AS valor_venda,
    r.custom_fields->>'Salário acordado com o talento' AS valor_fechado,

    -- Informações do candidato contratado
    cc.candidato_nome,
    cc.candidato_email,

    -- Informações adicionais
    p.hired_at AS data_contratacao,
    cl.name AS cliente,
    v.user_name AS recrutadora,
    r.user_name AS responsavel_requisicao,
    r.custom_fields->>'Email do responsável por parte do cliente' AS email_responsavel_cliente,  -- ✨ NOVO (posição 15)

    -- Datas de controle
    DATE(p.opened_at) AS data_publicacao,
    DATE(r.requested_at) AS data_solicitacao

FROM posicoes p
INNER JOIN vagas v ON v.id = p.vaga_id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN candidatos_contratados cc ON cc.vaga_id = v.id

-- Filtrar apenas posições com hired_at preenchido
WHERE p.hired_at IS NOT NULL

ORDER BY p.hired_at DESC;

-- Comentários
COMMENT ON VIEW vw_dados_jade IS
'View para exportação de dados de contratações incluindo valores salariais.
Criada em 2026-02-06 (Migration 040).
Atualizada em 2026-02-13 (Migration 048) - adicionado email_responsavel_cliente após responsavel_requisicao.
Destino: Google Sheets - API_Dados_Jade';

COMMENT ON COLUMN vw_dados_jade.email_responsavel_cliente IS
'E-mail do responsável pela vaga por parte do cliente. Extraído de requisicoes.custom_fields. Adicionado em 2026-02-13 (Migration 048).';


-- ============================================================================
-- 2. ATUALIZAR VIEW vw_analise_posicoes
--    Email ao lado do campo responsavel (posição 17)
-- ============================================================================

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL AND cd.stage_order IS NOT NULL
),
pessoa_contratada AS (
    SELECT
        cd.vaga_id,
        cd.talent_inhire_id,
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
),
ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
eventos_pausa AS (
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            WHEN (previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused'
                THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed')
                THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE
        ((previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused')
        OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS data_inicio,
        COALESCE(
            (SELECT MIN(fim.changed_at)
             FROM eventos_pausa fim
             WHERE fim.posicao_id = inicio.posicao_id
               AND fim.tipo_evento = 'FIM_PAUSA'
               AND fim.changed_at > inicio.changed_at
            ),
            CURRENT_TIMESTAMP
        ) AS data_fim
    FROM eventos_pausa inicio
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
),
periodos_unicos AS (
    SELECT DISTINCT
        posicao_id,
        data_inicio,
        data_fim
    FROM periodos_pausa
),
pendencias_posicao AS (
    SELECT
        posicao_id,
        SUM(DATE(data_fim) - DATE(data_inicio)) AS total_dias_pausado,
        MIN(data_inicio) AS primeira_pausa,
        MAX(data_fim) AS ultima_retomada,
        COUNT(*) AS num_ciclos,
        STRING_AGG(TO_CHAR(data_inicio, 'DD/MM/YYYY'), '; ' ORDER BY data_inicio) AS datas_inicio_pausa,
        STRING_AGG(
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Em andamento'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END,
            '; '
            ORDER BY data_inicio
        ) AS datas_fim_pausa,
        STRING_AGG(
            TO_CHAR(data_inicio, 'DD/MM/YYYY') || ' a ' ||
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Hoje'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END ||
            ' (' || (DATE(data_fim) - DATE(data_inicio))::text || 'd)',
            '; '
            ORDER BY data_inicio
        ) AS detalhamento_periodos
    FROM periodos_unicos
    GROUP BY posicao_id
)
SELECT
    -- 1. ID
    p.id AS id_position,

    -- 2. Cargo
    v.name AS cargo,

    -- 3. Data de abertura
    DATE(r.requested_at) AS data_abertura,

    -- 4. Data da publicação
    DATE(p.opened_at) AS data_publicacao,

    -- 5. Prazo do Processo Seletivo
    v.sla_days_goal AS prazo_processo_seletivo,

    -- 6. Cliente
    c.name AS cliente,

    -- 7. Torre
    v.custom_fields->>'Torre' AS torre,

    -- 8. Status
    COALESCE(usp.new_status, p.status) AS status_atual,

    -- 9. Data de Encerramento
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
        THEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- 10. Motivo de cancelamento/paralisação
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,

    -- 11. Etapa Funil
    ue.stage_name AS etapa_funil,

    -- 12. Senioridade
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,

    -- 13. Motivo de contratação (TRADUZIDO PARA PORTUGUÊS - Migration 047)
    CASE p.reason
        WHEN 'expansion' THEN 'Aumento de quadro'
        WHEN 'replacement' THEN 'Substituição'
        WHEN 'other' THEN 'Outros'
        WHEN 'new-position' THEN 'Nova posição'
        WHEN 'turnover' THEN 'Turnover'
        WHEN 'internal-transfer' THEN 'Transferência interna'
        ELSE p.reason
    END AS motivo_contratacao,

    -- 14. Modalidade de Contratação
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    -- 15. Pessoa a Ser Substituida
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- 16. Responsável
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,

    -- 17. ✨ Email Responsável Cliente (NOVO - Migration 048)
    r.custom_fields->>'Email do responsável por parte do cliente' AS email_responsavel_cliente,

    -- 18. Recrutador da vaga
    v.user_name AS recrutador_vaga,

    -- 19. Inicio Pendência com Cliente
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,

    -- 20. Fim Pendência com Cliente
    pp.datas_fim_pausa AS fim_pendencia_cliente,

    -- 21. SLA Pendência Cliente
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 22. Num Ciclos Pausa
    pp.num_ciclos AS num_ciclos_pausa,

    -- 23. Detalhamento Pausas
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 24. SLA Recrutamento
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,

    -- 25. Nome da Pessoa Contratada
    pct.talent_name AS nome_pessoa_contratada,

    -- 26. E-mail Pessoal
    pct.talent_email AS email_pessoal,

    -- 27. SLA Geral
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,

    -- 28. Meta Recrutamento (indicador_prazo)
    CASE
        WHEN v.sla_days_goal IS NOT NULL
            AND p.hired_at IS NOT NULL
            AND DATE(p.hired_at) >= DATE(p.opened_at)
        THEN
            CASE
                WHEN (DATE(p.hired_at) - DATE(p.opened_at))::INTEGER <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- Comentários
COMMENT ON VIEW vw_analise_posicoes IS 'View FINAL para análise de posições - Migration 047 (2026-02-10) + Migration 048 (2026-02-13). 28 campos. Campo motivo_contratacao traduzido. Campo email_responsavel_cliente adicionado ao lado de responsavel.';

COMMENT ON COLUMN vw_analise_posicoes.email_responsavel_cliente IS
'E-mail do responsável pela vaga por parte do cliente. Extraído de requisicoes.custom_fields ("Email do responsável por parte do cliente"). Adicionado em 2026-02-13 (Migration 048).';


-- ============================================================================
-- VALIDAÇÃO
-- ============================================================================

DO $$
DECLARE
    v_total_jade INTEGER;
    v_com_email_jade INTEGER;
    v_total_analise INTEGER;
    v_com_email_analise INTEGER;
BEGIN
    -- View vw_dados_jade
    SELECT COUNT(*) INTO v_total_jade FROM vw_dados_jade;

    SELECT COUNT(*) INTO v_com_email_jade
    FROM vw_dados_jade
    WHERE email_responsavel_cliente IS NOT NULL;

    -- View vw_analise_posicoes
    SELECT COUNT(*) INTO v_total_analise FROM vw_analise_posicoes;

    SELECT COUNT(*) INTO v_com_email_analise
    FROM vw_analise_posicoes
    WHERE email_responsavel_cliente IS NOT NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 048 - EMAIL RESPONSAVEL CLIENTE ADICIONADO';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'VIEW: vw_dados_jade';
    RAISE NOTICE '  Total de registros: %', v_total_jade;
    RAISE NOTICE '  Com email_responsavel_cliente: % (%.1f%%)',
        v_com_email_jade,
        CASE WHEN v_total_jade > 0 THEN (v_com_email_jade::float / v_total_jade * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE 'VIEW: vw_analise_posicoes';
    RAISE NOTICE '  Total de registros: %', v_total_analise;
    RAISE NOTICE '  Com email_responsavel_cliente: % (%.1f%%)',
        v_com_email_analise,
        CASE WHEN v_total_analise > 0 THEN (v_com_email_analise::float / v_total_analise * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE 'Campo extraido de: requisicoes.custom_fields->>''Email do responsavel por parte do cliente''';
    RAISE NOTICE 'Posicao: vw_dados_jade (col 15 - apos responsavel_requisicao)';
    RAISE NOTICE 'Posicao: vw_analise_posicoes (col 17 - apos responsavel)';
    RAISE NOTICE '================================================================================';
END $$;
