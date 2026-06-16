-- Migration 004: Adicionar novas entidades descobertas nos testes de endpoints
-- Data: 25/11/2025
-- Descrição: Requisições, Scorecards, Form Responses, Tags, Automações, Clientes, Custom Fields

BEGIN;

-- ========================================
-- 1. REQUISIÇÕES
-- ========================================
CREATE TABLE IF NOT EXISTS requisicoes (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,
    vaga_id BIGINT REFERENCES vagas(id) ON DELETE SET NULL,

    -- IDs relacionados
    job_inhire_id VARCHAR(100),
    client_id VARCHAR(100),

    -- Dados principais
    status VARCHAR(50),
    reason TEXT,
    position_amount INTEGER,

    -- Responsáveis
    requester_id VARCHAR(100),
    requester_name VARCHAR(255),
    approver_id VARCHAR(100),
    approver_name VARCHAR(255),

    -- Dados adicionais
    custom_fields JSONB,

    -- Timing
    requested_at TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_requisicao_inhire_id ON requisicoes(inhire_id);
CREATE INDEX idx_requisicao_vaga ON requisicoes(vaga_id);
CREATE INDEX idx_requisicao_job_inhire ON requisicoes(job_inhire_id);
CREATE INDEX idx_requisicao_status ON requisicoes(status);
CREATE INDEX idx_requisicao_requester ON requisicoes(requester_id);

COMMENT ON TABLE requisicoes IS 'Requisições de vagas (processo de aprovação)';

-- ========================================
-- 2. SCORECARD INTERVIEWS (Templates)
-- ========================================
CREATE TABLE IF NOT EXISTS scorecard_interviews (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,

    -- Dados principais
    name VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100),

    -- Configuração
    questions JSONB,
    skill_categories JSONB,

    -- Responsável
    user_id VARCHAR(100),
    user_name VARCHAR(255),
    tenant_id VARCHAR(100),

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_scorecard_interview_inhire_id ON scorecard_interviews(inhire_id);
CREATE INDEX idx_scorecard_interview_type ON scorecard_interviews(type);
CREATE INDEX idx_scorecard_interview_tenant ON scorecard_interviews(tenant_id);

COMMENT ON TABLE scorecard_interviews IS 'Templates de entrevistas/scorecards';

-- ========================================
-- 3. SCORECARD JOBS
-- ========================================
CREATE TABLE IF NOT EXISTS scorecard_jobs (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,
    vaga_id BIGINT REFERENCES vagas(id) ON DELETE CASCADE,

    -- IDs relacionados
    job_inhire_id VARCHAR(100) NOT NULL,

    -- Configuração
    skill_categories JSONB,
    criteria JSONB,

    -- Responsável
    user_id VARCHAR(100),
    user_name VARCHAR(255),
    tenant_id VARCHAR(100),

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_scorecard_job_inhire_id ON scorecard_jobs(inhire_id);
CREATE INDEX idx_scorecard_job_vaga ON scorecard_jobs(vaga_id);
CREATE INDEX idx_scorecard_job_inhire ON scorecard_jobs(job_inhire_id);

COMMENT ON TABLE scorecard_jobs IS 'Scorecards configurados por vaga';

-- ========================================
-- 4. SCORECARD AVALIAÇÕES
-- ========================================
CREATE TABLE IF NOT EXISTS scorecard_avaliacoes (
    id BIGSERIAL PRIMARY KEY,
    candidatura_id BIGINT REFERENCES candidaturas(id) ON DELETE CASCADE NOT NULL,
    scorecard_interview_id BIGINT REFERENCES scorecard_interviews(id) ON DELETE SET NULL,

    -- IDs relacionados
    candidatura_inhire_id VARCHAR(200) NOT NULL,
    talent_inhire_id VARCHAR(100),
    interview_inhire_id VARCHAR(100),

    -- Avaliador
    evaluator_id VARCHAR(100),
    evaluator_name VARCHAR(255),

    -- Resultado
    overall_score DOUBLE PRECISION,
    recommendation VARCHAR(100),

    -- Detalhes
    responses JSONB,
    skill_scores JSONB,
    notes TEXT,

    -- Timing
    evaluated_at TIMESTAMP,

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_avaliacao_candidatura ON scorecard_avaliacoes(candidatura_id);
CREATE INDEX idx_avaliacao_candidatura_inhire ON scorecard_avaliacoes(candidatura_inhire_id);
CREATE INDEX idx_avaliacao_talent ON scorecard_avaliacoes(talent_inhire_id);
CREATE INDEX idx_avaliacao_evaluator ON scorecard_avaliacoes(evaluator_id);

COMMENT ON TABLE scorecard_avaliacoes IS 'Avaliações de candidatos (scorecards preenchidos)';

-- ========================================
-- 5. FORM RESPONSES
-- ========================================
CREATE TABLE IF NOT EXISTS form_responses (
    id BIGSERIAL PRIMARY KEY,
    candidatura_id BIGINT REFERENCES candidaturas(id) ON DELETE CASCADE NOT NULL,

    -- IDs relacionados
    candidatura_inhire_id VARCHAR(200) NOT NULL,
    talent_inhire_id VARCHAR(100),
    job_inhire_id VARCHAR(100),

    -- Tipo de formulário
    form_type VARCHAR(100),
    form_id VARCHAR(100),

    -- Respostas
    forms_answers JSONB,
    personality_answers JSONB,
    disc_interpretation JSONB,
    generic_form_responses JSONB,

    -- Metadados
    submitted_at TIMESTAMP,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_form_response_candidatura ON form_responses(candidatura_id);
CREATE INDEX idx_form_response_candidatura_inhire ON form_responses(candidatura_inhire_id);
CREATE INDEX idx_form_response_talent ON form_responses(talent_inhire_id);
CREATE INDEX idx_form_response_job ON form_responses(job_inhire_id);
CREATE INDEX idx_form_response_type ON form_responses(form_type);

COMMENT ON TABLE form_responses IS 'Respostas de formulários (DISC, personalidade, etc)';

-- ========================================
-- 6. VAGA TAGS
-- ========================================
CREATE TABLE IF NOT EXISTS vaga_tags (
    id BIGSERIAL PRIMARY KEY,
    vaga_id BIGINT REFERENCES vagas(id) ON DELETE CASCADE NOT NULL,

    -- Dados da tag
    tag_inhire_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    color VARCHAR(50),

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_vaga_tag_vaga ON vaga_tags(vaga_id);
CREATE INDEX idx_vaga_tag_name ON vaga_tags(name);
CREATE INDEX idx_vaga_tag_category ON vaga_tags(category);

COMMENT ON TABLE vaga_tags IS 'Tags/categorias de vagas';

-- ========================================
-- 7. AUTOMATIONS
-- ========================================
CREATE TABLE IF NOT EXISTS automations (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,

    -- Dados principais
    name VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100),

    -- Configuração
    trigger JSONB,
    conditions JSONB,
    actions JSONB,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Tenant
    tenant_id VARCHAR(100),

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_automation_inhire_id ON automations(inhire_id);
CREATE INDEX idx_automation_type ON automations(type);
CREATE INDEX idx_automation_active ON automations(is_active);
CREATE INDEX idx_automation_tenant ON automations(tenant_id);

COMMENT ON TABLE automations IS 'Automações/Workflows configurados';

-- ========================================
-- 8. CLIENTES
-- ========================================
CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,

    -- Dados principais
    name VARCHAR(500) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Endereço
    address TEXT,
    city VARCHAR(255),
    state VARCHAR(100),
    country VARCHAR(100),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Tenant
    tenant_id VARCHAR(100),

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_cliente_inhire_id ON clientes(inhire_id);
CREATE INDEX idx_cliente_name ON clientes(name);
CREATE INDEX idx_cliente_active ON clientes(is_active);
CREATE INDEX idx_cliente_tenant ON clientes(tenant_id);

COMMENT ON TABLE clientes IS 'Clientes do tenant (se multi-client)';

-- ========================================
-- 9. CUSTOM FIELDS
-- ========================================
CREATE TABLE IF NOT EXISTS custom_fields (
    id BIGSERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE NOT NULL,

    -- Dados principais
    entity_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_label VARCHAR(500),
    field_type VARCHAR(50),

    -- Configuração
    field_options JSONB,
    validation_rules JSONB,

    -- Status
    is_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Ordem
    display_order INTEGER,

    -- Tenant
    tenant_id VARCHAR(100),

    -- Auditoria
    created_at_inhire TIMESTAMP,
    updated_at_inhire TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_custom_field_inhire_id ON custom_fields(inhire_id);
CREATE INDEX idx_custom_field_entity ON custom_fields(entity_type);
CREATE INDEX idx_custom_field_name ON custom_fields(field_name);
CREATE INDEX idx_custom_field_active ON custom_fields(is_active);
CREATE INDEX idx_custom_field_tenant ON custom_fields(tenant_id);

COMMENT ON TABLE custom_fields IS 'Definições de campos customizados';

-- ========================================
-- FUNÇÕES DE TRIGGER (updated_at)
-- ========================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para todas as novas tabelas
CREATE TRIGGER update_requisicoes_updated_at BEFORE UPDATE ON requisicoes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scorecard_interviews_updated_at BEFORE UPDATE ON scorecard_interviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scorecard_jobs_updated_at BEFORE UPDATE ON scorecard_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scorecard_avaliacoes_updated_at BEFORE UPDATE ON scorecard_avaliacoes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_form_responses_updated_at BEFORE UPDATE ON form_responses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vaga_tags_updated_at BEFORE UPDATE ON vaga_tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automations_updated_at BEFORE UPDATE ON automations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clientes_updated_at BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_fields_updated_at BEFORE UPDATE ON custom_fields
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- VIEWS ÚTEIS
-- ========================================

-- View: Requisições com dados da vaga
CREATE OR REPLACE VIEW v_requisicoes_completas AS
SELECT
    r.*,
    v.name as vaga_name,
    v.status as vaga_status,
    v.area as vaga_area
FROM requisicoes r
LEFT JOIN vagas v ON r.vaga_id = v.id;

COMMENT ON VIEW v_requisicoes_completas IS 'Requisições com informações das vagas';

-- View: Scorecards com totais
CREATE OR REPLACE VIEW v_scorecard_stats AS
SELECT
    sj.job_inhire_id,
    v.name as vaga_name,
    COUNT(DISTINCT sa.id) as total_avaliacoes,
    AVG(sa.overall_score) as score_medio,
    COUNT(CASE WHEN sa.recommendation = 'approve' THEN 1 END) as aprovados,
    COUNT(CASE WHEN sa.recommendation = 'reject' THEN 1 END) as rejeitados
FROM scorecard_jobs sj
LEFT JOIN vagas v ON sj.vaga_id = v.id
LEFT JOIN scorecard_avaliacoes sa ON sa.candidatura_id IN (
    SELECT id FROM candidaturas WHERE vaga_id = sj.vaga_id
)
GROUP BY sj.job_inhire_id, v.name;

COMMENT ON VIEW v_scorecard_stats IS 'Estatísticas de scorecards por vaga';

-- View: Form responses por tipo
CREATE OR REPLACE VIEW v_form_response_stats AS
SELECT
    form_type,
    COUNT(*) as total_responses,
    COUNT(DISTINCT talent_inhire_id) as unique_talents,
    COUNT(DISTINCT job_inhire_id) as unique_jobs
FROM form_responses
GROUP BY form_type;

COMMENT ON VIEW v_form_response_stats IS 'Estatísticas de respostas de formulários por tipo';

COMMIT;

-- ========================================
-- VERIFICAÇÃO
-- ========================================
SELECT 'Migration 004 executada com sucesso!' as status;
SELECT 'Total de tabelas criadas: 9' as info;
SELECT 'Total de views criadas: 3' as info;
