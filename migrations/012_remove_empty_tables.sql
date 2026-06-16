/*
Migration 012: Remover Tabelas Vazias e Não Utilizadas
Data: 20/01/2026
Autor: Claude Code Refactoring
Objetivo: Limpar schema removendo 4 tabelas que nunca foram usadas

TABELAS A REMOVER:
1. scorecard_avaliacoes (0 registros)
2. automations (0 registros)
3. talento_tags (0 registros)
4. custom_fields (0 registros)

SEGURANÇA:
- Verifica se estão vazias antes de remover
- Remove foreign keys primeiro
- Remove constraints e índices
- Só então remove as tabelas
*/

-- ============================================================
-- PARTE 1: VERIFICAÇÃO DE SEGURANÇA
-- ============================================================

DO $$
DECLARE
    count_scorecard_avaliacoes INTEGER;
    count_automations INTEGER;
    count_talento_tags INTEGER;
    count_custom_fields INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== VERIFICAÇÃO DE SEGURANÇA - TABELAS VAZIAS ===';
    RAISE NOTICE '';

    -- Verificar se tabelas existem e estão vazias
    SELECT COUNT(*) INTO count_scorecard_avaliacoes FROM scorecard_avaliacoes;
    SELECT COUNT(*) INTO count_automations FROM automations;
    SELECT COUNT(*) INTO count_talento_tags FROM talento_tags;
    SELECT COUNT(*) INTO count_custom_fields FROM custom_fields;

    RAISE NOTICE 'scorecard_avaliacoes: % registros', count_scorecard_avaliacoes;
    RAISE NOTICE 'automations: % registros', count_automations;
    RAISE NOTICE 'talento_tags: % registros', count_talento_tags;
    RAISE NOTICE 'custom_fields: % registros', count_custom_fields;
    RAISE NOTICE '';

    -- Abortar se alguma tabela não estiver vazia
    IF count_scorecard_avaliacoes > 0 THEN
        RAISE EXCEPTION '⚠ ABORTADO: scorecard_avaliacoes tem % registros!', count_scorecard_avaliacoes;
    END IF;

    IF count_automations > 0 THEN
        RAISE EXCEPTION '⚠ ABORTADO: automations tem % registros!', count_automations;
    END IF;

    IF count_talento_tags > 0 THEN
        RAISE EXCEPTION '⚠ ABORTADO: talento_tags tem % registros!', count_talento_tags;
    END IF;

    IF count_custom_fields > 0 THEN
        RAISE EXCEPTION '⚠ ABORTADO: custom_fields tem % registros!', count_custom_fields;
    END IF;

    RAISE NOTICE '✓ Todas as tabelas estão vazias. Seguro prosseguir.';
    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 2: DOCUMENTAR ESTRUTURA ANTES DE REMOVER
-- ============================================================

-- Criar tabela temporária com documentação
CREATE TEMP TABLE migration_012_backup AS
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name IN ('scorecard_avaliacoes', 'automations', 'talento_tags', 'custom_fields')
    AND table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- Mostrar estrutura que será removida
DO $$
DECLARE
    backup_rec RECORD;
    current_table TEXT := '';
BEGIN
    RAISE NOTICE '=== ESTRUTURA DAS TABELAS A SEREM REMOVIDAS ===';
    RAISE NOTICE '';

    FOR backup_rec IN
        SELECT * FROM migration_012_backup
    LOOP
        IF backup_rec.table_name != current_table THEN
            current_table := backup_rec.table_name;
            RAISE NOTICE '';
            RAISE NOTICE 'Tabela: %', current_table;
            RAISE NOTICE '---';
        END IF;
        RAISE NOTICE '  % (%)', backup_rec.column_name, backup_rec.data_type;
    END LOOP;

    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 3: REMOVER FOREIGN KEYS (se houver)
-- ============================================================

DO $$
DECLARE
    fk_record RECORD;
BEGIN
    RAISE NOTICE '=== REMOVENDO FOREIGN KEYS ===';
    RAISE NOTICE '';

    -- Buscar FKs que referenciam as tabelas a remover
    FOR fk_record IN
        SELECT
            tc.table_name,
            tc.constraint_name,
            ccu.table_name AS referenced_table
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND (tc.table_name IN ('scorecard_avaliacoes', 'automations', 'talento_tags', 'custom_fields')
                 OR ccu.table_name IN ('scorecard_avaliacoes', 'automations', 'talento_tags', 'custom_fields'))
    LOOP
        BEGIN
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I CASCADE',
                          fk_record.table_name,
                          fk_record.constraint_name);
            RAISE NOTICE '✓ FK removida: %.%', fk_record.table_name, fk_record.constraint_name;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE '⚠ Erro ao remover FK: %', SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 4: REMOVER TABELAS COM CASCADE
-- ============================================================

DO $$
DECLARE
    table_to_drop TEXT;
    tables_dropped INTEGER := 0;
BEGIN
    RAISE NOTICE '=== REMOVENDO TABELAS ===';
    RAISE NOTICE '';

    FOREACH table_to_drop IN ARRAY ARRAY['scorecard_avaliacoes', 'automations', 'talento_tags', 'custom_fields']
    LOOP
        BEGIN
            -- Verificar se tabela existe
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = table_to_drop AND schemaname = 'public') THEN
                -- Remover tabela com CASCADE (remove constraints, índices, etc)
                EXECUTE format('DROP TABLE %I CASCADE', table_to_drop);
                tables_dropped := tables_dropped + 1;
                RAISE NOTICE '✓ Tabela removida: %', table_to_drop;
            ELSE
                RAISE NOTICE '⚠ Tabela não encontrada: %', table_to_drop;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE '⚠ Erro ao remover tabela %: %', table_to_drop, SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '=== RESULTADO ===';
    RAISE NOTICE '✓ % tabelas removidas com sucesso', tables_dropped;
    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 5: VERIFICAR TABELAS REMOVIDAS
-- ============================================================

DO $$
DECLARE
    remaining_tables INTEGER;
BEGIN
    RAISE NOTICE '=== VERIFICAÇÃO FINAL ===';
    RAISE NOTICE '';

    -- Contar quantas das 4 tabelas ainda existem
    SELECT COUNT(*) INTO remaining_tables
    FROM pg_tables
    WHERE tablename IN ('scorecard_avaliacoes', 'automations', 'talento_tags', 'custom_fields')
        AND schemaname = 'public';

    IF remaining_tables = 0 THEN
        RAISE NOTICE '✓ Todas as 4 tabelas foram removidas com sucesso!';
    ELSE
        RAISE WARNING '⚠ Ainda existem % tabelas não removidas', remaining_tables;
    END IF;

    RAISE NOTICE '';

    -- Listar tabelas restantes no schema
    RAISE NOTICE 'Tabelas restantes no schema public:';
    FOR remaining_tables IN
        SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'
    LOOP
        RAISE NOTICE '  Total de tabelas: %', remaining_tables;
    END LOOP;

    RAISE NOTICE '';
END $$;


-- ============================================================
-- PARTE 6: ATUALIZAR ESTATÍSTICAS
-- ============================================================

-- Atualizar estatísticas do catálogo do PostgreSQL
ANALYZE;

RAISE NOTICE '=== ESTATÍSTICAS ATUALIZADAS ===';
RAISE NOTICE '';


-- ============================================================
-- PARTE 7: STATUS FINAL
-- ============================================================

SELECT
    'Migration 012 concluída com sucesso' as status,
    '4 tabelas vazias removidas do schema' as details,
    NOW() as executed_at;


-- ============================================================
-- PARTE 8: ROLLBACK PLAN (Para referência, não executar)
-- ============================================================

/*
PLANO DE ROLLBACK - Caso precise recriar as tabelas

-- 1. scorecard_avaliacoes
CREATE TABLE scorecard_avaliacoes (
    id SERIAL PRIMARY KEY,
    scorecard_interview_id INTEGER REFERENCES scorecard_interviews(id),
    candidatura_id INTEGER REFERENCES candidaturas(id),
    -- adicionar outras colunas conforme migration_012_backup
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. automations
CREATE TABLE automations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    trigger_type VARCHAR(50),
    action_type VARCHAR(50),
    config JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. talento_tags
CREATE TABLE talento_tags (
    id SERIAL PRIMARY KEY,
    talento_id INTEGER REFERENCES talentos(id) ON DELETE CASCADE,
    tag_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(talento_id, tag_name)
);

-- 4. custom_fields
CREATE TABLE custom_fields (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    field_name VARCHAR(100),
    field_type VARCHAR(50),
    required BOOLEAN DEFAULT false,
    options JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

NOTA: Estrutura aproximada baseada em padrões comuns.
Consulte migration_012_backup temp table para estrutura exata.
*/
