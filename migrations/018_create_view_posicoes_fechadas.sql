-- Migration: Criar view de posições fechadas com dados dos contratados
-- Data: 2026-02-03
-- Descrição: View consolidada com informações sobre posições fechadas/preenchidas

-- Remove a view se já existir
DROP VIEW IF EXISTS vw_posicoes_fechadas;

-- Cria a view com as informações solicitadas
CREATE OR REPLACE VIEW vw_posicoes_fechadas AS
SELECT
    p.inhire_id AS codigo_posicao,
    p.hired_at AS data_fechamento,
    p.status AS status_fechado,
    t.name AS nome_contratado,
    t.email AS email_contratado,
    -- Informações adicionais úteis
    p.vaga_id,
    v.name AS nome_vaga,
    v.area AS area_vaga,
    p.opened_at AS data_abertura,
    -- Calcula tempo para preenchimento (em dias)
    CASE
        WHEN p.hired_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN EXTRACT(DAY FROM (p.hired_at - p.opened_at))
        ELSE NULL
    END AS dias_para_preencher,
    -- Responsável pela contratação
    p.user_name AS responsavel_contratacao,
    -- Timestamps de auditoria
    p.created_at,
    p.updated_at
FROM
    posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN talentos t ON p.talent_id = t.inhire_id
WHERE
    -- Filtra apenas posições fechadas/preenchidas/contratadas
    p.status IN ('filled', 'hired', 'closed')
    AND p.hired_at IS NOT NULL
ORDER BY
    p.hired_at DESC;

-- Adiciona comentário na view
COMMENT ON VIEW vw_posicoes_fechadas IS
'View consolidada de posições fechadas com informações dos contratados.
Inclui apenas posições com status filled/hired/closed e data de contratação preenchida.';

-- Adiciona comentários nas colunas principais
COMMENT ON COLUMN vw_posicoes_fechadas.codigo_posicao IS 'ID da posição no sistema InHire';
COMMENT ON COLUMN vw_posicoes_fechadas.data_fechamento IS 'Data em que a posição foi preenchida/fechada';
COMMENT ON COLUMN vw_posicoes_fechadas.status_fechado IS 'Status final da posição (filled, hired ou closed)';
COMMENT ON COLUMN vw_posicoes_fechadas.nome_contratado IS 'Nome completo do talento contratado';
COMMENT ON COLUMN vw_posicoes_fechadas.email_contratado IS 'E-mail do talento contratado';
COMMENT ON COLUMN vw_posicoes_fechadas.dias_para_preencher IS 'Número de dias entre abertura e fechamento da posição';
