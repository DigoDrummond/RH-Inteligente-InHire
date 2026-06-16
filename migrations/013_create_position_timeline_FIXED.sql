/*
Migration 013: Criar Tabela position_timeline (VERSÃO CORRIGIDA)
Data: 20/01/2026
Autor: Claude Code Refactoring
Objetivo: Rastrear histórico de mudanças de status das posições

CORREÇÃO: Removida seção problemática de estatísticas com loop
*/

-- ============================================================
-- PARTE 1: VERIFICAÇÃO DE SEGURANÇA
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== MIGRATION 013: Criar Tabela position_timeline ===';
    RAISE NOTICE '';

    -- Verificar se tabela já existe
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'position_timeline' AND schemaname = 'public') THEN
        RAISE NOTICE 'Tabela position_timeline já existe. Abortando.';
        RAISE EXCEPTION 'Tabela position_timeline já existe';
    END IF;

    RAISE NOTICE 'Verificação de segurança concluída';
    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 2: CRIAR TABELA position_timeline
-- ============================================================

CREATE TABLE position_timeline (
    -- Identificação
    id SERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE,

    -- Relacionamentos
    posicao_id INTEGER NOT NULL REFERENCES posicoes(id) ON DELETE CASCADE,
    vaga_id INTEGER REFERENCES vagas(id) ON DELETE SET NULL,

    -- Informações do Evento
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP NOT NULL,

    -- Auditoria da Mudança
    changed_by VARCHAR(100),
    changed_by_name VARCHAR(255),
    reason TEXT,
    notes TEXT,

    -- Metadados
    metadata JSONB,

    -- Controle Interno
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_position_timeline_status_not_empty
        CHECK (new_status IS NOT NULL AND LENGTH(TRIM(new_status)) > 0),
    CONSTRAINT chk_position_timeline_changed_at_not_future
        CHECK (changed_at <= NOW() + INTERVAL '1 day')
);

COMMENT ON TABLE position_timeline IS 'Histórico de mudanças de status das posições';


-- ============================================================
-- PARTE 3: CRIAR ÍNDICES
-- ============================================================

CREATE INDEX idx_position_timeline_posicao ON position_timeline(posicao_id, changed_at DESC);
CREATE INDEX idx_position_timeline_vaga ON position_timeline(vaga_id, changed_at DESC) WHERE vaga_id IS NOT NULL;
CREATE INDEX idx_position_timeline_status ON position_timeline(new_status, changed_at DESC);
CREATE INDEX idx_position_timeline_changed_at ON position_timeline(changed_at DESC);
CREATE INDEX idx_position_timeline_composite ON position_timeline(posicao_id, new_status, changed_at DESC);
CREATE UNIQUE INDEX idx_position_timeline_unique_event ON position_timeline(posicao_id, changed_at, new_status) WHERE inhire_id IS NULL;


-- ============================================================
-- PARTE 4: POPULAR COM DADOS HISTÓRICOS
-- ============================================================

DO $$
DECLARE
    posicao_rec RECORD;
    eventos_criados INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Populando Dados Históricos ===';
    RAISE NOTICE '';

    -- Para cada posição, criar evento inicial
    FOR posicao_rec IN
        SELECT id, vaga_id, status, created_at, hired_at
        FROM posicoes
        ORDER BY id
    LOOP
        -- Evento de criação
        BEGIN
            INSERT INTO position_timeline (
                posicao_id, vaga_id, previous_status, new_status,
                changed_at, notes, created_at, updated_at
            ) VALUES (
                posicao_rec.id,
                posicao_rec.vaga_id,
                NULL,
                'open',
                posicao_rec.created_at,
                'Evento inicial gerado pela migration 013',
                NOW(),
                NOW()
            );
            eventos_criados := eventos_criados + 1;
        EXCEPTION WHEN unique_violation THEN
            NULL;
        END;

        -- Se posição foi preenchida, criar evento hired
        IF posicao_rec.hired_at IS NOT NULL AND posicao_rec.status = 'filled' THEN
            BEGIN
                INSERT INTO position_timeline (
                    posicao_id, vaga_id, previous_status, new_status,
                    changed_at, notes, created_at, updated_at
                ) VALUES (
                    posicao_rec.id,
                    posicao_rec.vaga_id,
                    'open',
                    'filled',
                    posicao_rec.hired_at,
                    'Evento de contratação gerado pela migration 013',
                    NOW(),
                    NOW()
                );
                eventos_criados := eventos_criados + 1;
            EXCEPTION WHEN unique_violation THEN
                NULL;
            END;
        END IF;
    END LOOP;

    RAISE NOTICE 'Eventos históricos criados: %', eventos_criados;
    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 5: TRIGGER PARA ATUALIZAR updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_position_timeline_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_position_timeline_updated_at
BEFORE UPDATE ON position_timeline
FOR EACH ROW
EXECUTE FUNCTION update_position_timeline_updated_at();


-- ============================================================
-- PARTE 6: ESTATÍSTICAS SIMPLES
-- ============================================================

DO $$
DECLARE
    total_eventos INTEGER;
    total_posicoes INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_eventos FROM position_timeline;
    SELECT COUNT(*) INTO total_posicoes FROM posicoes;

    RAISE NOTICE '';
    RAISE NOTICE '=== Estatísticas ===';
    RAISE NOTICE 'Total de eventos criados: %', total_eventos;
    RAISE NOTICE 'Total de posições: %', total_posicoes;
    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 7: VERIFICAÇÃO FINAL
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '=== VERIFICAÇÃO FINAL ===';

    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'position_timeline') THEN
        RAISE NOTICE 'Tabela position_timeline criada';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_position_timeline_posicao') THEN
        RAISE NOTICE 'Índices criados';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_position_timeline_updated_at') THEN
        RAISE NOTICE 'Trigger criado';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '=== MIGRATION 013 CONCLUÍDA ===';
    RAISE NOTICE '';
END $$;


-- Atualizar estatísticas
ANALYZE position_timeline;

-- Status final
SELECT
    'Migration 013 concluída' as status,
    COUNT(*) as eventos_criados,
    NOW() as executed_at
FROM position_timeline;
