-- ================================================================================
-- MAPEAMENTO COMPLETO: CANDIDATOS, VAGAS, STATUS E PROGRESSÃO NO FUNIL (KANBAN)
-- ================================================================================
--
-- Este script mapeia todas as pessoas que se candidataram, mostrando:
-- 1. Dados do candidato (talento)
-- 2. Vaga para qual se candidatou
-- 3. Status atual da candidatura
-- 4. Progressão completa no funil (Kanban) via timeline
-- 5. Dados da requisição (se aprovada)
--
-- Data: 2026-07-07
-- ================================================================================

-- ================================================================================
-- TABELA 1: VISÃO GERAL - CANDIDATOS E STATUS ATUAL
-- ================================================================================
-- Mostra todos os candidatos, vaga, status atual e stage/phase atual no Kanban
-- ================================================================================

CREATE OR REPLACE VIEW vw_candidatos_status_atual AS
SELECT
    -- === DADOS DO CANDIDATO (TALENTO) ===
    t.id AS talento_id,
    t.inhire_id AS talento_inhire_id,
    t.name AS candidato_nome,
    t.email AS candidato_email,
    t.phone AS candidato_telefone,
    t.headline AS candidato_cargo_atual,
    t.company AS candidato_empresa_atual,
    t.location AS candidato_localizacao,
    t.linkedin_username AS candidato_linkedin,

    -- === DADOS DA VAGA ===
    v.id AS vaga_id,
    v.inhire_id AS vaga_inhire_id,
    v.name AS vaga_nome,
    v.area AS vaga_area,
    v.seniority AS vaga_senioridade,
    v.status AS vaga_status,
    v.location AS vaga_localizacao,
    v.salary_max AS vaga_salario_max,

    -- === DADOS DA CANDIDATURA ===
    c.id AS candidatura_id,
    c.inhire_id AS candidatura_inhire_id,
    c.status AS candidatura_status,
    c.source AS candidatura_origem,  -- LinkedIn, Indeed, Site da Empresa, etc.
    c.applied_at AS candidatura_data_aplicacao,

    -- === POSIÇÃO ATUAL NO KANBAN (STAGE/PHASE) ===
    c.stage_name AS kanban_stage_atual,
    c.stage_order AS kanban_stage_ordem,
    c.phase_name AS kanban_phase_atual,
    c.phase_order AS kanban_phase_ordem,

    -- === DADOS DA REQUISIÇÃO (SE EXISTE) ===
    r.id AS requisicao_id,
    r.status AS requisicao_status,
    r.reason AS requisicao_motivo,
    r.name AS requisicao_nome,

    -- === METADADOS ===
    c.created_at_inhire AS candidatura_criada_em,
    c.updated_at_inhire AS candidatura_atualizada_em,
    EXTRACT(DAY FROM NOW() - c.created_at_inhire) AS dias_desde_aplicacao,

    -- === CLASSIFICAÇÕES ÚTEIS ===
    CASE
        WHEN c.status = 'active' THEN 'Em Processo'
        WHEN c.status = 'hired' THEN 'Contratado ✅'
        WHEN c.status = 'rejected' THEN 'Rejeitado ❌'
        WHEN c.status = 'declined' THEN 'Declinou ⛔'
        ELSE 'Inativo'
    END AS candidatura_status_portugues,

    CASE
        WHEN c.status = 'hired' THEN 1
        WHEN c.status = 'active' AND c.stage_order >= 3 THEN 2
        WHEN c.status = 'active' THEN 3
        WHEN c.status = 'rejected' THEN 4
        ELSE 5
    END AS prioridade_acompanhamento

FROM candidaturas c
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN requisicoes r ON v.id = r.vaga_id
ORDER BY
    c.status DESC,
    c.updated_at_inhire DESC;


-- ================================================================================
-- TABELA 2: PROGRESSÃO COMPLETA NO FUNIL (TIMELINE DO KANBAN)
-- ================================================================================
-- Mostra TODAS as movimentações de cada candidato pelo Kanban
-- ================================================================================

CREATE OR REPLACE VIEW vw_candidatos_progressao_funil AS
SELECT
    -- === IDENTIFICAÇÃO ===
    t.name AS candidato_nome,
    v.name AS vaga_nome,
    c.inhire_id AS candidatura_inhire_id,

    -- === EVENTO NO TIMELINE ===
    ct.id AS evento_id,
    ct.changed_at AS evento_data,
    ct.event_type AS evento_tipo,

    -- === MOVIMENTAÇÃO NO KANBAN ===
    ct.from_stage_name AS de_stage,
    ct.from_stage_order AS de_stage_ordem,
    ct.to_stage_name AS para_stage,
    ct.to_stage_order AS para_stage_ordem,

    ct.from_phase_name AS de_phase,
    ct.from_phase_order AS de_phase_ordem,
    ct.to_phase_name AS para_phase,
    ct.to_phase_order AS para_phase_ordem,

    -- === DADOS ADICIONAIS ===
    ct.changed_by_name AS alterado_por,
    ct.notes AS observacoes,
    ct.duration_days AS dias_no_stage_anterior,

    -- === INTERPRETAÇÃO ===
    CASE
        WHEN ct.to_stage_order > ct.from_stage_order THEN '↗️ Avançou'
        WHEN ct.to_stage_order < ct.from_stage_order THEN '↘️ Retrocedeu'
        ELSE '↔️ Moveu lateralmente'
    END AS tipo_movimentacao,

    CASE
        WHEN ct.event_type LIKE '%hired%' THEN '✅ CONTRATADO'
        WHEN ct.event_type LIKE '%rejected%' THEN '❌ REJEITADO'
        WHEN ct.event_type LIKE '%declined%' THEN '⛔ DESISTIU'
        WHEN ct.event_type LIKE '%stage%' THEN '📊 Mudou de fase'
        ELSE ct.event_type
    END AS evento_tipo_portugues,

    -- === ORDEM CRONOLÓGICA ===
    ROW_NUMBER() OVER (
        PARTITION BY ct.candidatura_id
        ORDER BY ct.changed_at
    ) AS numero_movimento

FROM candidatura_timeline ct
INNER JOIN candidaturas c ON ct.candidatura_id = c.id
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
ORDER BY
    c.id,
    ct.changed_at;


-- ================================================================================
-- TABELA 3: FUNIL DE CONVERSÃO POR VAGA
-- ================================================================================
-- Análise quantitativa: quantos candidatos em cada stage do funil
-- ================================================================================

CREATE OR REPLACE VIEW vw_funil_conversao_vagas AS
SELECT
    v.name AS vaga_nome,
    v.area AS vaga_area,
    v.status AS vaga_status,

    -- === CONTADORES POR STATUS ===
    COUNT(DISTINCT c.id) AS total_candidaturas,
    COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) AS candidatos_ativos,
    COUNT(DISTINCT CASE WHEN c.status = 'hired' THEN c.id END) AS candidatos_contratados,
    COUNT(DISTINCT CASE WHEN c.status = 'rejected' THEN c.id END) AS candidatos_rejeitados,
    COUNT(DISTINCT CASE WHEN c.status = 'declined' THEN c.id END) AS candidatos_desistiram,

    -- === CONTADORES POR STAGE (KANBAN) ===
    COUNT(DISTINCT CASE WHEN c.stage_order = 1 THEN c.id END) AS stage_1_triagem,
    COUNT(DISTINCT CASE WHEN c.stage_order = 2 THEN c.id END) AS stage_2_entrevista_inicial,
    COUNT(DISTINCT CASE WHEN c.stage_order = 3 THEN c.id END) AS stage_3_entrevista_tecnica,
    COUNT(DISTINCT CASE WHEN c.stage_order = 4 THEN c.id END) AS stage_4_entrevista_final,
    COUNT(DISTINCT CASE WHEN c.stage_order >= 5 THEN c.id END) AS stage_5_proposta_ou_final,

    -- === TAXAS DE CONVERSÃO ===
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN c.status = 'hired' THEN c.id END) /
        NULLIF(COUNT(DISTINCT c.id), 0),
        2
    ) AS taxa_conversao_contratacao_pct,

    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN c.stage_order >= 3 THEN c.id END) /
        NULLIF(COUNT(DISTINCT c.id), 0),
        2
    ) AS taxa_chegou_entrevista_tecnica_pct,

    -- === TEMPOS MÉDIOS ===
    ROUND(AVG(EXTRACT(DAY FROM NOW() - c.created_at_inhire)), 1) AS dias_medio_processo,

    -- === DADOS DA REQUISIÇÃO ===
    r.status AS requisicao_status,
    r.reason AS requisicao_motivo

FROM vagas v
LEFT JOIN candidaturas c ON v.id = c.vaga_id
LEFT JOIN requisicoes r ON v.id = r.vaga_id
GROUP BY
    v.id, v.name, v.area, v.status,
    r.status, r.reason
HAVING COUNT(DISTINCT c.id) > 0  -- Apenas vagas com candidatos
ORDER BY
    total_candidaturas DESC;


-- ================================================================================
-- TABELA 4: CANDIDATOS COM DADOS COMPLETOS (TODAS AS FONTES)
-- ================================================================================
-- Combina TUDO: Talento + Candidatura + Timeline + Requisição
-- ================================================================================

CREATE OR REPLACE VIEW vw_candidatos_completo AS
SELECT
    -- === IDENTIFICAÇÃO ===
    t.id AS talento_id,
    t.inhire_id AS talento_inhire_id,
    c.id AS candidatura_id,
    c.inhire_id AS candidatura_inhire_id,

    -- === DADOS PESSOAIS ===
    t.name AS nome,
    t.email,
    t.phone AS telefone,
    t.headline AS cargo_atual,
    t.company AS empresa_atual,
    t.location AS localizacao,
    t.linkedin_username,
    t.picture AS foto_url,

    -- === DADOS DA VAGA ===
    v.id AS vaga_id,
    v.name AS vaga_nome,
    v.area AS vaga_area,
    v.seniority AS vaga_senioridade,
    v.status AS vaga_status,
    v.salary_max AS vaga_salario_max,

    -- === CANDIDATURA ===
    c.status AS candidatura_status,
    c.source AS candidatura_origem,
    c.applied_at AS data_aplicacao,
    c.stage_name AS stage_atual,
    c.stage_order AS stage_ordem,
    c.phase_name AS phase_atual,
    c.phase_order AS phase_ordem,

    -- === REQUISIÇÃO ===
    r.id AS requisicao_id,
    r.status AS requisicao_status,
    r.reason AS requisicao_motivo,
    r.name AS requisicao_nome,
    r.description AS requisicao_descricao,

    -- === TIMELINE (ÚLTIMA MOVIMENTAÇÃO) ===
    (
        SELECT ct.changed_at
        FROM candidatura_timeline ct
        WHERE ct.candidatura_id = c.id
        ORDER BY ct.changed_at DESC
        LIMIT 1
    ) AS ultima_movimentacao_data,

    (
        SELECT ct.to_stage_name
        FROM candidatura_timeline ct
        WHERE ct.candidatura_id = c.id
        ORDER BY ct.changed_at DESC
        LIMIT 1
    ) AS ultima_movimentacao_stage,

    (
        SELECT ct.event_type
        FROM candidatura_timeline ct
        WHERE ct.candidatura_id = c.id
        ORDER BY ct.changed_at DESC
        LIMIT 1
    ) AS ultimo_evento_tipo,

    -- === CONTADORES ===
    (
        SELECT COUNT(*)
        FROM candidatura_timeline ct
        WHERE ct.candidatura_id = c.id
    ) AS total_movimentacoes,

    -- === DATAS ===
    c.created_at_inhire AS candidatura_criada_em,
    c.updated_at_inhire AS candidatura_atualizada_em,
    t.created_at_inhire AS talento_criado_em,

    -- === CÁLCULOS ===
    EXTRACT(DAY FROM NOW() - c.created_at_inhire) AS dias_no_processo,

    -- === TAGS/SKILLS DO CANDIDATO ===
    ARRAY_AGG(DISTINCT tt.name) FILTER (WHERE tt.name IS NOT NULL) AS skills,

    -- === CUSTOM FIELDS ===
    t.metadata AS dados_adicionais_json

FROM candidaturas c
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN requisicoes r ON v.id = r.vaga_id
LEFT JOIN talento_tags tt ON t.id = tt.talento_id
GROUP BY
    t.id, c.id, v.id, r.id
ORDER BY
    c.updated_at_inhire DESC;


-- ================================================================================
-- EXEMPLO DE USO: QUERIES PRONTAS PARA ANÁLISE
-- ================================================================================

-- Query 1: Candidatos ativos em entrevistas técnicas
-- ================================================================================
-- SELECT * FROM vw_candidatos_status_atual
-- WHERE candidatura_status = 'active'
--   AND kanban_stage_ordem >= 3
-- ORDER BY kanban_stage_ordem DESC, candidatura_atualizada_em DESC;


-- Query 2: Ver todo o histórico de movimentações de um candidato específico
-- ================================================================================
-- SELECT * FROM vw_candidatos_progressao_funil
-- WHERE candidato_nome ILIKE '%João Silva%'
-- ORDER BY evento_data;


-- Query 3: Vagas com melhor taxa de conversão
-- ================================================================================
-- SELECT * FROM vw_funil_conversao_vagas
-- WHERE vaga_status = 'OPEN'
-- ORDER BY taxa_conversao_contratacao_pct DESC
-- LIMIT 10;


-- Query 4: Candidatos que foram contratados nos últimos 30 dias
-- ================================================================================
-- SELECT
--     nome,
--     email,
--     vaga_nome,
--     data_aplicacao,
--     dias_no_processo
-- FROM vw_candidatos_completo
-- WHERE candidatura_status = 'hired'
--   AND candidatura_atualizada_em >= NOW() - INTERVAL '30 days'
-- ORDER BY candidatura_atualizada_em DESC;


-- Query 5: Tempo médio em cada stage do funil
-- ================================================================================
-- SELECT
--     to_stage_name AS stage,
--     COUNT(*) AS total_passagens,
--     ROUND(AVG(duration_days), 1) AS media_dias,
--     MIN(duration_days) AS minimo_dias,
--     MAX(duration_days) AS maximo_dias
-- FROM vw_candidatos_progressao_funil
-- WHERE duration_days IS NOT NULL
-- GROUP BY to_stage_name
-- ORDER BY to_stage_name;


-- ================================================================================
-- CAMPOS DISPONÍVEIS POR TABELA (RESUMO)
-- ================================================================================

-- TABELA: talentos (candidatos)
-- ================================
-- ✅ id, inhire_id
-- ✅ name, email, phone
-- ✅ headline (cargo), company, location
-- ✅ linkedin_username, picture
-- ✅ contact_method, contact_preference
-- ✅ metadata (JSON com custom fields)
-- ✅ created_at_inhire, updated_at_inhire
--
-- Relacionamentos:
-- - talentos → talento_tags (skills/habilidades)
-- - talentos → talento_arquivos (currículos)
-- - talentos → candidaturas (aplicações)

-- TABELA: candidaturas (aplicações)
-- ===================================
-- ✅ id, inhire_id
-- ✅ vaga_id, talento_id
-- ✅ status (active, hired, rejected, declined)
-- ✅ source (origem da candidatura)
-- ✅ stage_id, stage_name, stage_order (posição no Kanban)
-- ✅ phase_id, phase_name, phase_order (subfase no Kanban)
-- ✅ applied_at (data de aplicação)
-- ✅ created_at_inhire, updated_at_inhire
--
-- Relacionamentos:
-- - candidaturas → talentos
-- - candidaturas → vagas
-- - candidaturas → candidatura_timeline (histórico)

-- TABELA: candidatura_timeline (histórico Kanban)
-- ================================================
-- ✅ id, candidatura_id
-- ✅ event_type (tipo de evento)
-- ✅ changed_at (data da mudança)
-- ✅ from_stage_name, from_stage_order (de onde veio)
-- ✅ to_stage_name, to_stage_order (para onde foi)
-- ✅ from_phase_name, from_phase_order
-- ✅ to_phase_name, to_phase_order
-- ✅ changed_by_id, changed_by_name (quem moveu)
-- ✅ notes (observações)
-- ✅ duration_days (tempo no stage anterior)
--
-- Relacionamentos:
-- - candidatura_timeline → candidaturas

-- TABELA: requisicoes (aprovações)
-- ==================================
-- ✅ id, inhire_id
-- ✅ vaga_id, client_id
-- ✅ status (approved, pending, canceled, rejected)
-- ✅ reason (motivo)
-- ✅ name, description
-- ✅ positions (JSON com posições)
-- ✅ approval_workflow (JSON com fluxo de aprovação)
-- ✅ approvers (JSON com aprovadores)
-- ✅ salary_min, salary_max
-- ✅ user_id, user_name (criador)
-- ✅ status_updated_at
-- ✅ created_at_inhire, updated_at_inhire
--
-- Relacionamentos:
-- - requisicoes → vagas
-- - requisicoes → clientes

-- TABELA: vagas (jobs)
-- =====================
-- ✅ id, inhire_id
-- ✅ name, description
-- ✅ area, seniority, status
-- ✅ location, location_required
-- ✅ salary_max
-- ✅ open_positions (vagas abertas)
-- ✅ user_id, user_name (recrutador)
-- ✅ manager_id (gestor)
-- ✅ tenant_client_id (cliente)
-- ✅ created_at_inhire, updated_at_inhire
--
-- Relacionamentos:
-- - vagas → candidaturas
-- - vagas → posicoes
-- - vagas → requisicoes
-- - vagas → vaga_tags

-- ================================================================================
-- FIM DO SCRIPT
-- ================================================================================
--
-- Para executar as views:
-- 1. Execute este script completo no PostgreSQL
-- 2. As 4 views serão criadas automaticamente
-- 3. Use as queries de exemplo acima para começar a análise
--
-- Exportar para Power BI / Google Sheets:
-- - Conecte diretamente nas views criadas
-- - Use as queries de exemplo como base
--
-- ================================================================================
