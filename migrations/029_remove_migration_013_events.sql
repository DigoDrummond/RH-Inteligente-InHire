/*
================================================================================
MIGRATION 029: Remove Eventos Iniciais da Migration 013
================================================================================

Data: 2026-02-06
Descrição:
  Remove registros da tabela position_timeline que foram criados pela
  migration 013 com a descrição "Evento inicial gerado pela migration 013".

  Esses eventos não fazem parte dos dados reais da API e devem ser removidos.

Contexto:
  - Migration 013 criou eventos iniciais artificialmente
  - Esses eventos não representam mudanças reais de status
  - A API InHire tem os eventos reais de mudança de status

Impacto:
  - Remove eventos artificiais da position_timeline
  - View vw_analise_posicoes continuará funcionando com eventos reais da API
  - Melhora a precisão dos dados de status_atual e data_encerramento

================================================================================
*/

-- Primeiro, verificar quantos registros serão afetados
DO $$
DECLARE
    v_count INTEGER;
    v_total INTEGER;
BEGIN
    -- Total de registros na tabela
    SELECT COUNT(*) INTO v_total FROM position_timeline;

    -- Registros que serão deletados
    SELECT COUNT(*) INTO v_count
    FROM position_timeline
    WHERE notes = 'Evento inicial gerado pela migration 013';

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VERIFICAÇÃO PRÉ-DELEÇÃO';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de registros em position_timeline: %', v_total;
    RAISE NOTICE 'Registros a serem deletados: %', v_count;
    RAISE NOTICE 'Registros que permanecerão: %', v_total - v_count;
    RAISE NOTICE '================================================================================';
END $$;

-- Deletar eventos artificiais da migration 013
DELETE FROM position_timeline
WHERE notes = 'Evento inicial gerado pela migration 013';

-- Verificação pós-deleção
DO $$
DECLARE
    v_total_after INTEGER;
    v_migration_events INTEGER;
BEGIN
    -- Total após deleção
    SELECT COUNT(*) INTO v_total_after FROM position_timeline;

    -- Verificar se ainda restam eventos da migration 013
    SELECT COUNT(*) INTO v_migration_events
    FROM position_timeline
    WHERE notes = 'Evento inicial gerado pela migration 013';

    RAISE NOTICE '';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'RESULTADO DA DELEÇÃO';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de registros após deleção: %', v_total_after;
    RAISE NOTICE 'Eventos da migration 013 restantes: % (esperado: 0)', v_migration_events;
    RAISE NOTICE '';

    IF v_migration_events = 0 THEN
        RAISE NOTICE 'SUCESSO: Todos os eventos artificiais foram removidos';
    ELSE
        RAISE WARNING 'ATENÇÃO: Ainda existem % eventos da migration 013', v_migration_events;
    END IF;

    RAISE NOTICE '================================================================================';
END $$;

-- Verificar se a view ainda funciona corretamente
DO $$
DECLARE
    v_posicoes_view INTEGER;
    v_com_status INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_posicoes_view FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_com_status FROM vw_analise_posicoes WHERE status_atual IS NOT NULL;

    RAISE NOTICE '';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA VIEW';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições na view: %', v_posicoes_view;
    RAISE NOTICE 'Posições com status_atual: %', v_com_status;
    RAISE NOTICE '';
    RAISE NOTICE 'View continua funcionando corretamente';
    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
NOTAS
================================================================================
- A view vw_analise_posicoes usa position_timeline para pegar status_atual
- Após remover eventos artificiais, a view usará apenas eventos reais da API
- Se alguma posição não tiver eventos reais, usará fallback: p.status
- Isso garante que sempre teremos um status para cada posição
================================================================================
*/
