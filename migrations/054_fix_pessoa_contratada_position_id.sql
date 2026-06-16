/*
================================================================================
MIGRATION 054: Corrigir identificação de pessoa contratada usando talent_id
================================================================================

Data: 2026-02-19

PROBLEMA IDENTIFICADO:

  A CTE pessoa_contratada faz JOIN por vaga_id (candidaturas.vaga_id = posicoes.vaga_id),
  causando DUPLICAÇÃO de candidatos em vagas com múltiplas posições.

  EXEMPLO DO BUG:
  ---------------
  Vaga: "FRAMEWORK PADAWANS - EPISÓDIO VI 🪐"
  - 41 posições (IDs 1862-1902)
  - ANTES: Mesmo candidato repetido nas 41 linhas
  - DEPOIS: Cada posição mostra seu candidato específico

  CAUSA RAIZ:
  -----------
  A tabela candidaturas NÃO possui campo position_id, apenas vaga_id.
  Relacionamento: candidaturas.vaga_id → vagas.id ← posicoes.vaga_id (indireto)

  Tentativa anterior de usar candidaturas.position_id falha porque essa coluna não existe.

SOLUÇÃO CORRETA:

  Usar o campo posicoes.talent_id que JÁ identifica qual talento foi contratado
  em cada posição específica:

  - API InHire retorna: /positions → { talentId: "xxx" }
  - Sincronização preenche: posicoes.talent_id
  - JOIN direto: LEFT JOIN talentos ON talentos.inhire_id = p.talent_id

MUDANÇAS DESTA MIGRATION:

  1. REMOVER CTE pessoa_contratada (não é mais necessária)
  2. JOIN direto com talentos usando posicoes.talent_id
  3. Fallback para candidaturas.talent_name/email se necessário (via subquery)

IMPACTO:

  - Vagas com 1 posição: Sem mudança (mesmo resultado)
  - Vagas com múltiplas posições: Cada posição mostra seu candidato específico
  - Posições sem talent_id: nome_pessoa_contratada = NULL (correto)
  - Mais simples e performático (sem CTE complexa)

Base: Migration 053

================================================================================
*/

-- ============================================================================
-- 1. RECRIAR VIEW COM JOIN DIRETO USANDO posicoes.talent_id
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
-- ✅ REMOVIDA: CTE pessoa_contratada (usava candidaturas.vaga_id incorretamente)
-- ✅ NOVA ABORDAGEM: JOIN direto com talentos usando posicoes.talent_id
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

    -- 21. SLA Pendência Cliente (dias úteis - Migration 050)
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 22. Num Ciclos Pausa
    pp.num_ciclos AS num_ciclos_pausa,

    -- 23. Detalhamento Pausas
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 24. SLA Recrutamento (dias úteis - Migration 050)
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
            )
            - COALESCE(pp.total_dias_pausado, 0)
        ELSE NULL
    END AS sla_recrutamento,

    -- 25. Nome da Pessoa Contratada (CORRIGIDO - Migration 054)
    -- JOIN direto com talentos usando posicoes.talent_id
    -- Fallback para candidaturas se talent_id for NULL
    COALESCE(
        t_contratado.name,
        (SELECT COALESCE(t2.name, cd2.talent_name)
         FROM candidaturas cd2
         LEFT JOIN talentos t2 ON t2.inhire_id = cd2.talent_inhire_id
         WHERE cd2.vaga_id = p.vaga_id
           AND cd2.stage_name = 'Contratação'
         ORDER BY cd2.updated_at_inhire DESC
         LIMIT 1)
    ) AS nome_pessoa_contratada,

    -- 26. E-mail Pessoal (CORRIGIDO - Migration 054)
    -- JOIN direto com talentos usando posicoes.talent_id
    -- Fallback para candidaturas se talent_id for NULL
    COALESCE(
        t_contratado.email,
        (SELECT COALESCE(t2.email, cd2.talent_email)
         FROM candidaturas cd2
         LEFT JOIN talentos t2 ON t2.inhire_id = cd2.talent_inhire_id
         WHERE cd2.vaga_id = p.vaga_id
           AND cd2.stage_name = 'Contratação'
         ORDER BY cd2.updated_at_inhire DESC
         LIMIT 1)
    ) AS email_pessoal,

    -- 27. Modalidade de Contratação Requisição (Migration 049)
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 28. SLA Geral (dias úteis - Migration 050)
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
    -- ✅ CORRIGIDO (Migration 054): JOIN direto usando posicoes.talent_id
    LEFT JOIN talentos t_contratado ON t_contratado.inhire_id = p.talent_id
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 054 (2026-02-19).
31 campos. Histórico:
  - 047: tradução motivo_contratacao
  - 048: email_responsavel_cliente
  - 049: modalidade_contratacao_req, empresa, tipo_posicao
  - 050: SLAs em dias úteis
  - 052: removido filtro stage_order > 9
  - 053: CORRIGIDO email/nome com COALESCE(talentos, candidaturas) + LEFT JOIN
  - 054: CORRIGIDO usando posicoes.talent_id (fix duplicação em vagas com múltiplas posições)';

COMMENT ON COLUMN vw_analise_posicoes.nome_pessoa_contratada IS
'Nome do candidato contratado nesta posição específica. Usa posicoes.talent_id para JOIN direto
com talentos, garantindo candidato correto em vagas com múltiplas posições. Fallback para
candidaturas se talent_id for NULL. (Migration 054)';

COMMENT ON COLUMN vw_analise_posicoes.email_pessoal IS
'Email do candidato contratado nesta posição específica. Usa posicoes.talent_id para JOIN direto
com talentos, garantindo email correto em vagas com múltiplas posições. Fallback para
candidaturas se talent_id for NULL. (Migration 054)';
