/*
================================================================================
MIGRATION 030: Implementar Cálculo de Dias Úteis nos SLAs
================================================================================

Data: 2026-02-06
Descrição:
  Implementa cálculo de dias úteis (excluindo finais de semana e feriados)
  para todos os campos de SLA na view vw_analise_posicoes.

  Inclui feriados nacionais e de Minas Gerais.

Impacto:
  - Cria tabela 'feriados' com feriados nacionais e de MG
  - Cria função 'calcular_dias_uteis' para cálculo de dias úteis
  - Atualiza view vw_analise_posicoes com cálculos corretos

Campos afetados:
  - sla_recrutamento (data_publicacao - data_abertura)
  - sla_geral (data_encerramento - data_abertura)
  - sla_pendencia_cliente (total de dias pausado)

================================================================================
*/

-- 1. Criar tabela de feriados
CREATE TABLE IF NOT EXISTS feriados (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- 'NACIONAL', 'ESTADUAL_MG', 'MUNICIPAL_MG'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE feriados IS 'Tabela de feriados nacionais e regionais (MG) para cálculo de dias úteis';

-- 2. Popular tabela de feriados (2024-2026)
-- Feriados Nacionais Fixos
INSERT INTO feriados (data, nome, tipo) VALUES
-- 2024
('2024-01-01', 'Ano Novo', 'NACIONAL'),
('2024-04-21', 'Tiradentes', 'NACIONAL'),
('2024-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2024-09-07', 'Independência do Brasil', 'NACIONAL'),
('2024-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2024-11-02', 'Finados', 'NACIONAL'),
('2024-11-15', 'Proclamação da República', 'NACIONAL'),
('2024-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2024-12-25', 'Natal', 'NACIONAL'),

-- 2025
('2025-01-01', 'Ano Novo', 'NACIONAL'),
('2025-04-21', 'Tiradentes', 'NACIONAL'),
('2025-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2025-09-07', 'Independência do Brasil', 'NACIONAL'),
('2025-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2025-11-02', 'Finados', 'NACIONAL'),
('2025-11-15', 'Proclamação da República', 'NACIONAL'),
('2025-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2025-12-25', 'Natal', 'NACIONAL'),

-- 2026
('2026-01-01', 'Ano Novo', 'NACIONAL'),
('2026-04-21', 'Tiradentes', 'NACIONAL'),
('2026-05-01', 'Dia do Trabalho', 'NACIONAL'),
('2026-09-07', 'Independência do Brasil', 'NACIONAL'),
('2026-10-12', 'Nossa Senhora Aparecida', 'NACIONAL'),
('2026-11-02', 'Finados', 'NACIONAL'),
('2026-11-15', 'Proclamação da República', 'NACIONAL'),
('2026-11-20', 'Dia da Consciência Negra', 'NACIONAL'),
('2026-12-25', 'Natal', 'NACIONAL')

ON CONFLICT (data) DO NOTHING;

-- Feriados Móveis (Carnaval, Páscoa, Corpus Christi)
INSERT INTO feriados (data, nome, tipo) VALUES
-- 2024
('2024-02-13', 'Carnaval', 'NACIONAL'),
('2024-03-29', 'Sexta-feira Santa', 'NACIONAL'),
('2024-05-30', 'Corpus Christi', 'NACIONAL'),

-- 2025
('2025-03-04', 'Carnaval', 'NACIONAL'),
('2025-04-18', 'Sexta-feira Santa', 'NACIONAL'),
('2025-06-19', 'Corpus Christi', 'NACIONAL'),

-- 2026
('2026-02-17', 'Carnaval', 'NACIONAL'),
('2026-04-03', 'Sexta-feira Santa', 'NACIONAL'),
('2026-06-04', 'Corpus Christi', 'NACIONAL')

ON CONFLICT (data) DO NOTHING;

-- Feriados Estaduais de Minas Gerais
INSERT INTO feriados (data, nome, tipo) VALUES
-- 2024
('2024-04-21', 'Tiradentes (Patrono de MG)', 'ESTADUAL_MG'),

-- 2025
('2025-04-21', 'Tiradentes (Patrono de MG)', 'ESTADUAL_MG'),

-- 2026
('2026-04-21', 'Tiradentes (Patrono de MG)', 'ESTADUAL_MG')

ON CONFLICT (data) DO NOTHING;

-- 3. Criar função para calcular dias úteis
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
    -- Se alguma data for NULL, retornar NULL
    IF data_inicio IS NULL OR data_fim IS NULL THEN
        RETURN NULL;
    END IF;

    -- Se data_fim < data_inicio, retornar 0
    IF data_fim < data_inicio THEN
        RETURN 0;
    END IF;

    -- Iterar por cada dia no período
    data_atual := data_inicio;

    WHILE data_atual <= data_fim LOOP
        -- Verificar dia da semana (1=domingo, 7=sábado)
        dia_semana := EXTRACT(DOW FROM data_atual);

        -- Verificar se é feriado
        SELECT EXISTS(SELECT 1 FROM feriados WHERE data = data_atual) INTO eh_feriado;

        -- Contar apenas se for dia útil (seg-sex e não feriado)
        IF dia_semana BETWEEN 1 AND 5 AND NOT eh_feriado THEN
            dias_uteis := dias_uteis + 1;
        END IF;

        data_atual := data_atual + 1;
    END LOOP;

    RETURN dias_uteis;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calcular_dias_uteis IS 'Calcula dias úteis entre duas datas, excluindo finais de semana e feriados';

-- 4. Atualizar view vw_analise_posicoes com cálculos de dias úteis
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

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
        -- Usar calcular_dias_uteis para cada período de pausa
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
    -- SLA Recrutamento em dias úteis
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN calcular_dias_uteis(DATE(r.requested_at), DATE(p.opened_at))
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    -- SLA Geral em dias úteis
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

COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance em DIAS ÚTEIS. SLAs calculados excluindo finais de semana e feriados (nacionais e MG). Atualizada em 2026-02-06.';

-- 5. Validação
DO $$
DECLARE
    v_total_posicoes INTEGER;
    v_total_feriados INTEGER;
    v_teste_dias_uteis INTEGER;
BEGIN
    -- Total de posições
    SELECT COUNT(*) INTO v_total_posicoes FROM vw_analise_posicoes;

    -- Total de feriados cadastrados
    SELECT COUNT(*) INTO v_total_feriados FROM feriados;

    -- Teste da função: contar dias úteis em janeiro/2024 (01 a 31)
    -- Esperado: 23 dias úteis (31 dias - 8 finais semana - 1 feriado ano novo)
    SELECT calcular_dias_uteis('2024-01-01'::DATE, '2024-01-31'::DATE) INTO v_teste_dias_uteis;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 030';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: % (esperado: 830)', v_total_posicoes;
    RAISE NOTICE 'Total de feriados cadastrados: %', v_total_feriados;
    RAISE NOTICE '';
    RAISE NOTICE 'Teste função calcular_dias_uteis:';
    RAISE NOTICE '  Período: 01/01/2024 a 31/01/2024';
    RAISE NOTICE '  Dias úteis: % (esperado: 22)', v_teste_dias_uteis;
    RAISE NOTICE '';
    RAISE NOTICE 'Melhorias implementadas:';
    RAISE NOTICE '  1. Tabela de feriados criada (nacionais e MG)';
    RAISE NOTICE '  2. Função calcular_dias_uteis implementada';
    RAISE NOTICE '  3. SLA Recrutamento - agora em dias úteis';
    RAISE NOTICE '  4. SLA Geral - agora em dias úteis';
    RAISE NOTICE '  5. SLA Pendência Cliente - agora em dias úteis';
    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
NOTAS
================================================================================
- Todos os SLAs agora são calculados em DIAS ÚTEIS
- Feriados incluídos: nacionais e estaduais de MG (2024-2026)
- Para adicionar mais feriados: INSERT INTO feriados (data, nome, tipo)
- Para adicionar anos futuros: executar novos INSERTs
================================================================================
*/
