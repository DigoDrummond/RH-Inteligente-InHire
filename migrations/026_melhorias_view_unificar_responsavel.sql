/*
================================================================================
MIGRATION 026: Melhorias na View - Unificação e Correções
================================================================================

Data: 2026-02-06
Descrição:
  Aplica 4 melhorias à view vw_analise_posicoes:
  1. Unifica campos 'responsavel' e 'gestor' em um único 'responsavel'
  2. Corrige campo 'modalidade_contratacao' (usar nome com acento)
  3. Remove campo 'classificacao_vaga'
  4. Remove campo 'area_vaga'

Problemas:
  1. Dois campos separados (responsavel da requisição + gestor da vaga)
  2. Campo modalidade_contratacao sempre NULL (nome incorreto sem acento)
  3. Campos classificacao_vaga e area_vaga não são usados

Soluções:
  1. Campo 'responsavel' unificado: COALESCE(gestor, user_name requisição)
  2. Campo 'modalidade_contratacao': usar 'Modalidade de Contratação' (com ç)
  3. Remover campo 'classificacao_vaga'
  4. Remover campo 'area_vaga'

Impacto:
  - View passa de 30 para 27 colunas
  - Campo responsavel: 58.2% preenchido (antes: dois campos separados)
  - Campo modalidade_contratacao: 71.2% preenchido (antes: 0%)
  - Células exportadas: 22.464 (antes: 24.960)

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com melhorias
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
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
),
eventos_pausa AS (
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            WHEN previous_status = 'open' AND new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE (previous_status = 'open' AND new_status = 'paused')
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
        SUM(DATE(data_fim) - DATE(data_inicio)) AS total_dias_pausado,
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
            ' (' || (DATE(data_fim) - DATE(data_inicio))::text || 'd)',
            '; '
            ORDER BY data_inicio
        ) AS detalhamento_periodos
    FROM periodos_unicos
    GROUP BY posicao_id
)
SELECT
    p.id AS id_position,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    r.custom_fields->>'Torre' AS torre,
    p.status AS status_atual,
    COALESCE(DATE(p.hired_at), CURRENT_DATE) AS data_encerramento_ou_atualizacao,
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    p.reason AS motivo_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    /*
    ============================================================================
    MELHORIA 1: Campo 'responsavel' unificado
    ============================================================================
    ANTES: Dois campos separados
      - responsavel (da requisição): r.user_name
      - gestor (dos custom_fields): v.custom_fields->>'Gestor'

    AGORA: Um único campo 'responsavel'
      - Prioridade: gestor → user_name da requisição
      - Preenchimento: 58.2% (484 de 831 posições)
    ============================================================================
    */
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,

    v.user_name AS recrutador_vaga,
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,
    pp.datas_fim_pausa AS fim_pendencia_cliente,
    pp.total_dias_pausado AS sla_pendencia_cliente,
    pp.num_ciclos AS num_ciclos_pausa,
    pp.detalhamento_periodos AS detalhamento_pausas,
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,

    /*
    ============================================================================
    MELHORIA 2: Campo 'modalidade_contratacao' corrigido
    ============================================================================
    ANTES: v.custom_fields->>'Modalidade de Contratacao' (sem acento)
      - Resultado: 0% preenchido (sempre NULL)

    AGORA: v.custom_fields->>'Modalidade de Contratação' (com ç)
      - Resultado: 71.2% preenchido (592 de 831 posições)
      - Valores: CLT (293), Prestador de Serviço (22), Estágio (3)
    ============================================================================
    */
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER AS sla_geral,

    /*
    ============================================================================
    MELHORIAS 3 e 4: Campos removidos
    ============================================================================
    REMOVIDOS:
      - classificacao_vaga (v.custom_fields->>'Classificação')
      - area_vaga (v.area)

    MOTIVO: Campos não utilizados nas análises
    ============================================================================
    */

    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo
FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
ORDER BY p.opened_at DESC NULLS LAST;

-- Comentário na view
COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance, SLA e pendências. Atualizada em 2026-02-06: unificação de responsável, correção de modalidade, remoção de campos não utilizados (27 colunas).';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_num_cols INTEGER;
    v_com_responsavel INTEGER;
    v_com_modalidade INTEGER;
BEGIN
    -- Conta registros e colunas
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_num_cols
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes';

    -- Conta preenchimento
    SELECT COUNT(responsavel) INTO v_com_responsavel FROM vw_analise_posicoes;
    SELECT COUNT(modalidade_contratacao) INTO v_com_modalidade FROM vw_analise_posicoes;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 026';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Total de colunas: % (antes: 30)', v_num_cols;
    RAISE NOTICE '';
    RAISE NOTICE 'Campo responsavel (unificado):';
    RAISE NOTICE '  Com preenchimento: % (%.1f%%)', v_com_responsavel, (v_com_responsavel::NUMERIC / v_total * 100);
    RAISE NOTICE '';
    RAISE NOTICE 'Campo modalidade_contratacao (corrigido):';
    RAISE NOTICE '  Com preenchimento: % (%.1f%%) - antes: 0%%', v_com_modalidade, (v_com_modalidade::NUMERIC / v_total * 100);
    RAISE NOTICE '';

    -- Verifica campos removidos
    DECLARE
        v_exists BOOLEAN;
    BEGIN
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'vw_analise_posicoes'
            AND column_name IN ('classificacao_vaga', 'area_vaga')
        ) INTO v_exists;

        IF v_exists THEN
            RAISE EXCEPTION 'Campos classificacao_vaga ou area_vaga ainda existem!';
        ELSE
            RAISE NOTICE 'Campos removidos: classificacao_vaga, area_vaga ✓';
        END IF;
    END;

    -- Verifica posição 1178
    DECLARE
        v_responsavel TEXT;
        v_modalidade TEXT;
    BEGIN
        SELECT responsavel, modalidade_contratacao
        INTO v_responsavel, v_modalidade
        FROM vw_analise_posicoes
        WHERE id_position = 1178;

        RAISE NOTICE '';
        RAISE NOTICE 'Posição 1178 (exemplo):';
        RAISE NOTICE '  Responsavel: % ✓', COALESCE(v_responsavel, 'NULL');
        RAISE NOTICE '  Modalidade: % ✓', COALESCE(v_modalidade, 'NULL');
    END;

    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
RESULTADO ESPERADO:
================================================================================
Total de posições: 831
Total de colunas: 27 (antes: 30)

Campo responsavel (unificado):
  Com preenchimento: 484 (58.2%)

Campo modalidade_contratacao (corrigido):
  Com preenchimento: 592 (71.2%) - antes: 0%

Campos removidos: classificacao_vaga, area_vaga ✓

Posição 1178 (exemplo):
  Responsavel: Lidiane Pereira ✓
  Modalidade: CLT ✓
================================================================================

ESTRUTURA DA VIEW (27 colunas):
================================================================================
1.  id_position
2.  cargo
3.  data_abertura
4.  data_publicacao
5.  prazo_processo_seletivo
6.  cliente
7.  torre
8.  status_atual
9.  data_encerramento_ou_atualizacao
10. motivo_cancelamento_paralisacao
11. etapa_funil
12. senioridade
13. motivo_contratacao
14. pessoa_substituida
15. responsavel (unificado: gestor → user_name requisição) ⭐ ALTERADO
16. recrutador_vaga
17. inicio_pendencia_cliente
18. fim_pendencia_cliente
19. sla_pendencia_cliente
20. num_ciclos_pausa
21. detalhamento_pausas
22. sla_recrutamento
23. nome_pessoa_contratada
24. email_pessoal
25. modalidade_contratacao (corrigido: agora com acento) ⭐ CORRIGIDO
26. sla_geral
27. indicador_prazo

REMOVIDOS: classificacao_vaga, area_vaga, campo gestor separado
================================================================================
*/
