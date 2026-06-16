/*
================================================================================
MIGRATION 049: Adicionar Empresa, Tipo de Posição e Modalidade de Contratação
================================================================================

Data: 2026-02-13
Descrição:
  Adiciona 3 novos campos na view vw_analise_posicoes extraídos de
  requisicoes.custom_fields (array de objetos JSONB):

  1. modalidade_contratacao_req - após email_pessoal (posição 27)
     Campo: "Modalidade de Contratação" em requisicoes.custom_fields

  2. empresa - no final (posição 29)
     Campo: "Time Rethink" em requisicoes.custom_fields

  3. tipo_posicao - no final (posição 30)
     Campo: "Tipo de Posição" em requisicoes.custom_fields

IMPORTANTE: requisicoes.custom_fields é um array de objetos:
[
  {
    "name": "Time Rethink",
    "value": "Product",
    "type": "select",
    ...
  }
]

Precisamos buscar pelo "name" e retornar o "value".

================================================================================
*/

-- ============================================================================
-- 1. CRIAR FUNÇÃO AUXILIAR PARA EXTRAIR VALORES DE CUSTOM_FIELDS
-- ============================================================================

-- Função para tipo JSON
CREATE OR REPLACE FUNCTION get_custom_field_value(
    custom_fields JSON,
    field_name TEXT
) RETURNS TEXT AS $$
DECLARE
    field_type TEXT;
BEGIN
    -- Retorna o valor do campo com o nome especificado
    -- custom_fields pode ser:
    --   1. Array de objetos: [{"name": "...", "value": "..."}]
    --   2. Objeto direto: {"Campo": "valor"}

    -- Verificar tipo do JSON
    field_type := json_typeof(custom_fields);

    -- Se for array, buscar pelo objeto com "name" = field_name
    IF field_type = 'array' THEN
        RETURN (
            SELECT elem->>'value'
            FROM json_array_elements(custom_fields) elem
            WHERE elem->>'name' = field_name
            LIMIT 1
        );
    -- Se for object, buscar diretamente pela chave
    ELSIF field_type = 'object' THEN
        RETURN custom_fields->>field_name;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Função para tipo JSONB (sobrecarga)
CREATE OR REPLACE FUNCTION get_custom_field_value(
    custom_fields JSONB,
    field_name TEXT
) RETURNS TEXT AS $$
DECLARE
    field_type TEXT;
BEGIN
    -- Retorna o valor do campo com o nome especificado
    -- custom_fields pode ser:
    --   1. Array de objetos: [{"name": "...", "value": "..."}]
    --   2. Objeto direto: {"Campo": "valor"}

    -- Verificar tipo do JSONB
    field_type := jsonb_typeof(custom_fields);

    -- Se for array, buscar pelo objeto com "name" = field_name
    IF field_type = 'array' THEN
        RETURN (
            SELECT elem->>'value'
            FROM jsonb_array_elements(custom_fields) elem
            WHERE elem->>'name' = field_name
            LIMIT 1
        );
    -- Se for object, buscar diretamente pela chave
    ELSIF field_type = 'object' THEN
        RETURN custom_fields->>field_name;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_custom_field_value(JSON, TEXT) IS
'Extrai o valor de um campo específico de custom_fields (JSON).
Suporta dois formatos:
  - Array: [{"name": "Campo", "value": "Valor"}]
  - Object: {"Campo": "Valor"}
Criada em Migration 049 (2026-02-13).';

COMMENT ON FUNCTION get_custom_field_value(JSONB, TEXT) IS
'Extrai o valor de um campo específico de custom_fields (JSONB).
Suporta dois formatos:
  - Array: [{"name": "Campo", "value": "Valor"}]
  - Object: {"Campo": "Valor"}
Criada em Migration 049 (2026-02-13).';


-- ============================================================================
-- 2. ATUALIZAR VIEW vw_analise_posicoes
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

    -- 13. Motivo de contratação (TRADUZIDO - Migration 047)
    CASE p.reason
        WHEN 'expansion' THEN 'Aumento de quadro'
        WHEN 'replacement' THEN 'Substituição'
        WHEN 'other' THEN 'Outros'
        WHEN 'new-position' THEN 'Nova posição'
        WHEN 'turnover' THEN 'Turnover'
        WHEN 'internal-transfer' THEN 'Transferência interna'
        ELSE p.reason
    END AS motivo_contratacao,

    -- 14. Modalidade de Contratação (de vagas.custom_fields)
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    -- 15. Pessoa a Ser Substituida
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- 16. Responsável
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,

    -- 17. Email Responsável Cliente (Migration 048)
    get_custom_field_value(r.custom_fields, 'Email do responsável por parte do cliente') AS email_responsavel_cliente,

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

    -- 27. ✨ Modalidade de Contratação Requisição (NOVO - Migration 049)
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 28. SLA Geral
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,

    -- 29. Meta Recrutamento (indicador_prazo)
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
    END AS indicador_prazo,

    -- 30. ✨ Empresa (Time Rethink) (NOVO - Migration 049)
    get_custom_field_value(r.custom_fields, 'Time Rethink') AS empresa,

    -- 31. ✨ Tipo de Posição (NOVO - Migration 049)
    get_custom_field_value(r.custom_fields, 'Tipo de Posição') AS tipo_posicao

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
COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 049 (2026-02-13).
31 campos. Adicionados: modalidade_contratacao_req (col 27), empresa (col 30), tipo_posicao (col 31).
Histórico: Migration 047 (tradução motivo_contratacao), Migration 048 (email_responsavel_cliente).';

COMMENT ON COLUMN vw_analise_posicoes.modalidade_contratacao_req IS
'Modalidade de contratação extraída de requisicoes.custom_fields ("Modalidade de Contratação"). Adicionado em 2026-02-13 (Migration 049).';

COMMENT ON COLUMN vw_analise_posicoes.empresa IS
'Empresa/Time extraído de requisicoes.custom_fields ("Time Rethink"). Adicionado em 2026-02-13 (Migration 049).';

COMMENT ON COLUMN vw_analise_posicoes.tipo_posicao IS
'Tipo de posição extraído de requisicoes.custom_fields ("Tipo de Posição"). Ex: Alocação, Contratação. Adicionado em 2026-02-13 (Migration 049).';


-- ============================================================================
-- VALIDAÇÃO
-- ============================================================================

DO $$
DECLARE
    v_total INTEGER;
    v_com_modalidade_req INTEGER;
    v_com_empresa INTEGER;
    v_com_tipo_posicao INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    SELECT COUNT(*) INTO v_com_modalidade_req
    FROM vw_analise_posicoes
    WHERE modalidade_contratacao_req IS NOT NULL;

    SELECT COUNT(*) INTO v_com_empresa
    FROM vw_analise_posicoes
    WHERE empresa IS NOT NULL;

    SELECT COUNT(*) INTO v_com_tipo_posicao
    FROM vw_analise_posicoes
    WHERE tipo_posicao IS NOT NULL;

    RAISE NOTICE '===============================================================================';
    RAISE NOTICE 'MIGRATION 049 - CAMPOS ADICIONADOS COM SUCESSO';
    RAISE NOTICE '===============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'VIEW: vw_analise_posicoes';
    RAISE NOTICE '  Total de registros: %', v_total;
    RAISE NOTICE '';
    RAISE NOTICE '  Campo modalidade_contratacao_req (posição 27):';
    RAISE NOTICE '    Registros com valor: % (%.1f%%)',
        v_com_modalidade_req,
        CASE WHEN v_total > 0 THEN (v_com_modalidade_req::float / v_total * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE '  Campo empresa - Time Rethink (posição 30):';
    RAISE NOTICE '    Registros com valor: % (%.1f%%)',
        v_com_empresa,
        CASE WHEN v_total > 0 THEN (v_com_empresa::float / v_total * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE '  Campo tipo_posicao (posição 31):';
    RAISE NOTICE '    Registros com valor: % (%.1f%%)',
        v_com_tipo_posicao,
        CASE WHEN v_total > 0 THEN (v_com_tipo_posicao::float / v_total * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE 'Fonte: requisicoes.custom_fields (array de objetos JSONB)';
    RAISE NOTICE 'Função auxiliar: get_custom_field_value(custom_fields, field_name)';
    RAISE NOTICE '===============================================================================';
END $$;


-- ============================================================================
-- TESTE RÁPIDO
-- ============================================================================

-- Verificar uma amostra dos novos campos
-- SELECT
--     id_position,
--     cargo,
--     modalidade_contratacao_req,
--     empresa,
--     tipo_posicao
-- FROM vw_analise_posicoes
-- WHERE empresa IS NOT NULL OR tipo_posicao IS NOT NULL
-- LIMIT 10;
