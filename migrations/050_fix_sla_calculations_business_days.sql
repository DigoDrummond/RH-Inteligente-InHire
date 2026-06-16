/*
================================================================================
MIGRATION 050: Corrigir Cálculos de SLA para Usar Dias Úteis
================================================================================

Data: 2026-02-13
Descrição:
  Atualiza a view vw_analise_posicoes para corrigir os cálculos de SLA
  usando dias úteis (excluindo fins de semana e feriados de BH/MG).

Regras Corretas:
  sla_geral = data_encerramento_ou_atualizacao - data_publicacao
  sla_pendencia_cliente = soma dos períodos de pausa
  sla_recrutamento = sla_geral - sla_pendencia_cliente

IMPORTANTE:
  - Todos os SLAs devem usar DIAS ÚTEIS
  - Usa função calcular_dias_uteis() (criada na migration 032)
  - Exclui sábados, domingos e feriados da tabela 'feriados'

Mudanças:
  - sla_recrutamento: ANTES calculava (data_publicacao - data_abertura)
                      AGORA calcula (sla_geral - sla_pendencia_cliente)
  - sla_geral: ANTES usava dias corridos
               AGORA usa dias úteis
  - sla_pendencia_cliente: ANTES somava períodos em dias corridos
                          AGORA soma períodos em dias úteis

================================================================================
*/

-- ============================================================================
-- 1. ATUALIZAR VIEW vw_analise_posicoes
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
        -- ✨ MUDANÇA: Calcular soma de dias ÚTEIS (não corridos)
        SUM(calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))) AS total_dias_pausado,
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
            -- ✨ MUDANÇA: Mostrar dias úteis nos detalhes
            ' (' || calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))::text || 'd úteis)',
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

    -- 21. ✨ SLA Pendência Cliente (CORRIGIDO - dias úteis)
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 22. Num Ciclos Pausa
    pp.num_ciclos AS num_ciclos_pausa,

    -- 23. Detalhamento Pausas
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 24. ✨ SLA Recrutamento (CORRIGIDO - sla_geral - sla_pendencia_cliente)
    --     ANTES: (data_publicacao - data_abertura)
    --     AGORA: sla_geral - sla_pendencia_cliente
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN
            -- Calcular SLA geral em dias úteis
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
            )
            -- Subtrair pendências com cliente
            - COALESCE(pp.total_dias_pausado, 0)
        ELSE NULL
    END AS sla_recrutamento,

    -- 25. Nome da Pessoa Contratada
    pct.talent_name AS nome_pessoa_contratada,

    -- 26. E-mail Pessoal
    pct.talent_email AS email_pessoal,

    -- 27. Modalidade de Contratação Requisição (Migration 049)
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 28. ✨ SLA Geral (CORRIGIDO - dias úteis)
    --     ANTES: dias corridos
    --     AGORA: dias úteis
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
            )
        ELSE NULL
    END AS sla_geral,

    -- 29. Meta Recrutamento (indicador_prazo)
    CASE
        WHEN v.sla_days_goal IS NOT NULL
            AND p.hired_at IS NOT NULL
            AND DATE(p.hired_at) >= DATE(p.opened_at)
        THEN
            CASE
                -- ✨ MUDANÇA: Comparar usando dias úteis
                WHEN calcular_dias_uteis(DATE(p.opened_at), DATE(p.hired_at)) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    -- 30. Empresa (Time Rethink) (Migration 049)
    get_custom_field_value(r.custom_fields, 'Time Rethink') AS empresa,

    -- 31. Tipo de Posição (Migration 049)
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
'View FINAL para análise de posições - Migration 050 (2026-02-13).
31 campos. SLAs CORRIGIDOS para usar dias úteis (excluindo fins de semana e feriados).
Histórico: Migration 047 (tradução motivo), 048 (email), 049 (empresa/tipo), 050 (SLAs dias úteis).';

COMMENT ON COLUMN vw_analise_posicoes.sla_recrutamento IS
'Dias úteis de recrutamento (SLA Geral - SLA Pendência Cliente). Exclui fins de semana e feriados. Corrigido em Migration 050 (2026-02-13).';

COMMENT ON COLUMN vw_analise_posicoes.sla_geral IS
'Dias úteis totais do processo (data_encerramento - data_abertura). Exclui fins de semana e feriados. Corrigido em Migration 050 (2026-02-13).';

COMMENT ON COLUMN vw_analise_posicoes.sla_pendencia_cliente IS
'Soma dos dias úteis de pausa (pendências com cliente). Exclui fins de semana e feriados. Corrigido em Migration 050 (2026-02-13).';


-- ============================================================================
-- VALIDAÇÃO
-- ============================================================================

DO $$
DECLARE
    v_total INTEGER;
    v_com_sla_geral INTEGER;
    v_com_sla_recrutamento INTEGER;
    v_exemplo RECORD;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    SELECT COUNT(*) INTO v_com_sla_geral
    FROM vw_analise_posicoes
    WHERE sla_geral IS NOT NULL;

    SELECT COUNT(*) INTO v_com_sla_recrutamento
    FROM vw_analise_posicoes
    WHERE sla_recrutamento IS NOT NULL;

    RAISE NOTICE '===============================================================================';
    RAISE NOTICE 'MIGRATION 050 - SLAs CORRIGIDOS PARA DIAS UTEIS';
    RAISE NOTICE '===============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'VIEW: vw_analise_posicoes';
    RAISE NOTICE '  Total de registros: %', v_total;
    RAISE NOTICE '  Com SLA Geral (dias uteis): % (%.1f%%)',
        v_com_sla_geral,
        CASE WHEN v_total > 0 THEN (v_com_sla_geral::float / v_total * 100) ELSE 0 END;
    RAISE NOTICE '  Com SLA Recrutamento (dias uteis): % (%.1f%%)',
        v_com_sla_recrutamento,
        CASE WHEN v_total > 0 THEN (v_com_sla_recrutamento::float / v_total * 100) ELSE 0 END;
    RAISE NOTICE '';
    RAISE NOTICE 'Formula SLA Recrutamento: sla_geral - sla_pendencia_cliente';
    RAISE NOTICE 'Todos os SLAs agora usam dias uteis (excluindo sabados, domingos e feriados)';
    RAISE NOTICE '';

    -- Mostrar exemplo de cálculo
    SELECT
        id_position,
        cargo,
        sla_geral,
        sla_pendencia_cliente,
        sla_recrutamento
    INTO v_exemplo
    FROM vw_analise_posicoes
    WHERE sla_recrutamento IS NOT NULL
    LIMIT 1;

    IF FOUND THEN
        RAISE NOTICE 'Exemplo de calculo (Posicao %):',  v_exemplo.id_position;
        RAISE NOTICE '  Cargo: %', v_exemplo.cargo;
        RAISE NOTICE '  SLA Geral: % dias uteis', v_exemplo.sla_geral;
        RAISE NOTICE '  SLA Pendencia Cliente: % dias uteis', COALESCE(v_exemplo.sla_pendencia_cliente, 0);
        RAISE NOTICE '  SLA Recrutamento: % dias uteis', v_exemplo.sla_recrutamento;
        RAISE NOTICE '  Validacao: % - % = %',
            v_exemplo.sla_geral,
            COALESCE(v_exemplo.sla_pendencia_cliente, 0),
            v_exemplo.sla_recrutamento;
    END IF;

    RAISE NOTICE '===============================================================================';
END $$;
