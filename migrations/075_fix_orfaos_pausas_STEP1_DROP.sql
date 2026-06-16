/*
================================================================================
MIGRATION 075 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 075:
  Eliminar INICIOs órfãos que causam SLA negativo.

PROBLEMA IDENTIFICADO:
  - 3 posições AINDA com SLA negativo após Migration 074
  - Posições: 782, 914, 1274
  - Causa raiz: LEFT JOIN permite INICIOs sem FIM correspondente

ANÁLISE DA FALHA DA MIGRATION 074:

  Migration 074 usou LEFT JOIN:
    ```sql
    FROM eventos_pausa_numerados i
    LEFT JOIN eventos_pausa_numerados f
        ON f.rn = i.rn AND f.tipo_evento = 'FIM_PAUSA'
    ```

  Problema: Se há mais INICIOs que FINs:
    - INICIO #1 → FIM #1 (OK)
    - INICIO #2 → NULL (órfão!)
    - INICIO #3 → NULL (órfão!)

  Órfãos recebem data_fim = CURRENT_DATE via COALESCE:
    - INICIO 12/08/2025 sem FIM → 12/08 a HOJE (03/03/2026) = ~170 dias
    - Resultado: SLA negativo massivo

EXEMPLOS REAIS (hipótese confirmada):

  Posição 782: SLA = -28
    - Provável: 3 INICIOs, 1 FIM
    - 2 INICIOs órfãos inflam dias pausados

  Posição 914: SLA = -22
    - Provável: 5 INICIOs, 3 FINs
    - 2 INICIOs órfãos inflam dias pausados

  Posição 1274: SLA = -4
    - Provável: 2 INICIOs, 1 FIM
    - 1 INICIO órfão infla dias pausados

SOLUÇÃO (Migration 075):
  Trocar LEFT JOIN por INNER JOIN:
  - Aceita APENAS ciclos completos (INICIO → FIM)
  - Descarta INICIOs órfãos (sem FIM correspondente)
  - Trade-off: Pode subestimar dias pausados, mas GARANTE SLA correto

JUSTIFICATIVA:
  - INICIOs órfãos indicam dados desatualizados da API
  - Melhor ignorar pausas incompletas que gerar SLA negativo
  - Após sync completa da API, órfãos serão resolvidos naturalmente

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
