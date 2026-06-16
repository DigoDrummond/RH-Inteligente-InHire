-- =====================================================
-- Migration: 021_add_torre_to_view_analise_posicoes.sql
-- Descrição: Adiciona campo 'torre' na view vw_analise_posicoes
--           extraindo do campo custom_fields da tabela vagas
-- Data: 2026-02-04
-- =====================================================

-- Remove a view existente
DROP VIEW IF EXISTS vw_analise_posicoes;

-- Recria a view com o campo torre
CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL
),
ultimo_status AS (
    SELECT
        posicao_id,
        new_status,
        changed_at,
        metadata,
        ROW_NUMBER() OVER (PARTITION BY posicao_id ORDER BY changed_at DESC) AS rn
    FROM position_timeline
    WHERE changed_by IS NOT NULL
)
SELECT
    p.id AS id_position,
    p.inhire_id AS codigo_posicao,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.created_at_inhire) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    COALESCE(us.new_status, p.status) AS status_atual,
    DATE(us.changed_at) AS data_encerramento,
    us.metadata AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    ue.stage_order AS id_etapa_funil,
    -- NOVO: Campo Torre extraído do custom_fields
    v.custom_fields->>'Torre' AS torre,
    -- Campos adicionais úteis
    v.area AS area_vaga,
    p.user_name AS responsavel_posicao,
    r.status AS status_requisicao,
    r.position_amount AS quantidade_posicoes_requisicao,
    -- Calcula dias em aberto (se ainda aberta)
    CASE
        WHEN us.changed_at IS NOT NULL THEN EXTRACT(DAY FROM (us.changed_at - COALESCE(r.requested_at, p.created_at_inhire)))
        ELSE EXTRACT(DAY FROM (CURRENT_DATE - COALESCE(r.requested_at, p.created_at_inhire)))
    END AS dias_em_aberto,
    -- Verifica se está dentro do prazo
    CASE
        WHEN v.sla_days_goal IS NOT NULL AND us.changed_at IS NOT NULL
        THEN CASE
            WHEN EXTRACT(DAY FROM (us.changed_at - COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
            THEN 'Dentro do Prazo'
            ELSE 'Fora do Prazo'
        END
        WHEN v.sla_days_goal IS NOT NULL AND us.changed_at IS NULL
        THEN CASE
            WHEN EXTRACT(DAY FROM (CURRENT_DATE - COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
            THEN 'Dentro do Prazo'
            ELSE 'Fora do Prazo'
        END
        ELSE NULL
    END AS indicador_prazo,
    -- Timestamps de auditoria
    p.created_at,
    p.updated_at
FROM
    posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultimo_status us ON us.posicao_id = p.id AND us.rn = 1
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
ORDER BY
    p.created_at_inhire DESC;

-- Adiciona comentário na view
COMMENT ON VIEW vw_analise_posicoes IS
'View consolidada para análise de posições com informações de status, etapas do funil, prazos, clientes e torre.
Inclui cálculo de dias em aberto e indicador de cumprimento de prazo.
Atualizada em 2026-02-04 para incluir campo torre extraído de custom_fields.';

-- Adiciona comentários nas colunas principais
COMMENT ON COLUMN vw_analise_posicoes.id_position IS 'ID interno da posição';
COMMENT ON COLUMN vw_analise_posicoes.codigo_posicao IS 'Código da posição no InHire';
COMMENT ON COLUMN vw_analise_posicoes.cargo IS 'Nome do cargo/vaga';
COMMENT ON COLUMN vw_analise_posicoes.data_abertura IS 'Data de abertura da requisição';
COMMENT ON COLUMN vw_analise_posicoes.data_publicacao IS 'Data de publicação da posição';
COMMENT ON COLUMN vw_analise_posicoes.prazo_processo_seletivo IS 'Prazo em dias para conclusão do processo';
COMMENT ON COLUMN vw_analise_posicoes.status_atual IS 'Status atual da posição';
COMMENT ON COLUMN vw_analise_posicoes.data_encerramento IS 'Data de encerramento/última atualização';
COMMENT ON COLUMN vw_analise_posicoes.etapa_funil IS 'Nome da última etapa do funil de candidatos';
COMMENT ON COLUMN vw_analise_posicoes.dias_em_aberto IS 'Número de dias que a posição está/esteve aberta';
COMMENT ON COLUMN vw_analise_posicoes.indicador_prazo IS 'Indica se a posição foi/está sendo preenchida dentro do prazo';
COMMENT ON COLUMN vw_analise_posicoes.torre IS 'Torre de negócio extraída do custom_fields da vaga (ex: Saúde e Indústria)';

-- Verificar resultado
SELECT
    'VERIFICAÇÃO - CAMPO TORRE' as verificacao,
    torre,
    COUNT(*) as quantidade
FROM vw_analise_posicoes
WHERE torre IS NOT NULL
GROUP BY torre
ORDER BY quantidade DESC
LIMIT 10;

-- Estatísticas
SELECT
    'ESTATÍSTICAS GERAIS' as relatorio,
    COUNT(*) as total_posicoes,
    COUNT(torre) as posicoes_com_torre,
    COUNT(*) - COUNT(torre) as posicoes_sem_torre,
    ROUND(100.0 * COUNT(torre) / COUNT(*), 2) as percentual_com_torre
FROM vw_analise_posicoes;
