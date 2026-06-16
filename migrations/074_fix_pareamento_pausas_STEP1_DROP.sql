/*
================================================================================
MIGRATION 074 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 074:
  Corrigir pareamento incorreto entre INICIO_PAUSA e FIM_PAUSA.

PROBLEMA IDENTIFICADO:
  - 3 posições AINDA com SLA negativo após Migration 073
  - Posições: 782, 914, 1274
  - Migration 073 deduplicou eventos no mesmo dia, mas...
  - ...múltiplos INICIO_PAUSA em dias DIFERENTES apontam para o MESMO FIM_PAUSA

ANÁLISE DOS DADOS (após Migration 073):

  Posição 782:
    - 3 períodos: 12/08→16/09 (26d), 21/08→16/09 (19d), 21/08→16/09 (19d)
    - Total: 64 dias pausados
    - Esperado: 1 período de ~26 dias

  Posição 914:
    - 5 períodos terminando em 14/07 ou 05/09
    - Total: 83 dias pausados
    - Esperado: 1-2 períodos reais

  Posição 1274:
    - 2 períodos: 05/06→27/06 (16d), 23/06→27/06 (5d)
    - Total: 21 dias pausados
    - Esperado: 1 período de ~16 dias

CAUSA RAIZ:
  CTE periodos_pausa usa MIN(fim.changed_at) WHERE fim > inicio.

  Se há:
    - INICIO 1: 12/08
    - INICIO 2: 21/08
    - FIM único: 16/09

  Ambos os INICIOs pegam o MESMO FIM (16/09), criando 2 períodos sobrepostos.

FALHA DA MIGRATION 073:
  DISTINCT ON (posicao_id, previous_status, new_status, DATE(changed_at))

  ↓ Mantém ambos os INICIOs porque estão em DIAS DIFERENTES (12/08 ≠ 21/08)

SOLUÇÃO (Migration 074):
  Pareamento 1:1 usando ROW_NUMBER():
  - INICIO nº1 → FIM nº1
  - INICIO nº2 → FIM nº2
  - ...

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
