/*
================================================================================
MIGRATION 073 - STEP 2: Corrigir Duplicatas na Position Timeline
================================================================================

IMPORTANTE: Executar este script APÓS o STEP 1 (DROP)

PROBLEMA IDENTIFICADO:
  - 3 posições com SLA negativo após Migrations 071 e 072
  - Posições: 782, 914, 1274
  - Eventos duplicados na position_timeline causando inflação de dias pausados

ANÁLISE (Posição 782):
  Total eventos: 8
  Eventos com sequência quebrada: 6 (75%)

  Duplicatas identificadas:
    - IDs 3320 e 5355: NULL→open em 30/07/2025 17:38:14
    - IDs 3321 e 5356: open→paused em 30/07/2025 17:38:18
    - IDs 3322 e 5357: paused→open em 16/09/2025 08:03:03

  Problema: 3 INICIO_PAUSA contados = 64 dias pausados
  Esperado: 1 INICIO_PAUSA = ~26 dias pausados

CAUSA RAIZ:
  - Eventos duplicados com mesmo timestamp mas IDs diferentes
  - Eventos com previous_status=NULL criando transições fantasmas
  - Falta de evento paused→open entre duas pausas

SOLUÇÃO:
  Deduplicação conservadora usando DISTINCT ON no CTE eventos_pausa:

  1. Criar eventos_pausa_raw com todos os dados (incluindo id e notes)
  2. Aplicar DISTINCT ON agrupando por:
     - posicao_id
     - previous_status
     - new_status
     - DATE(changed_at)

  3. Priorização (ORDER BY):
     a) Eventos com notes preenchido (informação adicional)
     b) Timestamp mais antigo (primeiro registro)
     c) ID menor (registro original)

MODIFICAÇÕES APLICADAS:
  Linhas 70-104: Deduplicação conservadora em eventos_pausa

  ANTES (Migration 072):
    eventos_pausa AS (
        SELECT DISTINCT
            posicao_id, changed_at, previous_status, new_status, tipo_evento
        FROM position_timeline
        WHERE ...
    )

  DEPOIS (Migration 073):
    eventos_pausa_raw AS (
        -- Busca todos os eventos, incluindo id e notes para priorização
        SELECT ... FROM position_timeline WHERE ...
    ),
    eventos_pausa AS (
        -- Deduplicação conservadora
        SELECT DISTINCT ON (posicao_id, previous_status, new_status, DATE(changed_at))
            posicao_id, changed_at, previous_status, new_status, tipo_evento
        FROM eventos_pausa_raw
        ORDER BY ... (priorizando events com notes, mais antigos, ID menor)
    )

RESULTADO ESPERADO:
  - Posição 782: 64 dias → ~26 dias (redução de ~60%)
  - Posição 914: 83 dias → valor correto
  - Posição 1274: 21 dias → valor correto
  - 0 posições com SLA negativo

Base: Migration 072 (correção de pausas em posições encerradas)

================================================================================
*/

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
        notes
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
-- ============================================================================
-- MODIFICADO EM MIGRATION 073: Deduplicação conservadora
-- ============================================================================
eventos_pausa_raw AS (
    -- STEP 1: Buscar todos os eventos de pausa, incluindo id e notes para priorização
    SELECT
        id,
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        notes,
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
eventos_pausa AS (
    -- STEP 2: Deduplicação conservadora usando DISTINCT ON
    -- Agrupa por: posição + transição de status + data (sem hora)
    -- Prioriza: eventos com notes > timestamp mais antigo > ID menor
    SELECT DISTINCT ON (
        posicao_id,
        COALESCE(previous_status, 'NULL'),  -- Tratar NULL como string para agrupamento
        new_status,
        DATE(changed_at)
    )
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        tipo_evento
    FROM eventos_pausa_raw
    ORDER BY
        posicao_id,
        COALESCE(previous_status, 'NULL'),
        new_status,
        DATE(changed_at),
        CASE WHEN notes IS NOT NULL AND notes != '' THEN 0 ELSE 1 END,  -- Eventos com notes primeiro
        changed_at ASC,  -- Timestamp mais antigo primeiro
        id ASC  -- ID menor primeiro (registro original)
),
-- ============================================================================
-- FIM DA MODIFICAÇÃO - Resto permanece igual a Migration 072
-- ============================================================================
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
            (SELECT usp.data_ultima_mudanca              -- PRESERVADO DE MIGRATION 072
             FROM ultimo_status_posicao usp
             WHERE usp.posicao_id = inicio.posicao_id
               AND usp.new_status IN ('canceled', 'closed')
            ),
            CURRENT_DATE  -- Só usa hoje se ainda está paused
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
    -- ========================================
    -- CAMPOS DA VAGA (Migration 064)
    -- ========================================

    -- 1. ID da Vaga
    v.id AS vaga_id,

    -- 2. Nome da Vaga
    v.name AS vaga_nome,

    -- ========================================
    -- CAMPOS DA POSIÇÃO
    -- ========================================

    -- 3. ID da Posição
    p.id AS id_position,

    -- 4. Cargo
    v.name AS cargo,

    -- 5. Data de abertura
    DATE(r.requested_at) AS data_abertura,

    -- 6. Data da publicação
    DATE(p.opened_at) AS data_publicacao,

    -- 7. Prazo do Processo Seletivo
    v.sla_days_goal AS prazo_processo_seletivo,

    -- 8. Cliente
    c.name AS cliente,

    -- 9. Torre
    COALESCE(
        get_custom_field_value(r.custom_fields, 'Torre'),
        v.custom_fields->>'Torre'
    ) AS torre,

    -- 10. Status
    COALESCE(usp.new_status, p.status) AS status_atual,

    -- 11. Data de Encerramento -- PRESERVADO DE MIGRATION 071
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
            THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
        WHEN usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- 12. Motivo (mesclado)
    CASE
        WHEN v.custom_fields->>'Motivo de Cancelamento' IS NOT NULL
             AND COALESCE(mst.descricao_pt, usp.notes) IS NOT NULL
        THEN v.custom_fields->>'Motivo de Cancelamento' || ' | ' || COALESCE(mst.descricao_pt, usp.notes)
        ELSE COALESCE(
            v.custom_fields->>'Motivo de Cancelamento',
            COALESCE(mst.descricao_pt, usp.notes)
        )
    END AS motivo_cancelamento_paralisacao,

    -- 13. Etapa Funil
    ue.stage_name AS etapa_funil,

    -- 14. Senioridade
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,

    -- 15. Motivo de contratação
    CASE p.reason
        WHEN 'expansion' THEN 'Aumento de quadro'
        WHEN 'replacement' THEN 'Substituição'
        WHEN 'other' THEN 'Outros'
        WHEN 'new-position' THEN 'Nova posição'
        WHEN 'turnover' THEN 'Turnover'
        WHEN 'internal-transfer' THEN 'Transferência interna'
        ELSE p.reason
    END AS motivo_contratacao,

    -- 16. Modalidade de Contratação
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    -- 17. Pessoa a Ser Substituida
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- 18. Responsável
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,

    -- 19. Email Responsável Cliente
    get_custom_field_value(r.custom_fields, 'Email do responsável por parte do cliente') AS email_responsavel_cliente,

    -- 20. Recrutador da vaga
    v.user_name AS recrutador_vaga,

    -- 21. Inicio Pendência com Cliente
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,

    -- 22. Fim Pendência com Cliente
    pp.datas_fim_pausa AS fim_pendencia_cliente,

    -- 23. SLA Pendência Cliente
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 24. Num Ciclos Pausa
    pp.num_ciclos AS num_ciclos_pausa,

    -- 25. Detalhamento Pausas
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 26. SLA Recrutamento -- PRESERVADO DE MIGRATION 071
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
                    THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
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
                        THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    ELSE NULL
                END
            )
            - COALESCE(pp.total_dias_pausado, 0)
        ELSE NULL
    END AS sla_recrutamento,

    -- 27. Nome da Pessoa Contratada
    t_contratado.name AS nome_pessoa_contratada,

    -- 28. E-mail Pessoal -- PRESERVADO DE MIGRATION 070
    COALESCE(
        t_contratado.email,
        (SELECT cd.talent_email
         FROM candidaturas cd
         WHERE cd.vaga_id = p.vaga_id
         AND cd.stage_name = 'Contratação'
         LIMIT 1)
    ) AS email_pessoal,

    -- 29. Modalidade de Contratação Requisição
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 30. SLA Geral -- PRESERVADO DE MIGRATION 071
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
                    THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
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
                        THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
                END
            )
        ELSE NULL
    END AS sla_geral,

    -- 31. Meta Recrutamento -- PRESERVADO DE MIGRATION 071
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
                    THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
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
                            THEN CURRENT_DATE  -- MODIFICADO EM MIGRATION 071
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

    -- 32. Empresa
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,

    -- 33. Tipo de Posição
    get_custom_field_value(r.custom_fields, 'Tipo de Serviço') AS tipo_posicao,

    -- 34. Nome do Workflow de Aprovação
    r.approval_workflow->>'name' AS nome_workflow_aprovacao

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN talentos t_contratado ON t_contratado.inhire_id = p.talent_id
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
    LEFT JOIN motivo_status_traducao mst ON mst.codigo = usp.notes AND mst.ativo = TRUE
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at ASC NULLS LAST;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 073 (2026-03-03).
34 campos. Histórico completo:
  - 047-062: evolução de campos e traduções
  - 063: REORDENAÇÃO + mesclagem de motivo
  - 064: ADICIONADO vaga_id e vaga_nome NO INÍCIO
  - 065: ALTERADA ORDENAÇÃO para ASC (data_publicacao)
  - 070: ADICIONADO FALLBACK no email_pessoal (busca de candidaturas)
  - 071: CORRIGIDO SLA para posições pausadas (CURRENT_DATE quando paused)
  - 072: CORRIGIDO pausas em posições encerradas (usa data encerramento)
  - 073: CORRIGIDO duplicatas na position_timeline (deduplicação conservadora)

ORDEM DOS CAMPOS:
  1-2: Informações da vaga
  3-34: Campos de análise e SLA

CARACTERÍSTICAS:
  - Usa calcular_dias_uteis() para SLAs
  - email_pessoal com fallback para candidaturas (Migration 070)
  - SLA corrigido para posições pausadas (Migration 071)
  - Pausas param na data de encerramento (Migration 072)
  - Deduplicação conservadora em eventos_pausa (Migration 073)
  - 34 campos estruturados';

COMMENT ON COLUMN vw_analise_posicoes.email_pessoal IS
'E-mail pessoal do talento contratado. Busca primeiro em talentos.email,
se NULL busca em candidaturas.talent_email (stage_name = Contratação).
Migration 070 (2026-03-03)';

COMMENT ON COLUMN vw_analise_posicoes.sla_recrutamento IS
'SLA de recrutamento em dias úteis (excluindo pausas). Para status paused,
usa CURRENT_DATE como data final para evitar valores negativos.
Migration 071 (2026-03-03)';

COMMENT ON COLUMN vw_analise_posicoes.sla_geral IS
'SLA geral em dias úteis (incluindo pausas). Para status paused,
usa CURRENT_DATE como data final para evitar valores negativos.
Migration 071 (2026-03-03)';

COMMENT ON COLUMN vw_analise_posicoes.sla_pendencia_cliente IS
'SLA de pendência com cliente em dias úteis. Para posições canceladas/fechadas
com pausas sem fim explícito, usa a data do encerramento. Eventos duplicados
são eliminados via deduplicação conservadora (prioriza eventos com notes,
timestamp mais antigo, ID menor).
Migrations 072 e 073 (2026-03-03)';
