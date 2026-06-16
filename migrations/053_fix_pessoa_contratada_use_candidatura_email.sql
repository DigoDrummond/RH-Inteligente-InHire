/*
================================================================================
MIGRATION 053: Corrigir Fonte do Email/Nome da Pessoa Contratada
================================================================================

Data: 2026-02-18

DIAGNÓSTICO COMPLETO:

  Dois problemas identificados como causa raiz:

  PROBLEMA 1 (migration 052 corrigiu): stage_order > 9 excluía candidatos
  PROBLEMA 2 (esta migration corrige): A view busca email APENAS de talentos.email,
    ignorando que candidaturas.talent_email tem o email embutido diretamente da API.

  Por que talentos.email é NULL em muitos casos?
  --------------------------------------------------
  A tabela `talentos` é populada via endpoint /talents/:id (sync explícito).
  A API InHire pode não retornar o campo email nesse endpoint para alguns talentos.

  Por que candidaturas.talent_email é NULL em muitos casos?
  ----------------------------------------------------------
  A tabela `candidaturas` INSERE talent_email via cand_api.talent.email (linha 737
  de database_service.py), mas o UPDATE de candidaturas NÃO atualiza talent_email
  (linhas 687-711 - talent_name e talent_email estão ausentes do bloco de update).
  Portanto, candidaturas antigas têm talent_email = NULL.

CORREÇÕES DESTA MIGRATION:

  1. INNER JOIN talentos → LEFT JOIN talentos
     Garante que candidatos na etapa Contratação apareçam mesmo que o talento
     não exista na tabela talentos.

  2. COALESCE(t.name, cd.talent_name) como nome_pessoa_contratada
     Usa o nome de talentos se disponível, fallback para candidaturas.talent_name

  3. COALESCE(t.email, cd.talent_email) como email_pessoal
     Usa o email de talentos se disponível, fallback para candidaturas.talent_email

NOTA: Também é necessário corrigir database_service.py para que o UPDATE de
candidaturas inclua talent_name e talent_email (ver correção separada).

Base: Migration 052 com as correções acima.

================================================================================
*/

-- ============================================================================
-- 1. RECRIAR VIEW COM CORREÇÃO DAS FONTES DE EMAIL E NOME
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
        -- ✅ CORRIGIDO (Migration 053): COALESCE entre talentos e candidaturas
        -- talentos.name tem prioridade; fallback para candidaturas.talent_name
        COALESCE(t.name, cd.talent_name) AS talent_name,
        -- talentos.email tem prioridade; fallback para candidaturas.talent_email
        COALESCE(t.email, cd.talent_email) AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    -- ✅ CORRIGIDO (Migration 053): LEFT JOIN para não excluir candidatos sem registro em talentos
    LEFT JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    -- ✅ CORRIGIDO (Migration 052): Sem filtro stage_order > 9
    WHERE cd.stage_name = 'Contratação'
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

    -- 25. Nome da Pessoa Contratada (CORRIGIDO - Migration 053)
    -- Prioridade: talentos.name → candidaturas.talent_name
    pct.talent_name AS nome_pessoa_contratada,

    -- 26. E-mail Pessoal (CORRIGIDO - Migration 053)
    -- Prioridade: talentos.email → candidaturas.talent_email
    pct.talent_email AS email_pessoal,

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
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 053 (2026-02-18).
31 campos. Histórico:
  - 047: tradução motivo_contratacao
  - 048: email_responsavel_cliente
  - 049: modalidade_contratacao_req, empresa, tipo_posicao
  - 050: SLAs em dias úteis
  - 052: removido filtro stage_order > 9
  - 053: CORRIGIDO email/nome com COALESCE(talentos, candidaturas) + LEFT JOIN';

COMMENT ON COLUMN vw_analise_posicoes.nome_pessoa_contratada IS
'Nome do candidato contratado. COALESCE: talentos.name → candidaturas.talent_name.
LEFT JOIN talentos para não excluir candidatos sem registro na tabela. (Migration 053)';

COMMENT ON COLUMN vw_analise_posicoes.email_pessoal IS
'Email do candidato contratado. COALESCE: talentos.email → candidaturas.talent_email.
Ambas as fontes usadas para máxima cobertura. (Migration 053)';
