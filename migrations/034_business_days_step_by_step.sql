/*
================================================================================
MIGRATION 034: Dias Úteis - Passo a Passo (VERSÃO FINAL)
================================================================================

IMPORTANTE: Execute esta migration em 3 PASSOS SEPARADOS no pgAdmin!
Não execute tudo de uma vez. Selecione e execute cada seção separadamente.

================================================================================
*/

-- ============================================================================
-- PASSO 1: LIMPAR TUDO (EXECUTE ESTE BLOCO PRIMEIRO)
-- ============================================================================

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vw_analise_posicoes CASCADE;
DROP FUNCTION IF EXISTS calcular_dias_uteis(DATE, DATE) CASCADE;
DROP TABLE IF EXISTS feriados CASCADE;

-- Verificação
DO $$
BEGIN
    RAISE NOTICE 'PASSO 1 COMPLETO - Tudo foi removido. Execute o PASSO 2 agora.';
END $$;

-- ============================================================================
-- PASSO 2: CRIAR TABELA, FUNÇÃO E TESTAR (EXECUTE ESTE BLOCO SEGUNDO)
-- ============================================================================

-- Criar tabela
CREATE TABLE feriados (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Popular feriados
INSERT INTO feriados (data, nome, tipo) VALUES
('2024-01-01', 'Ano Novo', 'NACIONAL'),
('2024-04-21', 'Tiradentes', 'NACIONAL'),
('2024-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2024-09-07', 'Independência do Brasil', 'NACIONAL'),
('2024-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2024-11-02', 'Finados', 'NACIONAL'),
('2024-11-15', 'Proclamação da República', 'NACIONAL'),
('2024-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2024-12-25', 'Natal', 'NACIONAL'),
('2025-01-01', 'Ano Novo', 'NACIONAL'),
('2025-04-21', 'Tiradentes', 'NACIONAL'),
('2025-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2025-09-07', 'Independência do Brasil', 'NACIONAL'),
('2025-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2025-11-02', 'Finados', 'NACIONAL'),
('2025-11-15', 'Proclamação da República', 'NACIONAL'),
('2025-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2025-12-25', 'Natal', 'NACIONAL'),
('2026-01-01', 'Ano Novo', 'NACIONAL'),
('2026-04-21', 'Tiradentes', 'NACIONAL'),
('2026-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2026-09-07', 'Independência do Brasil', 'NACIONAL'),
('2026-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2026-11-02', 'Finados', 'NACIONAL'),
('2026-11-15', 'Proclamação da República', 'NACIONAL'),
('2026-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2026-12-25', 'Natal', 'NACIONAL'),
('2024-02-13', 'Carnaval', 'NACIONAL'),
('2024-03-29', 'Sexta-feira Santa', 'NACIONAL'),
('2024-05-30', 'Corpus Christi', 'NACIONAL'),
('2025-03-04', 'Carnaval', 'NACIONAL'),
('2025-04-18', 'Sexta-feira Santa', 'NACIONAL'),
('2025-06-19', 'Corpus Christi', 'NACIONAL'),
('2026-02-17', 'Carnaval', 'NACIONAL'),
('2026-04-03', 'Sexta-feira Santa', 'NACIONAL'),
('2026-06-04', 'Corpus Christi', 'NACIONAL');

-- Criar função
CREATE OR REPLACE FUNCTION calcular_dias_uteis(
    data_inicio DATE,
    data_fim DATE
) RETURNS INTEGER AS $$
DECLARE
    dias_uteis INTEGER := 0;
    data_atual DATE;
    dia_semana INTEGER;
    eh_feriado BOOLEAN;
BEGIN
    IF data_inicio IS NULL OR data_fim IS NULL THEN
        RETURN NULL;
    END IF;

    IF data_fim < data_inicio THEN
        RETURN 0;
    END IF;

    data_atual := data_inicio;

    WHILE data_atual <= data_fim LOOP
        dia_semana := EXTRACT(DOW FROM data_atual);
        SELECT EXISTS(SELECT 1 FROM feriados WHERE data = data_atual) INTO eh_feriado;

        IF dia_semana BETWEEN 1 AND 5 AND NOT eh_feriado THEN
            dias_uteis := dias_uteis + 1;
        END IF;

        data_atual := data_atual + 1;
    END LOOP;

    RETURN dias_uteis;
END;
$$ LANGUAGE plpgsql;

-- Testar função
DO $$
DECLARE
    v_teste INTEGER;
    v_feriados INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_feriados FROM feriados;
    v_teste := calcular_dias_uteis('2024-01-01'::DATE, '2024-01-31'::DATE);

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'PASSO 2 COMPLETO';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Feriados cadastrados: %', v_feriados;
    RAISE NOTICE 'Teste função Janeiro/2024: % dias úteis (esperado: 22)', v_teste;
    RAISE NOTICE '';
    RAISE NOTICE 'Tudo OK! Execute o PASSO 3 agora para criar a view.';
    RAISE NOTICE '================================================================================';
END $$;

-- ============================================================================
-- PASSO 3: CRIAR MATERIALIZED VIEW E ÍNDICES (EXECUTE ESTE BLOCO POR ÚLTIMO)
-- ============================================================================

CREATE MATERIALIZED VIEW vw_analise_posicoes AS
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
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
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
),
source_posicao AS (
    SELECT
        p.id AS posicao_id,
        COALESCE(
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
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
    COALESCE(usp.new_status, p.status) AS status_atual,
    COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at), CURRENT_DATE) AS data_encerramento_ou_atualizacao,
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
        THEN calcular_dias_uteis(DATE(r.requested_at), DATE(p.opened_at))
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    calcular_dias_uteis(
        DATE(COALESCE(r.requested_at, p.opened_at)),
        COALESCE(DATE(p.hired_at), CURRENT_DATE)
    ) AS sla_geral,
    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN calcular_dias_uteis(
                    DATE(COALESCE(r.requested_at, p.opened_at)),
                    COALESCE(DATE(p.hired_at), CURRENT_DATE)
                ) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,
    sp.source AS source_candidato,
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
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- Criar índices
CREATE UNIQUE INDEX idx_vw_analise_posicoes_id ON vw_analise_posicoes (id_position);
CREATE INDEX idx_vw_analise_posicoes_status ON vw_analise_posicoes (status_atual);
CREATE INDEX idx_vw_analise_posicoes_cliente ON vw_analise_posicoes (cliente);
CREATE INDEX idx_vw_analise_posicoes_cargo ON vw_analise_posicoes (cargo);
CREATE INDEX idx_vw_analise_posicoes_torre ON vw_analise_posicoes (torre);

-- Validação final
DO $$
DECLARE
    v_total_posicoes INTEGER;
    v_sla_241 INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total_posicoes FROM vw_analise_posicoes;
    SELECT sla_geral INTO v_sla_241 FROM vw_analise_posicoes WHERE id_position = 241;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'PASSO 3 COMPLETO - MIGRATION 034 FINALIZADA!';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: % (esperado: 830)', v_total_posicoes;
    RAISE NOTICE 'Posição 241 - SLA Geral: % dias úteis', COALESCE(v_sla_241::TEXT, 'NULL');
    RAISE NOTICE '';
    RAISE NOTICE 'SUCESSO! Todos os SLAs agora em DIAS ÚTEIS!';
    RAISE NOTICE 'View é MATERIALIZED - consultas são instantâneas!';
    RAISE NOTICE '';
    RAISE NOTICE 'Para atualizar após sincronização:';
    RAISE NOTICE '  REFRESH MATERIALIZED VIEW vw_analise_posicoes;';
    RAISE NOTICE '================================================================================';
END $$;
