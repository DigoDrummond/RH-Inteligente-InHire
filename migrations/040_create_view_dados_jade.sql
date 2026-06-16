/*
================================================================================
MIGRATION 040: Criar View para Dados Jade (Salário e Contratações)
================================================================================

Data: 2026-02-06
Descrição:
  Cria view vw_dados_jade com informações de posições contratadas incluindo:
  - Posição ID
  - Salário Min (custom_field: "Custo Hora (ideal) - Ex. R$ xx,xx")
  - Salário Max (vagas.salary_max)
  - Valor Venda (custom_field: "Valor da venda")
  - Valor Fechado (custom_field: "Salário acordado com o talento")
  - Nome Candidato (talentos.name via stage_name = 'Contratação')
  - Email Candidato (talentos.email via stage_name = 'Contratação')

Destino: Google Sheets página API_Dados_Jade

================================================================================
*/

-- Remove view se existir
DROP VIEW IF EXISTS vw_dados_jade CASCADE;

-- Cria view com dados de contratações
CREATE OR REPLACE VIEW vw_dados_jade AS
WITH candidatos_contratados AS (
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
    -- Identificação da posição
    p.id AS posicao_id,
    p.inhire_id AS posicao_inhire_id,
    v.id AS vaga_id,
    v.name AS cargo,

    -- Informações salariais e de valores
    r.custom_fields->>'Custo Hora (ideal) - Ex. R$ xx,xx' AS salario_min,
    v.salary_max,
    r.custom_fields->>'Valor da venda' AS valor_venda,
    r.custom_fields->>'Salário acordado com o talento' AS valor_fechado,

    -- Informações do candidato contratado
    cc.candidato_nome,
    cc.candidato_email,

    -- Informações adicionais
    p.hired_at AS data_contratacao,
    cl.name AS cliente,
    v.user_name AS recrutadora,
    r.user_name AS responsavel_requisicao,

    -- Datas de controle
    DATE(p.opened_at) AS data_publicacao,
    DATE(r.requested_at) AS data_solicitacao

FROM posicoes p
INNER JOIN vagas v ON v.id = p.vaga_id
LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
LEFT JOIN candidatos_contratados cc ON cc.vaga_id = v.id

-- Filtrar apenas posições com hired_at preenchido
WHERE p.hired_at IS NOT NULL

ORDER BY p.hired_at DESC;

-- Comentários
COMMENT ON VIEW vw_dados_jade IS
'View para exportação de dados de contratações incluindo valores salariais.
Criada em 2026-02-06 (Migration 040).
Campos de custom_fields da requisição:
- Salário Min: "Custo Hora (ideal) - Ex. R$ xx,xx"
- Valor Venda: "Valor da venda"
- Valor Fechado: "Salário acordado com o talento"
Destino: Google Sheets - API_Dados_Jade';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_candidato INTEGER;
    v_com_salario_min INTEGER;
    v_com_valor_venda INTEGER;
    v_com_valor_fechado INTEGER;
BEGIN
    -- Total
    SELECT COUNT(*) INTO v_total FROM vw_dados_jade;

    -- Com candidato
    SELECT COUNT(*) INTO v_com_candidato
    FROM vw_dados_jade
    WHERE candidato_nome IS NOT NULL;

    -- Com salário min
    SELECT COUNT(*) INTO v_com_salario_min
    FROM vw_dados_jade
    WHERE salario_min IS NOT NULL;

    -- Com valor venda
    SELECT COUNT(*) INTO v_com_valor_venda
    FROM vw_dados_jade
    WHERE valor_venda IS NOT NULL;

    -- Com valor fechado
    SELECT COUNT(*) INTO v_com_valor_fechado
    FROM vw_dados_jade
    WHERE valor_fechado IS NOT NULL;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'MIGRATION 040 - VIEW DADOS JADE CRIADA';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total de posições contratadas: %', v_total;
    RAISE NOTICE '';
    RAISE NOTICE 'Cobertura de dados:';
    RAISE NOTICE '  - Com candidato identificado: % (%.1f%%)', v_com_candidato, (v_com_candidato::float / v_total * 100);
    RAISE NOTICE '  - Com salário min: % (%.1f%%)', v_com_salario_min, (v_com_salario_min::float / v_total * 100);
    RAISE NOTICE '  - Com valor venda: % (%.1f%%)', v_com_valor_venda, (v_com_valor_venda::float / v_total * 100);
    RAISE NOTICE '  - Com valor fechado: % (%.1f%%)', v_com_valor_fechado, (v_com_valor_fechado::float / v_total * 100);
    RAISE NOTICE '';
    RAISE NOTICE 'Campos disponíveis na view:';
    RAISE NOTICE '  1. posicao_id';
    RAISE NOTICE '  2. salario_min (custom_field requisição)';
    RAISE NOTICE '  3. salary_max (campo direto vaga)';
    RAISE NOTICE '  4. valor_venda (custom_field requisição)';
    RAISE NOTICE '  5. valor_fechado (custom_field requisição)';
    RAISE NOTICE '  6. candidato_nome';
    RAISE NOTICE '  7. candidato_email';
    RAISE NOTICE '================================================================================';
END $$;
