-- Migration 016: Criar tabela custom_fields
-- Data: 2026-01-24
-- Descrição: Criação da tabela custom_fields caso não exista

BEGIN;

-- ========================================
-- CUSTOM FIELDS
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

CREATE INDEX IF NOT EXISTS idx_custom_field_inhire_id ON custom_fields(inhire_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_entity ON custom_fields(entity_type);
CREATE INDEX IF NOT EXISTS idx_custom_field_name ON custom_fields(field_name);
CREATE INDEX IF NOT EXISTS idx_custom_field_active ON custom_fields(is_active);
CREATE INDEX IF NOT EXISTS idx_custom_field_tenant ON custom_fields(tenant_id);

COMMENT ON TABLE custom_fields IS 'Definições de campos customizados';

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_custom_fields_updated_at ON custom_fields;
CREATE TRIGGER update_custom_fields_updated_at BEFORE UPDATE ON custom_fields
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

SELECT 'Migration 016 executada com sucesso!' as status;
