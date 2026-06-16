/*
================================================================================
MIGRATION 076 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 076:
  Eliminar eventos fantasma com previous_status = NULL.

PROBLEMA IDENTIFICADO:
  - Posição 914 AINDA com SLA negativo após Migration 075
  - SLA recrutamento: -14 (sla_pendencia_cliente = 75 dias)
  - Causa: Eventos com previous_status = NULL sendo aceitos como INICIO_PAUSA

ANÁLISE DETALHADA (Posição 914):

  Total de 12 eventos na position_timeline:

  1. 13/06: NULL → paused (IDs 2330, 6364) ← FANTASMAS!
  2. 24/06: open → paused (ID 7752) ✅
  3. 24/06: paused → paused (ID 7753) ← Duplicata estranha
  4. 14/07: paused → open (IDs 2331, 6365) ✅
  5. 29/07: open → paused (IDs 2332, 6366) ✅
  6. 26/08: open → paused (ID 7754) ✅
  7. 26/08: NULL → paused (ID 7755) ← FANTASMA!
  8. 05/09: paused → canceled (IDs 2333, 6367) ✅

  Eventos fantasma identificados: 3 (IDs 2330, 6364, 7755)
  - Todos com previous_status = NULL
  - Classificados como INICIO_PAUSA pela lógica atual

LÓGICA ATUAL (Migration 075):
  ```sql
  WHEN (previous_status = 'open' OR previous_status IS NULL)
       AND new_status = 'paused'
      THEN 'INICIO_PAUSA'
  ```

  Problema: Aceita NULL como transição válida!

PAREAMENTO ATUAL (Migration 075):
  - Par 1: 13/06 (NULL→paused) → 14/07 (paused→open) = 22 dias ❌
  - Par 2: 24/06 (open→paused) → 05/09 (paused→canceled) = 53 dias ⚠️
  Total: 75 dias → SLA -14

SOLUÇÃO (Migration 076):
  Rejeitar previous_status = NULL:
  ```sql
  WHEN previous_status = 'open' AND new_status = 'paused'  ← Remove OR IS NULL
      THEN 'INICIO_PAUSA'
  ```

RESULTADO ESPERADO:
  - Par 1: 24/06 (open→paused) → 14/07 (paused→open) = 14 dias ✅
  - Par 2: 29/07 (open→paused) → 05/09 (paused→canceled) = 28 dias ✅
  Total: 42 dias → SLA positivo!

  Redução: 75 → 42 dias (-44%)

JUSTIFICATIVA:
  - Eventos com previous_status = NULL são sincronizações incorretas ou ajustes retroativos
  - Não representam transições reais de status
  - Causam inflação massiva de SLA
  - Melhor rejeitar que aceitar dados suspeitos

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
