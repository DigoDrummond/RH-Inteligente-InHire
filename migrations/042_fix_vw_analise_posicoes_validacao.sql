/*
================================================================================
MIGRATION 042: Correção da View vw_analise_posicoes
================================================================================

Data: 2026-02-10
Descrição:
  Corrige 3 problemas críticos identificados na validação:

  1. PRAZO_PROCESSO_SELETIVO 100% NULL
     - Problema: View usava custom_fields->>'Prazo do processo seletivo (dias)'
                 que não existe
     - Solução: Usar v.sla_days_goal que tem dados em 73% das vagas

  2. DATAS DE ENCERRAMENTO ANTERIORES À PUBLICAÇÃO
     - Problema: hired_at pode ser anterior a opened_at (dados históricos
                 importados após contratação)
     - Solução: Validar que data_encerramento >= data_publicacao, ou NULL

  3. INDICADOR_PRAZO 100% NULL
     - Problema: Consequência do problema 1
     - Solução: Usar sla_days_goal e validar contra SLA real

Problemas encontrados na validação:
  - 40 posições com hired_at < opened_at (Banco de Talentos histórico)
  - 40 SLAs negativos (consequência do problema acima)
  - 872 registros (100%) sem prazo_processo_seletivo
  - 872 registros (100%) sem indicador_prazo

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view COM CORREÇÕES
CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultimo_status_posicao AS (
    SELECT DISTINCT ON (pt.posicao_id)
        pt.posicao_id,
        pt.new_status AS status_atual,
        pt.changed_at AS data_ultima_mudanca
    FROM position_timeline pt
    ORDER BY pt.posicao_id, pt.changed_at DESC
),
eventos_pausa AS (
    SELECT DISTINCT
        pt.posicao_id,
        pt.changed_at,
        pt.previous_status,
        pt.new_status,
        CASE
            WHEN (pt.previous_status = 'open' OR pt.previous_status IS NULL)
                 AND pt.new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN pt.previous_status = 'paused'
                 AND pt.new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline pt
    WHERE
        ((pt.previous_status = 'open' OR pt.previous_status IS NULL) AND pt.new_status = 'paused')
        OR (pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS inicio_pausa,
        MIN(fim.changed_at) AS fim_pausa,
        CASE
            WHEN MIN(fim.changed_at) IS NOT NULL THEN
                (DATE(MIN(fim.changed_at)) - DATE(inicio.changed_at))::INTEGER
            ELSE NULL
        END AS dias_pausa
    FROM eventos_pausa inicio
    LEFT JOIN eventos_pausa fim
        ON fim.posicao_id = inicio.posicao_id
        AND fim.tipo_evento = 'FIM_PAUSA'
        AND fim.changed_at > inicio.changed_at
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
    GROUP BY inicio.posicao_id, inicio.changed_at
),
periodos_numerados AS (
    SELECT
        posicao_id,
        inicio_pausa,
        fim_pausa,
        dias_pausa,
        ROW_NUMBER() OVER (PARTITION BY posicao_id ORDER BY inicio_pausa) AS numero_pausa
    FROM periodos_pausa
),
agregacao_pausas AS (
    SELECT
        posicao_id,
        MIN(inicio_pausa) AS primeira_pausa,
        MAX(fim_pausa) AS ultima_retomada,
        SUM(dias_pausa) AS total_dias_pausa,
        COUNT(*) AS num_ciclos,
        STRING_AGG(
            'Pausa ' || numero_pausa ||
            ': ' || TO_CHAR(inicio_pausa, 'DD/MM/YYYY') ||
            ' a ' || COALESCE(TO_CHAR(fim_pausa, 'DD/MM/YYYY'), 'Em pausa') ||
            COALESCE(' (' || dias_pausa || ' dias)', ''),
            '; ' ORDER BY inicio_pausa
        ) AS detalhamento
    FROM periodos_numerados
    GROUP BY posicao_id
),
candidatos_contratados AS (
    -- Pega candidatos na etapa Contratação
    SELECT DISTINCT ON (c.vaga_id)
        c.vaga_id,
        t.name as candidato_nome,
        t.email as candidato_email,
        c.updated_at_inhire
    FROM candidaturas c
    INNER JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.stage_name = 'Contratação'
    ORDER BY c.vaga_id, c.updated_at_inhire DESC
)
SELECT
    -- Identificação
    p.id AS id_position,
    p.vaga_id,
    v.inhire_id AS vaga_inhire_id,
    v.name AS cargo,

    -- Status (prioriza timeline, fallback para posicoes.status)
    COALESCE(usp.status_atual, p.status) AS status_atual,

    -- Datas principais
    DATE(COALESCE(r.requested_at, p.opened_at)) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,

    -- *** CORRIGIDO: Data de encerramento/atualização COM VALIDAÇÃO ***
    -- Garante que a data não seja anterior à publicação
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
        THEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
        ELSE NULL  -- Se for anterior, considera NULL (dados inconsistentes)
    END AS data_encerramento_ou_atualizacao,

    -- Informações da requisição
    r.id AS requisicao_id,
    r.inhire_id AS requisicao_inhire_id,

    -- Dimensões de análise
    v.user_name AS recrutadora,
    cl.name AS cliente,
    v.custom_fields->>'Torre' AS torre,

    -- Status de preenchimento
    DATE(p.hired_at) AS data_contratacao,

    -- Dados do candidato contratado
    cc.candidato_nome,
    cc.candidato_email,

    -- *** CORRIGIDO: Métricas de SLA (apenas se datas válidas) ***
    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL  -- Não calcula SLA se datas inconsistentes
    END AS sla_geral,

    CASE
        WHEN p.opened_at IS NOT NULL
             AND COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(p.opened_at))::INTEGER
        ELSE NULL  -- Não calcula SLA se datas inconsistentes
    END AS sla_recrutamento,

    -- *** CORRIGIDO: Prazo do processo seletivo (usa sla_days_goal) ***
    v.sla_days_goal AS prazo_processo_seletivo,

    -- *** CORRIGIDO: Indicador de prazo (baseado em hired_at válido) ***
    CASE
        -- Só calcula se temos prazo E data de contratação válida
        WHEN v.sla_days_goal IS NOT NULL
             AND p.hired_at IS NOT NULL
             AND DATE(p.hired_at) >= DATE(p.opened_at)  -- Valida consistência
        THEN
            CASE
                WHEN (DATE(p.hired_at) - DATE(p.opened_at))::INTEGER <= v.sla_days_goal
                THEN 'Dentro do prazo'
                ELSE 'Fora do prazo'
            END
        ELSE NULL
    END AS indicador_prazo,

    -- Informações de pausa/pendência cliente
    DATE(ap.primeira_pausa) AS inicio_pendencia_cliente,
    DATE(ap.ultima_retomada) AS fim_pendencia_cliente,
    ap.total_dias_pausa AS sla_pendencia_cliente,
    ap.num_ciclos AS num_ciclos_pausa,
    ap.detalhamento AS detalhamento_pausas,

    -- Datas de criação/atualização
    DATE(p.created_at) AS created_at,
    DATE(p.updated_at) AS updated_at

FROM posicoes p
INNER JOIN vagas v ON p.vaga_id = v.id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
LEFT JOIN agregacao_pausas ap ON ap.posicao_id = p.id
LEFT JOIN candidatos_contratados cc ON cc.vaga_id = v.id

ORDER BY p.id DESC;

-- Comentários
COMMENT ON VIEW vw_analise_posicoes IS
'View para análise de posições e requisições com métricas de SLA e pausas.

**Atualizada em 2026-02-10 (Migration 042) - CORREÇÕES CRÍTICAS:**

1. prazo_processo_seletivo: Agora usa v.sla_days_goal (campo real) ao invés de
   custom_fields inexistente. Cobertura: ~73% das vagas.

2. data_encerramento_ou_atualizacao: Validada para nunca ser anterior a
   data_publicacao. Se hired_at < opened_at (dados históricos inconsistentes),
   retorna NULL.

3. sla_geral e sla_recrutamento: Só calculados se data_encerramento >= data_publicacao.
   Evita SLAs negativos.

4. indicador_prazo: Só calculado para posições com hired_at >= opened_at.
   Baseado em prazo real (sla_days_goal).

**Posições com dados inconsistentes (hired_at < opened_at):**
- Geralmente vagas de "Banco de Talentos" importadas historicamente
- Terão data_encerramento_ou_atualizacao = NULL
- Não terão SLA calculado
- Não terão indicador_prazo';

COMMENT ON COLUMN vw_analise_posicoes.prazo_processo_seletivo IS
'Prazo em dias (vem de vagas.sla_days_goal). NULL se vaga não tem meta definida.';

COMMENT ON COLUMN vw_analise_posicoes.data_encerramento_ou_atualizacao IS
'Data de encerramento validada (>= data_publicacao). NULL se dados inconsistentes.';

COMMENT ON COLUMN vw_analise_posicoes.sla_geral IS
'SLA geral em dias. NULL se sem data_encerramento válida.';

COMMENT ON COLUMN vw_analise_posicoes.indicador_prazo IS
'Dentro/Fora do prazo. NULL se sem prazo definido ou sem hired_at válido.';

-- Validação pós-migration
DO $$
DECLARE
    v_total INTEGER;
    v_com_prazo INTEGER;
    v_com_indicador INTEGER;
    v_sla_negativo INTEGER;
    v_data_invalida INTEGER;
BEGIN
    -- Total geral
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;

    -- Com prazo definido
    SELECT COUNT(*) INTO v_com_prazo
    FROM vw_analise_posicoes
    WHERE prazo_processo_seletivo IS NOT NULL;

    -- Com indicador de prazo
    SELECT COUNT(*) INTO v_com_indicador
    FROM vw_analise_posicoes
    WHERE indicador_prazo IS NOT NULL;

    -- SLA negativo (não deve existir mais)
    SELECT COUNT(*) INTO v_sla_negativo
    FROM vw_analise_posicoes
    WHERE sla_geral IS NOT NULL AND sla_geral < 0;

    -- Data encerramento < publicação (não deve existir mais)
    SELECT COUNT(*) INTO v_data_invalida
    FROM vw_analise_posicoes
    WHERE data_encerramento_ou_atualizacao IS NOT NULL
      AND data_publicacao IS NOT NULL
      AND data_encerramento_ou_atualizacao < data_publicacao;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 042 - CORREÇÃO DA VIEW vw_analise_posicoes';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Com prazo_processo_seletivo: % (%.1f%%)', v_com_prazo, (v_com_prazo::FLOAT / v_total * 100);
    RAISE NOTICE 'Com indicador_prazo: % (%.1f%%)', v_com_indicador, (v_com_indicador::FLOAT / v_total * 100);
    RAISE NOTICE '';
    RAISE NOTICE 'VALIDAÇÕES:';
    RAISE NOTICE '  SLAs negativos: % (esperado: 0)', v_sla_negativo;
    RAISE NOTICE '  Datas inválidas: % (esperado: 0)', v_data_invalida;
    RAISE NOTICE '';

    IF v_sla_negativo > 0 THEN
        RAISE WARNING '  [!] Ainda existem SLAs negativos!';
    ELSE
        RAISE NOTICE '  [OK] Nenhum SLA negativo';
    END IF;

    IF v_data_invalida > 0 THEN
        RAISE WARNING '  [!] Ainda existem datas inválidas!';
    ELSE
        RAISE NOTICE '  [OK] Todas as datas são válidas';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE 'CORREÇÕES APLICADAS:';
    RAISE NOTICE '  1. prazo_processo_seletivo: sla_days_goal (antes: custom_field inexistente)';
    RAISE NOTICE '  2. data_encerramento: validada >= data_publicacao';
    RAISE NOTICE '  3. sla_geral/sla_recrutamento: só calculados se datas válidas';
    RAISE NOTICE '  4. indicador_prazo: baseado em hired_at >= opened_at';
    RAISE NOTICE '================================================================================';
END $$;
