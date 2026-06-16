/*
================================================================================
MIGRATION 039: Criar View de Análise COMPLETA de Requisições
================================================================================

Data: 2026-02-06
Descrição:
  Cria view vw_analise_requisicoes que inclui TODAS as requisições,
  independente de terem sido publicadas como posição ou não.

Diferença vs vw_analise_posicoes:
  - vw_analise_posicoes: baseada em POSIÇÕES (290 em 2025)
  - vw_analise_requisicoes: baseada em REQUISIÇÕES (491 em 2025)

Casos cobertos:
  1. Requisições com 1 posição (maioria)
  2. Requisições com múltiplas posições (reabertas)
  3. Requisições canceladas antes de publicar (SEM posição)

Objetivo:
  Análise COMPLETA de demanda, incluindo vagas canceladas antes de abrir.

================================================================================
*/

-- Remove view se existir
DROP VIEW IF EXISTS vw_analise_requisicoes CASCADE;

-- Cria view baseada em requisições
CREATE OR REPLACE VIEW vw_analise_requisicoes AS
WITH posicoes_por_requisicao AS (
    -- Para cada requisição, agregar dados de TODAS as posições
    SELECT
        r.id as requisicao_id,
        r.inhire_id as requisicao_inhire_id,
        r.job_inhire_id,
        COUNT(p.id) as num_posicoes,
        MIN(p.id) as primeira_posicao_id,
        MAX(p.id) as ultima_posicao_id,
        MIN(p.opened_at) as data_primeira_abertura,
        MAX(p.opened_at) as data_ultima_abertura,
        MAX(p.hired_at) as data_contratacao,
        STRING_AGG(DISTINCT p.status, ', ' ORDER BY p.status) as status_posicoes
    FROM requisicoes r
    LEFT JOIN vagas v ON v.inhire_id = r.job_inhire_id
    LEFT JOIN posicoes p ON p.vaga_id = v.id
    GROUP BY r.id, r.inhire_id, r.job_inhire_id
),
ultimo_status_por_requisicao AS (
    -- Pega o último status da última posição (se houver)
    SELECT DISTINCT ON (ppr.requisicao_id)
        ppr.requisicao_id,
        COALESCE(pt.new_status, p.status) as status_atual,
        pt.changed_at as data_ultima_mudanca
    FROM posicoes_por_requisicao ppr
    LEFT JOIN posicoes p ON p.id = ppr.ultima_posicao_id
    LEFT JOIN position_timeline pt ON pt.posicao_id = p.id
    ORDER BY ppr.requisicao_id, pt.changed_at DESC NULLS LAST
),
pausas_por_requisicao AS (
    -- Agregar pausas de TODAS as posições da requisição
    SELECT
        ppr.requisicao_id,
        COUNT(DISTINCT ap.primeira_pausa) as total_ciclos_pausa,
        MIN(ap.primeira_pausa) as inicio_primeira_pausa,
        MAX(ap.ultima_retomada) as fim_ultima_pausa,
        SUM(ap.total_dias_pausa) as total_dias_pausado,
        STRING_AGG(ap.detalhamento, ' | ' ORDER BY ap.primeira_pausa) as detalhamento_pausas
    FROM posicoes_por_requisicao ppr
    LEFT JOIN posicoes p ON p.vaga_id = (
        SELECT v.id FROM vagas v WHERE v.inhire_id = ppr.job_inhire_id
    )
    LEFT JOIN (
        -- Subquery com agregação de pausas (mesma lógica da vw_analise_posicoes)
        SELECT
            posicao_id,
            MIN(inicio_pausa) as primeira_pausa,
            MAX(fim_pausa) as ultima_retomada,
            SUM(dias_pausa) as total_dias_pausa,
            COUNT(*) as num_ciclos,
            STRING_AGG(
                'Pausa: ' || TO_CHAR(inicio_pausa, 'DD/MM/YYYY') ||
                ' a ' || COALESCE(TO_CHAR(fim_pausa, 'DD/MM/YYYY'), 'Em pausa') ||
                COALESCE(' (' || dias_pausa || ' dias)', ''),
                '; ' ORDER BY inicio_pausa
            ) as detalhamento
        FROM (
            SELECT
                inicio.posicao_id,
                inicio.changed_at as inicio_pausa,
                MIN(fim.changed_at) as fim_pausa,
                CASE
                    WHEN MIN(fim.changed_at) IS NOT NULL THEN
                        (DATE(MIN(fim.changed_at)) - DATE(inicio.changed_at))::INTEGER
                    ELSE NULL
                END as dias_pausa
            FROM (
                SELECT DISTINCT
                    pt.posicao_id,
                    pt.changed_at,
                    pt.previous_status,
                    pt.new_status
                FROM position_timeline pt
                WHERE ((pt.previous_status = 'open' OR pt.previous_status IS NULL) AND pt.new_status = 'paused')
            ) inicio
            LEFT JOIN (
                SELECT DISTINCT
                    pt.posicao_id,
                    pt.changed_at,
                    pt.previous_status,
                    pt.new_status
                FROM position_timeline pt
                WHERE (pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed'))
            ) fim
                ON fim.posicao_id = inicio.posicao_id
                AND fim.changed_at > inicio.changed_at
            GROUP BY inicio.posicao_id, inicio.changed_at
        ) periodos_pausa
        GROUP BY posicao_id
    ) ap ON ap.posicao_id = p.id
    WHERE ap.posicao_id IS NOT NULL
    GROUP BY ppr.requisicao_id
)
SELECT
    -- Identificação da requisição
    r.id AS requisicao_id,
    r.inhire_id AS requisicao_inhire_id,
    ppr.job_inhire_id AS vaga_inhire_id,

    -- Identificação da vaga
    v.id AS vaga_id,
    v.name AS cargo,

    -- Informações de posições
    ppr.num_posicoes,
    ppr.primeira_posicao_id,
    ppr.ultima_posicao_id,

    -- Status
    CASE
        WHEN ppr.num_posicoes = 0 THEN 'Cancelada sem publicar'
        ELSE COALESCE(usp.status_atual, v.status::text, 'Desconhecido')
    END AS status_atual,

    -- Datas principais
    DATE(r.requested_at) AS data_solicitacao,
    DATE(ppr.data_primeira_abertura) AS data_primeira_publicacao,
    DATE(ppr.data_ultima_abertura) AS data_ultima_publicacao,
    DATE(COALESCE(usp.data_ultima_mudanca, ppr.data_contratacao)) AS data_encerramento,
    DATE(ppr.data_contratacao) AS data_contratacao,

    -- Dimensões de análise
    r.user_name AS responsavel_requisicao,
    v.user_name AS recrutadora,
    cl.name AS cliente,
    v.custom_fields->>'Torre' AS torre,

    -- SLAs (em dias)
    -- SLA Solicitação até Publicação
    CASE
        WHEN ppr.data_primeira_abertura IS NOT NULL THEN
            (DATE(ppr.data_primeira_abertura) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_solicitacao_publicacao,

    -- SLA Geral (Solicitação até Encerramento)
    CASE
        WHEN usp.data_ultima_mudanca IS NOT NULL OR ppr.data_contratacao IS NOT NULL THEN
            (COALESCE(DATE(usp.data_ultima_mudanca), DATE(ppr.data_contratacao)) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_geral,

    -- SLA Recrutamento (Publicação até Encerramento)
    CASE
        WHEN ppr.data_primeira_abertura IS NOT NULL
             AND (usp.data_ultima_mudanca IS NOT NULL OR ppr.data_contratacao IS NOT NULL) THEN
            (COALESCE(DATE(usp.data_ultima_mudanca), DATE(ppr.data_contratacao)) - DATE(ppr.data_primeira_abertura))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,

    -- Prazo esperado
    (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER AS prazo_processo_seletivo,

    -- Indicador de prazo
    CASE
        WHEN (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER IS NOT NULL
             AND ppr.data_contratacao IS NOT NULL THEN
            CASE
                WHEN (DATE(ppr.data_contratacao) - DATE(ppr.data_primeira_abertura))::INTEGER <=
                     (v.custom_fields->>'Prazo do processo seletivo (dias)')::INTEGER
                THEN 'Dentro do prazo'
                ELSE 'Fora do prazo'
            END
        ELSE NULL
    END AS indicador_prazo,

    -- Informações de pausa/pendência
    DATE(paus.inicio_primeira_pausa) AS inicio_pendencia_cliente,
    DATE(paus.fim_ultima_pausa) AS fim_pendencia_cliente,
    paus.total_dias_pausado AS sla_pendencia_cliente,
    paus.total_ciclos_pausa AS num_ciclos_pausa,
    paus.detalhamento_pausas,

    -- Situação da requisição
    CASE
        WHEN ppr.num_posicoes = 0 THEN 'Não publicada'
        WHEN ppr.num_posicoes = 1 THEN 'Publicada'
        ELSE 'Reaberta ' || (ppr.num_posicoes - 1) || ' vez(es)'
    END AS situacao,

    -- Datas de controle
    DATE(r.created_at) AS created_at,
    DATE(r.updated_at) AS updated_at

FROM requisicoes r
INNER JOIN posicoes_por_requisicao ppr ON ppr.requisicao_id = r.id
LEFT JOIN vagas v ON v.inhire_id = r.job_inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN ultimo_status_por_requisicao usp ON usp.requisicao_id = r.id
LEFT JOIN pausas_por_requisicao paus ON paus.requisicao_id = r.id

ORDER BY r.requested_at DESC;

-- Comentários
COMMENT ON VIEW vw_analise_requisicoes IS
'View de análise COMPLETA baseada em REQUISIÇÕES (não posições).
Criada em 2026-02-06 (Migration 039).
Inclui:
- Requisições com posição (publicadas)
- Requisições com múltiplas posições (reabertas)
- Requisições sem posição (canceladas antes de publicar)
Métrica de demanda completa do cliente.';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_2025 INTEGER;
    v_sem_posicao INTEGER;
    v_multiplas INTEGER;
    v_reaberta_exemplo RECORD;
BEGIN
    -- Total geral
    SELECT COUNT(*) INTO v_total FROM vw_analise_requisicoes;

    -- Total 2025
    SELECT COUNT(*) INTO v_2025
    FROM vw_analise_requisicoes
    WHERE EXTRACT(YEAR FROM data_solicitacao) = 2025;

    -- Sem posição
    SELECT COUNT(*) INTO v_sem_posicao
    FROM vw_analise_requisicoes
    WHERE num_posicoes = 0;

    -- Com múltiplas posições
    SELECT COUNT(*) INTO v_multiplas
    FROM vw_analise_requisicoes
    WHERE num_posicoes > 1;

    -- Exemplo de vaga reaberta
    SELECT
        requisicao_id,
        cargo,
        num_posicoes,
        situacao
    INTO v_reaberta_exemplo
    FROM vw_analise_requisicoes
    WHERE num_posicoes > 1
    ORDER BY num_posicoes DESC
    LIMIT 1;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 039 - VIEW ANÁLISE REQUISIÇÕES CRIADA';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total de requisições: %', v_total;
    RAISE NOTICE 'Requisições de 2025: %', v_2025;
    RAISE NOTICE '';
    RAISE NOTICE 'Distribuição:';
    RAISE NOTICE '  - Sem posição (canceladas antes de publicar): %', v_sem_posicao;
    RAISE NOTICE '  - Com múltiplas posições (reabertas): %', v_multiplas;
    RAISE NOTICE '';
    RAISE NOTICE 'Exemplo de vaga reaberta:';
    RAISE NOTICE '  Requisição: % | Cargo: %', v_reaberta_exemplo.requisicao_id, v_reaberta_exemplo.cargo;
    RAISE NOTICE '  Posições: % | Situação: %', v_reaberta_exemplo.num_posicoes, v_reaberta_exemplo.situacao;
    RAISE NOTICE '';
    RAISE NOTICE 'Comparação com planilha de controle (498):';
    RAISE NOTICE '  Requisições 2025: %', v_2025;
    RAISE NOTICE '  Diferença: %', 498 - v_2025;
    RAISE NOTICE '================================================================================';
END $$;
