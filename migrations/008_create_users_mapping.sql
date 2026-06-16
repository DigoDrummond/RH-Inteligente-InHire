-- Migration 008: Criar tabela de mapeamento UUID → Nome para Responsáveis e Recrutadores
-- Data: 09/01/2026
-- Objetivo: Permitir conversão de UUIDs em nomes legíveis na exportação

-- Criar tabela de usuários (mapeamento UUID → Nome)
CREATE TABLE IF NOT EXISTS users_mapping (
    id SERIAL PRIMARY KEY,
    user_uuid VARCHAR(100) UNIQUE NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    user_type VARCHAR(50), -- 'manager', 'recruiter', 'both'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_users_mapping_uuid ON users_mapping(user_uuid);
CREATE INDEX IF NOT EXISTS idx_users_mapping_name ON users_mapping(user_name);

-- Comentários
COMMENT ON TABLE users_mapping IS 'Mapeamento de UUIDs para nomes de usuários (Gestores e Recrutadores)';
COMMENT ON COLUMN users_mapping.user_uuid IS 'UUID do usuário no InHire';
COMMENT ON COLUMN users_mapping.user_name IS 'Nome completo do usuário';
COMMENT ON COLUMN users_mapping.user_type IS 'Tipo do usuário: manager, recruiter ou both';

SELECT 'Migration 008 executada - Tabela users_mapping criada' AS status;
