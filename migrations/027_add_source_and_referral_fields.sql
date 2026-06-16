/*
================================================================================
MIGRATION 027: Adiciona Campos de Origem e Indicação
================================================================================

Data: 2026-02-06
Descrição:
  Adiciona 2 novos campos à view vw_analise_posicoes:
  1. source_candidato - canal de origem do candidato
  2. is_referral - boolean indicando se é indicação

Contexto:
  Após análise da cobertura da API InHire, identificamos que:
  - Campo 'source' existe em candidaturas (100% preenchido)
  - 2.040 candidaturas são indicações (2.5% do total)
  - Dados de origem são valiosos para análise de ROI e conversão

Solução:
  1. Criar CTE 'source_posicao' que identifica o source da posição
     - Prioriza source do candidato contratado
     - Fallback para source mais comum se não houver contratado
  2. Adicionar campo 'source_candidato' com o canal de origem
  3. Adicionar campo 'is_referral' (boolean) para indicações

Impacto:
  - View passa de 27 para 29 colunas
  - 88.4% das posições têm source identificado
  - 1.9% das posições identificadas como indicação
  - Permite análise de conversão por canal

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com campos de origem
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
),
/*
================================================================================
NOVA CTE: source_posicao
================================================================================
Identifica o canal de origem da posição
Lógica:
  1. Prioriza o source do candidato contratado (se houver)
  2. Se não houver contratado, pega o source mais comum entre candidatos
  3. Null se não houver candidatos
================================================================================
*/
source_posicao AS (
    SELECT
        p.id AS posicao_id,
        COALESCE(
            -- Prioriza source do candidato contratado
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            -- Fallback: source mais comum
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             GROUP BY cd.source
             ORDER BY COUNT(*) DESC
             LIMIT 1)
        ) AS source
    FROM posicoes p
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
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER AS sla_geral,
    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    /*
    ============================================================================
    NOVOS CAMPOS
    ============================================================================
    */

    -- Campo 1: Canal de origem do candidato
    -- Valores: linkedin, manual, jobPage, referral, direct-referral, employee, etc
    sp.source AS source_candidato,

    -- Campo 2: Indicador booleano de indicação
    -- TRUE se source for: referral, direct-referral ou employee
    CASE
        WHEN sp.source IN ('referral', 'direct-referral', 'employee') THEN TRUE
        ELSE FALSE
    END AS is_referral

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN source_posicao sp ON sp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
ORDER BY p.opened_at DESC NULLS LAST;

-- Comentário na view
COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance, SLA, pendências e origem dos candidatos. Atualizada em 2026-02-06 com campos source_candidato e is_referral (29 colunas).';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_num_cols INTEGER;
    v_com_source INTEGER;
    v_referrals INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_num_cols
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes';

    SELECT COUNT(source_candidato) INTO v_com_source FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_referrals FROM vw_analise_posicoes WHERE is_referral = TRUE;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 027';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Total de colunas: % (antes: 27)', v_num_cols;
    RAISE NOTICE '';
    RAISE NOTICE 'Campo source_candidato:';
    RAISE NOTICE '  Com preenchimento: % (%.1f%%)', v_com_source, (v_com_source::NUMERIC / v_total * 100);
    RAISE NOTICE '';
    RAISE NOTICE 'Campo is_referral:';
    RAISE NOTICE '  Indicações: % (%.1f%%)', v_referrals, (v_referrals::NUMERIC / v_total * 100);
    RAISE NOTICE '';

    -- Distribuição por canal
    RAISE NOTICE 'Top 5 canais:';
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN
            SELECT source_candidato, COUNT(*) as qtd
            FROM vw_analise_posicoes
            WHERE source_candidato IS NOT NULL
            GROUP BY source_candidato
            ORDER BY qtd DESC
            LIMIT 5
        LOOP
            RAISE NOTICE '  %: %', r.source_candidato, r.qtd;
        END LOOP;
    END;

    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
RESULTADO ESPERADO:
================================================================================
Total de posições: 831
Total de colunas: 29 (antes: 27)

Campo source_candidato:
  Com preenchimento: 735 (88.4%)

Campo is_referral:
  Indicações: 16 (1.9%)

Top 5 canais:
  manual: 337
  linkedin: 274
  jobPage: 95
  gupy: 11
  referral: 6
================================================================================

ESTRUTURA DA VIEW (29 colunas):
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
15. responsavel
16. recrutador_vaga
17. inicio_pendencia_cliente
18. fim_pendencia_cliente
19. sla_pendencia_cliente
20. num_ciclos_pausa
21. detalhamento_pausas
22. sla_recrutamento
23. nome_pessoa_contratada
24. email_pessoal
25. modalidade_contratacao
26. sla_geral
27. indicador_prazo
28. source_candidato ⭐ NOVO
29. is_referral ⭐ NOVO
================================================================================

VALOR AGREGADO:
================================================================================
- Análise de ROI por canal de aquisição
- Identificação de indicações (programa de referral)
- Comparação de conversão entre canais
- Priorização de canais mais efetivos
- Dashboard de performance por origem
- Benchmark de fontes de candidatos
================================================================================
*/
