-- =====================================================
-- Migration: 022_update_view_analise_posicoes_completa.sql
-- Descrição: Atualiza view vw_analise_posicoes com todos os campos solicitados
-- Data: 2026-02-04
-- =====================================================

-- Remove a view existente
DROP VIEW IF EXISTS vw_analise_posicoes;

-- Recria a view com TODOS os campos solicitados
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
),
pessoa_contratada AS (
    -- Busca o candidato contratado (etapa Contratação, stage_order > 9)
    SELECT
        cd.vaga_id,
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
),
pendencias_cliente AS (
    -- Calcula datas de início e fim de pendências com cliente
    -- (assumindo que pendências são mudanças de status antes de closed/canceled)
    SELECT
        pt.posicao_id,
        MIN(pt.changed_at) FILTER (WHERE pt.metadata IS NOT NULL AND pt.new_status NOT IN ('closed', 'canceled')) AS inicio_pendencia,
        MAX(pt.changed_at) FILTER (WHERE pt.metadata IS NOT NULL AND pt.new_status NOT IN ('closed', 'canceled')) AS fim_pendencia
    FROM position_timeline pt
    GROUP BY pt.posicao_id
)
SELECT
    -- 1. ID
    p.id AS id_position,

    -- 2. Cargo
    v.name AS cargo,

    -- 3. Data de abertura
    DATE(r.requested_at) AS data_abertura,

    -- 4. Data da publicação
    DATE(p.created_at_inhire) AS data_publicacao,

    -- 5. Quantidade
    r.position_amount AS quantidade,

    -- 6. Prazo do Processo Seletivo
    v.sla_days_goal AS prazo_processo_seletivo,

    -- 7. Cliente
    c.name AS cliente,

    -- 8. Torre
    v.custom_fields->>'Torre' AS torre,

    -- 9. Status
    COALESCE(us.new_status, p.status) AS status_atual,

    -- 10. Data de Encerramento
    DATE(us.changed_at) AS data_encerramento,

    -- 11. IA (campo a definir - deixando NULL por enquanto)
    NULL::TEXT AS ia,

    -- 12. Motivo de cancelamento/paralisação
    CASE
        WHEN COALESCE(us.new_status, p.status) = 'canceled'
        THEN COALESCE(v.custom_fields->>'Motivo de Cancelamento', us.metadata::text)
        WHEN COALESCE(us.new_status, p.status) = 'paused'
        THEN COALESCE(v.custom_fields->>'Motivo de Congelamento', us.metadata::text)
        ELSE us.metadata::text
    END AS motivo_cancelamento_paralisacao,

    -- 13. Etapa Funil
    ue.stage_name AS etapa_funil,

    -- 14. Senioridade
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,

    -- 15. Motivo de contratação
    p.reason AS motivo_contratacao,

    -- 16. Mod Contratação Pessoa a Ser Substituida
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- 17. Responsável
    r.user_name AS responsavel,

    -- 18. Recrutador da vaga
    v.user_name AS recrutador_vaga,

    -- 19. Inicio Pendência com Cliente
    DATE(pc.inicio_pendencia) AS inicio_pendencia_cliente,

    -- 20. Fim Pendência com Cliente
    DATE(pc.fim_pendencia) AS fim_pendencia_cliente,

    -- 21. SLA Pendência Cliente (dias)
    CASE
        WHEN pc.inicio_pendencia IS NOT NULL AND pc.fim_pendencia IS NOT NULL
        THEN EXTRACT(DAY FROM (pc.fim_pendencia - pc.inicio_pendencia))
        ELSE NULL
    END AS sla_pendencia_cliente,

    -- 22. SLA Recrutamento (dias desde abertura até publicação)
    CASE
        WHEN r.requested_at IS NOT NULL AND p.created_at_inhire IS NOT NULL
        THEN EXTRACT(DAY FROM (p.created_at_inhire - r.requested_at))
        ELSE NULL
    END AS sla_recrutamento,

    -- 23. Nome da Pessoa Contratada
    pct.talent_name AS nome_pessoa_contratada,

    -- 24. E-mail Pessoal
    pct.talent_email AS email_pessoal,

    -- 25. Modalidade de Contratação
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    -- 26. SLA Geral (dias desde abertura até encerramento ou até hoje se ainda aberta)
    CASE
        WHEN us.changed_at IS NOT NULL
        THEN EXTRACT(DAY FROM (us.changed_at - COALESCE(r.requested_at, p.created_at_inhire)))
        ELSE EXTRACT(DAY FROM (CURRENT_DATE - COALESCE(r.requested_at, p.created_at_inhire)))
    END AS sla_geral,

    -- 27. Meta Recrutamento (a definir - campo custom_fields?)
    v.custom_fields->>'Meta Recrutamento' AS meta_recrutamento,

    -- 28. Classificação da vaga (a definir - campo custom_fields?)
    v.custom_fields->>'Classificação' AS classificacao_vaga,

    -- 29. Teste data (Marcão) - campo temporário de teste
    NULL::DATE AS teste_data_marcao,

    -- 30. Empresa (cliente ou custom_fields?)
    COALESCE(c.name, v.custom_fields->>'Empresa') AS empresa,

    -- Campos auxiliares adicionais
    v.area AS area_vaga,
    ue.stage_order AS id_etapa_funil,

    -- Indicador de prazo
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

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultimo_status us ON us.posicao_id = p.id AND us.rn = 1
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_cliente pc ON pc.posicao_id = p.id

WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)

ORDER BY p.created_at_inhire DESC;

-- Comentários na view
COMMENT ON VIEW vw_analise_posicoes IS
'View consolidada para análise completa de posições.
Inclui informações de status, etapas, prazos, cliente, torre, responsáveis,
pessoa contratada, pendências e cálculos de SLA.
Atualizada em 2026-02-04 com campos completos de análise.';

-- Comentários nas colunas
COMMENT ON COLUMN vw_analise_posicoes.id_position IS 'ID interno da posição';
COMMENT ON COLUMN vw_analise_posicoes.cargo IS 'Nome do cargo/vaga';
COMMENT ON COLUMN vw_analise_posicoes.data_abertura IS 'Data de abertura da requisição';
COMMENT ON COLUMN vw_analise_posicoes.data_publicacao IS 'Data de publicação da posição';
COMMENT ON COLUMN vw_analise_posicoes.quantidade IS 'Quantidade de posições na requisição';
COMMENT ON COLUMN vw_analise_posicoes.prazo_processo_seletivo IS 'Prazo em dias para conclusão (SLA da vaga)';
COMMENT ON COLUMN vw_analise_posicoes.cliente IS 'Nome do cliente';
COMMENT ON COLUMN vw_analise_posicoes.torre IS 'Torre de negócio (ex: Saúde e Indústria)';
COMMENT ON COLUMN vw_analise_posicoes.status_atual IS 'Status atual da posição';
COMMENT ON COLUMN vw_analise_posicoes.data_encerramento IS 'Data de encerramento/última atualização';
COMMENT ON COLUMN vw_analise_posicoes.motivo_cancelamento_paralisacao IS 'Motivo de cancelamento ou congelamento';
COMMENT ON COLUMN vw_analise_posicoes.etapa_funil IS 'Última etapa do funil de candidatos';
COMMENT ON COLUMN vw_analise_posicoes.senioridade IS 'Nível de senioridade da vaga';
COMMENT ON COLUMN vw_analise_posicoes.motivo_contratacao IS 'Motivo/razão da contratação';
COMMENT ON COLUMN vw_analise_posicoes.pessoa_substituida IS 'Nome do colaborador a ser substituído';
COMMENT ON COLUMN vw_analise_posicoes.responsavel IS 'Responsável pela requisição';
COMMENT ON COLUMN vw_analise_posicoes.recrutador_vaga IS 'Recrutador responsável pela vaga';
COMMENT ON COLUMN vw_analise_posicoes.inicio_pendencia_cliente IS 'Data de início da pendência com cliente';
COMMENT ON COLUMN vw_analise_posicoes.fim_pendencia_cliente IS 'Data de fim da pendência com cliente';
COMMENT ON COLUMN vw_analise_posicoes.sla_pendencia_cliente IS 'Dias em pendência com cliente';
COMMENT ON COLUMN vw_analise_posicoes.sla_recrutamento IS 'Dias entre abertura e publicação';
COMMENT ON COLUMN vw_analise_posicoes.nome_pessoa_contratada IS 'Nome do talento contratado';
COMMENT ON COLUMN vw_analise_posicoes.email_pessoal IS 'E-mail do talento contratado';
COMMENT ON COLUMN vw_analise_posicoes.modalidade_contratacao IS 'Modalidade de contratação (CLT, PJ, etc)';
COMMENT ON COLUMN vw_analise_posicoes.sla_geral IS 'SLA geral em dias (abertura até encerramento)';
COMMENT ON COLUMN vw_analise_posicoes.meta_recrutamento IS 'Meta de recrutamento da vaga';
COMMENT ON COLUMN vw_analise_posicoes.classificacao_vaga IS 'Classificação da vaga';
COMMENT ON COLUMN vw_analise_posicoes.teste_data_marcao IS 'Campo de teste temporário';
COMMENT ON COLUMN vw_analise_posicoes.empresa IS 'Nome da empresa/cliente';

-- Verificações
SELECT 'VERIFICAÇÃO - PRIMEIRAS 10 POSIÇÕES' as tipo;
SELECT * FROM vw_analise_posicoes LIMIT 10;

-- Estatísticas
SELECT
    'ESTATÍSTICAS GERAIS' as relatorio,
    COUNT(*) as total_posicoes,
    COUNT(torre) as com_torre,
    COUNT(nome_pessoa_contratada) as com_contratacao,
    COUNT(inicio_pendencia_cliente) as com_pendencias,
    ROUND(AVG(sla_geral), 2) as sla_geral_medio
FROM vw_analise_posicoes;
