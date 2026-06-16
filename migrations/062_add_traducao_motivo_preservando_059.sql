/*
================================================================================
MIGRATION 062: Adiciona tradução de motivo PRESERVANDO estrutura da 059
================================================================================

Data: 2026-02-20

OBJETIVO:
  Adicionar tradução do campo motivo_status, PRESERVANDO TODA a estrutura
  da migration 059 (cálculos de dias úteis, lógica complexa, etc.)

ANTES (Migration 059):
  - 33 campos
  - Campo 33: motivo_status (código técnico, ex: 'waiting_schedule')
  - Usa calcular_dias_uteis() para SLAs
  - Lógica complexa de data_encerramento_ou_atualizacao

DEPOIS (Migration 062):
  - 34 campos
  - Campo 33: motivo_status (TRADUZIDO, ex: 'Cartas enviadas, aguardando retorno')
  - Campo 34: motivo_status_codigo (código técnico para referência)
  - MANTÉM toda estrutura, cálculos e lógica da 059

ALTERAÇÕES:
  - Adiciona LEFT JOIN com motivo_status_traducao
  - Campo motivo_status passa a mostrar tradução (ou código se não houver)
  - Novo campo motivo_status_codigo com código original

Base: Migration 059 (PRESERVANDO TUDO)

================================================================================
*/

-- ============================================================================
-- RECRIAR VIEW COM TRADUÇÃO
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
ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes  -- Código do motivo
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

    -- 7. Torre (Migration 056)
    COALESCE(
        get_custom_field_value(r.custom_fields, 'Torre'),
        v.custom_fields->>'Torre'
    ) AS torre,

    -- 8. Status
    COALESCE(usp.new_status, p.status) AS status_atual,

    -- 9. Data de Encerramento (Migration 056)
    CASE
        WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
            THEN DATE(p.hired_at)
        WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
             AND usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        WHEN COALESCE(usp.new_status, p.status) = 'open'
            THEN CURRENT_DATE
        WHEN COALESCE(usp.new_status, p.status) = 'paused'
             AND usp.data_ultima_mudanca IS NOT NULL
            THEN DATE(usp.data_ultima_mudanca)
        WHEN usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- 10. Motivo de cancelamento/paralisação
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,

    -- 11. Etapa Funil
    ue.stage_name AS etapa_funil,

    -- 12. Senioridade
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,

    -- 13. Motivo de contratação (Migration 047)
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

    -- 21. SLA Pendência Cliente (Migration 050)
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 22. Num Ciclos Pausa
    pp.num_ciclos AS num_ciclos_pausa,

    -- 23. Detalhamento Pausas
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 24. SLA Recrutamento (Migration 050, 056)
    CASE
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                     AND usp.data_ultima_mudanca IS NOT NULL
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                CASE
                    WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                        THEN DATE(p.hired_at)
                    WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                         AND usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN COALESCE(usp.new_status, p.status) = 'open'
                        THEN CURRENT_DATE
                    WHEN COALESCE(usp.new_status, p.status) = 'paused'
                         AND usp.data_ultima_mudanca IS NOT NULL
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    ELSE NULL
                END
            )
            - COALESCE(pp.total_dias_pausado, 0)
        ELSE NULL
    END AS sla_recrutamento,

    -- 25. Nome da Pessoa Contratada (Migration 055)
    t_contratado.name AS nome_pessoa_contratada,

    -- 26. E-mail Pessoal (Migration 055)
    t_contratado.email AS email_pessoal,

    -- 27. Modalidade de Contratação Requisição (Migration 049)
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 28. SLA Geral (Migration 050, 056)
    CASE
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                     AND usp.data_ultima_mudanca IS NOT NULL
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                CASE
                    WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                        THEN DATE(p.hired_at)
                    WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                         AND usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN COALESCE(usp.new_status, p.status) = 'open'
                        THEN CURRENT_DATE
                    WHEN COALESCE(usp.new_status, p.status) = 'paused'
                         AND usp.data_ultima_mudanca IS NOT NULL
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    ELSE NULL
                END
            )
        ELSE NULL
    END AS sla_geral,

    -- 29. Meta Recrutamento (indicador_prazo) (Migration 056)
    CASE
        WHEN v.sla_days_goal IS NULL
            THEN 'Sem Meta Definida'
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                     AND usp.data_ultima_mudanca IS NOT NULL
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            CASE
                WHEN calcular_dias_uteis(
                    DATE(p.opened_at),
                    CASE
                        WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                            THEN DATE(p.hired_at)
                        WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                             AND usp.data_ultima_mudanca IS NOT NULL
                             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                            THEN DATE(usp.data_ultima_mudanca)
                        WHEN COALESCE(usp.new_status, p.status) = 'open'
                            THEN CURRENT_DATE
                        WHEN COALESCE(usp.new_status, p.status) = 'paused'
                             AND usp.data_ultima_mudanca IS NOT NULL
                            THEN DATE(usp.data_ultima_mudanca)
                        WHEN usp.data_ultima_mudanca IS NOT NULL
                             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                            THEN DATE(usp.data_ultima_mudanca)
                        ELSE NULL
                    END
                ) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    -- 30. Empresa (Migration 056)
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,

    -- 31. Tipo de Posição (Migration 056)
    get_custom_field_value(r.custom_fields, 'Tipo de Serviço') AS tipo_posicao,

    -- 32. Nome do Workflow de Aprovação (Migration 057)
    r.approval_workflow->>'name' AS nome_workflow_aprovacao,

    -- 33. Motivo do Status TRADUZIDO (Migration 062)
    COALESCE(mst.descricao_pt, usp.notes) AS motivo_status,

    -- 34. Código do Motivo (Migration 062 - para referência)
    usp.notes AS motivo_status_codigo

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN talentos t_contratado ON t_contratado.inhire_id = p.talent_id
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
    -- JOIN com tabela de tradução (Migration 062)
    LEFT JOIN motivo_status_traducao mst ON mst.codigo = usp.notes AND mst.ativo = TRUE
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 062 (2026-02-20).
34 campos. Histórico completo:
  - 047: tradução motivo_contratacao
  - 048: email_responsavel_cliente
  - 049: modalidade_contratacao_req, empresa, tipo_posicao
  - 050: SLAs em dias úteis
  - 052: removido filtro stage_order > 9
  - 053: CORRIGIDO email/nome com COALESCE(talentos, candidaturas) + LEFT JOIN
  - 054: CORRIGIDO usando posicoes.talent_id (fix duplicação em vagas com múltiplas posições)
  - 055: REMOVIDO fallback problemático que usava candidaturas.vaga_id
  - 056: CORRIGIDO mapeamento JSONB (torre, empresa, tipo_posicao) + indicador_prazo para TODOS os status
  - 057: ADICIONADO nome_workflow_aprovacao
  - 059: ADICIONADO motivo_status (da position_timeline.notes)
  - 062: TRADUÇÃO de motivo_status PRESERVANDO toda estrutura da 059

CARACTERÍSTICAS:
  - Usa calcular_dias_uteis() para SLAs (dias úteis, não corridos)
  - Lógica complexa de data_encerramento validada
  - 34 campos estruturados e prontos para análise
  - Campo motivo_status traduzido em português
  - Campo motivo_status_codigo para referência técnica';

COMMENT ON COLUMN vw_analise_posicoes.motivo_status IS
'Descrição traduzida do motivo da última mudança de status.
Exemplos: "Mudança de estratégia", "Fechado com outro fornecedor", "Mudança de perfil".
Se não houver tradução, mostra o código original.
Cobertura: ~86% das posições. (Migration 062)';

COMMENT ON COLUMN vw_analise_posicoes.motivo_status_codigo IS
'Código técnico do motivo retornado pela API.
Exemplos: waiting_schedule, feedback_received_from_client, strategy_change.
Mantido para referência e debug. (Migration 062)';
