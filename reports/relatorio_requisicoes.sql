-- ===============================================================
-- RELATÓRIO DE REQUISIÇÕES
-- ===============================================================
-- Relatório completo de requisições com todas as informações
-- solicitadas: description, name, requested_at
--
-- Data de criação: 2026-07-21
-- ===============================================================

SELECT
    r.id AS id_requisicao,
    r.inhire_id AS inhire_id_requisicao,

    -- Campos principais solicitados
    r.name AS titulo_requisicao,
    r.description AS descricao,
    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao,

    -- Informações da vaga relacionada
    v.id AS id_vaga,
    v.inhire_id AS inhire_id_vaga,
    v.name AS nome_vaga,
    v.status AS status_vaga,
    v.area AS area_vaga,
    v.seniority AS senioridade_vaga,

    -- Status e timing da requisição
    r.status AS status_requisicao,
    r.approved_at AT TIME ZONE 'America/Sao_Paulo' AS data_aprovacao,
    r.rejected_at AT TIME ZONE 'America/Sao_Paulo' AS data_rejeicao,
    r.status_updated_at AT TIME ZONE 'America/Sao_Paulo' AS data_atualizacao_status,

    -- Informações de salário
    r.salary_min AS salario_minimo,
    r.salary_max AS salario_maximo,

    -- Quantidade de posições
    r.position_amount AS quantidade_posicoes,

    -- Responsáveis
    r.requester_name AS solicitante_nome,
    r.requester_id AS solicitante_id,
    r.approver_name AS aprovador_nome,
    r.approver_id AS aprovador_id,
    r.user_name AS usuario_nome,
    r.user_id AS usuario_id,

    -- Cliente
    r.client_id AS cliente_id,

    -- Motivo (caso tenha sido rejeitada)
    r.reason AS motivo_rejeicao,

    -- Auditoria
    r.created_at_inhire AT TIME ZONE 'America/Sao_Paulo' AS criado_em_inhire,
    r.updated_at_inhire AT TIME ZONE 'America/Sao_Paulo' AS atualizado_em_inhire,
    r.created_at AT TIME ZONE 'America/Sao_Paulo' AS criado_em_bd,
    r.updated_at AT TIME ZONE 'America/Sao_Paulo' AS atualizado_em_bd,

    -- Custom fields (JSON completo)
    r.custom_fields AS campos_customizados,

    -- Workflow de aprovação (JSON)
    r.approval_workflow AS workflow_aprovacao,
    r.approvers AS aprovadores_lista

FROM requisicoes r
LEFT JOIN vagas v ON r.vaga_id = v.id

-- Ordenar por data de solicitação mais recente
ORDER BY r.requested_at DESC NULLS LAST, r.created_at DESC;


-- ===============================================================
-- QUERY ALTERNATIVA: Resumo Estatístico de Requisições
-- ===============================================================
-- Pode ser útil para análises gerais

SELECT
    status AS status_requisicao,
    COUNT(*) AS total_requisicoes,
    COUNT(DISTINCT job_inhire_id) AS vagas_unicas,
    SUM(position_amount) AS total_posicoes,
    AVG(salary_max) AS salario_maximo_medio,
    MIN(requested_at AT TIME ZONE 'America/Sao_Paulo') AS primeira_solicitacao,
    MAX(requested_at AT TIME ZONE 'America/Sao_Paulo') AS ultima_solicitacao,
    COUNT(DISTINCT requester_id) AS solicitantes_unicos,
    COUNT(DISTINCT approver_id) AS aprovadores_unicos
FROM requisicoes
WHERE requested_at IS NOT NULL
GROUP BY status
ORDER BY total_requisicoes DESC;


-- ===============================================================
-- QUERY AUXILIAR: Requisições com Tempo de Aprovação
-- ===============================================================

SELECT
    r.name AS titulo_requisicao,
    r.status AS status,
    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS solicitado_em,
    r.approved_at AT TIME ZONE 'America/Sao_Paulo' AS aprovado_em,

    -- Tempo de aprovação em dias úteis (aproximado)
    CASE
        WHEN r.approved_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (r.approved_at - r.requested_at)) / 86400
        ELSE NULL
    END AS dias_para_aprovacao,

    r.requester_name AS solicitante,
    r.approver_name AS aprovador,
    v.name AS vaga_nome,
    r.position_amount AS posicoes_solicitadas

FROM requisicoes r
LEFT JOIN vagas v ON r.vaga_id = v.id

WHERE r.requested_at IS NOT NULL
ORDER BY r.requested_at DESC;
