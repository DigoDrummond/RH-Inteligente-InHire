/*
================================================================================
MIGRATION 077 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 077:
  Capturar pausas em andamento (órfãs) que não possuem evento de FIM_PAUSA.

PROBLEMA IDENTIFICADO:
  - Posição 589 está pausada há 121 dias (desde 03/11/2025)
  - Eventos de INICIO_PAUSA existem na timeline
  - NÃO existe evento de FIM_PAUSA (pausa ainda em andamento)
  - Migration 076 usa INNER JOIN que REJEITA pausas órfãs

IMPACTO DO PROBLEMA:
  - SLA pendência cliente = NULL (deveria ser ~121 dias)
  - SLA recrutamento = 135 (deveria ser ~14 dias)
  - Pausas em andamento não são contabilizadas

EXEMPLO (Posição 589):

  Status atual: paused
  Data pausa: 03/11/2025 16:55:07.499
  Eventos na timeline:
    - 2025-11-03: open → paused (ID 3685) ✅ INICIO_PAUSA
    - (sem evento de FIM_PAUSA) ❌

  SLA ATUAL (Migration 076):
    sla_geral: 135 dias
    sla_pendencia_cliente: NULL ← Pausa não contada (INNER JOIN rejeita órfão)
    sla_recrutamento: 135 dias ← Errado! Deveria subtrair a pausa
    num_ciclos_pausa: NULL

  SLA ESPERADO (Migration 077):
    sla_geral: 135 dias
    sla_pendencia_cliente: 121 dias (03/11/2025 até 04/03/2026)
    sla_recrutamento: 14 dias (135 - 121)
    num_ciclos_pausa: 1
    detalhamento_pausas: "Ciclo 1: 03/11/2025 até hoje (121 dias)"

SOLUÇÃO (Migration 077):
  Modificar CTE periodos_pausa para usar LEFT JOIN com fallback inteligente:

  ```sql
  periodos_pausa AS (
      SELECT
          i.posicao_id,
          i.changed_at AS data_inicio,
          COALESCE(
              f.changed_at,                    -- FIM explícito (se existe)
              (SELECT data de encerramento),   -- Fallback 1: closed/canceled
              CURRENT_DATE                     -- Fallback 2: ainda pausada
          ) AS data_fim
      FROM eventos_pausa_numerados i
      LEFT JOIN eventos_pausa_numerados f  -- ← INNER → LEFT (aceita órfãos)
          ON f.posicao_id = i.posicao_id
          AND f.tipo_evento = 'FIM_PAUSA'
          AND f.rn = i.rn
      WHERE i.tipo_evento = 'INICIO_PAUSA'
  )
  ```

COMPORTAMENTO POR CENÁRIO:

  1. Pausa com FIM explícito:
     - INICIO_PAUSA (10/01) → FIM_PAUSA (20/01)
     - data_fim = 20/01 ✅

  2. Pausa órfã + posição encerrada:
     - INICIO_PAUSA (10/01), sem FIM_PAUSA
     - Posição closed em 15/01
     - data_fim = 15/01 (usa closed_at) ✅

  3. Pausa órfã + posição ainda pausada:
     - INICIO_PAUSA (03/11/2025), sem FIM_PAUSA
     - Posição ainda em status paused
     - data_fim = CURRENT_DATE (04/03/2026) ✅

JUSTIFICATIVA:
  - Pausas em andamento são reais e devem ser contabilizadas
  - LEFT JOIN permite capturar INICIOs sem FIM
  - Fallback usa data de encerramento se posição foi fechada
  - Se ainda pausada, usa CURRENT_DATE (atualiza diariamente)
  - Comportamento similar à Migration 072, mas mais robusto

IMPACTO ESPERADO:
  - Posições com pausas em andamento terão SLA calculado corretamente
  - SLA de recrutamento refletirá tempo efetivo sem pausas
  - Métricas mais precisas para gestão

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
