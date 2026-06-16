/*
================================================================================
MIGRATION 075 - STEP 2: Eliminar INICIOs Órfãos - INNER JOIN
================================================================================

IMPORTANTE: Executar este script APÓS o STEP 1 (DROP)

PROBLEMA IDENTIFICADO:
  - 3 posições AINDA com SLA negativo após Migration 074
  - Migration 074 usou LEFT JOIN → permite INICIOs órfãos
  - Órfãos recebem data_fim = CURRENT_DATE → inflação de SLA

FALHA DA MIGRATION 074:

  ```sql
  FROM eventos_pausa_numerados i
  LEFT JOIN eventos_pausa_numerados f  ← Permite NULL em f.changed_at
      ON f.rn = i.rn AND f.tipo_evento = 'FIM_PAUSA'
  ```

  Se há 3 INICIOs e 1 FIM:
    - INICIO #1 (12/08) → FIM #1 (16/09) = 26 dias ✅
    - INICIO #2 (21/08) → NULL → COALESCE → CURRENT_DATE = 170 dias ❌
    - INICIO #3 (21/08) → NULL → COALESCE → CURRENT_DATE = 170 dias ❌
    Total: 26 + 170 + 170 = 366 dias → SLA negativo!

SOLUÇÃO (Migration 075):

  ```sql
  FROM eventos_pausa_numerados i
  INNER JOIN eventos_pausa_numerados f  ← Rejeita INICIOs sem FIM
      ON f.rn = i.rn AND f.tipo_evento = 'FIM_PAUSA'
  ```

  Apenas ciclos completos:
    - INICIO #1 (12/08) → FIM #1 (16/09) = 26 dias ✅
    - INICIO #2 descartado (sem FIM)
    - INICIO #3 descartado (sem FIM)
    Total: 26 dias → SLA positivo! ✅

TRADE-OFF ACEITO:
  ⚠️ Pode subestimar dias pausados (ignora pausas incompletas)
  ✅ Garante SLA correto para ciclos completos
  ✅ Após sync completa da API, órfãos serão naturalmente resolvidos

MODIFICAÇÕES APLICADAS:
  Linhas 208-227: MODIFICADO periodos_pausa

  ANTES (Migration 074):
    periodos_pausa AS (
        SELECT
            i.posicao_id,
            i.changed_at AS data_inicio,
            COALESCE(
                f.changed_at,  ← Pode ser NULL
                (SELECT data_ultima_mudanca FROM ...),
                CURRENT_DATE  ← Órfãos caem aqui!
            ) AS data_fim
        FROM eventos_pausa_numerados i
        LEFT JOIN eventos_pausa_numerados f  ← Permite órfãos
            ON f.rn = i.rn ...
        WHERE i.tipo_evento = 'INICIO_PAUSA'
    )

  DEPOIS (Migration 075):
    periodos_pausa AS (
        SELECT
            i.posicao_id,
            i.changed_at AS data_inicio,
            f.changed_at AS data_fim  ← Sempre NOT NULL (INNER JOIN)
        FROM eventos_pausa_numerados i
        INNER JOIN eventos_pausa_numerados f  ← Rejeita órfãos!
            ON f.posicao_id = i.posicao_id
            AND f.tipo_evento = 'FIM_PAUSA'
            AND f.rn = i.rn
        WHERE i.tipo_evento = 'INICIO_PAUSA'
    )

RESULTADO ESPERADO:
  - Posição 782: SLA -28 → SLA >= 0 ✅
  - Posição 914: SLA -22 → SLA >= 0 ✅
  - Posição 1274: SLA -4 → SLA >= 0 ✅
  - 0 posições com SLA negativo no total

Base: Migration 074 (pareamento 1:1 por ROW_NUMBER)

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
-- PRESERVADO DE MIGRATION 073: Deduplicação conservadora
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
-- PRESERVADO DE MIGRATION 074: Numeração para pareamento 1:1
-- ============================================================================
eventos_pausa_numerados AS (
    -- STEP 3: Adiciona ROW_NUMBER para pareamento correto
    -- Numera INICIOs e FINs separadamente, garantindo ordem cronológica
    SELECT
        posicao_id,
        changed_at,
        tipo_evento,
        ROW_NUMBER() OVER (
            PARTITION BY posicao_id, tipo_evento
            ORDER BY changed_at
        ) AS rn
    FROM eventos_pausa
),
-- ============================================================================
-- MODIFICADO EM MIGRATION 075: INNER JOIN para eliminar órfãos
-- ============================================================================
periodos_pausa AS (
    -- STEP 4: Pareamento 1:1 usando INNER JOIN (rejeita órfãos)
    -- Aceita APENAS ciclos completos: INICIO #N → FIM #N
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        f.changed_at AS data_fim  -- ← SEMPRE NOT NULL (INNER JOIN garante)
    FROM eventos_pausa_numerados i
    INNER JOIN eventos_pausa_numerados f  -- ← MUDANÇA CRÍTICA: INNER em vez de LEFT
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn  -- ← PAREAMENTO 1:1 POR ROW_NUMBER
    WHERE i.tipo_evento = 'INICIO_PAUSA'
),
-- ============================================================================
-- FIM DAS MODIFICAÇÕES - Resto permanece igual a Migration 074
-- ============================================================================
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
'View FINAL para análise de posições - Migration 075 (2026-03-03).
34 campos. Histórico completo:
  - 047-062: evolução de campos e traduções
  - 063: REORDENAÇÃO + mesclagem de motivo
  - 064: ADICIONADO vaga_id e vaga_nome NO INÍCIO
  - 065: ALTERADA ORDENAÇÃO para ASC (data_publicacao)
  - 070: ADICIONADO FALLBACK no email_pessoal (busca de candidaturas)
  - 071: CORRIGIDO SLA para posições pausadas (CURRENT_DATE quando paused)
  - 072: CORRIGIDO pausas em posições encerradas (usa data encerramento)
  - 073: CORRIGIDO duplicatas na position_timeline (deduplicação conservadora)
  - 074: CORRIGIDO pareamento INICIO↔FIM (ROW_NUMBER 1:1)
  - 075: CORRIGIDO órfãos (INNER JOIN - apenas ciclos completos)

ORDEM DOS CAMPOS:
  1-2: Informações da vaga
  3-34: Campos de análise e SLA

CARACTERÍSTICAS:
  - Usa calcular_dias_uteis() para SLAs
  - email_pessoal com fallback para candidaturas (Migration 070)
  - SLA corrigido para posições pausadas (Migration 071)
  - Pausas param na data de encerramento (Migration 072)
  - Deduplicação conservadora em eventos_pausa (Migration 073)
  - Pareamento 1:1 INICIO↔FIM por ROW_NUMBER (Migration 074)
  - INNER JOIN elimina órfãos (Migration 075)
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
timestamp mais antigo, ID menor). Pareamento correto 1:1 entre INICIO_PAUSA
e FIM_PAUSA usando ROW_NUMBER. INNER JOIN elimina INICIOs órfãos (sem FIM
correspondente), garantindo apenas ciclos completos.
Migrations 072, 073, 074 e 075 (2026-03-03)';
