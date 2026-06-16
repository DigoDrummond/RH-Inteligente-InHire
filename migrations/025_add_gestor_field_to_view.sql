/*
================================================================================
MIGRATION 025: Adiciona campo 'gestor' à view vw_analise_posicoes
================================================================================

Data: 2026-02-06
Descrição:
  Adiciona o campo 'gestor' extraído de v.custom_fields->>'Gestor'
  à view vw_analise_posicoes.

Problema:
  - O campo "Gestor" existia nos custom_fields de 12.7% das vagas
  - Mas não estava sendo exibido na view
  - Usuários relataram que o gestor aparece no InHire mas não na exportação

Solução:
  - Adiciona coluna 'gestor' usando v.custom_fields->>'Gestor'
  - Posicionada entre 'recrutador_vaga' e 'inicio_pendencia_cliente'

Impacto:
  - 111 posições (13.4%) terão campo gestor preenchido
  - View passa de 29 para 30 colunas
  - Exemplo: Posição 1178 agora mostra "Gestor: Lidiane Pereira"

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com campo gestor
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
    r.user_name AS responsavel,
    v.user_name AS recrutador_vaga,

    /*
    ============================================================================
    NOVO CAMPO: gestor
    ============================================================================
    Origem: v.custom_fields->>'Gestor'
    Descrição: Nome do gestor responsável pela vaga (quando informado)
    Preenchimento: ~13% das posições
    ============================================================================
    */
    v.custom_fields->>'Gestor' AS gestor,

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
    v.custom_fields->>'Classificação' AS classificacao_vaga,
    v.area AS area_vaga,
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
COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance, SLA e pendências. Atualizada em 2026-02-06 com adição do campo gestor (30 colunas).';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_gestor INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;
    SELECT COUNT(gestor) INTO v_com_gestor FROM vw_analise_posicoes;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 025';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Posições com gestor: % (%.1f%%)', v_com_gestor, (v_com_gestor::NUMERIC / v_total * 100);

    -- Verifica posição 1178 (exemplo reportado)
    DECLARE
        v_gestor TEXT;
    BEGIN
        SELECT gestor INTO v_gestor FROM vw_analise_posicoes WHERE id_position = 1178;
        IF v_gestor IS NOT NULL THEN
            RAISE NOTICE 'Posição 1178 - Gestor: % ✓', v_gestor;
        ELSE
            RAISE WARNING 'Posição 1178 - Gestor: NULL';
        END IF;
    END;

    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
RESULTADO ESPERADO:
================================================================================
Total de posições: 831
Posições com gestor: 111 (13.4%)
Posição 1178 - Gestor: Lidiane Pereira ✓
================================================================================

ESTRUTURA DA VIEW (30 colunas):
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
15. responsavel (da requisição)
16. recrutador_vaga (da vaga)
17. gestor (custom_fields da vaga) ⭐ NOVO
18. inicio_pendencia_cliente
19. fim_pendencia_cliente
20. sla_pendencia_cliente
21. num_ciclos_pausa
22. detalhamento_pausas
23. sla_recrutamento
24. nome_pessoa_contratada
25. email_pessoal
26. modalidade_contratacao
27. sla_geral
28. classificacao_vaga
29. area_vaga
30. indicador_prazo
================================================================================
*/
