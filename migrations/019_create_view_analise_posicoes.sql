-- Migration: Criar view de análise de posições
-- Data: 2026-02-03
-- Descrição: View consolidada para análise de posições com status, etapas e prazos

-- Remove a view se já existir
DROP VIEW IF EXISTS vw_analise_posicoes;

-- Cria a view com as informações solicitadas
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
'View consolidada para análise de posições com informações de status, etapas do funil, prazos e clientes.
Inclui cálculo de dias em aberto e indicador de cumprimento de prazo.';

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
