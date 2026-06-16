/*
================================================================================
MIGRATION 072 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 072:
  Corrigir pausas que continuam contando após cancelamento/fechamento da posição.

PROBLEMA IDENTIFICADO:
  - 5 posições com SLA negativo após Migration 071
  - Posições canceladas/fechadas mas pausas "Em andamento" até hoje
  - Exemplo: Posição 143 cancelada em 22/01 mas pausa conta até 03/03 (360 dias!)

CAUSA:
  CTE periodos_pausa usa CURRENT_DATE quando não há FIM_PAUSA,
  mas não verifica se posição foi encerrada.

SOLUÇÃO:
  Usar data de encerramento para posições canceled/closed sem FIM_PAUSA.

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
