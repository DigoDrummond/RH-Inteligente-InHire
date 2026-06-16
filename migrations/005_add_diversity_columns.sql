-- Migration: Adicionar colunas de diversidade na tabela talentos
-- Data: 27/11/2025
-- Descrição: Extrair campos de diversidade do JSON attributes para colunas dedicadas
--            para facilitar queries de analytics e relatórios

-- ========================================
-- 1. Adicionar colunas de diversidade
-- ========================================

ALTER TABLE talentos
  ADD COLUMN IF NOT EXISTS diversity_black BOOLEAN DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS diversity_woman BOOLEAN DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS diversity_lgbt BOOLEAN DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS diversity_disability BOOLEAN DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS diversity_trans BOOLEAN DEFAULT NULL;

COMMENT ON COLUMN talentos.diversity_black IS 'Pessoa negra (extraído de attributes.diversityBlack)';
COMMENT ON COLUMN talentos.diversity_woman IS 'Mulher (extraído de attributes.diversityWoman)';
COMMENT ON COLUMN talentos.diversity_lgbt IS 'LGBT+ (extraído de attributes.diversityLgbt)';
COMMENT ON COLUMN talentos.diversity_disability IS 'Pessoa com deficiência (extraído de attributes.diversityDisability)';
COMMENT ON COLUMN talentos.diversity_trans IS 'Pessoa trans (extraído de attributes.diversityTrans)';

-- ========================================
-- 2. Popular colunas com dados existentes
-- ========================================

UPDATE talentos
SET
    diversity_black = CASE
        WHEN attributes::jsonb ? 'diversityBlack'
        THEN (attributes::jsonb->'diversityBlack'->0->>'value')::boolean
        ELSE NULL
    END,
    diversity_woman = CASE
        WHEN attributes::jsonb ? 'diversityWoman'
        THEN (attributes::jsonb->'diversityWoman'->0->>'value')::boolean
        ELSE NULL
    END,
    diversity_lgbt = CASE
        WHEN attributes::jsonb ? 'diversityLgbt'
        THEN (attributes::jsonb->'diversityLgbt'->0->>'value')::boolean
        ELSE NULL
    END,
    diversity_disability = CASE
        WHEN attributes::jsonb ? 'diversityDisability'
        THEN (attributes::jsonb->'diversityDisability'->0->>'value')::boolean
        ELSE NULL
    END,
    diversity_trans = CASE
        WHEN attributes::jsonb ? 'diversityTrans'
        THEN (attributes::jsonb->'diversityTrans'->0->>'value')::boolean
        ELSE NULL
    END
WHERE attributes IS NOT NULL;

-- ========================================
-- 3. Criar índices parciais (apenas valores true)
-- ========================================

CREATE INDEX IF NOT EXISTS idx_talento_diversity_black
  ON talentos(diversity_black)
  WHERE diversity_black = true;

CREATE INDEX IF NOT EXISTS idx_talento_diversity_woman
  ON talentos(diversity_woman)
  WHERE diversity_woman = true;

CREATE INDEX IF NOT EXISTS idx_talento_diversity_lgbt
  ON talentos(diversity_lgbt)
  WHERE diversity_lgbt = true;

CREATE INDEX IF NOT EXISTS idx_talento_diversity_disability
  ON talentos(diversity_disability)
  WHERE diversity_disability = true;

CREATE INDEX IF NOT EXISTS idx_talento_diversity_trans
  ON talentos(diversity_trans)
  WHERE diversity_trans = true;

-- ========================================
-- 4. Verificar resultados
-- ========================================

DO $$
DECLARE
    total_talentos INTEGER;
    count_black INTEGER;
    count_woman INTEGER;
    count_lgbt INTEGER;
    count_disability INTEGER;
    count_trans INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_talentos FROM talentos;
    SELECT COUNT(*) INTO count_black FROM talentos WHERE diversity_black = true;
    SELECT COUNT(*) INTO count_woman FROM talentos WHERE diversity_woman = true;
    SELECT COUNT(*) INTO count_lgbt FROM talentos WHERE diversity_lgbt = true;
    SELECT COUNT(*) INTO count_disability FROM talentos WHERE diversity_disability = true;
    SELECT COUNT(*) INTO count_trans FROM talentos WHERE diversity_trans = true;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION CONCLUÍDA COM SUCESSO';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total de talentos:           %', total_talentos;
    RAISE NOTICE 'Pessoas negras:              %', count_black;
    RAISE NOTICE 'Mulheres:                    %', count_woman;
    RAISE NOTICE 'LGBT+:                       %', count_lgbt;
    RAISE NOTICE 'Pessoas com deficiência:     %', count_disability;
    RAISE NOTICE 'Pessoas trans:               %', count_trans;
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
END $$;

-- ========================================
-- Rollback (se necessário)
-- ========================================
/*
DROP INDEX IF EXISTS idx_talento_diversity_black;
DROP INDEX IF EXISTS idx_talento_diversity_woman;
DROP INDEX IF EXISTS idx_talento_diversity_lgbt;
DROP INDEX IF EXISTS idx_talento_diversity_disability;
DROP INDEX IF EXISTS idx_talento_diversity_trans;

ALTER TABLE talentos
  DROP COLUMN IF EXISTS diversity_black,
  DROP COLUMN IF EXISTS diversity_woman,
  DROP COLUMN IF EXISTS diversity_lgbt,
  DROP COLUMN IF EXISTS diversity_disability,
  DROP COLUMN IF EXISTS diversity_trans;
*/
